import graphics.drawing as drawing
import graphics.robot_drawings as robot_drawings
import graphics.huds as huds
import robot_components.robots as robots
import files.files_reader as filesr


class Layer:

    def __init__(self):
        """
        Constructor for superclass layer
        """
        self.drawing = drawing.Drawing()
        self.is_drawing = False
        self.hud = None
        self.robot = None
        self.robot_drawing: robot_drawings.RobotDrawing = None
        self._zoom_percentage()
        self.is_drawing = False
        self.is_board = False

        self.rdr = filesr.RobotDataReader()

    def execute(self):
        """
        Executes the code, showing what the robot will do on the canvas
        """
        self._drawing_config()
        self.robot_drawing.draw()
        self.is_drawing = True

    def stop(self):
        """
        Stops all the executing code and clears the canvas
        """
        self.drawing.empty_drawing()
        self.hud.reboot()
        self.is_drawing = False

    def zoom_in(self):
        """
        Broadens the drawing
        """
        self.drawing.zoom_in()
        self._zoom_config()

    def zoom_out(self):
        """
        Unbroads the drawing
        """
        self.drawing.zoom_out()
        self._zoom_config()

    def move(self, using_keys, move_WASD):
        """
        Moves the robot that is being used
        Arguments:
            using_keys: specifies keys are being used for movement (True)
            or not (False)
            move_WASD: a map that specifies if any of the keys WASD is being
            pressed
        """
        pass

    def set_canvas(self, canvas, hud_canvas):
        """
        Sets the canvas that the drawing and will use
        Arguments:
            canvas: the canvas of the drawing
            hud_canvas: the canvas of the hud
        """
        self.drawing.set_canvas(canvas)
        self.drawing.set_size(self.robot_drawing.drawing_width,
                              self.robot_drawing.drawing_height)
        self.hud.set_canvas(hud_canvas)

    def _zoom_config(self):
        """
        Configures the zoom in case when it changes
        """
        self._zoom_percentage()
        if self.is_drawing:
            self._zoom_redraw()

    def _zoom_redraw(self):
        """
        Once the zoom changes, use this method for redrawing everything
        up to scale
        """
        self.drawing.delete_zoomables()
        self._draw_before_robot()
        self.robot_drawing.draw()
        self._draw_after_robot()

    def _draw_before_robot(self):
        pass

    def _draw_after_robot(self):
        pass

    def _zoom_percentage(self):
        """
        Updates the percentage of zoom that is being used currently
        """
        self.zoom_percent = self.drawing.zoom_percentage()

    def _drawing_config(self):
        """
        Method used to configure the drawing before executing
        """
        self.drawing.empty_drawing()

    def delete_elements(self):
        self.drawing.components.clear()
        self.drawing.empty_drawing()
        self.robot.reset()
        self.robot_drawing.draw()
        self.drawing.draw_buttons(self.robot, 500.0, 500.0)
        self.robot.board.pines = []


class MobileRobotLayer(Layer):

    # Side of the (square) world used by the infinite circuit. Big enough to
    # feel limitless during a session; the camera keeps the robot centred.
    INFINITE_SIZE = 200000

    def __init__(self, n_light_sens):
        """
        Constructor for MobileRobotLayer
        Arguments:
            n_light_sens: the number of light sensors
        """
        super().__init__()
        self.hud = huds.MobileHUD()
        self.robot_data = self.rdr.parse_robot(n_light_sens - 2)
        self.robot = robots.MobileRobot(n_light_sens, self.robot_data)
        self.robot_drawing = robot_drawings.MobileRobotDrawing(
            self.drawing, n_light_sens)

        self.n_sens = n_light_sens

        self.is_rotating = False
        self.is_moving = False
        self.circuit = None
        self.obstacle = None
        # Última intención de movimiento (px/tick de avance y grados/tick de giro). La lee
        # el controller para conducir el coche físico en vivo (jog) bajo control del gemelo.
        self.last_v = 0
        self.last_da = 0
        # Bajo control del gemelo (lazo cerrado), la pose la fija el coche físico vía
        # mensajes "5,<der>,<izq>"; el desplazamiento local del teclado se suprime.
        self.twin_external = False
        # Infinite circuit: free unbounded plane with a trail behind the robot
        self.infinite = False
        self.trail = None
        # Last camera scroll offset (canvas px); None = not positioned yet
        self._cam_x = None
        self._cam_y = None

    def move(self, using_keys, move_WASD):
        """
        Move method of the layer. Moves the robot and rotates it
        """
        v = 0  # Velocity
        da = 0  # Angle
        if using_keys:
            v, da = self.__move_keys(move_WASD)
        else:
            v, da = self.__move_code()

        # Se conserva la intención (la lee el controller para el jog del gemelo) aunque
        # bajo control externo no se mueva el robot en local.
        self.last_v = v
        self.last_da = da
        if self.twin_external:
            # Bajo control del gemelo la pose la dicta el coche físico (feedback
            # "5,<der>,<izq>", aplicado por el traductor); se suprime el movimiento local.
            return

        future_p = self.robot_drawing.predict_movement(v)
        hit_border = (
                future_p[0] <= self.robot_drawing.width / 2
                or future_p[0] >= self.robot_drawing.drawing_width - self.robot_drawing.width / 2
                or future_p[1] <= self.robot_drawing.height / 2
                or future_p[1] >= self.robot_drawing.drawing_height - self.robot_drawing.height / 2
        )
        # On the infinite circuit there are no borders nor obstacles to block
        if (
                v == 0
                or (not self.infinite
                    and (hit_border
                         or self.__check_obstacle_collision(future_p[0], future_p[1])))
        ):
            v = 0
            self.is_moving = False
        # Move or rotate
        if not self.is_rotating:
            self.robot_drawing.move(v)
        if not self.is_moving:
            self.robot_drawing.change_angle(da)
        self.__hud_velocity()

        # Overlapping check
        if self.circuit is not None:
            self.__check_circuit_overlap()
        if self.obstacle is not None:
            self.__detect_obstacle()

        # Infinite circuit: extend the trail and keep the camera on the robot
        if self.infinite and self.trail is not None:
            self.trail.add_point(self.robot_drawing.x, self.robot_drawing.y)
            self.__follow_camera()

    # ------------------------------------------------- Gemelo digital (reflejo)
    def apply_twin_move(self, v, da):
        """Aplica al dibujo un avance ``v`` (px) y/o giro ``da`` (grados) reflejados del
        coche físico, RESPETANDO los bordes del mundo y los obstáculos igual que el control
        local: si el avance chocaría, se anula (el coche del sim no atraviesa la pared ni el
        obstáculo, aunque el coche real siga). Lo llama ``CarTranslator.apply_to_sim``.
        """
        if v != 0:
            future_p = self.robot_drawing.predict_movement(v)
            hit_border = (
                    future_p[0] <= self.robot_drawing.width / 2
                    or future_p[0] >= self.robot_drawing.drawing_width - self.robot_drawing.width / 2
                    or future_p[1] <= self.robot_drawing.height / 2
                    or future_p[1] >= self.robot_drawing.drawing_height - self.robot_drawing.height / 2
            )
            # En el circuito infinito no hay bordes ni obstáculos que bloqueen.
            if not self.infinite and (
                    hit_border
                    or self.__check_obstacle_collision(future_p[0], future_p[1])):
                v = 0
            self.robot_drawing.move(v)
        if da != 0:
            self.robot_drawing.change_angle(da)
        self.__hud_velocity()

        if self.circuit is not None:
            self.__check_circuit_overlap()
        if self.obstacle is not None:
            self.__detect_obstacle()
        if self.infinite and self.trail is not None:
            self.trail.add_point(self.robot_drawing.x, self.robot_drawing.y)
            self.__follow_camera()

    def apply_twin_sensors(self, ir_values, dist_cm):
        """Refleja en el canvas los sensores REALES del coche físico (modo pasivo del gemelo).

        Lo llama ``CarTranslator.apply_to_sim`` al recibir la trama ``7,...``. Reusa los mismos
        efectos que la detección virtual (``__check_circuit_overlap`` / ``__detect_obstacle``)
        pero con los valores del robot físico en vez de los del circuito simulado.

        Arguments:
            ir_values: secuencia de 0/1 de los IR en orden físico izquierda->derecha
                (1 = oscuro / sobre la línea). Se mapea posicionalmente a los sensores de luz
                del dibujo; si el robot del sim tiene menos sensores, sobran los últimos IR.
            dist_cm: distancia del ultrasonido en cm, o None si no hay eco.
        """
        light_sensors = self.robot_drawing.sensors["light"]
        measurements = []
        values = []
        for sens, raw in zip(light_sensors, ir_values):
            if raw:
                sens.dark()
                measurements.append(True)
                values.append(1)
            else:
                sens.light()
                measurements.append(False)
                values.append(0)
        if measurements:
            self.robot.set_light_sens_value(values)
            self.robot_drawing.repaint_light_sensors()
            self.hud.set_circuit(measurements)

        detecting = dist_cm is not None and dist_cm >= 0
        self.robot_drawing.sensors["sound"].set_detect(detecting)
        self.robot.sound.value = 1 if detecting else 0
        self.robot.sound.dist = dist_cm if detecting else -1
        self.hud.set_detect_obstacle([dist_cm if detecting else -1], unit="cm")
    # ----------------------------------------------- Fin Gemelo digital (reflejo)

    def set_circuit(self, circuit_opt):
        """
        Changes the circuit
        Arguments:
            circuit_opt: the number of the chosen circuit
        """
        circuit_name = self.__parse_circuit_opt(circuit_opt)
        if circuit_name == "infinite":
            self.__set_infinite_circuit()
            return
        self.infinite = False
        self.trail = None
        map_tuple = self.rdr.parse_circuit(circuit_name)
        straights = map_tuple[0]
        obstacles = map_tuple[1]
        self.circuit = robot_drawings.Circuit(straights, self.drawing)
        self.obstacle = None
        if len(obstacles) > 0:
            self.obstacle = robot_drawings.Obstacle(obstacles[0], self.drawing)
        self.reset_robot()

    def __set_infinite_circuit(self):
        """
        Configures the infinite circuit: an unbounded empty plane where the
        robot is driven freely, the camera follows it and it leaves a trail.
        """
        self.infinite = True
        self.circuit = None
        self.obstacle = None
        self._cam_x = None
        self._cam_y = None
        self.reset_robot(infinite=True)
        self.trail = robot_drawings.Trail(self.drawing)

    def reset_robot(self, infinite=False):
        """
        Resets the robot
        Arguments:
            infinite: if True, builds the robot on the enlarged world and
            centred, for the infinite circuit
        """
        self.hud = huds.MobileHUD()
        self.robot = robots.MobileRobot(self.n_sens, self.robot_data)
        if infinite:
            size = self.INFINITE_SIZE
            self.robot_drawing = robot_drawings.MobileRobotDrawing(
                self.drawing, self.n_sens, size, size, size // 2, size // 2)
        else:
            self.robot_drawing = robot_drawings.MobileRobotDrawing(
                self.drawing, self.n_sens)

    def __move_keys(self, movement):
        """
        Moves the robot using WASD
        Arguments:
            movement: contains the information about the pressing
            of the keys
        """
        v = 0
        da = 0
        if not self.is_rotating:
            if movement["w"] or movement["W"]:
                v = -20
            if movement["s"] or movement["S"]:
                v = 20
            if v != 0:
                self.is_moving = True
            else:
                self.is_moving = False
        if not self.is_moving:
            if movement["a"] or movement["A"]:
                da = 5
            if movement["d"] or movement["D"]:
                da = -5
            if da != 0:
                self.is_rotating = True
            else:
                self.is_rotating = False
        return v, da

    def __move_code(self):
        """
        Moves the robot using the programmed instructions
        """
        v = 0
        da = 0
        # self.robot.servo_left.value = 0
        # self.robot.servo_right.value = 0
        v_i = int((self.robot.servo_left.get_value() - 90) / 10)
        v_r = int((self.robot.servo_right.get_value() - 90) / 10)
        rotates = False
        if v_i >= 0 and v_r >= 0:
            if v_i != 0 or v_r != 0:
                da = 5
                rotates = True
        if v_i <= 0 and v_r <= 0:
            if v_i != 0 or v_r != 0:
                da = -5
                rotates = True
        if abs(v_i) == abs(v_r) and not rotates:
            if v_i > 0:
                v = v_i * 2
            if v_i < 0:
                v = v_i * 2
        if v != 0:
            self.is_moving = True
        else:
            self.is_moving = False
        if da != 0:
            self.is_rotating = True
        else:
            self.is_rotating = False
        return v, da

    def __parse_circuit_opt(self, circuit_opt):
        """
        Parses the option chosen for the circuit
        Arguments:
            circuit_opt: the number which specifies the option
        Returns:
            A string with the corresponding name
        """
        if circuit_opt == 0:
            return "circuit"
        elif circuit_opt == 1:
            return "labyrinth"
        elif circuit_opt == 2:
            return "straight"
        elif circuit_opt == 3:
            return "obstacle"
        elif circuit_opt == 4:
            return "straight and obstacle"
        elif circuit_opt == 5:
            return "node circuit"
        elif circuit_opt == 6:
            return "infinite"
        return "circuit"

    def _drawing_config(self):
        """
        Configures the drawing before executing or after
        updating
        """
        super()._drawing_config()
        if self.infinite and self.trail is not None:
            self.trail.reset()  # start each run with a clean trail
        self.__create_circuit()
        self.__create_obstacle()

    def _draw_before_robot(self):
        """
        Draws before the robot so the z-index is correct
        """
        self.__create_circuit()
        self.__create_obstacle()
        if self.infinite and self.trail is not None:
            self.trail.draw()

    def __follow_camera(self):
        """
        Scrolls the canvas so the robot stays centred in the viewport,
        giving the infinite plane its "camera follows the car" feel.

        The target scroll is quantised to whole canvas pixels and only applied
        when it actually changes; otherwise the per-frame sub-pixel rounding of
        xview_moveto fights the robot position and makes the car vibrate.
        """
        canvas = self.drawing.canvas
        if canvas is None:
            return
        scale = self.drawing.scale
        total_w = self.robot_drawing.drawing_width * scale
        total_h = self.robot_drawing.drawing_height * scale
        view_w = canvas.winfo_width()
        view_h = canvas.winfo_height()
        # Robot pixel on the canvas, computed exactly like Drawing.move_image
        # (int(coord * scale)). Driving the camera from the same integer keeps
        # the robot's screen position constant (no sub-pixel wobble).
        robot_px = int(self.robot_drawing.x * scale)
        robot_py = int(self.robot_drawing.y * scale)
        cam_x = min(max(robot_px - view_w // 2, 0), int(max(total_w - view_w, 0)))
        cam_y = min(max(robot_py - view_h // 2, 0), int(max(total_h - view_h, 0)))
        # +0.5 px bias so tkinter's fraction->pixel truncation lands on cam_*
        if total_w > 0 and cam_x != self._cam_x:
            self._cam_x = cam_x
            canvas.xview_moveto((cam_x + 0.5) / total_w)
        if total_h > 0 and cam_y != self._cam_y:
            self._cam_y = cam_y
            canvas.yview_moveto((cam_y + 0.5) / total_h)

    def __create_circuit(self):
        """
        Creates and draws the circuit in the canvas
        """
        if self.circuit is not None:
            self.circuit.create_circuit()

    def __create_obstacle(self):
        """
        Draws the obstacle in the canvas
        """
        if self.obstacle is not None:
            self.obstacle.draw()

    def __check_circuit_overlap(self):
        """
        Checks if the robot is inside or outside of the circuit
        """
        measurements = []
        values = []
        for sens in self.robot_drawing.sensors["light"]:
            x = sens.x
            y = sens.y
            if self.circuit.is_overlapping(x, y):
                sens.dark()
                measurements.append(True)
                values.append(1)
            else:
                sens.light()
                measurements.append(False)
                values.append(0)
        self.robot.set_light_sens_value(values)
        self.robot_drawing.repaint_light_sensors()
        self.hud.set_circuit(measurements)

    def __check_obstacle_collision(self, x, y):
        """
        Checks if the robot collides with the obstacle
        Arguments:
            x: the expected x position
            y: the expected y position
        Returns:
            True if collides, False if else
        """
        if self.obstacle is None:
            return False
        return (
                x + self.robot_drawing.width / 2 >= self.obstacle.x
                and y + self.robot_drawing.height / 2 >= self.obstacle.y
                and x <= self.obstacle.x + (self.obstacle.width + self.robot_drawing.width / 2)
                and y <= self.obstacle.y
                + (self.obstacle.height + self.robot_drawing.height / 2)
        )

    def __detect_obstacle(self):
        """
        Checks for every ultrasound sensor if it detects
        any obstacle in front of it, and then sends the data
        to the hud, so it can be parsed
        """
        dists = []
        dists.append(self.obstacle.calculate_distance(self.robot_drawing.sensors["sound"].x,
                                                      self.robot_drawing.sensors["sound"].y, self.robot_drawing.angle))
        if dists[-1] != -1:
            self.robot_drawing.sensors["sound"].set_detect(True)
            self.robot.sound.value = 1
            self.robot.sound.dist = dists[-1]
        else:
            self.robot_drawing.sensors["sound"].set_detect(False)
            self.robot.sound.value = 0
            self.robot.sound.dist = -1
        self.hud.set_detect_obstacle(dists)

    def __hud_velocity(self):
        """
        Sends the velocity data of the wheels to the hud,
        so it can be parsed
        """
        self.hud.set_wheel([self.robot_drawing.vl, self.robot_drawing.vr])


class LinearActuatorLayer(Layer):

    def __init__(self):
        """
        Constuctor for LinearActuatorLayer
        """
        super().__init__()
        self.hud = huds.ActuatorHUD()
        self.robot_data = self.rdr.parse_robot(3)
        self.robot = robots.LinearActuator(self.robot_data)
        self.robot_drawing = robot_drawings.LinearActuatorDrawing(self.drawing)
        self.last_v = 0  # última velocidad del bloque (px/tick), la lee el controller
        # Bajo control del gemelo (lazo cerrado), la posición del bloque la fija ALF
        # vía mensajes "5,<pos>"; el desplazamiento local del teclado se suprime.
        self.twin_external = False

    def move(self, using_keys, move_WASD):
        """
        Move method of the layer. Moves the block of the
        linear actuator
        """
        v = 0
        self.robot_drawing.hit = False
        if self.twin_external:
            # Bajo control del gemelo, la dirección (teclado o código) sale SOLO de la
            # intención, sin toparse con los bordes simulados (508/1912): el límite real
            # lo decide ALF (final de carrera físico). Si se gateara con 'block.x' (que
            # aquí lo fija el feedback de ALF), al llegar el bloque al borde se frenaría
            # a ALF antes de tocar el tope físico.
            if using_keys:
                v = self.__key_direction(move_WASD)
            else:
                v = self.__code_direction()
        else:
            if using_keys:
                v = self.__move_keys(move_WASD)
            else:
                v = self.__move_code()
        # Última velocidad del bloque (px/tick). La lee el controller para conducir
        # el actuador físico en vivo (jog) cuando el gemelo tiene el control.
        self.last_v = v
        # Bajo control del gemelo, el bloque no se desplaza en local: su posición la
        # fija ALF (lazo cerrado). Se conserva 'v' solo como dirección para el jog.
        self.robot_drawing.move(0 if self.twin_external else v)
        self.hud.set_direction(v * 25)
        self.hud.set_pressed(
            [self.robot_drawing.but_left.pressed, self.robot_drawing.but_right.pressed])

    def __move_keys(self, movement):
        """
        Moves the robot using WASD
        Arguments:
            movement: contains the information about the pressing
            of the keys
        """
        v = 0
        if movement["a"] or movement["A"]:
            if self.robot_drawing.block.x > 508:
                v -= 15
            self.__hit_left(v == 0)
        elif movement["d"] or movement["D"]:
            if self.robot_drawing.block.x < 1912:
                v += 15
            self.__hit_right(v == 0)
        return v

    def __key_direction(self, movement):
        """
        Devuelve solo la dirección de las teclas (sin tope por bordes ni gestión de
        pulsadores), para conducir el jog del actuador físico bajo control del gemelo.
        Arguments:
            movement: estado de las teclas WASD
        """
        if movement["a"] or movement["A"]:
            return -15
        if movement["d"] or movement["D"]:
            return 15
        return 0

    def __code_direction(self):
        """
        Devuelve solo la dirección que pide el código (servo), sin tope por bordes ni
        gestión de pulsadores, para conducir el jog del actuador físico bajo control del
        gemelo cuando se ejecuta código en el simulador.
        Convención de __move_code: servo.value < 90 -> hacia el motor (derecha, +);
        > 90 -> hacia el sensor (izquierda, -); == 90 -> parado.
        """
        if self.robot.servo.value < 90:
            return 15
        if self.robot.servo.value > 90:
            return -15
        return 0

    def __move_code(self):
        """
        Moves the robot using the programmed instructions
        """
        v = 0
        v_s = int((self.robot.servo.value - 90) / 10) * -1
        if v_s > 0:
            if self.robot_drawing.block.x < 1912:
                v = v_s * 2
            else:
                self.__hit_right(True)
        if v_s < 0:
            if self.robot_drawing.block.x > 508:
                v = v_s * 2
            else:
                self.__hit_left(True)
        if v != 0:
            self.__hit_left(False)
            self.__hit_right(False)
        return v

    # ------------------------------------------------- Gemelo digital (reflejo)
    def set_physical_limits(self, motor_pressed, sensor_pressed):
        """
        Refleja el estado real de los finales de carrera del actuador físico en la
        interfaz (lazo cerrado del gemelo). Motor = pulsador derecho, sensor = izquierdo.
        Actualiza el dibujo, el modelo (button_left/right.value) y el HUD.
        Arguments:
            motor_pressed: True si el final de carrera del motor está pulsado
            sensor_pressed: True si el final de carrera del sensor está pulsado
        """
        self.robot_drawing.set_buttons(
            left_pressed=sensor_pressed, right_pressed=motor_pressed)
        self.robot.button_left.value = 0 if sensor_pressed else 1
        self.robot.button_right.value = 0 if motor_pressed else 1
        self.hud.set_pressed(
            [self.robot_drawing.but_left.pressed, self.robot_drawing.but_right.pressed])
    # ----------------------------------------------- Fin Gemelo digital (reflejo)

    def __hit_left(self, has_hit):
        """
        Establishes the value for the left button
        Arguments:
            has_hit: True if the button has been hit, False
            if else
        """
        if has_hit:
            self.robot_drawing.hit = True
            self.robot.button_left.value = 0
        else:
            self.robot_drawing.hit = False
            self.robot.button_left.value = 1

    def __hit_right(self, has_hit):
        """
        Establishes the value for the right button
        Arguments:
            has_hit: True if the button has been hit, False
            if else
        """
        if has_hit:
            self.robot_drawing.hit = True
            self.robot.button_right.value = 0
        else:
            self.robot_drawing.hit = False
            self.robot.button_right.value = 1


class ArduinoBoardLayer(Layer):
    def __init__(self):
        """
        Constuctor for ArduinoBoard
        """
        super().__init__()
        self.is_board = True
        self.prev_x = 0
        self.prev_y = 0
        self.hud = huds.ArduinoBoardHUD()
        self.robot = robots.ArduinoBoard(self)
        self.robot_drawing = robot_drawings.ArduinoBoardDrawing(
            self.drawing)
        self.drawing.setBoard(self.robot.board)

    def set_canvas(self, canvas, hud_canvas):
        """
        Sets the canvas that the drawing and will use
        Arguments:
            canvas: the canvas of the drawing
            hud_canvas: the canvas of the hud
        """
        self.drawing.set_canvas(canvas)
        self.drawing.set_size(self.robot_drawing.drawing_width,
                              self.robot_drawing.drawing_height)
        self.hud.set_canvas(hud_canvas)
        self.robot_drawing.draw()
        self.drawing.draw_buttons(self.robot, 500.0, 500.0)

    def _zoom_config(self):
        """
        Configures the zoom in case when it changes
        """
        self._zoom_percentage()
        self._zoom_redraw()

    def stop(self):
        """
        Stops all the executing code and clears the canvas
        """
        self.is_drawing = False

    def draw_component(self, x, y):
        if self.hud.drawing is not None:
            element = self.robot.add_component(self.hud.drawing)
            self.drawing.draw_component(element, x, y)
            self.hud.drawing = None
        elif self.hud.draw_wire:
            dibujar = self.drawing.draw_part_wire(x, y)
            # It is needed to the correct work of the wire
            if not dibujar:
                self.hud.draw_wire = False

    def _draw_after_robot(self):
        """Draw the components on the canvas"""
        self.drawing.draw_all_components()
        self.drawing.draw_all_buttons()
        self.drawing.redraw_wire()

    def probe(self, option_gamification, user_code, robot_code):
        return self.drawing.probe(option_gamification, user_code, robot_code,
                                  self.robot, self.get_robot_challenge(option_gamification))

    def show_tutorial(self):
        self.drawing.show_tutorial()

    def show_results(self):
        self.drawing.show_results()

    def show_help(self, option_gamification):
        self.drawing.show_help(option_gamification)

    def get_robot_challenge(self, option_gamification):
        return self.drawing.get_robot_challenge(option_gamification)
