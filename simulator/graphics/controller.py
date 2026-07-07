import threading
import time
import graphics.layers as layers
import output.console as console
import output.console_gamification as console_gamification
import compiler.commands as commands
import graphics.screen_updater as screen_updater
from datetime import datetime


class RobotsController:
    _ARM3D_RENDER_ACTIVE_MS = 16
    _ARM3D_RENDER_IDLE_MS = 33
    _ARM3D_RENDER_WAIT_MS = 50
    _ARM3D_PANEL_REFRESH_S = 1.0 / 30.0

    def __init__(self, view):
        self.view = view
        self.console: console.Console = None
        self.robot_layer: layers.Layer = None
        self.consoleGamification = console_gamification.ConsoleGamification()
        self.compile_command = commands.Compile(self)
        self.setup_command = commands.Setup(self)
        self.loop_command = commands.Loop(self)
        self.executing = False
        self.paused = False        # True cuando la ejecución está pausada (breakpoint o Pause)
        self.step_pending = False  # True cuando se ha pedido avanzar una sentencia
        self._breakpoints = set()  # Líneas Arduino con breakpoint activo
        self._loop_generation = 0  # Incrementa en cada execute(); invalida loops huérfanos
        self._sim_state = "idle"   # Estado actual del simulador para evitar notificaciones duplicadas
        self.board = False
        self.arm3d = False
        self.new = True
        self._last_arm3d_panel_refresh = 0.0
        self._arm3d_loop_running = False  # evita múltiples instancias del render loop

    def execute(self, option_gamification):
        if self.executing:
            return  # ignorar si ya hay una ejecución en curso
        if not self.board:
            screen_updater.layer = self.robot_layer
            screen_updater.view = self.view
            screen_updater.controller = self  # Para debug_line()
            self.view.abort_after()
            self.robot_layer.execute()
            self.console.clear()
            if self.compile_command.execute():
                if self.setup_command.execute():
                    self.executing = True
                    self._loop_generation += 1
                    self._notify_state("running")
                    self.drawing_loop(self._loop_generation)
        else:
            user_ast = self.compile_command.compile(self.get_code())
            if user_ast is not None:
                self.probe_robot(option_gamification)

    def drawing_loop(self, generation=None):
        current_generation = getattr(self, "_loop_generation", 0)
        if generation is None:
            generation = current_generation
        if generation != current_generation or not getattr(self, "executing", False):
            return  # iteración huérfana: otra ejecución tomó el control o se detuvo
        screen_updater.refresh()
        self._refresh_arm3d_control_panel()
        view = getattr(self, "view", None)
        if view is None:
            return
        if not getattr(view, "keys_used", False):
            # RF3.1.2/RF3.3.4: pausar la ejecución del sketch cuando la seguridad está bloqueada.
            safety_blocked = (
                getattr(self, "arm3d", False)
                and isinstance(getattr(self, "robot_layer", None), layers.Arm3DLayer)
                and getattr(self.robot_layer, "safety_blocked", False)
            )
            # RF4.2.2: no ejecutar loop() cuando la simulación está pausada (breakpoint o Pause).
            if not safety_blocked and not getattr(self, "paused", False):
                loop_command = getattr(self, "loop_command", None)
                if loop_command is not None:
                    loop_command.execute()
        if hasattr(view, "after"):
            view.identifier = view.after(16, lambda: self.drawing_loop(generation))

    def arm3d_render_loop(self):
        """Bucle de renderizado pasivo para el brazo 3D cuando no hay código ejecutándose."""
        # Si el brazo ya no está activo, terminar el loop y liberar el flag
        if not self.arm3d or not isinstance(self.robot_layer, layers.Arm3DLayer):
            self._arm3d_loop_running = False
            return
        if self.executing:
            # El drawing_loop ya renderiza; volver a comprobar en el próximo tick
            self.view.after(self._ARM3D_RENDER_WAIT_MS, self.arm3d_render_loop)
            return
        interval_ms = self._ARM3D_RENDER_IDLE_MS
        try:
            layer = self.robot_layer
            move_wasd = getattr(self.view, "move_WASD", {})
            layer.move(False, move_wasd)
            self._refresh_arm3d_control_panel()
            if any(move_wasd.values()) or layer.wants_fast_render():
                interval_ms = self._ARM3D_RENDER_ACTIVE_MS
        except Exception:
            pass
        self.view.after(interval_ms, self.arm3d_render_loop)

    def _refresh_arm3d_control_panel(self):
        view = getattr(self, "view", None)
        panel = getattr(view, "arm3d_control_panel", None)
        if panel is None:
            return
        if not self.arm3d or not isinstance(self.robot_layer, layers.Arm3DLayer):
            return
        now = time.monotonic()
        last_refresh = getattr(self, "_last_arm3d_panel_refresh", 0.0)
        if now - last_refresh < self._ARM3D_PANEL_REFRESH_S:
            return
        try:
            panel.refresh_from_model()
            self._last_arm3d_panel_refresh = now
        except Exception:
            pass

    def stop(self):
        self.executing = False
        self.paused = False
        self.step_pending = False
        self.compile_command.reboot()
        self.setup_command.reboot()
        self.loop_command.reboot()
        self.robot_layer.stop()
        self.view.abort_after()
        if hasattr(self.view, "editor_frame"):
            self.view.editor_frame.clear_exec_line()
        self._notify_state("idle")

    # ------------------------------------------------------------------
    # Control de depuración (RF4.2.2 / RF4.2.3)
    # ------------------------------------------------------------------

    def toggle_pause(self):
        """Alterna entre pausado y ejecutando (botón Pause/Play)."""
        if self.executing:
            self.paused = not self.paused
            if not self.paused:
                self.step_pending = False
                if hasattr(self.view, "editor_frame"):
                    self.view.editor_frame.clear_exec_line()
            self._notify_state("paused" if self.paused else "running")

    def step_once(self):
        """Ejecuta exactamente una sentencia más y vuelve a pausar (botón Step)."""
        if getattr(self, "executing", False) and getattr(self, "paused", False):
            # Limpiar el highlight inmediatamente: feedback visual de que el paso se registró
            view = getattr(self, "view", None)
            if view is not None and hasattr(view, "editor_frame"):
                view.editor_frame.clear_exec_line()
            self.step_pending = True
            self.paused = False  # Desbloquea el hilo; debug_line() volverá a pausar
            self._notify_state("running")


    # ------------------------------------------------------------------
    # Notificaciones de estado
    # ------------------------------------------------------------------

    _STATE_MESSAGES = {
        "running": "▶ Ejecutando sketch...\n",
        "paused":  "⏸ Simulación pausada.\n",
        "idle":    "■ Simulación detenida.\n",
    }

    def _notify_state(self, state: str):
        """Actualiza el badge visual y escribe en la consola del simulador."""
        view = getattr(self, "view", None)
        if threading.current_thread() is not threading.main_thread():
            if view is not None and hasattr(view, "after"):
                view.after(0, lambda: self._notify_state(state))
            return
        changed = state != getattr(self, "_sim_state", None)
        self._sim_state = state
        if view is not None and hasattr(view, "button_bar"):
            view.button_bar.update_state(state)
        # Solo escribir mensaje en consola cuando hay transición real de estado
        console_obj = getattr(self, "console", None)
        if changed and console_obj and state in self._STATE_MESSAGES:
            console_obj.write_output(self._STATE_MESSAGES[state])

    def set_breakpoints(self, lines):
        """Establece el conjunto de líneas Arduino con breakpoint activo."""
        self._breakpoints = set(lines)

    def toggle_breakpoint(self, line_no: int):
        """Añade o quita un breakpoint en la línea dada."""
        if line_no in self._breakpoints:
            self._breakpoints.discard(line_no)
        else:
            self._breakpoints.add(line_no)

    def debug_should_pause_at_line(self, line_no):
        """Consultado por screen_updater.debug_line(). Devuelve True si hay que pausar."""
        if getattr(self, "paused", False):
            return True
        breakpoints = getattr(self, "_breakpoints", set())
        if line_no in breakpoints or getattr(self, "step_pending", False):
            self.step_pending = False
            self.paused = True
            self._notify_state("paused")
            return True
        return False

    def zoom_in(self):
        self.robot_layer.zoom_in()
        self.view.change_zoom_label(self.robot_layer.drawing.zoom_percentage())

    def zoom_out(self):
        self.robot_layer.zoom_out()
        self.view.change_zoom_label(self.robot_layer.drawing.zoom_percentage())

    def configure_layer(self, drawing_canvas, hud_canvas):
        self.robot_layer.set_canvas(drawing_canvas, hud_canvas)
        self.view.change_zoom_label(self.robot_layer.drawing.zoom_percentage())
        if self.arm3d and isinstance(self.robot_layer, layers.Arm3DLayer):
            if not self._arm3d_loop_running:
                self._arm3d_loop_running = True
                self.view.after(self._ARM3D_RENDER_IDLE_MS, self.arm3d_render_loop)

    def configure_console(self, text_component):
        self.console = console.Console(text_component)

    def change_robot(self, option):
        """
        Here you write the parts of the GUI that you want to show when a robot is chosen
        :param option: Selected robot (mobile: 0, 1, 2, linear, 3, Arduino: 4)
        :return: None
        """
        if self.robot_layer is not None:
            self.stop()
        self.arm3d = False
        self._arm3d_loop_running = False
        # Mobile Robot, 2 infrared
        if option == 0:
            self.view.show_circuit_selector(True)
            self.view.show_gamification_option_selector(False)
            self.view.show_joystick(False)
            self.view.show_button_keys_movement(True)
            self.view.show_buttons_gamification(False)
            self.view.show_key_drawing(False)
            self.view.show_arm3d_panel(False)
            self.view.keys_used = True
            self.robot_layer = layers.MobileRobotLayer(2)
            self.board = False
        # Mobile Robot, 3 infrared
        elif option == 1:
            self.view.show_circuit_selector(True)
            self.view.show_gamification_option_selector(False)
            self.view.show_joystick(False)
            self.view.show_button_keys_movement(True)
            self.view.show_buttons_gamification(False)
            self.view.show_key_drawing(False)
            self.view.show_arm3d_panel(False)
            self.view.keys_used = True
            self.robot_layer = layers.MobileRobotLayer(3)
            self.board = False
        # Mobile Robot,  4 infrared
        elif option == 2:
            self.view.show_circuit_selector(True)
            self.view.show_gamification_option_selector(False)
            self.view.show_joystick(False)
            self.view.show_button_keys_movement(True)
            self.view.show_buttons_gamification(False)
            self.view.show_key_drawing(False)
            self.view.show_arm3d_panel(False)
            self.view.keys_used = True
            self.robot_layer = layers.MobileRobotLayer(4)
            self.board = False
        # Linear Actuator
        elif option == 3:
            self.view.show_circuit_selector(False)
            self.view.show_gamification_option_selector(False)
            self.view.show_joystick(True)
            self.view.show_button_keys_movement(True)
            self.view.show_buttons_gamification(False)
            self.view.show_key_drawing(False)
            self.view.show_arm3d_panel(False)
            self.view.keys_used = True
            self.robot_layer = layers.LinearActuatorLayer()
            self.board = False
        # Option for the Arduino Board
        elif option == 4:
            self.view.show_circuit_selector(False)
            self.view.show_gamification_option_selector(True)
            self.view.show_joystick(False)
            self.view.show_button_keys_movement(False)
            self.view.show_buttons_gamification(True)
            self.view.show_key_drawing(False)
            self.view.show_arm3d_panel(False)
            self.robot_layer = layers.ArduinoBoardLayer()
            self.board = True
        # Brazo robótico 3D (Braccio)
        elif option == 5:
            self.view.show_circuit_selector(False)
            self.view.show_gamification_option_selector(False)
            self.view.show_joystick(False)
            self.view.show_button_keys_movement(False)
            self.view.show_buttons_gamification(False)
            self.view.show_key_drawing(False)
            self.view.show_arm3d_panel(True)
            # El Arm3D no usa teclado para mover el robot: el sketch debe
            # ejecutarse siempre. keys_used=False desbloquea drawing_loop.
            self.view.keys_used = False
            self.robot_layer = layers.Arm3DLayer()
            self.board = False
            self.arm3d = True

    def update_arm3d_joint(self, joint_idx, angle):
        """Actualiza el ángulo articular del brazo 3D (llamado desde la GUI)."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.set_joint_angle(joint_idx, angle)

    def solve_arm3d_ik(self, x, y, z):
        """Lanza la cinemática inversa del brazo 3D."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            return self.robot_layer.solve_ik(x, y, z)
        return False, "No hay brazo 3D activo"

    def drag_arm3d_camera(self, dx, dy, pan=False):
        """Arrastra la cámara del brazo 3D."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.drag_camera(dx, dy, pan=pan)

    def dolly_arm3d_camera(self, dy):
        """Acerca o aleja la cámara del brazo 3D con arrastre."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.dolly_camera(dy)
            self.view.change_zoom_label(self.robot_layer.drawing.zoom_percentage())

    def reset_arm3d_camera(self):
        """Resetea la cámara del brazo 3D."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.reset_camera()

    def toggle_arm3d_trail(self, show):
        """Activa o desactiva la trayectoria del brazo 3D."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.motor3d.set_show_trail(show)

    def toggle_arm3d_joint_ranges(self, show):
        """Activa o desactiva los arcos de rango articular del brazo 3D."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.motor3d.set_show_joint_ranges(show)

    def toggle_arm3d_joint_axes(self, show):
        """Activa o desactiva los ejes XYZ locales de cada articulación del brazo 3D."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.motor3d.set_show_joint_axes(show)

    def toggle_arm3d_fps_counter(self, show):
        """Activa o desactiva el contador FPS del visor 3D."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.set_fps_counter(show)

    def set_arm3d_camera_view(self, view_name):
        """Aplica un preset de cámara 3D: 'caballera', 'isometrica' o libre."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.set_camera_view(view_name)

    def unlock_arm3d_camera_view(self):
        """Vuelve a vista libre sin reiniciar la cámara actual."""
        if isinstance(self.robot_layer, layers.Arm3DLayer):
            self.robot_layer.unlock_camera_view()
            self.view.change_zoom_label(self.robot_layer.drawing.zoom_percentage())

    def open_arm3d_config(self):
        """Abre la ventana de configuración del brazo 3D (delegado a la vista)."""
        if hasattr(self.view, 'open_arm3d_configuration'):
            self.view.open_arm3d_configuration()

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

