import queue
import graphics.layers as layers
import output.console as console
import output.console_gamification as console_gamification
import compiler.commands as commands
import graphics.screen_updater as screen_updater
import digital_twin.mqtt_adapter as mqtt_adapter
import digital_twin.secure_config as secure_config
import digital_twin.twin_identity as twin_identity
import digital_twin.translators as translators
from datetime import datetime

# Tiempo máximo de espera (ms) para establecer la conexión MQTT antes de
# informar de un fallo (respaldo del callback on_connect_fail de paho).
_CONNECT_TIMEOUT_MS = 8000


class RobotsController:

    def __init__(self, view):
        self.view = view
        self.console: console.Console = None
        self.robot_layer: layers.Layer = None
        self.consoleGamification = console_gamification.ConsoleGamification()
        self.compile_command = commands.Compile(self)
        self.setup_command = commands.Setup(self)
        self.loop_command = commands.Loop(self)
        self.executing = False
        self.board = False
        self.new = True
        self.twin_client = None
        # Estrategia de traducción del gemelo según el robot (la fija change_robot):
        # CarTranslator para los coches, ActuatorTranslator para el actuador, None si no
        # hay robot enlazable (placa Arduino).
        self.translator: translators.TwinTranslator = None
        self._twin_identity = twin_identity.TwinIdentity()
        self._twin_poll_id = None
        self._twin_connected = False
        self._twin_connect_watchdog = None
        # Control en vivo del actuador físico (jog) desde el simulador.
        self._twin_control_active = False  # True tras enviar "C O" (0,1)
        self._twin_jog_state = None        # último jog publicado: "3,0"/"3,1"/"4"
        self._twin_jog_last_ms = 0         # marca de tiempo del último envío (keepalive)

    def execute(self, option_gamification):
        if not self.board:
            screen_updater.layer = self.robot_layer
            screen_updater.view = self.view
            self.view.abort_after()
            self.robot_layer.execute()
            self.console.clear()
            if self.compile_command.execute():
                if self.setup_command.execute():
                    self.executing = True
                    self.drawing_loop()
        else:
            user_ast = self.compile_command.compile(self.get_code())
            if user_ast is not None:
                self.probe_robot(option_gamification)

    def drawing_loop(self):
        screen_updater.refresh()
        if not self.view.keys_used:
            self.loop_command.execute()
        self._twin_drive_loop()
        self.view.identifier = self.view.after(10, self.drawing_loop)

    def stop(self):
        self.executing = False
        self.compile_command.reboot()
        self.setup_command.reboot()
        self.loop_command.reboot()
        self.robot_layer.stop()
        self.view.abort_after()

    def zoom_in(self):
        self.robot_layer.zoom_in()
        self.view.change_zoom_label(self.robot_layer.drawing.zoom_percentage())

    def zoom_out(self):
        self.robot_layer.zoom_out()
        self.view.change_zoom_label(self.robot_layer.drawing.zoom_percentage())

    def configure_layer(self, drawing_canvas, hud_canvas):
        self.robot_layer.set_canvas(drawing_canvas, hud_canvas)
        self.view.change_zoom_label(self.robot_layer.drawing.zoom_percentage())

    def configure_console(self, text_component):
        self.console = console.Console(text_component)

    # ----------------------------------------------------- Gemelo digital MQTT
    def is_twin_active(self):
        """True si hay un cliente de gemelo digital creado (conectado o
        intentando conectar)."""
        return self.twin_client is not None

    def connect_twin(self, theme):
        """Inicia la conexión del gemelo digital con el theme dado.

        La conexión es **asíncrona** (no bloquea la GUI): el resultado llega
        después por la cola de eventos y se procesa en _handle_twin_event.
        """
        theme = (theme or "").strip()
        if self.twin_client is not None:
            self.disconnect_twin()
        if theme == "":
            self.console.write_output(
                "Gemelo digital: introduce un tema antes de conectar.\n")
            return
        try:
            host, port = secure_config.load_broker_config()
        except Exception as error:
            self.console.write_output(
                "Gemelo digital: no se pudo leer la configuración del broker ("
                + str(error) + ").\n")
            return
        client = mqtt_adapter.MQTTAdapter(
            theme, host, port, self._twin_identity)
        try:
            client.connect_async()
        except (ValueError, OSError) as error:
            self.console.write_output(
                "Gemelo digital: configuración de conexión inválida ("
                + str(error) + ").\n")
            return
        self.twin_client = client
        self._twin_connected = False
        self._twin_poll_id = self.view.after(50, self._poll_twin_inbox)
        self._twin_connect_watchdog = self.view.after(
            _CONNECT_TIMEOUT_MS, self._twin_connect_timeout)
        self.console.write_output(
            "Gemelo digital: conectando a " + str(host) + ":" + str(port)
            + " ...\n")
        self.view.on_twin_connected()

    def disconnect_twin(self):
        """Desconecta el gemelo digital (acción del usuario)."""
        self._teardown_twin(announce=True, release_control=True)

    def _teardown_twin(self, announce, release_control=False):
        """Detiene cliente, sondeo y watchdog. Si announce, informa en consola.

        Si ``release_control`` y el gemelo está conectado, publica primero la
        instrucción de soltar el control (``0,0``) para que el dispositivo
        físico vuelva a su modo autónomo en vez de quedarse congelado. Solo se
        hace en la desconexión iniciada por el usuario: en una caída inesperada
        o un fallo de conexión el socket ya no sirve y no tiene sentido esperar.
        """
        if self.twin_client is None:
            return
        self._cancel_twin_watchdog()
        if self._twin_poll_id is not None:
            self.view.after_cancel(self._twin_poll_id)
            self._twin_poll_id = None
        farewell = None
        if release_control and self._twin_connected and self.translator is not None:
            farewell = self.translator.control_off()
        try:
            self.twin_client.disconnect(farewell)
        except Exception:
            pass
        self.twin_client = None
        self._twin_connected = False
        self._twin_control_active = False
        self._twin_jog_state = None
        if self.translator is not None:
            self.translator.detach(self.robot_layer)
        if announce:
            self.console.write_output("Gemelo digital desconectado.\n")
        self.view.on_twin_disconnected()

    def _cancel_twin_watchdog(self):
        if self._twin_connect_watchdog is not None:
            self.view.after_cancel(self._twin_connect_watchdog)
            self._twin_connect_watchdog = None

    def _twin_connect_timeout(self):
        """Respaldo: si pasado el tiempo límite no hubo respuesta, falla."""
        self._twin_connect_watchdog = None
        if self.twin_client is not None and not self._twin_connected:
            self.console.write_output(
                "Gemelo digital: no se pudo conectar al broker (sin respuesta).\n")
            self._teardown_twin(announce=False)

    def publish_twin(self, text):
        """Publica texto en el tema del gemelo (hook para la capa de estado)."""
        if self.twin_client is not None:
            self.twin_client.publish_text(text)

    def send_twin_input(self, text):
        """Traduce la instrucción legible de la consola a su forma compacta y la
        publica por MQTT (botón "Twin").

        La traducción **solo entra en juego con el gemelo conectado**: si no hay
        conexión (CONNACK recibido) no se publica nada y se avisa en consola. Si la
        instrucción no es válida, se informa del error y tampoco se publica. En el eco
        se muestran ambas formas (legible -> compacta).
        """
        text = (text or "").strip()
        if not self._twin_connected:
            self.console.write_output(
                "Gemelo digital no conectado: no se puede publicar.\n")
            return
        if text == "":
            return
        if self.translator is None:
            self.console.write_output(
                "Gemelo digital: este robot no admite instrucciones.\n")
            return
        try:
            compact = self.translator.encode(text)
        except translators.TranslationError as error:
            self.console.write_output(
                "Instrucción no válida (" + str(error) + ").\n")
            return
        self.publish_twin(compact)
        # El control en vivo (jog) solo actúa tras ceder el control con "C O".
        if compact == "0,1":
            self._activate_twin_control()
        elif compact == "0,0":
            # Suelta el control: ALF vuelve a su modo autónomo y el simulador SIGUE
            # reflejándolo (modo pasivo). twin_external se mantiene; solo lo desactiva
            # la desconexión.
            self._twin_control_active = False
            self._twin_jog_state = None
        if compact in ("0,1", "0,0"):
            # Mantiene el botón Controlar/Soltar en sintonía si el control se
            # cambia desde la consola en vez de con el botón.
            self.view.on_twin_control_changed(self._twin_control_active)
        self.console.write_output(
            'Publicado en "' + self.twin_client.pub_topic + '": '
            + text + "  ->  " + compact + "\n")

    def is_twin_control_active(self):
        return self._twin_control_active

    def toggle_twin_control(self):
        """Botón Controlar/Soltar: toma (0,1) o suelta (0,0) el control en vivo del
        dispositivo físico, sin tener que escribir 'C O'/'C F' en la consola."""
        if not self._twin_connected:
            self.console.write_output(
                "Gemelo digital no conectado: no se puede controlar.\n")
            return
        if self.translator is None:
            self.console.write_output(
                "Gemelo digital: este robot no admite control.\n")
            return
        self._send_twin_control(not self._twin_control_active)

    def _send_twin_control(self, active):
        """Publica la trama de control y actualiza estado, consola y botón. Misma
        lógica que send_twin_input para 'C O'/'C F', reutilizable desde el botón."""
        compact = self.translator.control_on() if active else self.translator.control_off()
        self.publish_twin(compact)
        if active:
            self._activate_twin_control()
        else:
            self._twin_control_active = False
            self._twin_jog_state = None
        self.console.write_output(
            'Publicado en "' + self.twin_client.pub_topic + '": '
            + ("C O" if active else "C F") + "  ->  " + compact + "\n")
        self.view.on_twin_control_changed(self._twin_control_active)

    def _activate_twin_control(self):
        """Activa el control en vivo y delega en el traductor el anclaje específico del
        robot (p. ej. fijar el bloque del actuador al extremo motor)."""
        self._twin_control_active = True
        self._twin_jog_state = None
        if self.translator is not None:
            self.translator.on_control_activated(self.robot_layer)

    def _twin_drive_loop(self):
        """Conduce el robot físico en vivo: el traductor traduce la intención de
        movimiento del layer a jog continuo (3,<dir>) / parada (4) y se publica por MQTT.

        Solo con el gemelo conectado y el control activo ("C O" enviado). Publica solo al
        cambiar de estado, con un keepalive periódico mientras se mueve (no satura el canal
        ni hace eco en consola)."""
        if not (self._twin_connected and self._twin_control_active):
            return
        if self.translator is None:
            return
        desired = self.translator.drive_from_sim(self.robot_layer)
        if desired is None:
            return

        now = datetime.now().timestamp() * 1000.0
        moving = desired != "4"
        changed = desired != self._twin_jog_state
        keepalive = moving and (now - self._twin_jog_last_ms) >= 150
        if changed or keepalive:
            self.publish_twin(desired)
            self._twin_jog_state = desired
            self._twin_jog_last_ms = now

    def _apply_twin_position(self, text):
        """Refleja en el canvas el estado real reportado por el robot físico (lazo
        cerrado). Devuelve True si el mensaje era un reporte válido (se haya aplicado o
        no), para no duplicarlo como eco en consola.

        El traductor decodifica el reporte y lo aplica al layer. Solo se refleja si el
        robot está EN EJECUCIÓN: antes de pulsar "Ejecutar" sus piezas no están dibujadas
        en el canvas (move_image daría KeyError). No hace falta tener el control: basta
        con estar conectado y ejecutando.
        """
        if self.translator is None:
            return False
        fb = self.translator.decode(text)
        if fb is None:
            return False
        if self.executing:
            self.translator.apply_to_sim(self.robot_layer, fb)
        return True

    def _poll_twin_inbox(self):
        """Drena la cola de eventos MQTT en el hilo de Tk y se reprograma."""
        client = self.twin_client
        if client is None:
            return
        while True:
            try:
                event = client.events.get_nowait()
            except queue.Empty:
                break
            self._handle_twin_event(event)
        if self.twin_client is not None:
            self._twin_poll_id = self.view.after(50, self._poll_twin_inbox)

    def _handle_twin_event(self, event):
        """Traduce un evento de la cola MQTT a mensajes/efectos en la GUI."""
        kind = event[0]
        if kind == "connect":
            self._cancel_twin_watchdog()
            if event[1] == 0:
                self._twin_connected = True
                # Modo pasivo: con solo conectar, el simulador refleja la pose real del
                # robot físico (que puede moverse solo). El traductor suprime el
                # desplazamiento local para que el teclado no pelee con la pose reflejada.
                if self.translator is not None:
                    self.translator.attach(self.robot_layer)
                # Presencia: anuncia el simulador en su topic de salida para que el
                # broker lo registre como publicador del tema. El dispositivo lo
                # descarta sin procesarlo (ver TwinNode::reenvioMqtt).
                self.twin_client.publish_text(mqtt_adapter.HELLO)
                self.console.write_output(
                    "Gemelo digital conectado — pub: " + self.twin_client.pub_topic
                    + " · sub: " + self.twin_client.sub_topic + "\n")
                self.view.on_twin_connected()
            else:
                self.console.write_output(
                    "Gemelo digital: el broker rechazó la conexión (código "
                    + str(event[1]) + ").\n")
                self._teardown_twin(announce=False)
        elif kind == "connect_fail":
            if self.twin_client is not None and not self._twin_connected:
                self.console.write_output(
                    "Gemelo digital: no se pudo conectar al broker.\n")
                self._teardown_twin(announce=False)
        elif kind == "message":
            # Centinela de presencia del dispositivo: se descarta sin procesar ni
            # imprimir (solo sirve para registrar al publicador en el broker).
            if event[2] == mqtt_adapter.HELLO:
                return
            if self._apply_twin_position(event[2]):
                return
            self.console.write_output(
                'Mensaje recibido en el tema "' + event[1] + '": ' + event[2] + "\n")
        elif kind == "suback":
            if event[1] and self.twin_client is not None:
                self.console.write_output(
                    "Gemelo digital: el tema " + self.twin_client.sub_topic
                    + " ya está ocupado por otro cliente (whitelist).\n")
        elif kind == "disconnect":
            if event[1] != 0:
                self.console.write_output(
                    "Gemelo digital: conexión perdida (código "
                    + str(event[1]) + ").\n")
    # --------------------------------------------------- Fin Gemelo digital MQTT

    def change_robot(self, option):
        """
        Here you write the parts of the GUI that you want to show when a robot is chosen
        :param option: Selected robot (mobile: 0, 1, 2, linear, 3, Arduino: 4)
        :return: None
        """
        if self.robot_layer is not None:
            self.stop()
        # Mobile Robot, 2 infrared
        if option == 0:
            self.view.show_circuit_selector(True)
            self.view.show_gamification_option_selector(False)
            self.view.show_joystick(False)
            self.view.show_button_keys_movement(True)
            self.view.show_buttons_gamification(False)
            self.view.show_key_drawing(False)
            self.robot_layer = layers.MobileRobotLayer(2)
            self.board = False
            self.translator = translators.CarTranslator()
        # Mobile Robot, 3 infrared
        elif option == 1:
            self.view.show_circuit_selector(True)
            self.view.show_gamification_option_selector(False)
            self.view.show_joystick(False)
            self.view.show_button_keys_movement(True)
            self.view.show_buttons_gamification(False)
            self.view.show_key_drawing(False)
            self.robot_layer = layers.MobileRobotLayer(3)
            self.board = False
            self.translator = translators.CarTranslator()
        # Mobile Robot,  4 infrared
        elif option == 2:
            self.view.show_circuit_selector(True)
            self.view.show_gamification_option_selector(False)
            self.view.show_joystick(False)
            self.view.show_button_keys_movement(True)
            self.view.show_buttons_gamification(False)
            self.view.show_key_drawing(False)
            self.robot_layer = layers.MobileRobotLayer(4)
            self.board = False
            self.translator = translators.CarTranslator()
        # Linear Actuator
        elif option == 3:
            self.view.show_circuit_selector(False)
            self.view.show_gamification_option_selector(False)
            self.view.show_joystick(True)
            self.view.show_button_keys_movement(True)
            self.view.show_buttons_gamification(False)
            self.view.show_key_drawing(False)
            self.robot_layer = layers.LinearActuatorLayer()
            self.board = False
            self.translator = translators.ActuatorTranslator()
        # Option for the Arduino Board
        elif option == 4:
            self.view.show_circuit_selector(False)
            self.view.show_gamification_option_selector(True)
            self.view.show_joystick(False)
            self.view.show_button_keys_movement(False)
            self.view.show_buttons_gamification(True)
            self.view.show_key_drawing(False)
            self.robot_layer = layers.ArduinoBoardLayer()
            self.board = True
            self.translator = None


    def change_circuit(self, option):
        if self.robot_layer is not None:
            self.stop()
        if isinstance(self.robot_layer, layers.MobileRobotLayer):
            self.robot_layer.set_circuit(option)

    def send_input(self, text):
        self.console.input(text)

    def update_joystick(self, elem, value):
        if elem == "dx":
            self.robot_layer.robot.joystick.dx = value
        elif elem == "dy":
            self.robot_layer.robot.joystick.dy = value
        elif elem == "button":
            self.robot_layer.robot.joystick.value = value

    def filter_console(self, options):
        messages = []
        if options['info']:
            messages.append('info')
        if options['warning']:
            messages.append('warning')
        if options['error']:
            messages.append('error')
        self.console.filter_messages(messages)

    def get_pin_data(self):
        return self.robot_layer.robot.get_data()

    def save_pin_data(self, pin_data):
        robot = self.robot_layer.robot
        self.__detach_pins(robot, pin_data)
        self.__set_pins(robot, pin_data)
        if 'servo_left' in pin_data:
            robot.detach_servo_left()
            robot.set_servo_left(robot.parse_pin(pin_data['servo_left']))
        if 'servo_right' in pin_data:
            robot.detach_servo_right()
            robot.set_servo_right(robot.parse_pin(pin_data['servo_right']))
        if 'light_mleft' in pin_data:
            robot.detach_light_mleft()
            robot.set_light_mleft(robot.parse_pin(pin_data['light_mleft']))
        if 'light_left' in pin_data:
            robot.detach_light_left()
            robot.set_light_left(robot.parse_pin(pin_data['light_left']))
        if 'light_right' in pin_data:
            robot.detach_light_right()
            robot.set_light_right(robot.parse_pin(pin_data['light_right']))
        if 'light_mright' in pin_data:
            robot.detach_light_mright()
            robot.set_light_mright(robot.parse_pin(pin_data['light_mright']))
        if 'sound_trig' in pin_data:
            robot.detach_sound_trig()
            robot.set_sound_trig(robot.parse_pin(pin_data['sound_trig']))
        if 'sound_echo' in pin_data:
            robot.detach_sound_echo()
            robot.set_sound_echo(robot.parse_pin(pin_data['sound_echo']))
        if 'button_left' in pin_data:
            robot.detach_button_left()
            robot.set_button_left(robot.parse_pin(pin_data['button_left']))
        if 'button_right' in pin_data:
            robot.detach_button_right()
            robot.set_button_right(robot.parse_pin(pin_data['button_right']))
        if 'servo' in pin_data:
            robot.detach_servo()
            robot.set_servo(robot.parse_pin(pin_data['servo']))
        if 'button_joystick' in pin_data:
            robot.detach_joystick_button()
            robot.set_joystick_button(
                robot.parse_pin(pin_data['button_joystick']))
        if 'joystick_x' in pin_data:
            robot.detach_joystick_x()
            robot.set_joystick_x(robot.parse_pin(pin_data['joystick_x']))
        if 'joystick_y' in pin_data:
            robot.detach_joystick_y()
            robot.set_joystick_y(robot.parse_pin(pin_data['joystick_y']))

    def __detach_pins(self, robot, pin_data):
        """
        Detaches all the pins present in the data from the robot
        Arguments:
            robot: the instance of the robot being modified
            pin_data: the pin data to change
        """
        if 'servo_left' in pin_data:
            robot.detach_servo_left()
        if 'servo_right' in pin_data:
            robot.detach_servo_right()
        if 'light_mleft' in pin_data:
            robot.detach_light_mleft()
        if 'light_left' in pin_data:
            robot.detach_light_left()
        if 'light_right' in pin_data:
            robot.detach_light_right()
        if 'light_mright' in pin_data:
            robot.detach_light_mright()
        if 'sound_trig' in pin_data:
            robot.detach_sound_trig()
        if 'sound_echo' in pin_data:
            robot.detach_sound_echo()
        if 'button_left' in pin_data:
            robot.detach_button_left()
        if 'button_right' in pin_data:
            robot.detach_button_right()
        if 'servo' in pin_data:
            robot.detach_servo()
        if 'button_joystick' in pin_data:
            robot.detach_joystick_button()
        if 'joystick_x' in pin_data:
            robot.detach_joystick_x()
        if 'joystick_y' in pin_data:
            robot.detach_joystick_y()

    def __set_pins(self, robot, pin_data):
        """
        Sets attaches the corresponding robot pins
        Arguments:
            robot: the instance of the robot being modified
            pin_data: the pin data to change
        """
        if 'servo_left' in pin_data:
            robot.set_servo_left(pin_data['servo_left'])
        if 'servo_right' in pin_data:
            robot.set_servo_right(pin_data['servo_right'])
        if 'light_mleft' in pin_data:
            robot.set_light_mleft(pin_data['light_mleft'])
        if 'light_left' in pin_data:
            robot.set_light_left(pin_data['light_left'])
        if 'light_right' in pin_data:
            robot.set_light_right(pin_data['light_right'])
        if 'light_mright' in pin_data:
            robot.set_light_mright(pin_data['light_mright'])
        if 'sound_trig' in pin_data:
            robot.set_sound_trig(pin_data['sound_trig'])
        if 'sound_echo' in pin_data:
            robot.set_sound_echo(pin_data['sound_echo'])
        if 'button_left' in pin_data:
            robot.set_button_left(pin_data['button_left'])
        if 'button_right' in pin_data:
            robot.set_button_right(pin_data['button_right'])
        if 'servo' in pin_data:
            robot.set_servo(pin_data['servo'])
        if 'button_joystick' in pin_data:
            robot.set_joystick_button(pin_data['button_joystick'])
        if 'joystick_x' in pin_data:
            robot.set_joystick_x(pin_data['joystick_x'])
        if 'joystick_y' in pin_data:
            robot.set_joystick_y(pin_data['joystick_y'])

    def get_code(self):
        return self.view.get_code()

    def exit(self):
        self.console.logger.close_log()

    def show_tutorial(self):
        self.robot_layer.show_tutorial()

    def show_results(self):
        self.robot_layer.show_results()

    def show_help(self, option_gamification):
        self.robot_layer.show_help(option_gamification)

    def delete_elements(self):
        self.robot_layer.delete_elements()

    def probe_robot(self, option_gamification):
        self.new = False
        code, circuit = self.robot_layer.probe(option_gamification, self.get_code(),
                               self.robot_layer.get_robot_challenge(option_gamification).get_code())
        self.console.logger.write_log('info', "El usuario ha comprobado el desafío " + str(option_gamification+1))
        mensaje = "El usuario tiene los siguientes componentes: "
        for component in self.robot_layer.drawing.components:
            mensaje += component['element'].name
            mensaje += " "
        self.console.logger.write_log('info', mensaje)
        if code and circuit:
            log = "El usuario ha completado el desafío correctamente.\nLa puntuación del usuario es de " \
                  + str(self.robot_layer.drawing.points) + "\n\n"
            self.record_results(True, option_gamification)
        else:
            log = "El usuario ha comprobado el desafío.\n"
            if not code:
                log += "\tEl código introducido no es correcto (-1 punto)\n"
            if not circuit:
                log += "\tEl circuito creado no es correcto (-1 punto)\n"
            log += "\tPuntuación actual: " + str(self.robot_layer.drawing.points) + "\n\n"
        self.consoleGamification.write_encrypted(log, option_gamification+1)

    def record_results(self, correct, challenge):
        if not self.new:
            points = self.robot_layer.drawing.points
            date = datetime.now().strftime("%d-%m-%Y")
            if challenge == 0:
                return

            if correct:
                log = date + " - El usuario ha completado el desafío " + str(challenge) + " con una nota de: " \
                      + str(points) + "\n"
            else:
                log = date + " - El usuario ha abandonado el desafío " + str(challenge) + " cuando su nota era: " \
                      + str(points) + "\n"
            self.consoleGamification.write(log)

