from math import atan2, sqrt
from math import cos, pi, sin
import graphics.drawing as drawing
import robot_components.boards as boards


class RobotDrawing:

    def __init__(self, drawing: drawing.Drawing):
        """
        Constructor for Robot superclass
        Arguments:
            drawing: the drawing where the robot is
            going to be represented
        """
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.drawing_width = 0
        self.drawing_height = 0
        self.drawing = drawing

    def move(self, vel):
        """
        Moves the robot
        """
        pass

    def create_robot(self):
        """
        Creates the robot
        """
        pass

    def draw(self):
        """
        Draws the robot
        """
        pass

    def reboot(self):
        """
        Restarts all the parameters of the drawing
        """
        self.drawing.empty_drawing()


class LinearActuatorDrawing(RobotDrawing):

    def __init__(self, drawing: drawing.Drawing):
        """
        Constructor for the Linear actuator robot
        Arguments:
            drawing: the drawing where the robot is going
            to be represented
        """
        super().__init__(drawing)
        self.img_act = "assets/actuator.png"

        self.drawing_width = 2500
        self.drawing_height = 600
        self.x = int(self.drawing_width / 2)
        self.y = int(self.drawing_height / 2)
        self.width = 2280
        self.height = 380
        self.hit = False
        self.direction = "stop"

        self.create_robot()

    def move(self, vel):
        """
        Moves the block of the actuator by a determined
        velocity. The movement is limited by the position
        of the buttons
        Arguments:
            vel: the determined velocity
        """
        vel = vel
        if (not self.hit) and vel != 0:
            if self.but_right.pressed:
                self.but_right.stop_press()
            if self.but_left.pressed:
                self.but_left.stop_press()
            self.__redraw_buttons()
        if vel < 0:
            self.direction = "left"
        elif vel > 0:
            self.direction = "right"
        if vel == 0 and self.hit and not self.direction == "stop":
            if not self.but_left.pressed and self.direction == "left":
                self.but_left.press()
            if not self.but_right.pressed and self.direction == "right":
                self.but_right.press()
            self.__redraw_buttons()
            self.direction = "stop"
        else:
            self.block.x += vel
            self.drawing.move_image("block", self.block.x, self.block.y)

    def set_buttons(self, left_pressed, right_pressed):
        """
        Fija el estado de los pulsadores (final de carrera) y los redibuja.
        Usado por el gemelo digital para reflejar el estado físico real.
        Arguments:
            left_pressed: True si el pulsador izquierdo (sensor) está pulsado
            right_pressed: True si el pulsador derecho (motor) está pulsado
        """
        if left_pressed:
            self.but_left.press()
        else:
            self.but_left.stop_press()
        if right_pressed:
            self.but_right.press()
        else:
            self.but_right.stop_press()
        self.__redraw_buttons()

    def __redraw_buttons(self):
        """
        Redraws the buttons when they are changed
        """
        self.drawing.redraw_image(self.but_left.get_image(), "button_left")
        self.drawing.rotate_image(
            self.but_left.get_image(), 180, "button_left")
        self.drawing.redraw_image(self.but_right.get_image(), "button_right")

    def create_robot(self):
        """
        Creates the linear actuator, piecing all of the
        elements that compose it
        """
        self.image = {
            "x": self.x,
            "y": self.y,
            "image": self.img_act
        }
        self.but_left = self.ActuatorButton(
            "assets/button-hit.png",
            "assets/button-no-hit.png",
            self.x - 960, self.y + 70
        )
        self.but_right = self.ActuatorButton(
            "assets/button-hit.png",
            "assets/button-no-hit.png",
            self.x + 875, self.y - 185
        )
        self.block = self.Block(
            "assets/mobile-part.png",
            self.x, self.y - 50
        )

    def draw(self):
        """
        Draws the robot by drawing all its pieces
        """
        self.drawing.draw_image(self.image, "actuator")
        self.drawing.draw_image(self.but_left.get_image(), "button_left")
        self.drawing.rotate_image(
            self.but_left.get_image(), 180, "button_left")
        self.drawing.draw_image(self.but_right.get_image(), "button_right")
        self.drawing.draw_image(self.block.get_image(), "block")

    class ActuatorElement:

        def __init__(self):
            """
            Constructor for ActuatorElement superclass
            """
            self.x = 0
            self.y = 0
            self.img_shown = None

        def get_image(self):
            """
            Returns: a dictionary with the coordinates
            of the element, as well as the image that
            represent it (as Image instance)
            """
            return {
                "x": self.x,
                "y": self.y,
                "image": self.img_shown
            }

    class Block(ActuatorElement):

        def __init__(self, img_path, x, y):
            """
            Constructor for the block element
            Arguments:
                img_path: the image to show
                x: the x coordinate of the block
                y: the y coordinate of the block
            """
            self.img_shown = img_path
            self.x = x
            self.y = y

    class ActuatorButton(ActuatorElement):

        def __init__(self, img_path_hit, img_path_no_hit, x, y):
            """
            Constructor for linear actuator's buttons
            Arguments:
                img_path_hit: the image to show the button
                has been pressed
                img_path_no_hit: the image to show the button
                has not been pressed
                x: the x coordinate of the button
                y: the y coordinate of the button
                rotate: tells if the button needs to be rotated
            """
            self.img_hit = img_path_hit
            self.img_no_hit = img_path_no_hit
            self.img_shown = self.img_no_hit
            self.x = x
            self.y = y
            self.pressed = False

        def press(self):
            """
            Presses the button, changing its state and image
            """
            self.pressed = True
            self.img_shown = self.img_hit

        def stop_press(self):
            """
            Unpresses the button, changing its state and image
            """
            self.pressed = False
            self.img_shown = self.img_no_hit


class MobileRobotDrawing(RobotDrawing):

    def __init__(self, drawing: drawing.Drawing, n_light_sens,
                 drawing_width=6300, drawing_height=4300,
                 start_x=500, start_y=500):
        """
        Constructor for mobile robot
        Arguments:
            drawing: the drawing where the robot is going
            to be represented
            n_light_sens: the number of light sensors of the
            robot
            drawing_width: width of the world (canvas) the robot
            moves on. Enlarged for the infinite circuit
            drawing_height: height of the world (canvas)
            start_x: initial x position of the robot (centred on
            the world for the infinite circuit)
            start_y: initial y position of the robot
        """
        super().__init__(drawing)
        self.img_mobrob = "assets/mobile-robot.png"

        self.drawing_width = drawing_width
        self.drawing_height = drawing_height
        self.x = start_x
        self.y = start_y
        self.real_x = self.x
        self.real_y = self.y
        self.width = 516
        self.height = 584
        self.vl = 0
        self.vr = 0
        self.angle = 90
        self.n_light_sens = n_light_sens
        self.sensors = {}

        self.create_robot()

    def create_robot(self):
        """
        Creates the robot with all of its pieces
        """
        self.robot = {
            "x": self.x,
            "y": self.y,
            "image": self.img_mobrob
        }
        self.sensors["light"] = []
        init_diff = 30
        if self.n_light_sens == 4:
            init_diff = 105
        for i in range(0, self.n_light_sens):
            self.sensors["light"].append(
                self.LightSensor(
                    self.x - init_diff + (70 * i),
                    self.y - 110
                )
            )
        self.sensors["sound"] = self.UltrasoundSensor(
            self.x - 30,
            self.y - 285,
            7630
        )

    def draw(self):
        """
        Draws the robot with all of its elements
        """
        self.drawing.draw_image(self.robot, "robot")
        self.drawing.rotate_image(
            {
                "x": self.x,
                "y": self.y,
                "image": self.img_mobrob
            },
            self.angle - 90,
            "robot"
        )
        i = 1
        for sens in self.sensors["light"]:
            self.drawing.draw_image(sens.get_image(), "light_{}".format(i))
            i += 1

    def predict_movement(self, vel):
        """
        Predicts the future position of the robot. Used to
        check if a collision with an object will happen
        Arguments:
            vel: the velocity of the robot (with no axis)
        Returns:
            The predicted coordinates of the robot (tuple)
        """
        angle = self.angle * pi / 180
        vx = -vel * cos(angle)
        vy = vel * sin(angle)
        real_x = self.real_x + vx
        real_y = self.real_y + vy
        x = self.x
        y = self.y
        if real_x != x or real_y != y:
            x = int(real_x)
            y = int(real_y)
        return (x, y)

    def move(self, vel):
        """
        Moves the robot
        Arguments:
            vel: the velocity that the robot is going at,
            from it the velocity in each axis is calculated
            by using sin and cos with the angle
        """
        self.vl = -vel * 25
        self.vr = -vel * 25
        angle = self.angle * pi / 180
        vx = -vel * cos(angle)
        vy = vel * sin(angle)
        if self.__update_coords(vx, vy):
            self.drawing.move_image("robot", self.x, self.y)
            i = 1
            for sens in self.sensors["light"]:
                self.drawing.move_image("light_{}".format(i), sens.x, sens.y)
                i += 1

    def change_angle(self, d_angle):
        """
        Changes robot's angle when turning
        Arguments:
            d_angle: the number of degrees that the robot
            is going to rotate. Can be + or -
        """
        self.vl = -d_angle * 50
        self.vr = d_angle * 50
        if self.angle + d_angle >= 0 and self.angle + d_angle <= 360:
            self.angle += d_angle
        else:
            if self.angle + d_angle < 0:
                self.angle = 360 + (self.angle + d_angle)
            else:
                self.angle = (self.angle + d_angle) - 360
        if d_angle != 0:
            self.drawing.rotate_image(
                {
                    "x": self.x,
                    "y": self.y,
                    "image": self.img_mobrob
                },
                self.angle - 90,
                "robot"
            )
            self.__rotate_sensors(d_angle)

    def repaint_light_sensors(self):
        """
        Repaints the light sensors
        """
        i = 1
        for sens in self.sensors["light"]:
            self.drawing.redraw_image(sens.get_image(), "light_{}".format(i))
            i += 1

    def configure_distance(self, dist_sens):
        """
        Configures the distance of detection of the ultrasounds
        Arguments:
            dist_sens: the distance at which the sensor returns True
        """
        self.sensors["sound"].dist = dist_sens

    def __update_coords(self, dx, dy):
        """
        Updates the coordinates of the different components
        of the robot. It does so by updating the real position
        and when it changes compared to the coordinates, this are
        updated.
        Arguments:
            dx: the change on x coordinates
            dy: the change on y coordinates
        """
        self.real_x += dx
        self.real_y += dy
        for sens in self.sensors["light"]:
            dx_sens = sens.real_x + dx
            dy_sens = sens.real_y + dy
            sens.change_coords(dx_sens, dy_sens)
        dx_sens = self.sensors["sound"].real_x + dx
        dy_sens = self.sensors["sound"].real_y + dy
        self.sensors["sound"].change_coords(dx_sens, dy_sens)
        if self.__check_change_coords():
            self.x = int(self.real_x)
            self.y = int(self.real_y)
            self.robot["x"] = self.x
            self.robot["y"] = self.y
            return True
        return False

    def __check_change_coords(self):
        """
        Checks if the real coords (real_x and real_y)
        are different when they are truncated, compared
        to the int ones (x and y)
        """
        x = int(self.real_x)
        y = int(self.real_y)
        return self.x != x or self.y != y

    def __rotate_sensors(self, da):
        """
        Rotates the sensors taking the robot position
        as reference so they can move based on the radius
        Arguments:
            da: the differential of angle
        """
        i = 1
        for sens in self.sensors["light"]:
            x, y = self.__rotate_center(
                (sens.real_x, sens.real_y),
                (self.x, self.y),
                da
            )
            sens.change_coords(self.x + x, self.y + y)
            img = sens.get_image()
            self.drawing.redraw_image(img, "light_{}".format(i))
            i += 1
        x, y = self.__rotate_center(
            (self.sensors["sound"].real_x, self.sensors["sound"].real_y),
            (self.x, self.y),
            da
        )
        self.sensors["sound"].change_coords(self.x + x, self.y + y)

    def __rotate_center(self, tp, c, da):
        """
        Rotates a component relative to a center
        Arguments:
            tp: point to be translated. Tuple = (x, y)
            c: center point. Tuple = (x, y)
            da: number of degrees to rotate (sixagesimal)
        """
        abs_px = tp[0] - c[0]
        abs_py = tp[1] - c[1]
        rads = da * (pi / 180)  # degrees to radians

        # Rotate
        cos_r = cos(rads)
        sin_r = sin(rads)
        x = (abs_px * cos_r) + (abs_py * sin_r)
        y = (-abs_px * sin_r) + (abs_py * cos_r)

        return (x, y)

    class Sensor:

        def __init__(self, x, y):
            """
            Constructor for sensor
            Arguments:
                x: the x position of the sensor
                y: the y position of the sensor
            """
            self.x = x
            self.y = y
            self.real_x = self.x
            self.real_y = self.y
            self.img_shown = None

        def change_coords(self, x, y):
            """
            Moves the real coordinates of the sensor (double cooords)
            Arguments:
                x: the new real x coordinate
                y: the new real y coordinate
            """
            self.real_x = x
            self.real_y = y
            self.x = int(self.real_x)
            self.y = int(self.real_y)

        def get_image(self):
            """
            Converts the image to a dictionary so the drawing
            can parse it:
            Returns:
                A dictionary with the following keys:
                    x: the x coordinate
                    y: the y coordinate
                    image: the image to represent
            """
            if self.img_shown is not None:
                return {
                    "x": self.x,
                    "y": self.y,
                    "image": self.img_shown
                }
            return None

    class LightSensor(Sensor):

        def __init__(self, x, y):
            """
            Constructor for light sensor
            Arguments:
                x: the x position of the sensor
                y: the y position of the sensor
            """
            super().__init__(x, y)
            self.img_light = "assets/light-bright.png"
            self.img_dark = "assets/light-dark.png"
            self.img_shown = self.img_light

        def light(self):
            """
            Changes the sensor to light
            """
            self.img_shown = self.img_light

        def dark(self):
            """
            Changes the sensor to dark
            """
            self.img_shown = self.img_dark

    class UltrasoundSensor(Sensor):

        def __init__(self, x, y, dist):
            """
            Constructor for ultrasound sensor
            Arguments:
                x: the x position of the sensor
                y: the y position of the sensor
                dist: the distance to check
            """
            super().__init__(x, y)
            self.dist = dist
            self.is_detecting = False

        def set_detect(self, is_detecting):
            """
            Changes the state of the sensor
            Arguments:
                is_detecting: True if detects, False if else
            """
            self.is_detecting = is_detecting


class ArduinoBoardDrawing(RobotDrawing):

    def __init__(self, drawing: drawing.Drawing):
        """
        Constructor for arduino board drawing
        Arguments:
            drawing: the drawing where the robot is going
            to be represented
        """
        super().__init__(drawing)

        self.drawing_width = 6300
        self.drawing_height = 4300
        self.x = 500
        self.y = 500
        self.real_x = self.x
        self.real_y = self.y
        self.width = 516
        self.height = 584
        self.create_robot()
        self.drawing.set_robot(robot=self)

    def create_robot(self):
        """
        Creates the board
        """
        self.board = {
            "x": self.x,
            "y": self.y,
            "image": "assets/arduinoBoard.png"
        }

    def draw(self):
        """
        Draws the board
        """
        self.drawing.draw_image(self.board, "arduinoBoard")


class Circuit:

    def __init__(self, parts, drawing: drawing.Drawing):
        """
        Constructor for Circuit
        Arguments:
            parts: a list with circuit*s parts (map with
            orientation: length)
            drawing: the drawing where the circuit is
            going to be represented
        """
        self.parts = parts
        self.circuit_parts = []
        self.drawing = drawing
        self.ROAD_WIDTH = 100

    def create_circuit(self):
        """
        Creates and draws a circuit
        """
        self.create_straights()
        self.draw_circuit()

    def create_straights(self):
        """
        Creates all the circuit pieces
        """
        x = 550
        y = 550
        saved_coords = []
        for part in self.parts:
            if part['type'] == 'straight':
                save = False
                extend_saved = []
                if 'load' in str(part['anchor']).split():
                    x, y = saved_coords.pop()
                if "x" in part:
                    self.__create_straight(x, y, part["x"], self.ROAD_WIDTH)
                    if part['save'] != '':
                        extend_saved = self.__save_coords_x(x, y, part)
                    x, save = self.__update_straight_x(x, part)
                elif "y" in part:
                    self.__create_straight(x, y, self.ROAD_WIDTH, part["y"])
                    if part['save'] != '':
                        extend_saved = self.__save_coords_y(x, y, part)
                    y, save = self.__update_straight_y(y, part)
                if save:
                    saved_coords.extend(extend_saved)
                    saved_coords.append((x, y))
            elif part['type'] == 'turn':
                x, y = self.__correct_turn_start(x, y, part)
                self.__create_turn(
                    x, y, part['bounding_len'], part['angle'], part['starting_angle'],
                    self.ROAD_WIDTH)
                x, y = self.__correct_turn_end(x, y, part)
            elif part['type'] == 'id':
                self.__create_id(x, y, part["dist"], self.ROAD_WIDTH, part["number"])
                x += part["dist"]


    def __save_coords_x(self, x, y, part):
        list_coords = []
        list_pos = str(part['save']).split(" ")
        for pos in list_pos:
            cop_x = x
            if pos == 'end':
                cop_x += part["x"]
            elif pos == 'mid':
                cop_x += part["x"] / 2 - self.ROAD_WIDTH / 2
            elif pos == '1/4':
                cop_x += part["x"] / 4
            elif pos == '3/4':
                cop_x += part["x"] * 3 / 4
            list_coords.append((cop_x, y))
        return list_coords

    def __save_coords_y(self, x, y, part):
        list_coords = []
        list_pos = str(part['save']).split(" ")
        for pos in list_pos:
            cop_y = y
            if pos == 'end':
                cop_y += part["y"]
            elif pos == 'mid':
                cop_y += part["y"] / 2 - self.ROAD_WIDTH / 2
            elif pos == '1/4':
                cop_y += part["y"] / 4
            elif pos == '3/4':
                cop_y += part["y"] * 3 / 4
            list_coords.append((x, cop_y))
        return list_coords

    def __update_straight_x(self, x, part):
        position, save = self.__split_anchor(part)
        if position == 'end':
            x += part["x"]
        elif position == 'mid':
            x += part["x"] / 2 - self.ROAD_WIDTH / 2
        return x, save

    def __update_straight_y(self, y, part):
        position, save = self.__split_anchor(part)
        if position == 'end':
            y += part["y"]
        elif position == 'mid':
            y += part["y"] / 2 - self.ROAD_WIDTH / 2
        return y, save

    def __split_anchor(self, part):
        anchor_split = str(part['anchor']).split(" ")
        position = anchor_split[0]
        save = False
        if 'save' in anchor_split:
            save = True
        return position, save

    def __correct_turn_start(self, xcoord, ycoord, turn):
        """
        Fixes the starting point of the turn
        Arguments:
            xcoord: the current x coord
            ycoord: the current y coord
            turn: the turn that is being fixed
        """
        x = xcoord
        y = ycoord

        start_angle = turn['starting_angle']
        angle = turn['angle']

        if start_angle == 0:
            if angle > 0:
                x -= turn['bounding_len'] - self.ROAD_WIDTH / 2
                y += turn['bounding_len'] - self.ROAD_WIDTH / 2
            else:
                x -= turn['bounding_len'] - self.ROAD_WIDTH / 2
                y -= turn['bounding_len'] / 2
        elif start_angle == 90:
            if angle > 0:
                x += self.ROAD_WIDTH / 2
                y -= turn['bounding_len'] / 2
            else:
                x -= turn['bounding_len'] / 2
                y += self.ROAD_WIDTH / 2
        elif start_angle == 180:
            if angle > 0:
                x -= turn['bounding_len'] / 2 - self.ROAD_WIDTH
                y -= turn['bounding_len'] - self.ROAD_WIDTH / 2
            else:
                x += self.ROAD_WIDTH / 2
                y -= turn['bounding_len'] / 2
        if start_angle == 270:
            if angle > 0:
                x -= turn['bounding_len'] / 2
                y -= turn['bounding_len'] - self.ROAD_WIDTH / 2
            else:
                x -= turn['bounding_len'] / 2 - self.ROAD_WIDTH
                y -= turn['bounding_len'] - self.ROAD_WIDTH / 2
        return (x, y)

    def __correct_turn_end(self, xcoord, ycoord, turn):
        """
        Fixes the starting point of the turn
        Arguments:
            xcoord: the current x coord
            ycoord: the current y coord
            turn: the turn that is being fixed
        """
        x = xcoord
        y = ycoord

        starting_angle = turn['starting_angle']
        angle = turn['angle']

        if starting_angle == 0:
            if angle > 0:
                x += turn['bounding_len'] / 2 - self.ROAD_WIDTH / 2
                y -= self.ROAD_WIDTH / 2
            else:
                x += turn['bounding_len'] / 2 - self.ROAD_WIDTH
                y += turn['bounding_len'] - self.ROAD_WIDTH / 2
        elif starting_angle == 90:
            if angle > 0:
                x += turn['bounding_len'] / 2
                y -= self.ROAD_WIDTH / 2
            else:
                x += turn['bounding_len'] - self.ROAD_WIDTH / 2
                y += turn['bounding_len'] / 2
        elif starting_angle == 180:
            if angle > 0:
                x -= self.ROAD_WIDTH / 2
                y += turn['bounding_len'] / 2
            else:
                x += turn['bounding_len'] / 2
                y -= self.ROAD_WIDTH / 2
        elif starting_angle == 270:
            if angle > 0:
                x += turn['bounding_len'] - self.ROAD_WIDTH / 2
                y -= turn['bounding_len'] - self.ROAD_WIDTH / 2
            else:
                x -= self.ROAD_WIDTH / 2
                y += turn['bounding_len'] / 2 - self.ROAD_WIDTH / 2
        return (x, y)

    def draw_circuit(self):
        """
        Draws the circuit
        """
        for part in self.circuit_parts:
            part.draw(self.drawing)

    def __create_straight(self, x, y, width, height):
        """
        Creates a straight
        Arguments:
            x: the x coordinate of the straight
            y: the y coordinate of the straight
            width: the width of the straight
            heigth: the height of the straight
        """
        if width < 0:
            x += self.ROAD_WIDTH
            x += width
            width *= -1
        if height < 0:
            y += self.ROAD_WIDTH
            y += height
            height *= -1
        self.circuit_parts.append(
            self.CircuitStraight(x, y, width, height)
        )
    def __create_id(self, x, y, width, height, number):
        """
        Creates a straight
        Arguments:
            x: the x coordinate of the straight
            y: the y coordinate of the straight
            width: the width of the straight
            heigth: the height of the straight
        """
        if width < 0:
            x += self.ROAD_WIDTH
            x += width
            width *= -1
        if height < 0:
            y += self.ROAD_WIDTH
            y += height
            height *= -1
        self.circuit_parts.append(
            self.CircuitId(x, y, width, height, number)
        )
    def __create_turn(self, x, y, bounding_len, angle, starting_angle, track_width):
        """
        Creates a turn
        Arguments:
            x: the x coordinate of the turn
            y: the y coordinate of the turn
            width: the length of turn's bounding box
            angle: the angle that is covered by the turn
            track_width: the width of the track
        """
        self.circuit_parts.append(
            self.CircuitTurn(x, y, bounding_len, bounding_len,
                             angle, starting_angle, track_width)
        )

    def is_overlapping(self, x, y):
        """
        Checks if the coordinates are overlapping with the circuit
        Arguments:
            x: the x coordinate to check
            y: the y coordinate to check
        Returns:
            True if is overlapping, False if else
        """
        overlap = False
        for part in self.circuit_parts:
            overlap = part.check_overlap(x, y)
            if overlap:
                break
        return overlap

    class CircuitPart:

        def __init__(self, x, y):
            """
            Constructor for circuit straight
            Arguments:
                x: the x coordinate of the part
                y: the y coordinate of the part
            """
            self.x = x
            self.y = y

        def draw(self, drawing: drawing.Drawing):
            """
            Draws the circuit part
            """
            pass

        def check_overlap(self, x, y):
            """
            Checks if the point is overlapped with the
            circuit
            """
            pass


    class CircuitStraight(CircuitPart):

        def __init__(self, x, y, width, height):
            """
            Constructor for circuit straight
            Arguments:
                x: the x coordinate of the straight
                y: the y coordinate of the straight
                width: the width of the straight
                heigth: the height of the straight
            """
            super().__init__(x, y)
            self.width = width
            self.height = height

        def draw(self, drawing: drawing.Drawing):
            drawing.draw_rectangle(
                {
                    "x": self.x,
                    "y": self.y,
                    "width": self.width,
                    "height": self.height,
                    "color": "black",
                    "group": "circuit"
                }
            )

        def check_overlap(self, x, y):
            """
            Checks if the point is overlapped with the
            circuit
            """
            return (
                (
                    x >= self.x
                    and x <= self.x + self.width
                ) and (
                    y >= self.y
                    and y <= self.y + self.height
                )
            )

    class CircuitId(CircuitStraight):

            def __init__(self, x, y, width, height, number):
                """
                Constructor for circuit straight
                Arguments:
                x: the x coordinate of the id
                y: the y coordinate of the id
                width: the width of the id
                heigth: the height of the id
                number: the identifier of the id
                """
                super().__init__(x, y, width, height)
                self.number = number

            def draw(self, drawing: drawing.Drawing):
                temp = self.number
                bits = []
                for cont in range(3):
                    bits.append((temp >> cont) % 2)
                bits.append(0)
                bits.reverse()
                for cont, bit in enumerate(bits):
                    drawing.draw_rectangle(
                        {
                            "x": self.x + (2 * cont + 1) * self.width / 8,
                            "y": self.y,
                            "width": self.width / 8,
                            "height": self.height,
                            "color": "black",
                            "group": "circuit"
                        }
                    )
                    if bit:
                        drawing.draw_rectangle(
                            {
                                "x": self.x + cont * self.width / 4,
                                "y": self.y - 2 * self.height,
                                "width": self.width / 8,
                                "height": 5 * self.height,
                                "color": "black",
                                "group": "circuit"
                            }
                        )
            def check_overlap(self, x, y):
                """
                Checks if the point is overlapped with the
                circuit
                """
                temp = self.number
                bits = []
                for cont in range(3):
                    bits.append((temp >> cont) % 2)
                bits.append(0)
                bits.reverse()
                for cont, bit in enumerate(bits):
                    if ((self.x + (2 * cont + 1) * self.width / 8 <= x
                         <= self.x + (2 * cont + 2) * self.width / 8)
                        and
                        (self.y <= y <= self.y + self.height)
                        ):
                        return True
                    if bit:
                        if ((self.x + cont * self.width / 4 <= x
                             <= self.x + (2 * cont + 1) * self.width / 8)
                            and
                            (self.y - 2 * self.height <= y <= self.y + 2 * self.height)
                            ):
                            return True
                return False

    class CircuitTurn(CircuitPart):

        def __init__(self, x, y, width, height, angle, starting_angle, track_width):
            """
            Constructor for circuit turns
            Arguments:
                x: the x coordinate of the turn
                y: the y corrdinate of the turn
                width: the width of the arc box
                height: the height of the arc box
                angle: the angle that is covered by the turn
                starting_angle: the angle of start
                track_width: the width of the turn
            """
            super().__init__(x, y)
            self.width = width
            self.height = height
            self.angle = angle
            self.starting_angle = starting_angle
            if angle < 0:
                self.angle = abs(angle)
                self.starting_angle += angle
                if self.starting_angle < 0:
                    self.starting_angle += 360
            self.track_width = track_width
            self.center = (x + width / 2, y + height / 2)
            self.radius = sqrt((self.center[0] - x) ** 2)

        def draw(self, drawing: drawing.Drawing):
            drawing.draw_arc(
                {
                    "x": self.x,
                    "y": self.y,
                    "width": self.width,
                    "height": self.height,
                    "track_width": self.track_width,
                    "angle": self.angle,
                    "starting_angle": self.starting_angle,
                    "group": "circuit"
                }
            )

        def check_overlap(self, x, y):
            """
            Checks if the point is overlapped with the turn
            """
            r_in = self.radius - (self.track_width / 2)
            r_out = self.radius + (self.track_width / 2)

            dist = sqrt(
                ((x - self.center[0]) ** 2)
                + ((y - self.center[1]) ** 2)
            )

            inside_arc = (
                dist >= r_in
                and dist <= r_out
            )

            if inside_arc:
                dx = x - self.center[0]
                dy = y - self.center[1]
                inside_angle = atan2(dy, dx) * (180 / pi)
                if inside_angle < 0:
                    inside_angle += 360
                inside_angle = abs(inside_angle - 360)
                end_angle = self.starting_angle + self.angle
                if end_angle == 0:
                    end_angle = 360
                return (
                    inside_angle
                    and self.starting_angle <= inside_angle <= end_angle
                )
            return False


class Obstacle:

    def __init__(self, obstacle, drawing: drawing.Drawing):
        """
        Constructor for Obstacle
        Arguments:
            obstacle: an obstacle (map with int x, y, width and height)
            drawing: the drawing in which the obstacle will
            be drawn
        """
        self.x = obstacle['x']
        self.y = obstacle['y']
        self.width = obstacle['width']
        self.height = obstacle['height']
        self.drawing = drawing

    def draw(self):
        """
        Draws the obstacle in the corresponding drawing
        """
        self.drawing.draw_rectangle(
            {
                "x": self.x,
                "y": self.y,
                "width": self.width,
                "height": self.height,
                "color": "orange",
                "group": "obstacle"
            }
        )

    def calculate_distance(self, sx, sy, angle):
        """
        Checks if is detected by the ultrasound sensor.
        It does so by using the sin or cos (depending on
        if it's x coordinate or y coordinate) and the coordinate.
        With it, we have the distance, so we get a point with
        the angle and the distance (and sin or cos, to get the
        other coordinate). Can be done by using basic trigonometry
        Arguments:
            sx: the x coordinate of the sensor
            sy: the y coordinate of the sensor
            angle: the angle of the line (from ox)
        Returns:
            True if is detected, False if else
        """
        # Abs coords of obstacle
        x1 = self.x - sx
        x2 = self.x + self.width - sx
        y1 = self.y - sy
        y2 = self.y + self.height - sy
        rads = angle * (pi / 180)

        # Distance
        if angle % 90 != 0 or angle % 180 == 0:
            dist_x1 = int(abs(x1 / cos(rads)))
            dist_x2 = int(abs(x2 / cos(rads)))
        else:
            dist_x1 = "inf"
            dist_x2 = "inf"
        if angle % 180 != 0:
            dist_y1 = int(abs(y1 / sin(rads)))
            dist_y2 = int(abs(y2 / sin(rads)))
        else:
            dist_y1 = "inf"
            dist_y2 = "inf"

        # Point distance
        def dy(d, r):
            return int(-sin(r) * d)

        def dx(d, r):
            return int(cos(r) * d)

        dist = -1

        # 10 coords in each point to ensure the fixed coord is inside
        if dist_x1 != "inf":
            px1 = (dx(dist_x1, rads), dy(dist_x1, rads))
            if self.__check_inbounds(px1[0] + sx + 10, px1[1] + sy):
                if dist == -1 or dist_x1 < dist:
                    dist = dist_x1
        if dist_x2 != "inf":
            px2 = (dx(dist_x2, rads), dy(dist_x2, rads))
            if self.__check_inbounds(px2[0] + sx - 10, px2[1] + sy):
                if dist == -1 or dist_x2 < dist:
                    dist = dist_x2
        if dist_y1 != "inf":
            py1 = (dx(dist_y1, rads), dy(dist_y1, rads))
            if self.__check_inbounds(py1[0] + sx, py1[1] + sy + 10):
                if dist == -1 or dist_y1 < dist:
                    dist = dist_y1
        if dist_y2 != "inf":
            py2 = (dx(dist_y2, rads), dy(dist_y2, rads))
            if self.__check_inbounds(py2[0] + sx, py2[1] + sy - 10):
                if dist == -1 or dist_y2 < dist:
                    dist = dist_y2

        return dist

    def __check_inbounds(self, x, y):
        """
        Checks if a point is inbounds of the obstacle (caution with
        absolute coordinates)
        Arguments:
            x: the x coordinate of the point
            y: the y coordinate of the point
        Returns:
            True if inbounds, False if else
        """
        return (
            self.x <= x <= (self.x + self.width)
            and self.y <= y <= (self.y + self.height)
        )


class Trail:
    """
    The path the robot leaves behind itself on the infinite circuit.

    It is drawn to look like the road of the regular circuits: a black band of
    the same width (``ROAD_WIDTH``) sitting underneath the robot. It stores the
    visited world positions (un-scaled coordinates) so the whole trail can be
    redrawn at the current scale after a zoom, exactly like the wires do.
    """

    # Same road width the circuits use (Circuit.ROAD_WIDTH), so the trail
    # matches the look of the other tracks.
    ROAD_WIDTH = 100

    def __init__(self, drawing: drawing.Drawing, color="black", width=ROAD_WIDTH):
        """
        Arguments:
            drawing: the drawing where the trail is represented
            color: the colour of the trail (black, like the road)
            width: the trail width in world units (scaled when drawn)
        """
        self.drawing = drawing
        self.color = color
        self.width = width
        self.points = []  # world coordinates (x, y)

    def reset(self):
        """
        Clears the stored path (used when a new run starts).
        """
        self.points = []

    def add_point(self, x, y):
        """
        Adds a new world position and draws the segment from the previous
        one. Repeated positions (no real movement) are ignored.
        Arguments:
            x: the world x coordinate of the robot
            y: the world y coordinate of the robot
        """
        if self.points:
            x0, y0 = self.points[-1]
            if int(x0) == int(x) and int(y0) == int(y):
                return
            self.__draw_segment(x0, y0, x, y)
        self.points.append((x, y))

    def draw(self):
        """
        Redraws the whole trail at the current scale (e.g. after a zoom).
        """
        for i in range(1, len(self.points)):
            x0, y0 = self.points[i - 1]
            x1, y1 = self.points[i]
            self.__draw_segment(x0, y0, x1, y1)

    def __draw_segment(self, x1, y1, x2, y2):
        """
        Draws a single road segment scaling the world coordinates to canvas
        coordinates (same convention as Drawing.draw_rectangle). Round caps
        and joins make consecutive segments blend into a continuous band, and
        the segment is pushed to the bottom so the robot stays on top.
        """
        canvas = self.drawing.canvas
        if canvas is None:
            return
        scale = self.drawing.scale
        line_id = canvas.create_line(
            x1 * scale, y1 * scale + self.drawing.hud_h,
            x2 * scale, y2 * scale + self.drawing.hud_h,
            tags="trail", fill=self.color,
            width=max(1, int(self.width * scale)),
            capstyle="round", joinstyle="round")
        # Keep the road underneath the robot and the sensors
        canvas.tag_lower(line_id)
