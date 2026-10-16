import tkinter as tk
from tkinter import Scrollbar, Text
from PIL import ImageTk, Image
import robot_components.robots as rbts
import subprocess
import os
import robot_components.robots as robots

from pathlib import Path


class Drawing:

    def __init__(self):
        """
        Constructor for the drawing
        """
        self.canvas = None
        self.robot = None
        self.images = {}
        self.canvas_images = {}
        self.scale = 0.2
        self.component = 0
        self.components = []
        self.hud_w = 0
        self.hud_h = 0
        self.dx = 0
        self.dy = 0
        self.robots = []
        self.initialize_robots()
        self.wires = []
        self.buttons = []
        self.button = 0
        self.component_to_attach = None
        self.pin_component_to_attach = 0
        self.component_to_attach_x = 0
        self.component_to_attach_y = 0
        self.board = None
        self.points = 10

    def set_canvas(self, canvas: tk.Canvas):
        """
        Sets the canvas in which the drawing is going to be done
        Arguments:
            canvas: the canvas
        """
        self.canvas = canvas

    def setBoard(self, board):
        self.board = board

    def initialize_robots(self):
        """
        Initialise the combobox of Arduino challenges
        :return:
        """
        robot0 = rbts.Challenge0Robot(self)
        self.robots.append(robot0)
        robot1 = rbts.Challenge1Robot(self)
        self.robots.append(robot1)
        robot2 = rbts.Challenge2Robot(self)
        self.robots.append(robot2)
        robot3 = rbts.Challenge3Robot(self)
        self.robots.append(robot3)
        robot4 = rbts.Challenge4Robot(self)
        self.robots.append(robot4)
        robot5 = rbts.Challenge5Robot(self)
        self.robots.append(robot5)
        robot6 = rbts.Challenge6Robot(self)
        self.robots.append(robot6)

    def set_robot(self, robot):
        self.robot = robot

    def empty_drawing(self):
        """
        Deletes all elements from the drawing
        """
        self.canvas.delete('all')
        self.canvas_images = {}
        self.wires = []
        self.buttons = []

    def delete_zoomables(self):
        """
        Deletes all the elements that have to be zoomed
        """
        self.canvas.delete('actuator', 'button_left', 'button_right', 'block', 'arduinoBoard')
        self.canvas.delete('robot', 'circuit', 'obstacle', 'wire', 'trail',
                           'light_1', 'light_2', 'light_3', 'light_4')
        self.canvas.delete('prueba')
        for component in self.components:
            self.canvas.delete(component["group"])
        for button in self.buttons:
            self.canvas.delete(button["group"])

    def draw_image(self, element, group):
        """
        Draws an image
        Arguments:
            element: a dict whose content is the x and y
            coordinates and the image (as Image instance)
            group: the tag where the image is going to
            be added to
        """
        image = self.__open_image(element["image"], group)
        return self.__add_to_canvas(element["x"], element["y"], image, group)

    def redraw_image(self, element, group):
        """
        Redraws an already existing image
        Arguments:
            element: a dict whose content is the x and y
            coordinates and the image (as Image instance)
            group: the tag where the image is going to
            be added to
        """
        self.canvas.delete(group)
        del self.canvas_images[group]
        image = self.__open_image(element["image"], group)
        self.__add_to_canvas(element["x"], element["y"], image, group)

    def move_image(self, group, x, y):
        """
        Moves a image (or group of) of the drawing
        Arguments:
            group: the tag of the image(s)
            x: the x differential
            y: the y differential
        """
        current_x = self.canvas_images[group]["x"]
        current_y = self.canvas_images[group]["y"]
        scale_x = int(x * self.scale)
        scale_y = int(y * self.scale)
        dx = scale_x - current_x
        dy = scale_y - current_y
        self.canvas_images[group]["x"] = scale_x
        self.canvas_images[group]["y"] = scale_y
        self.canvas.move(group, dx, dy)

    def rotate_image(self, element, angle, group):
        """
        Rotates a image by an angle
        Arguments:
            element: a dict whose elements are the x and
            y coordinates and the image (as str path)
            angle: the differential of the angle
            group: the group of the image(s)
        """
        self.canvas.delete(group)
        image = self.__open_image(element["image"], group)
        rotated_img = self.images[element["image"]
        ] = image.rotate(angle, expand=True)
        self.__add_to_canvas(element["x"], element["y"], rotated_img, group)

    def draw_rectangle(self, form: dict):
        """
        Draws a rectangle given some measurements
        Arguments:
            form: a dictionary whose elements are the x and
            y coordinates, the width and height of the
            rectangle and the color and group (tag of tkinter)
        """
        x = int(form["x"] * self.scale)
        y = int(form["y"] * self.scale) + self.hud_h
        width = int(form["width"] * self.scale)
        height = int(form["height"] * self.scale)
        color = form["color"]
        group = form["group"]
        self.canvas.create_rectangle(
            x, y, x + width, y + height, fill=color, tags=group)

    def draw_part_wire(self, x, y):
        if self.component_to_attach is not None:
            self.draw_wire(x + self.dx, y + self.dy, self.component_to_attach_x + self.dx,
                           self.component_to_attach_y + self.dy)
            self.component_to_attach_x = x
            self.component_to_attach_y = y
            return True
        else:
            return False

    def draw_wire(self, x1, y1, x2, y2):
        self.canvas.create_line(x1, y1, x2, y2, tags='wire', fill="blue", width=2)
        wire = {
            "x1": x1 / self.scale,
            "y1": y1 / self.scale,
            "x2": x2 / self.scale,
            "y2": y2 / self.scale
        }
        self.wires.append(wire)

    def redraw_wire(self):
        for wire in self.wires:
            x1 = wire['x1'] * self.scale
            y1 = wire['y1'] * self.scale
            x2 = wire['x2'] * self.scale
            y2 = wire['y2'] * self.scale
            self.canvas.create_line(x1, y1, x2, y2, tags='wire', fill="blue", width=2)

    def draw_arc(self, form: dict):
        """
        Draws an arc given some measurements
        Arguments:
            form: a dictionary whose elements are the x and y
            coordinates, the width and height of the bounding of
            the arc, the width of the arc, the angle of the arc
            and the group (tag of tkinter)
        """
        x = int(form["x"] * self.scale)
        y = int(form["y"] * self.scale) + self.hud_h
        width = int(form["width"] * self.scale)
        height = int(form["height"] * self.scale)
        track_width = int(form["track_width"] * self.scale)
        starting_angle = form["starting_angle"]
        angle = form["angle"]
        group = form["group"]
        self.canvas.create_arc(x, y, x + width, y + height, width=track_width, style="arc", start=starting_angle,
                               extent=angle, tags=group)


    def zoom_in(self):
        """
        Zooms in the scale and updates the drawing
        It contains the Max zoom in (1)
        """
        if self.scale < 1:
            self.scale += 0.1
        self.scale = round(self.scale, 1)
        self.__update_size()

    def zoom_out(self):
        """
        Zooms out the scale and updates the drawing
        It contains the Max zoom in (0.1)
        """
        if self.scale > 0.1:
            self.scale -= 0.1
        self.scale = round(self.scale, 1)
        self.__update_size()

    def zoom_percentage(self):
        """
        Returns the zoom percentage to be shown in the GUI
        """
        return self.scale * 100

    def set_size(self, width, height):
        """
        Sets the size limits of the canvas
        Arguments:
            width: the width of the canvas
            height: the height of the canvas
        """
        self.width = width
        self.height = height
        self.__update_size()

    def __update_size(self):
        """
        Updates the size of the canvas according
        to the scale and the size of it
        """
        w = self.width * self.scale
        h = self.height * self.scale
        self.canvas.configure(scrollregion=(0, 0, w, h))

    def __add_to_canvas(self, x, y, image: Image, group):
        """
        Adds an image to the canvas
        Arguments:
            x: the x coordinate of the image
            y: the y coordinate of the image
            image: the image to add (as Image instance)
            group: the group (tag of tkinter)
        """
        width = int(image.width * self.scale)
        height = int(image.height * self.scale)
        res_img = image.resize((width, height), Image.LANCZOS)
        scale_x = x * self.scale
        scale_y = y * self.scale + self.hud_h
        self.canvas_images[group] = {
            "x": scale_x,
            "y": scale_y,
            "image": ImageTk.PhotoImage(res_img)
        }
        return self.canvas.create_image(
            scale_x, scale_y, image=self.canvas_images[group]["image"], tags=group)

    def __open_image(self, image_path, group):
        image = None
        if group not in self.images:
            image = self.__get_image(image_path, group)
        elif not self.images[group]["path"] == image_path:
            image = self.__get_image(image_path, group)
        else:
            image = self.images[group]["image"]
        return image

    def __get_image(self, image_path, group):
        image = Image.open(image_path)
        self.images[group] = {
            "image": image,
            "path": image_path
        }
        return image

    def draw_component(self, element, x, y):
        x_total = (x + self.dx) / self.scale
        y_total = (y + self.dy) / self.scale
        image = element.draw_self(x_total, y_total, self.component)
        self.draw_image(image, image["group"])
        self.components.append(image)
        self.component += 1
        self.draw_buttons(element, x_total, y_total)

    def draw_all_components(self):
        for component in self.components:
            self.draw_image(component, component["group"])

    def initialize_points(self):
        self.points = 10

    def probe(self, option_gamification, user_code, robot_code, user_robot, robot):
        self.probe_window = tk.Toplevel()
        self.probe_window.geometry("800x450")
        self.probe_window.title("Resultado desafío " + str(option_gamification))
        self.probe_window.configure(background="#006468")
        code = False
        circuit = False

        if not user_code.replace(" ", "").replace("\n", "").replace("\t", "") == \
               robot_code.replace(" ", "").replace("\n", "").replace("\t", ""):
            sol_code = tk.Label(self.probe_window, text="El código no es correcto",
                                font=("Arial", 15), background="#006468")
            self.decrement_points(1)
        else:
            code = True
            sol_code = tk.Label(self.probe_window, text="Código OK", font=("Arial", 15), background="#006468")
        sol_code.pack(padx=10, pady=20)

        errors = robot.probe_robot(user_robot)
        if len(errors) == 0:
            circuit = True
            sol_robot = tk.Label(self.probe_window, text="Robot OK", font=("Arial", 15), background="#006468")
            sol_robot.pack(padx=10, pady=20)
        else:
            sol_robot = tk.Label(self.probe_window, text="El robot no es correcto. ERRORES:",
                                 font=("Arial", 15), background="#006468")
            self.decrement_points(1)
            sol_robot.pack(padx=10, pady=20)
            for error in errors:
                sol_robot = tk.Label(self.probe_window, text=error, font=("Arial", 15), background="#006468")
                sol_robot.pack(padx=10, pady=10)
        if code and circuit:
            correct = tk.Label(self.probe_window, text="DESAFÍO CORRECTO. NOTA OBTENIDA: " + str(self.points),
                               font=("Arial", 15), background="#006468")
            correct.pack(padx=10, pady=20)
        return code, circuit

    def decrement_points(self, quantity):
        self.points -= quantity
        if self.points < 0:
            self.points = 0


    def show_tutorial(self):
        path = "tutorials/Tutorial.pdf"
        subprocess.Popen([os.path.abspath(path)], shell=True)


    def show_results(self):
        folder = 'gamification_logs'
        log = "No hay resultados que mostrar"

        if not os.path.exists(folder):
            Path(folder).mkdir(parents=True, exist_ok=True)

        if os.path.exists(folder+"/resultados.txt"):
            path = folder+"/resultados.txt"
            with open(path, 'r', encoding='utf-8') as log:
                log = log.read()

        self.results_window = tk.Toplevel()
        self.results_window.geometry("950x600")
        self.results_window.title("Resultados")
        self.results_window.configure(background="#006468")
        scrollbar = Scrollbar(self.results_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text = Text(self.results_window, font=("Arial", 15), background="#006468", yscrollcommand=scrollbar.set)
        text.pack(padx=10, pady=20, fill=tk.BOTH)
        scrollbar.config(command=text.yview)
        text.insert(tk.END, log)
        text.config(state=tk.DISABLED)
        self.results_window.mainloop()

    def show_help(self, option_gamification):
        self.help_window = tk.Toplevel()
        self.help_window.geometry("600x620")
        self.help_window.title("Ayuda desafío " + str(option_gamification))
        self.help_window.configure(background="#006468")
        ayuda = tk.Label(self.help_window, text=self.get_robot_challenge(option_gamification).get_help(),
                         font=("Arial", 15), background="#006468")
        ayuda.pack(padx=10, pady=20)

    def get_robot_challenge(self, option_gamification):
        if option_gamification == 0:
            return self.robots[0]
        if option_gamification == 1:
            return self.robots[1]
        if option_gamification == 2:
            return self.robots[2]
        if option_gamification == 3:
            return self.robots[3]
        if option_gamification == 4:
            return self.robots[4]
        if option_gamification == 5:
            return self.robots[5]
        if option_gamification == 6:
            return self.robots[6]

    def attach(self, component1, pin_component1, component2, pin_component2):
        if isinstance(component1, Drawing) or isinstance(component1, robots.ArduinoBoard):
            self.board.attach_pin(pin_component1, component2)
            component2.attach_element(pin_component2, self.board, pin_component1)
        elif isinstance(component2, Drawing) or isinstance(component2, robots.ArduinoBoard):
            self.board.attach_pin(pin_component2, component1)
            component1.attach_element(pin_component1, self.board, pin_component2)
        else:
            component1.attach_element(pin_component1, component2, pin_component2)
            component2.attach_element(pin_component2, component1, pin_component1)

    def attach_component(self, component, pin, x, y):
        if self.component_to_attach is None:
            """Si todavía no se ha seleccionado el primer componente, se selecciona"""
            self.component_to_attach = component
            self.component_to_attach_x = x
            self.component_to_attach_y = y
            self.pin_component_to_attach = pin
        elif component is self.component_to_attach:
            """Si el segundo componente seleccionado es el mismo que el primero se actualiza el pin seleccionado"""
            self.component_to_attach = component
            self.component_to_attach_x = x
            self.component_to_attach_y = y
            self.pin_component_to_attach = pin
        elif component is not None and component is not self.component_to_attach:
            """Si ya se ha seleccionado anteriormente un componente, se unen ambos"""
            self.attach(self.component_to_attach, self.pin_component_to_attach, component, pin)
            self.draw_part_wire(x, y)
            self.component_to_attach = None
            self.component_to_attach_x = 0
            self.component_to_attach_y = 0
            self.pin_component_to_attach = 0

    def draw_buttons(self, element, x, y):
        buttons = element.draw_buttons(x, y)
        for button in buttons:
            x_total = button['x']
            y_total = button['y']
            button1 = {
                "x": x_total,
                "y": y_total,
                "image": "assets/point.png",
                "group": "button" + str(self.button),
                "element": self,
                "n_pin": button['n_pin']
            }
            self.buttons.append(button1)
            self.button += 1
            self.asign_function(button1, element)

    def draw_all_buttons(self):
        for button in self.buttons:
            self.draw_image(button, button['group'])
            self.asign_function(button, button['element'])

    def asign_function(self, button, element):
        img = self.draw_image(button, button["group"])
        if button['n_pin'] == 1:
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin1(element, event))
        elif button['n_pin'] == 2:
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin2(element, event))
        elif button['n_pin'] == 3:
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin3(element, event))
        elif button['n_pin'] == 4:
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin4(element, event))
        elif button['n_pin'] == 5:
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin5(element, event))
        elif button['n_pin'] == 6:
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin6(element, event))
        elif button['n_pin'] == 7:
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin7(element, event))
        elif button['n_pin'] == 8:
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin8(element, event))
        elif button['n_pin'] == "pin0":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb0(element, event))
        elif button['n_pin'] == "pin1":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb1(element, event))
        elif button['n_pin'] == "pin2":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb2(element, event))
        elif button['n_pin'] == "pin3":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb3(element, event))
        elif button['n_pin'] == "pin4":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb4(element, event))
        elif button['n_pin'] == "pin5":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb5(element, event))
        elif button['n_pin'] == "pin6":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb6(element, event))
        elif button['n_pin'] == "pin7":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb7(element, event))
        elif button['n_pin'] == "pin8":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb8(element, event))
        elif button['n_pin'] == "pin9":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb9(element, event))
        elif button['n_pin'] == "pin10":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb10(element, event))
        elif button['n_pin'] == "pin11":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb11(element, event))
        elif button['n_pin'] == "pin12":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb12(element, event))
        elif button['n_pin'] == "pin13":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pinb13(element, event))
        elif button['n_pin'] == "pinA0":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pina0(element, event))
        elif button['n_pin'] == "pinA1":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pina1(element, event))
        elif button['n_pin'] == "pinA2":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pina2(element, event))
        elif button['n_pin'] == "pinA3":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pina3(element, event))
        elif button['n_pin'] == "pinA4":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pina4(element, event))
        elif button['n_pin'] == "pinA5":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pina5(element, event))
        elif button['n_pin'] == "pin3V":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin3v(element, event))
        elif button['n_pin'] == "pin5V":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin5v(element, event))
        elif button['n_pin'] == "pinGND1":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin_gnd1(element, event))
        elif button['n_pin'] == "pinGND2":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin_gnd2(element, event))
        elif button['n_pin'] == "pinGND3":
            self.canvas.tag_bind(img, "<Button-1>", lambda event: self.select_pin_gnd3(element, event))

    def select_pin1(self, element, event):
        self.attach_component(element, 1, event.x, event.y)

    def select_pin2(self, element, event):
        self.attach_component(element, 2, event.x, event.y)

    def select_pin3(self, element, event):
        self.attach_component(element, 3, event.x, event.y)

    def select_pin4(self, element, event):
        self.attach_component(element, 4, event.x, event.y)

    def select_pin5(self, element, event):
        self.attach_component(element, 5, event.x, event.y)

    def select_pin6(self, element, event):
        self.attach_component(element, 6, event.x, event.y)

    def select_pin7(self, element, event):
        self.attach_component(element, 7, event.x, event.y)

    def select_pin8(self, element, event):
        self.attach_component(element, 8, event.x, event.y)

    def select_pinb0(self, element, event):
        self.attach_component(element, 0, event.x, event.y)

    def select_pinb1(self, element, event):
        self.attach_component(element, 1, event.x, event.y)

    def select_pinb2(self, element, event):
        self.attach_component(element, 2, event.x, event.y)

    def select_pinb3(self, element, event):
        self.attach_component(element, 3, event.x, event.y)

    def select_pinb4(self, element, event):
        self.attach_component(element, 4, event.x, event.y)

    def select_pinb5(self, element, event):
        self.attach_component(element, 5, event.x, event.y)

    def select_pinb6(self, element, event):
        self.attach_component(element, 6, event.x, event.y)

    def select_pinb7(self, element, event):
        self.attach_component(element, 7, event.x, event.y)

    def select_pinb8(self, element, event):
        self.attach_component(element, 8, event.x, event.y)

    def select_pinb9(self, element, event):
        self.attach_component(element, 9, event.x, event.y)

    def select_pinb10(self, element, event):
        self.attach_component(element, 10, event.x, event.y)

    def select_pinb11(self, element, event):
        self.attach_component(element, 11, event.x, event.y)

    def select_pinb12(self, element, event):
        self.attach_component(element, 12, event.x, event.y)

    def select_pinb13(self, element, event):
        self.attach_component(element, 13, event.x, event.y)

    def select_pina0(self, element, event):
        self.attach_component(element, 14, event.x, event.y)

    def select_pina1(self, element, event):
        self.attach_component(element, 15, event.x, event.y)

    def select_pina2(self, element, event):
        self.attach_component(element, 16, event.x, event.y)

    def select_pina3(self, element, event):
        self.attach_component(element, 17, event.x, event.y)

    def select_pina4(self, element, event):
        self.attach_component(element, 18, event.x, event.y)

    def select_pina5(self, element, event):
        self.attach_component(element, 19, event.x, event.y)

    def select_pin3v(self, element, event):
        self.attach_component(element, 20, event.x, event.y)

    def select_pin5v(self, element, event):
        self.attach_component(element, 21, event.x, event.y)

    def select_pin_gnd1(self, element, event):
        self.attach_component(element, 22, event.x, event.y)

    def select_pin_gnd2(self, element, event):
        self.attach_component(element, 23, event.x, event.y)

    def select_pin_gnd3(self, element, event):
        self.attach_component(element, 24, event.x, event.y)
