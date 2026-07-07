import graphics.drawing as drawing
import graphics.robot_drawings as robot_drawings
import graphics.huds as huds
import robot_components.robots as robots
import files.files_reader as filesr
import time
from motor3d.api import Motor3DApi


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

        future_p = self.robot_drawing.predict_movement(v)
        if (
                v == 0
                or future_p[0] <= self.robot_drawing.width / 2
                or future_p[0] >= self.robot_drawing.drawing_width - self.robot_drawing.width / 2
                or future_p[1] <= self.robot_drawing.height / 2
                or future_p[1] >= self.robot_drawing.drawing_height - self.robot_drawing.height / 2
                or self.__check_obstacle_collision(future_p[0], future_p[1])
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

    def set_circuit(self, circuit_opt):
        """
        Changes the circuit
        Arguments:
            circuit_opt: the number of the chosen circuit
        """
        circuit_name = self.__parse_circuit_opt(circuit_opt)
        map_tuple = self.rdr.parse_circuit(circuit_name)
        straights = map_tuple[0]
        obstacles = map_tuple[1]
        self.circuit = robot_drawings.Circuit(straights, self.drawing)
        self.obstacle = None
        if len(obstacles) > 0:
            self.obstacle = robot_drawings.Obstacle(obstacles[0], self.drawing)
        self.reset_robot()

    def reset_robot(self):
        """
        Resets the robot
        """
        self.hud = huds.MobileHUD()
        self.robot = robots.MobileRobot(self.n_sens, self.robot_data)
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
        return "circuit"

    def _drawing_config(self):
        """
        Configures the drawing before executing or after
        updating
        """
        super()._drawing_config()
        self.__create_circuit()
        self.__create_obstacle()

    def _draw_before_robot(self):
        """
        Draws before the robot so the z-index is correct
        """
        self.__create_circuit()
        self.__create_obstacle()

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

    def move(self, using_keys, move_WASD):
        """
        Move method of the layer. Moves the block of the
        linear actuator
        """
        v = 0
        self.robot_drawing.hit = False
        if using_keys:
            v = self.__move_keys(move_WASD)
        else:
            v = self.__move_code()
        self.robot_drawing.move(v)
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


class Arm3DLayer(Layer):
    """
    Capa de integración entre el sistema legado S4R y el motor 3D.
    Puente entre la GUI y Motor3DApi.

    Conversión de ángulos:
        joint_angle (DH) = servo_value - 90.0
        servo_value       = clamp(angle + 90.0, 0, 180)
    """
    CAMERA_PRESETS = {
        'caballera': {
            # Use the free camera projection, but start from a flatter
            # side-oblique angle, pulled back to frame the whole arm cleanly.
            'yaw': 240.0,
            'pitch': 18.0,
            'distance': 950.0,
            'projection_mode': 'perspective',
        },
        'isometrica': {
            'yaw': 45.0,
            'pitch': 32.0,
            'projection_mode': 'isometrica',
        },
        'iso': {
            'yaw': 45.0,
            'pitch': 32.0,
            'projection_mode': 'isometrica',
        },
    }
    DEFAULT_BRACCIO_SERVO_CALIBRATION = (
        ((0.0, -7.0), (7.0, 0.0), (180.0, 173.0)),
        ((15.0, 15.0), (90.0, 90.0), (165.0, 165.0)),
        ((20.0, 200.0), (130.0, 90.0), (180.0, 40.0)),
        ((0.0, 15.0), (75.0, 90.0), (180.0, 195.0)),
        ((0.0, 0.0), (90.0, 90.0), (180.0, 180.0)),
        ((10.0, 10.0), (40.0, 40.0), (73.0, 73.0)),
    )
    DEFAULT_SERVO_PINS = [11, 10, 9, 6, 5, 3]
    _PRISMATIC_CODE_NEUTRAL = 90.0
    _PRISMATIC_CODE_STEP = 10.0
    _PRISMATIC_CODE_SPEED_MM_S_PER_STEP = 10.0

    def __init__(self):
        # No llamamos a super().__init__() porque no usamos Drawing ni RobotDrawing
        import graphics.drawing as _drawing
        self.drawing = _drawing.Drawing()
        self.is_drawing = False
        self.is_board = False
        self.hud = huds.Arm3DHUD()
        self.robot = robots.ArmHardwareRobot()
        self.robot_drawing = None
        self._zoom_percentage()

        self.motor3d = Motor3DApi()
        self.safety_blocked = False
        self.warning_message = ""
        self._canvas = None
        self._current_joints = None  # ángulos animados actuales (interpolados)
        self._last_sync_time = None
        self._interactive_render_until = 0.0
        self._camera_locked = False
        self._fps_last_frame_time = None
        self._fps_display_value = 0.0
        # Sincronizar la escala del Drawing con el zoom inicial de la cámara
        self.drawing.scale = self.motor3d.camera.zoom
        self.apply_servo_pin_mapping()
        self._sync_servos_from_model(reset_animation=True)

    def set_canvas(self, canvas, hud_canvas):
        self._canvas = canvas
        self.drawing.set_canvas(canvas)
        self.hud.set_canvas(hud_canvas)
        # Resetear el ID de imagen del renderer para que se cree nuevo
        self.motor3d.renderer._canvas_image_id = None

    def execute(self):
        self.is_drawing = True
        self.apply_servo_pin_mapping()
        self.motor3d.scene.update()

    def stop(self):
        self.is_drawing = False
        self.safety_blocked = False
        self.warning_message = ""
        self._current_joints = None  # resetear animación
        self._last_sync_time = None
        self._interactive_render_until = 0.0
        self._fps_last_frame_time = None
        self._fps_display_value = 0.0
        if self._canvas is not None:
            try:
                self._canvas.delete("all")
            except Exception:
                pass
        # Invalidar el ID de imagen del renderer para que el siguiente draw()
        # cree un nuevo item en lugar de intentar itemconfig sobre uno inexistente.
        self.motor3d.renderer._canvas_image_id = None
        if self.hud:
            self.hud.reboot()

    def move(self, using_keys, move_WASD):
        """
        Tick principal (~16 ms). Lee los servos del robot, actualiza Motor3D y renderiza.
        """
        if not self.is_drawing and not self._canvas:
            return

        # Mover cámara con teclado
        if not getattr(self, "_camera_locked", False):
            self.motor3d.keyboard_camera(move_WASD)

        # Sincronizar valores de servo → ángulos DH
        self.__sync_from_servos()

        # Renderizar
        if self._canvas:
            camera_moving = bool(move_WASD and any(move_WASD.values()))
            self.motor3d.renderer.set_fast_quality(camera_moving or self.wants_fast_render())
            self.motor3d.draw(self._canvas)
            self._draw_fps_counter()

        # Evaluar seguridad y actualizar HUD
        safety = self.motor3d.evaluate_safety()
        self.safety_blocked = safety['blocked']
        self.warning_message = safety['message']
        self._update_hud(safety)

    def zoom_in(self):
        cam = self.motor3d.camera
        cam.set_distance(cam.distance / 1.25)
        self.drawing.scale = cam.zoom   # sincroniza la etiqueta

    def zoom_out(self):
        cam = self.motor3d.camera
        cam.set_distance(cam.distance * 1.25)
        self.drawing.scale = cam.zoom   # sincroniza la etiqueta

    def _zoom_config(self):
        self._zoom_percentage()

    def _zoom_redraw(self):
        pass

    # ------------------------------------------------------------------
    # API expuesta al controlador
    # ------------------------------------------------------------------

    def set_joint_angle(self, joint_idx, angle):
        """
        Fija la articulación desde el valor visible en la UI.
        Para juntas R, la UI trabaja en grados tipo servo (0..180).
        """
        model_value = self._to_model_value(joint_idx, angle)
        self.motor3d.set_joint(joint_idx, model_value)
        servos = [
            self.robot.servo_base,
            self.robot.servo_shoulder,
            self.robot.servo_elbow,
            self.robot.servo_wrist_vertical,
            self.robot.servo_wrist,
            self.robot.servo_gripper,
        ]
        if 0 <= joint_idx < len(servos):
            self._set_servo_position_value(servos[joint_idx], self._to_control_value(
                joint_idx, self.motor3d.model.joints[joint_idx]
            ))
        if self._current_joints is not None and 0 <= joint_idx < len(self._current_joints):
            self._current_joints[joint_idx] = float(self.motor3d.model.joints[joint_idx])
        self._request_fast_render()

    def solve_ik(self, x, y, z):
        """Lanza IK y anima la transicion hacia la mejor solucion encontrada."""
        start_joints = None
        model = self.motor3d.model
        if self._current_joints is not None and len(self._current_joints) == model.dof:
            start_joints = list(self._current_joints)
        else:
            start_joints = list(model.joints[:model.dof])

        result = self.motor3d.solve_ik(x, y, z, track_trail=False)
        self._sync_servos_from_model(reset_animation=False)
        self._current_joints = list(start_joints)
        for i, joint in enumerate(start_joints):
            self.motor3d.model.set_joint(i, joint)
        # Inicia la animación dentro de la propia acción IK para que la mejor
        # aproximación empiece a verse ya en el primer clic.
        self._last_sync_time = time.monotonic() - self._IK_ANIM_KICKSTART_S
        self._Arm3DLayer__sync_from_servos()
        self._request_fast_render()
        return result

    def drag_camera(self, dx, dy, pan=False):
        if getattr(self, "_camera_locked", False):
            return
        self.motor3d.drag_camera(dx, dy, pan=pan)
        self._request_fast_render()

    def dolly_camera(self, dy):
        self.motor3d.dolly_camera(dy)
        self.drawing.scale = self.motor3d.camera.zoom
        self._request_fast_render()

    def set_camera_yaw(self, yaw):
        if getattr(self, "_camera_locked", False):
            return
        self.motor3d.set_camera(yaw=yaw)
        self._request_fast_render()

    def set_camera_pitch(self, pitch):
        if getattr(self, "_camera_locked", False):
            return
        self.motor3d.set_camera(pitch=pitch)
        self._request_fast_render()

    def reset_camera(self):
        self.motor3d.reset_camera()
        self._camera_locked = False
        self._request_fast_render()

    def unlock_camera_view(self):
        """Vuelve a libre; solo reencuadra si se sale de un preset fijo."""
        if getattr(self, "_camera_locked", False):
            self.motor3d.reset_camera()
            self.drawing.scale = self.motor3d.camera.zoom
        self._camera_locked = False
        self._request_fast_render()

    def set_camera_view(self, view_name):
        """Aplica un preset de cámara: 'caballera', 'isometrica' o libre."""
        preset = self.CAMERA_PRESETS.get(view_name)
        if preset is not None:
            self.motor3d.reset_camera()
            self.motor3d.set_camera(**preset)
            self.drawing.scale = self.motor3d.camera.zoom
            self._camera_locked = view_name in ('caballera', 'isometrica', 'iso')
        else:
            self.motor3d.reset_camera()
            self.drawing.scale = self.motor3d.camera.zoom
            self._camera_locked = False
        self._request_fast_render()

    def set_trail(self, enabled):
        self.motor3d.set_show_trail(enabled)
        self._request_fast_render()

    def clear_trail(self):
        self.motor3d.scene.clear_trail()
        self._request_fast_render()

    def set_fps_counter(self, enabled):
        self.motor3d.set_show_fps_counter(enabled)
        if not enabled and self._canvas is not None:
            try:
                self._canvas.delete("arm3d_fps_counter")
            except Exception:
                pass
        self._request_fast_render()

    def get_model_config(self):
        return self.motor3d.get_model_config()

    def apply_servo_pin_mapping(self):
        """Sincroniza los pines configurados del modelo con el robot virtual."""
        pins = list(getattr(self.motor3d.model, 'servo_pins', []) or [])
        if not any(pin is not None for pin in pins):
            pins = list(self.DEFAULT_SERVO_PINS[:self.motor3d.model.dof])
        self.robot.set_servo_pin_mapping(pins)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    # Velocidad de animación en grados por segundo.
    # Se usa tiempo real y no "grados por frame" para que el movimiento
    # no dependa de los FPS del render 3D.
    _ANIM_SPEED_DPS = 45.0
    _IK_ANIM_KICKSTART_S = 1.0 / 30.0
    _FAST_RENDER_WINDOW_S = 0.25
    _FAST_RENDER_EPS = 1e-3

    def _draw_fps_counter(self):
        if self._canvas is None:
            return

        show = self.motor3d.model.visual.get('show_fps_counter', True)
        try:
            self._canvas.delete("arm3d_fps_counter")
        except Exception:
            return
        if not show:
            self._fps_last_frame_time = time.monotonic()
            return

        now = time.monotonic()
        if self._fps_last_frame_time is not None:
            dt = now - self._fps_last_frame_time
            if dt > 1e-6:
                instant_fps = 1.0 / dt
                if self._fps_display_value <= 0.0:
                    self._fps_display_value = instant_fps
                else:
                    self._fps_display_value = (
                        self._fps_display_value * 0.85 + instant_fps * 0.15
                    )
        self._fps_last_frame_time = now

        text = "FPS: {:.0f}".format(self._fps_display_value)
        try:
            width = self._canvas.winfo_width()
            height = self._canvas.winfo_height()
        except Exception:
            width, height = 800, 600
        # Tamaño de fuente, margen y padding proporcionales al viewport para que
        # el contador encoja/crezca con la ventana (responsive).
        ref = max(160, min(width, int(height * 1.4)))
        size = max(8, min(16, int(round(ref / 55.0))))
        margin = max(6, int(round(ref / 70.0)))
        pad = max(3, int(round(size * 0.45)))
        x = max(size * 5, width - margin)
        y = margin
        try:
            text_id = self._canvas.create_text(
                x, y, text=text, anchor="ne",
                font=("Consolas", size, "bold"),
                fill="#E8FFFB",
                tags="arm3d_fps_counter",
            )
            bbox = self._canvas.bbox(text_id)
            if bbox:
                rect_id = self._canvas.create_rectangle(
                    bbox[0] - pad, bbox[1] - pad,
                    bbox[2] + pad, bbox[3] + pad,
                    fill="#102729",
                    outline="#00D8C0",
                    width=1,
                    tags="arm3d_fps_counter",
                )
                self._canvas.tag_lower(rect_id, text_id)
        except Exception:
            pass

    def _uses_braccio_calibration(self):
        return bool(
            getattr(self.motor3d, "uses_legacy_servo_degrees", lambda: False)()
        )

    def _servo_calibration_points(self, joint_idx):
        model_points = getattr(self.motor3d.model, 'servo_calibration', None) or []
        if 0 <= joint_idx < len(model_points) and len(model_points[joint_idx]) >= 2:
            return model_points[joint_idx]
        if (self._uses_braccio_calibration()
                and 0 <= joint_idx < len(self.DEFAULT_BRACCIO_SERVO_CALIBRATION)):
            return self.DEFAULT_BRACCIO_SERVO_CALIBRATION[joint_idx]
        return ()

    @staticmethod
    def _interpolate_calibration(points, value):
        value = float(value)
        ordered = sorted((float(x), float(y)) for x, y in points)
        if value <= ordered[0][0]:
            return ordered[0][1]
        if value >= ordered[-1][0]:
            return ordered[-1][1]
        for (x0, y0), (x1, y1) in zip(ordered, ordered[1:]):
            if x0 <= value <= x1:
                if x1 == x0:
                    return y1
                ratio = (value - x0) / (x1 - x0)
                return y0 + (y1 - y0) * ratio
        return ordered[-1][1]

    def _braccio_digital_to_real(self, joint_idx, value):
        points = self._servo_calibration_points(joint_idx)
        return self._interpolate_calibration(points, value)

    def _braccio_real_to_digital(self, joint_idx, value):
        points = (
            (real_value, digital_value)
            for digital_value, real_value in self._servo_calibration_points(joint_idx)
        )
        return self._interpolate_calibration(points, value)

    def _to_control_value(self, joint_idx, value):
        model = self.motor3d.model
        if joint_idx < len(model.joint_types) and model.joint_types[joint_idx] == 'P':
            return float(value)
        if self._servo_calibration_points(joint_idx):
            return self._braccio_real_to_digital(joint_idx, float(value) + 90.0)
        return float(value) + 90.0

    def _to_model_value(self, joint_idx, value):
        model = self.motor3d.model
        if joint_idx < len(model.joint_types) and model.joint_types[joint_idx] == 'P':
            return float(value)
        if self._servo_calibration_points(joint_idx):
            return self._braccio_digital_to_real(joint_idx, value) - 90.0
        return float(value) - 90.0

    def _pulse_to_model_value(self, joint_idx, servo):
        model = self.motor3d.model
        if self._servo_calibration_points(joint_idx) and not self._is_prismatic_joint(joint_idx):
            return self._to_model_value(joint_idx, getattr(servo, "value", 90.0))
        if joint_idx >= len(model.joint_limits):
            return self._to_model_value(joint_idx, getattr(servo, "value", 90.0))
        try:
            pulse = float(getattr(servo, "pulse_value"))
            pulse_min = float(getattr(servo, "pulse_min", getattr(servo, "min", 544)))
            pulse_max = float(getattr(servo, "pulse_max", getattr(servo, "max", 2400)))
        except (TypeError, ValueError):
            return self._to_model_value(joint_idx, getattr(servo, "value", 90.0))
        if pulse_max <= pulse_min:
            return self._to_model_value(joint_idx, getattr(servo, "value", 90.0))
        ratio = (pulse - pulse_min) / (pulse_max - pulse_min)
        ratio = max(0.0, min(1.0, ratio))
        mn, mx = model.joint_limits[joint_idx]
        return float(mn) + ratio * (float(mx) - float(mn))

    def _servo_to_model_value(self, joint_idx, servo):
        if getattr(servo, "command_mode", "position") == "pulse":
            return self._pulse_to_model_value(joint_idx, servo)
        return self._to_model_value(joint_idx, getattr(servo, "value", servo))

    def _set_servo_position_value(self, servo, value):
        if hasattr(servo, "set_position_value"):
            servo.set_position_value(value)
        else:
            servo.value = value

    def _is_prismatic_joint(self, joint_idx):
        model = self.motor3d.model
        return joint_idx < len(model.joint_types) and model.joint_types[joint_idx] == 'P'

    def _is_prismatic_velocity_command(self, joint_idx):
        if not self._is_prismatic_joint(joint_idx):
            return False
        if joint_idx >= len(self.robot._joint_servos):
            return False
        servo = self.robot._joint_servos[joint_idx]
        return getattr(servo, "command_mode", "position") in ("velocity", "pulse")

    def _prismatic_velocity_steps(self, value):
        try:
            return int((float(value) - self._PRISMATIC_CODE_NEUTRAL) /
                       self._PRISMATIC_CODE_STEP) * -1
        except (TypeError, ValueError):
            return 0

    def _prismatic_velocity_can_move(self, joint_idx, value):
        if not self._is_prismatic_velocity_command(joint_idx):
            return False
        steps = self._prismatic_velocity_steps(value)
        if steps == 0:
            return False
        model = self.motor3d.model
        if self._current_joints is not None and joint_idx < len(self._current_joints):
            current = float(self._current_joints[joint_idx])
        elif joint_idx < len(model.joints):
            current = float(model.joints[joint_idx])
        else:
            return False
        if joint_idx < len(model.joint_limits):
            mn, mx = model.joint_limits[joint_idx]
            if steps > 0 and current >= float(mx) - self._FAST_RENDER_EPS:
                return False
            if steps < 0 and current <= float(mn) + self._FAST_RENDER_EPS:
                return False
        return True

    def _request_fast_render(self, duration_s=None):
        """Mantiene el render en modo rapido durante una breve ventana temporal."""
        window = self._FAST_RENDER_WINDOW_S if duration_s is None else max(0.0, float(duration_s))
        self._interactive_render_until = max(
            self._interactive_render_until,
            time.monotonic() + window,
        )

    def wants_fast_render(self):
        """Indica si conviene refrescar a mayor frecuencia por interacción reciente."""
        if time.monotonic() < self._interactive_render_until:
            return True

        model = self.motor3d.model
        if self._current_joints is None or model.dof == 0:
            return False

        joint_servos = self.robot._joint_servos[:model.dof]
        for i, servo in enumerate(joint_servos):
            sv = servo.value
            if self._is_prismatic_velocity_command(i):
                if self._prismatic_velocity_can_move(i, sv):
                    return True
                continue
            target = self._servo_to_model_value(i, servo)
            if i < len(model.joint_limits):
                mn, mx = model.effective_joint_limits(i)
                target = max(mn, min(mx, target))
            if i < len(self._current_joints):
                if abs(target - self._current_joints[i]) > self._FAST_RENDER_EPS:
                    return True
        return False

    def is_motion_active(self):
        """Indica si el brazo todavia esta animando hacia los servos objetivo."""
        model = self.motor3d.model
        if self._current_joints is None or model.dof == 0:
            return False

        joint_servos = self.robot._joint_servos[:model.dof]
        for i, servo in enumerate(joint_servos):
            sv = servo.value
            if self._is_prismatic_velocity_command(i):
                if self._prismatic_velocity_can_move(i, sv):
                    return True
                continue
            target = self._servo_to_model_value(i, servo)
            if i < len(model.joint_limits):
                mn, mx = model.effective_joint_limits(i)
                target = max(mn, min(mx, target))
            if i < len(self._current_joints):
                if abs(target - self._current_joints[i]) > self._FAST_RENDER_EPS:
                    return True
        return False

    def snap_to_servo_targets(self):
        """Aplica inmediatamente al modelo los valores actuales de los servos."""
        model = self.motor3d.model
        targets = []
        joint_servos = self.robot._joint_servos[:model.dof]
        for i, servo in enumerate(joint_servos):
            if self._is_prismatic_velocity_command(i):
                target = model.joints[i] if i < len(model.joints) else 0.0
            else:
                target = self._servo_to_model_value(i, servo)
            if i < len(model.joint_limits):
                mn, mx = model.effective_joint_limits(i)
                target = max(mn, min(mx, target))
            targets.append(target)

        for i, target in enumerate(targets):
            model.set_joint(i, target)
        self._current_joints = list(targets)
        self._last_sync_time = time.monotonic()
        self.motor3d.scene.update()
        self._request_fast_render()

    def _sync_servos_from_model(self, reset_animation=False):
        """Sincroniza los servos virtuales con el estado actual del modelo."""
        model = self.motor3d.model
        for i, servo in enumerate(self.robot._joint_servos[:model.dof]):
            self._set_servo_position_value(servo, self._to_control_value(i, model.joints[i]))
        if reset_animation:
            self._current_joints = list(model.joints[:model.dof])
            self._last_sync_time = time.monotonic()

    def __sync_from_servos(self):
        """Lee los valores objetivo de los servos e interpola suavemente hacia ellos."""
        model = self.motor3d.model
        now = time.monotonic()
        joint_servos = self.robot._joint_servos[:model.dof]

        # Inicializar posición actual en el primer frame
        if self._current_joints is None or len(self._current_joints) != model.dof:
            self._current_joints = []
            for i, servo in enumerate(joint_servos):
                if self._is_prismatic_velocity_command(i):
                    target = model.joints[i] if i < len(model.joints) else 0.0
                else:
                    target = self._servo_to_model_value(i, servo)
                    if i < len(model.joint_limits):
                        mn, mx = model.effective_joint_limits(i)
                        target = max(mn, min(mx, target))
                self._current_joints.append(target)
            self._last_sync_time = now

        if self._last_sync_time is None:
            dt = 0.016
        else:
            # Permitimos frames lentos (p. ej. 5 FPS) sin frenar artificialmente
            # la animación. Solo se limita para evitar saltos enormes tras pausas
            # largas o al reanudar depuración.
            dt = max(0.0, min(0.25, now - self._last_sync_time))
        self._last_sync_time = now

        speed = self._ANIM_SPEED_DPS * dt
        scene_needs_update = self.motor3d.scene.last_chain is None
        for i, servo in enumerate(joint_servos):
            sv = servo.value
            curr = self._current_joints[i]
            if self._is_prismatic_velocity_command(i):
                steps = self._prismatic_velocity_steps(sv)
                target = curr + steps * self._PRISMATIC_CODE_SPEED_MM_S_PER_STEP * dt
                if i < len(model.joint_limits):
                    mn, mx = model.effective_joint_limits(i)
                    target = max(mn, min(mx, target))
                self._current_joints[i] = target
            else:
                target = self._servo_to_model_value(i, servo)
                if i < len(model.joint_limits):
                    mn, mx = model.effective_joint_limits(i)
                    target = max(mn, min(mx, target))
                    if (not self._servo_calibration_points(i)
                            and getattr(servo, "command_mode", "position") != "pulse"
                            and i < len(self.robot._joint_servos)):
                        self._set_servo_position_value(
                            self.robot._joint_servos[i],
                            self._to_control_value(i, target)
                        )
                diff = target - curr
                if abs(diff) <= speed:
                    self._current_joints[i] = target
                else:
                    self._current_joints[i] = curr + speed * (1.0 if diff > 0 else -1.0)
            prev = model.joints[i] if i < len(model.joints) else None
            self.motor3d.model.set_joint(i, self._current_joints[i])
            if prev is None or abs(float(model.joints[i]) - float(prev)) > self._FAST_RENDER_EPS:
                scene_needs_update = True

        if scene_needs_update or self.motor3d.scene.show_trail:
            self.motor3d.scene.update()

    def _update_hud(self, safety):
        ee = self.motor3d.scene.get_end_effector()
        model = self.motor3d.model
        jtypes = model.joint_types

        def _jval(i, j):
            if i < len(jtypes) and jtypes[i] == 'P':
                return j
            return self._to_control_value(i, j)

        def _jlim(i, mn, mx):
            if i < len(jtypes) and jtypes[i] == 'P':
                return mn, mx
            lo = self._to_control_value(i, mn)
            hi = self._to_control_value(i, mx)
            return min(lo, hi), max(lo, hi)

        joints_display = [_jval(i, j) for i, j in enumerate(model.joints)]
        limits_display = [_jlim(i, *model.effective_joint_limits(i)) for i in range(model.dof)]
        self.hud.update(
            dof=model.dof,
            joints=joints_display,
            end_effector=ee,
            joint_limits=limits_display,
            joint_types=list(jtypes),
            in_workspace=safety['in_workspace'],
            singular=safety['singular'],
            safety_blocked=safety['blocked'],
            warning_message=safety['message'],
        )

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
