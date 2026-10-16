import re
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
import tkinter.ttk as ttk
import graphics.controller as controller
import files.files_reader as files
import subprocess
import robot_components.robots as robots

DARK_BLUE = "#006468"
BLUE = "#17a1a5"


class MainApplication(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Simulador Software para Robots")
        self.geometry("1280x720")
        # self.iconbitmap('assets/simlogo.ico')

        self.menu_bar = MenuBar(self, self)

        self.tools_frame = tk.Frame(self, bg=DARK_BLUE)
        self.button_bar = ButtonBar(self.tools_frame, self, bg=DARK_BLUE)
        self.selector_bar = SelectorBar(self.tools_frame, self, bg=DARK_BLUE)

        self.vertical_pane = tk.PanedWindow(
            orient=tk.VERTICAL, sashpad=5, sashrelief="solid", bg=DARK_BLUE)
        self.horizontal_pane = tk.PanedWindow(
            self.vertical_pane, orient=tk.HORIZONTAL, sashpad=5, sashrelief="solid", bg=BLUE)
        self.drawing_frame = DrawingFrame(
            self.horizontal_pane, self, bg=BLUE)
        self.editor_frame = EditorFrame(self.horizontal_pane, bg=BLUE)
        self.console_frame = ConsoleFrame(
            self.vertical_pane, self, bg=DARK_BLUE)

        self.identifier = None
        self.controller = controller.RobotsController(self)
        self.prepare_controller()
        self.keys_used = True
        self.file_manager = files.FileManager()

        self.config(menu=self.menu_bar)
        self.button_bar.pack(fill=tk.X, side="left")
        self.selector_bar.pack(fill=tk.X, side="right")
        # These keys are the accepted ones for move the application. If you need more keys, added them here
        self.move_WASD = {
            "W": False,
            "A": False,
            "S": False,
            "D": False,
            "w": False,
            "a": False,
            "s": False,
            "d": False
        }

        self.tools_frame.pack(fill=tk.X)
        self.vertical_pane.pack(fill="both", expand=True)

        self.horizontal_pane.add(
            self.drawing_frame, stretch="first", width=1100, minsize=100)
        self.horizontal_pane.add(self.editor_frame, minsize=100)
        self.vertical_pane.add(self.horizontal_pane,
                               stretch="first", minsize=100)
        self.vertical_pane.add(
            self.console_frame, stretch="never", height=200, minsize=100)

        self.bind("<KeyPress>", self.key_press)
        self.bind("<KeyRelease>", self.key_release)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.challenge = 0

    def prepare_controller(self):
        self.__update_robot()  # call first so the robot_layer is created
        self.controller.configure_layer(self.drawing_frame.canvas,
                                        self.drawing_frame.hud_canvas)  # call second so the canvas are initialized
        # call third so the console is initialized
        self.controller.configure_console(self.console_frame.console)
        # call last so all the three elements that are configured before are initialized
        self.__update_track()
        # if not, the track raises exception

    def execute(self, event=None):
        self.drawing_frame.canvas.focus_force()
        self.controller.execute(self.selector_bar.gamification_option_selector.current())

    def stop(self, event=None):
        self.controller.stop()

    # ----------------------------------------------------- Gemelo digital MQTT
    def toggle_digital_twin_mode(self, event=None):
        if self.selector_bar.twin_var.get():
            self.selector_bar.show_twin_controls()
            self.selector_bar.hide_arduino_robot()
            self.console_frame.show_twin_button()
        else:
            if self.controller.is_twin_active():
                self.controller.disconnect_twin()
            self.selector_bar.hide_twin_controls()
            self.selector_bar.recover_arduino_robot()
            self.console_frame.hide_twin_button()

    def mqtt_connect(self, event=None):
        if self.controller.is_twin_active():
            self.controller.disconnect_twin()
        else:
            self.controller.connect_twin(self.selector_bar.theme_entry.get())

    def mqtt_disconnect(self, event=None):
        self.controller.disconnect_twin()

    def mqtt_toggle_control(self, event=None):
        self.controller.toggle_twin_control()

    def on_twin_connected(self):
        self.selector_bar.set_connected(True)
        self.selector_bar.show_control_button()

    def on_twin_disconnected(self):
        self.selector_bar.set_connected(False)
        self.selector_bar.hide_control_button()

    def on_twin_control_changed(self, controlling):
        self.selector_bar.set_controlling(controlling)
    # --------------------------------------------------- Fin Gemelo digital MQTT

    def editor_undo(self):
        self.editor_frame.text.edit_undo()

    def editor_redo(self):
        self.editor_frame.text.edit_redo()

    def open_file(self, event=None):
        self.editor_frame.text.delete("1.0", tk.END)
        file = askopenfilename(filetypes=[("Arduino sketch", ".ino")])
        if file != '':
            content = self.file_manager.open(file)
            for line in content:
                self.editor_frame.text.insert(tk.END, f"{line}")

    def save_file(self, event=None):
        content = self.editor_frame.text.get("1.0", tk.END)
        file = asksaveasfilename(defaultextension=".ino", filetypes=[
            ("Arduino sketch", ".ino")])
        if file != '':
            self.file_manager.save(file, content)

    def get_code(self):
        return self.editor_frame.text.get("1.0", tk.END)

    def open_pin_configuration(self, event=None):
        """
        Top level window to configure pins connected to the
        Arduino board
        """
        robot = self.selector_bar.robot_selector.current()
        PinConfigurationWindow(self, robot, self)

    def zoom_in(self):
        self.controller.zoom_in()

    def zoom_out(self):
        self.controller.zoom_out()

    def change_zoom_label(self, zoom_level):
        self.drawing_frame.change_zoom_label(zoom_level)

    def change_robot(self, event):
        self.controller.stop()
        self.__update_robot()
        self.__update_track()  # Needed to set the circuit of the layer
        self.__update_gamification_option()
        self.__update_editor_frame_text()
        self.console_frame.console.config(state=tk.NORMAL)
        self.console_frame.console.insert(tk.END, "Robot cambiado con éxito\n")
        self.console_frame.console.config(state=tk.DISABLED)
        self.controller.robot_layer.is_drawing = False
        self.drawing_frame.key_drawing.deselect()

    def __update_robot(self):
        robot = self.selector_bar.robot_selector.current()
        self.controller.change_robot(robot)
        self.controller.configure_layer(
            self.drawing_frame.canvas, self.drawing_frame.hud_canvas)

    def change_track(self, event):
        self.controller.stop()
        self.__update_track()

    def change_gamification_option(self, event):
        self.controller.record_results(False, self.challenge)
        self.challenge = self.selector_bar.gamification_option_selector.current()
        self.controller.stop()
        self.__update_editor_frame_text()
        self.__update_gamification_option()
        self.controller.robot_layer.is_drawing = False
        self.drawing_frame.key_drawing.deselect()
        self.controller.delete_elements()

    def __update_track(self):
        circuit = self.selector_bar.track_selector.current()
        robot = self.selector_bar.robot_selector.current()
        if robot in (0, 1, 2):  # Aquí hay que mejorar los tipos de robots
            self.controller.change_circuit(circuit)
        self.controller.configure_layer(
            self.drawing_frame.canvas, self.drawing_frame.hud_canvas)

    def __update_editor_frame_text(self):
        if self.controller.board:
            challenge = self.selector_bar.gamification_option_selector.current()
            code = self.controller.robot_layer.drawing.get_robot_challenge(challenge).get_initial_code()
            self.editor_frame.change_text(code)

    def __update_gamification_option(self):
        if self.controller.board:
            challenge = self.selector_bar.gamification_option_selector.current()
            self.console_frame.console.config(state=tk.NORMAL)
            self.console_frame.console.delete("1.0", "end")
            self.show_buttons_gamification(True)
            text = "Nuevo intento. Puntuación inicial: 10\n\n"
            if challenge == 0:
                self.console_frame.console.insert(tk.END,
                                                  self.controller.robot_layer.drawing.
                                                  get_robot_challenge(0).get_challenge())
            if challenge == 1:
                self.console_frame.console.insert(tk.END,
                                                  self.controller.robot_layer.drawing.
                                                  get_robot_challenge(1).get_challenge())
            if challenge == 2:
                self.console_frame.console.insert(tk.END,
                                                  self.controller.robot_layer.drawing.
                                                  get_robot_challenge(2).get_challenge())
            if challenge == 3:
                self.console_frame.console.insert(tk.END,
                                                  self.controller.robot_layer.drawing.
                                                  get_robot_challenge(3).get_challenge())
            if challenge == 4:
                self.console_frame.console.insert(tk.END,
                                                  self.controller.robot_layer.drawing.
                                                  get_robot_challenge(4).get_challenge())
            if challenge == 5:
                self.console_frame.console.insert(tk.END,
                                                  self.controller.robot_layer.drawing.
                                                  get_robot_challenge(5).get_challenge())
            if challenge == 6:
                self.console_frame.console.insert(tk.END,
                                                  self.controller.robot_layer.drawing.
                                                  get_robot_challenge(6).get_challenge())
            self.controller.consoleGamification.write_encrypted(text, challenge + 1)
            self.console_frame.console.config(state=tk.DISABLED)
            self.controller.configure_layer(
                self.drawing_frame.canvas, self.drawing_frame.hud_canvas)
            self.controller.robot_layer.drawing.initialize_points()
            self.controller.new = True

    def show_circuit_selector(self, showing):
        if showing:
            self.selector_bar.recover_circuit_selector()
        else:
            self.selector_bar.hide_circuit_selector()

    def show_gamification_option_selector(self, showing):
        if showing:
            self.selector_bar.recover_gamification_option_selector()
        else:
            self.selector_bar.hide_gamification_option_selector()

    def show_joystick(self, showing):
        if showing:
            self.drawing_frame.show_joystick()
        else:
            self.drawing_frame.hide_joystick()

    def show_button_keys_movement(self, showing):
        if showing:
            self.drawing_frame.show_button_keys_movement()
        else:
            self.drawing_frame.hide_button_keys_movement()

    def show_buttons_gamification(self, showing):
        if showing:
            self.drawing_frame.show_buttons_gamification()
        else:
            self.drawing_frame.hide_buttons_gamification()

    def show_hud(self, showing):
        if showing:
            self.drawing_frame.show_hud()
        else:
            self.drawing_frame.hide_hud()

    def show_keys_movements(self, show):
        """
        Show or hide the checkbox Keys Movement from the Hub
        :param show: boolean
        :return: None
        """
        if show:
            self.drawing_frame.key_movement.pack()
        else:
            self.drawing_frame.key_movement.forget()

    def show_key_drawing(self, show):
        """
        Show or hide the checkbox Drawing from the Hub
        :param show: boolean
        :return: None
        """
        if show:
            self.drawing_frame.key_drawing.pack()
        else:
            self.drawing_frame.key_drawing.forget()

    def _typing_in_text_widget(self):
        """True si el foco está en un campo de texto (consola, tema, editor,
        configuración de pines...). En ese caso WASD escribe, no mueve el robot."""
        widget = self.focus_get()
        return isinstance(widget, (tk.Entry, tk.Text, ttk.Entry, ttk.Combobox))

    def _clear_movement(self):
        """Suelta todas las teclas de movimiento (evita que una quede 'pulsada')."""
        for key in self.move_WASD:
            self.move_WASD[key] = False

    def key_press(self, event):
        # Mientras se escribe en un campo de texto, no se mueve el robot en ejecución.
        if self._typing_in_text_widget():
            self._clear_movement()
            return
        pressed_key = event.char
        if pressed_key in self.move_WASD:
            self.move_WASD[pressed_key] = True

    def key_release(self, event):
        if self._typing_in_text_widget():
            self._clear_movement()
            return
        pressed_key = event.char
        if pressed_key in self.move_WASD:
            self.move_WASD[pressed_key] = False

    def abort_after(self):
        if self.identifier is not None:
            self.after_cancel(self.identifier)

    def console_filter(self):
        msg_filters = {}
        if self.console_frame.output.get() == 1:
            msg_filters['info'] = True
        else:
            msg_filters['info'] = False
        if self.console_frame.warning.get() == 1:
            msg_filters['warning'] = True
        else:
            msg_filters['warning'] = False
        if self.console_frame.error.get() == 1:
            msg_filters['error'] = True
        else:
            msg_filters['error'] = False
        self.controller.filter_console(msg_filters)

    def toggle_keys(self):
        self.keys_used = not self.keys_used

    def set_drawing(self):
        self.controller.robot_layer.is_drawing = not self.controller.robot_layer.is_drawing
        if self.controller.robot_layer.is_drawing:
            self.controller.robot_layer.hud.drawing = None

    def close(self):
        self.controller.exit()
        self.controller.record_results(False, self.challenge)
        self.stop()
        if self.controller.is_twin_active():
            self.controller.disconnect_twin()
        self.destroy()


class PinConfigurationWindow(tk.Toplevel):

    def __init__(self, parent, robot_option, application: MainApplication = None, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.focus_force()
        self.application = application
        self.data = {}

        frame_content = tk.Frame(self)
        frame_buttons = tk.Frame(self)
        self.robot_option = robot_option

        # Actuator
        self.lb_actuator = tk.Label(frame_content, text="Actuador lineal:")
        self.lb_pin_bt1 = tk.Label(
            frame_content, text="Pin final izquierdo:", underline=10)
        self.entry_pin_bt1 = tk.Entry(frame_content)
        self.lb_pin_bt2 = tk.Label(
            frame_content, text="Pin final derecho:", underline=10)
        self.entry_pin_bt2 = tk.Entry(frame_content)
        self.lb_pin_joystick = tk.Label(
            frame_content, text="Pin botón Joystick:", underline=10)
        self.entry_pin_joystick = tk.Entry(frame_content)
        self.lb_pin_aservo = tk.Label(
            frame_content, text="Pin Servo:", underline=4)
        self.entry_pin_aservo = tk.Entry(frame_content)
        self.lb_pin_joystick_x = tk.Label(
            frame_content, text="Pin Joystick (x):", underline=14)
        self.entry_pin_joystick_x = tk.Entry(frame_content)
        self.lb_pin_joystick_y = tk.Label(
            frame_content, text="Pin Joystick (y):", underline=14)
        self.entry_pin_joystick_y = tk.Entry(frame_content)

        self.lb_mobile = tk.Label(frame_content, text="Robot móvil")
        self.lb_pin_servo1 = tk.Label(
            frame_content, text="Pin servo izquierdo:", underline=10)
        self.entry_pin_se1 = tk.Entry(frame_content)
        self.lb_pin_servo2 = tk.Label(
            frame_content, text="Pin servo derecho:", underline=7)
        self.entry_pin_se2 = tk.Entry(frame_content)
        self.lb_pin_light2 = tk.Label(
            frame_content, text="Pin luz izquierda:", underline=9)
        self.entry_pin_l2 = tk.Entry(frame_content)
        self.lb_pin_light3 = tk.Label(
            frame_content, text="Pin luz derecha:", underline=10)
        self.entry_pin_l3 = tk.Entry(frame_content)
        self.lb_pin_light1 = tk.Label(
            frame_content, text="Pin luz mas izquierda:", underline=14)
        self.entry_pin_l1 = tk.Entry(frame_content)
        self.lb_pin_light4 = tk.Label(
            frame_content, text="Pin luz mas derecha:", underline=17)
        self.entry_pin_l4 = tk.Entry(frame_content)
        self.lb_pin_sound1 = tk.Label(
            frame_content, text="Pin trigger:", underline=4)
        self.entry_pin_so1 = tk.Entry(frame_content)
        self.lb_pin_sound2 = tk.Label(
            frame_content, text="Pin echo:", underline=4)
        self.entry_pin_so2 = tk.Entry(frame_content)

        self.lb_board = tk.Label(frame_content, text="Placa arduino")
        self.lb_arduinoBoardComponent = tk.Entry(frame_content)

        self.btn_accept = tk.Button(
            frame_buttons, text="Aceptar", command=self.commit_data, underline=0)
        self.btn_cancel = tk.Button(
            frame_buttons, text="Cancelar", command=self.destroy, underline=0)

        if robot_option == 0:
            self.show_for_mobile2()
        if robot_option == 1:
            self.show_for_mobile3()
        if robot_option == 2:
            self.show_for_mobile4()
        if robot_option == 3:
            self.show_for_actuator()
        if robot_option == 4:
            self.show_for_arduinoboard()

        self.btn_accept.grid(row=0, column=0, sticky="se", padx=(0, 10))
        self.btn_cancel.grid(row=0, column=1, sticky="se")

        frame_content.pack(padx=5, pady=5)
        frame_buttons.pack(anchor="se", padx=5, pady=5)

        x = (parent.winfo_x() + (parent.winfo_width() / 2)) - \
            (self.winfo_reqwidth() / 2)
        y = (parent.winfo_y() + (parent.winfo_height() / 2)) - \
            (self.winfo_reqheight() / 2)
        self.geometry("+%d+%d" % (x, y))
        self.resizable(False, False)

        self.bind("<Alt-a>", self.commit_data)
        self.bind("<Alt-c>", lambda event: self.destroy())

    def commit_data(self, event=None):
        pin_data = {}
        if 'servo_left' in self.data:
            value = self.entry_pin_se1.get()
            if self.data['servo_left'] != value:
                pin_data['servo_left'] = value
        if 'servo_right' in self.data:
            value = self.entry_pin_se2.get()
            if self.data['servo_right'] != value:
                pin_data['servo_right'] = value
        if 'light_mleft' in self.data:
            value = self.entry_pin_l1.get()
            if self.data['light_mleft'] != value:
                pin_data['light_mleft'] = value
        if 'light_left' in self.data:
            value = self.entry_pin_l2.get()
            if self.data['light_left'] != value:
                pin_data['light_left'] = value
        if 'light_right' in self.data:
            value = self.entry_pin_l3.get()
            if self.data['light_right'] != value:
                pin_data['light_right'] = value
        if 'light_mright' in self.data:
            value = self.entry_pin_l4.get()
            if self.data['light_mright'] != value:
                pin_data['light_mright'] = value
        if 'sound_trig' in self.data:
            value = self.entry_pin_so1.get()
            if self.data['sound_trig'] != value:
                pin_data['sound_trig'] = value
        if 'sound_echo' in self.data:
            value = self.entry_pin_so2.get()
            if self.data['sound_echo'] != value:
                pin_data['sound_echo'] = value
        if 'button_left' in self.data:
            value = self.entry_pin_bt1.get()
            if self.data['button_left'] != value:
                pin_data['button_left'] = value
        if 'button_right' in self.data:
            value = self.entry_pin_bt2.get()
            if self.data['button_right'] != value:
                pin_data['button_right'] = value
        if 'servo' in self.data:
            value = self.entry_pin_aservo.get()
            if self.data['servo'] != value:
                pin_data['servo'] = value
        if 'button_joystick' in self.data:
            value = self.entry_pin_joystick.get()
            if self.data['button_joystick'] != value:
                pin_data['button_joystick'] = value
        if 'joystick_x' in self.data:
            value = self.entry_pin_joystick_x.get()
            if self.data['joystick_x'] != value:
                pin_data['joystick_x'] = value
        if 'joystick_y' in self.data:
            value = self.entry_pin_joystick_y.get()
            if self.data['joystick_y'] != value:
                pin_data['joystick_y'] = value
        self.application.controller.save_pin_data(pin_data)
        self.destroy()

    def show_for_mobile2(self):
        """
        Shows the window with the components needed to
        configure the mobile robot which has 2 light sensors
        """
        self.data = self.application.controller.get_pin_data()

        self.lb_mobile.grid(row=0, column=0, sticky="w")
        self.lb_pin_servo1.grid(row=1, column=0, sticky="w")
        self.entry_pin_se1.grid(row=1, column=1, sticky="w", padx=5)
        self.lb_pin_servo2.grid(row=1, column=2, sticky="w")
        self.entry_pin_se2.grid(row=1, column=3, sticky="w", padx=5)
        self.lb_pin_light2.grid(row=2, column=0, sticky="w")
        self.entry_pin_l2.grid(row=2, column=1, sticky="w", padx=5)
        self.lb_pin_light3.grid(row=2, column=2, sticky="w")
        self.entry_pin_l3.grid(row=2, column=3, sticky="w", padx=5)
        self.lb_pin_sound1.grid(row=4, column=0, sticky="w")
        self.entry_pin_so1.grid(row=4, column=1, sticky="w", padx=5)
        self.lb_pin_sound2.grid(row=4, column=2, sticky="w")
        self.entry_pin_so2.grid(row=4, column=3, sticky="w", padx=5)

        self.entry_pin_se1.insert(tk.END, self.data["servo_left"])
        self.entry_pin_se2.insert(tk.END, self.data["servo_right"])
        self.entry_pin_l2.insert(tk.END, self.data["light_left"])
        self.entry_pin_l3.insert(tk.END, self.data["light_right"])
        self.entry_pin_so1.insert(tk.END, self.data["sound_trig"])
        self.entry_pin_so2.insert(tk.END, self.data["sound_echo"])

        self.bind("<Alt-i>", lambda event: self.entry_pin_se1.focus())
        self.bind("<Alt-v>", lambda event: self.entry_pin_se2.focus())
        self.bind("<Alt-z>", lambda event: self.entry_pin_l2.focus())
        self.bind("<Alt-r>", lambda event: self.entry_pin_l3.focus())
        self.bind("<Alt-t>", lambda event: self.entry_pin_so1.focus())
        self.bind("<Alt-e>", lambda event: self.entry_pin_so2.focus())

    def show_for_mobile3(self):
        """
        Shows the window with the components needed to
        configure the mobile robot which has 3 light sensors
        """
        self.data = self.application.controller.get_pin_data()

        self.lb_mobile.grid(row=0, column=0, sticky="w")
        self.lb_pin_servo1.grid(row=1, column=0, sticky="w")
        self.entry_pin_se1.grid(row=1, column=1, sticky="w", padx=5)
        self.lb_pin_servo2.grid(row=1, column=2, sticky="w")
        self.entry_pin_se2.grid(row=1, column=3, sticky="w", padx=5)
        self.lb_pin_light2.grid(row=2, column=0, sticky="w")
        self.entry_pin_l2.grid(row=2, column=1, sticky="w", padx=5)
        self.lb_pin_light3.grid(row=2, column=2, sticky="w")
        self.entry_pin_l3.grid(row=2, column=3, sticky="w", padx=5)
        self.lb_pin_light1.grid(row=3, column=0, sticky="w")
        self.entry_pin_l1.grid(row=3, column=1, sticky="w", padx=5)
        # self.lb_pin_light4.grid(row=3, column=2, sticky="w")
        # self.entry_pin_l4.grid(row=3, column=3, sticky="w", padx=5)
        self.lb_pin_sound1.grid(row=4, column=0, sticky="w")
        self.entry_pin_so1.grid(row=4, column=1, sticky="w", padx=5)
        self.lb_pin_sound2.grid(row=4, column=2, sticky="w")
        self.entry_pin_so2.grid(row=4, column=3, sticky="w", padx=5)

        self.entry_pin_se1.insert(tk.END, self.data["servo_left"])
        self.entry_pin_se2.insert(tk.END, self.data["servo_right"])
        self.entry_pin_l1.insert(tk.END, self.data["light_mleft"])
        self.entry_pin_l2.insert(tk.END, self.data["light_left"])
        self.entry_pin_l3.insert(tk.END, self.data["light_right"])
        # self.entry_pin_l4.insert(tk.END, self.data["light_mright"])
        self.entry_pin_so1.insert(tk.END, self.data["sound_trig"])
        self.entry_pin_so2.insert(tk.END, self.data["sound_echo"])

        self.bind("<Alt-i>", lambda event: self.entry_pin_se1.focus())
        self.bind("<Alt-v>", lambda event: self.entry_pin_se2.focus())
        self.bind("<Alt-z>", lambda event: self.entry_pin_l2.focus())
        self.bind("<Alt-r>", lambda event: self.entry_pin_l3.focus())
        self.bind("<Alt-q>", lambda event: self.entry_pin_l1.focus())
        # self.bind("<Alt-h>", lambda event: self.entry_pin_l4.focus())
        self.bind("<Alt-t>", lambda event: self.entry_pin_so1.focus())
        self.bind("<Alt-e>", lambda event: self.entry_pin_so2.focus())

    def show_for_mobile4(self):
        """
        Shows the window with the components needed to
        configure the mobile robot which has 4 light sensors
        """
        self.data = self.application.controller.get_pin_data()

        self.lb_mobile.grid(row=0, column=0, sticky="w")
        self.lb_pin_servo1.grid(row=1, column=0, sticky="w")
        self.entry_pin_se1.grid(row=1, column=1, sticky="w", padx=5)
        self.lb_pin_servo2.grid(row=1, column=2, sticky="w")
        self.entry_pin_se2.grid(row=1, column=3, sticky="w", padx=5)
        self.lb_pin_light2.grid(row=2, column=0, sticky="w")
        self.entry_pin_l2.grid(row=2, column=1, sticky="w", padx=5)
        self.lb_pin_light3.grid(row=2, column=2, sticky="w")
        self.entry_pin_l3.grid(row=2, column=3, sticky="w", padx=5)
        self.lb_pin_light1.grid(row=3, column=0, sticky="w")
        self.entry_pin_l1.grid(row=3, column=1, sticky="w", padx=5)
        self.lb_pin_light4.grid(row=3, column=2, sticky="w")
        self.entry_pin_l4.grid(row=3, column=3, sticky="w", padx=5)
        self.lb_pin_sound1.grid(row=4, column=0, sticky="w")
        self.entry_pin_so1.grid(row=4, column=1, sticky="w", padx=5)
        self.lb_pin_sound2.grid(row=4, column=2, sticky="w")
        self.entry_pin_so2.grid(row=4, column=3, sticky="w", padx=5)

        self.entry_pin_se1.insert(tk.END, self.data["servo_left"])
        self.entry_pin_se2.insert(tk.END, self.data["servo_right"])
        self.entry_pin_l1.insert(tk.END, self.data["light_mleft"])
        self.entry_pin_l2.insert(tk.END, self.data["light_left"])
        self.entry_pin_l3.insert(tk.END, self.data["light_right"])
        self.entry_pin_l4.insert(tk.END, self.data["light_mright"])
        self.entry_pin_so1.insert(tk.END, self.data["sound_trig"])
        self.entry_pin_so2.insert(tk.END, self.data["sound_echo"])

        self.bind("<Alt-i>", lambda event: self.entry_pin_se1.focus())
        self.bind("<Alt-v>", lambda event: self.entry_pin_se2.focus())
        self.bind("<Alt-z>", lambda event: self.entry_pin_l2.focus())
        self.bind("<Alt-r>", lambda event: self.entry_pin_l3.focus())
        self.bind("<Alt-q>", lambda event: self.entry_pin_l1.focus())
        self.bind("<Alt-h>", lambda event: self.entry_pin_l4.focus())
        self.bind("<Alt-t>", lambda event: self.entry_pin_so1.focus())
        self.bind("<Alt-e>", lambda event: self.entry_pin_so2.focus())

    def show_for_actuator(self):
        """
        Shows the window with the components needed to
        configure the actuator
        """
        self.data = self.application.controller.get_pin_data()

        self.lb_actuator.grid(row=0, column=0, sticky="w")
        self.lb_pin_bt1.grid(row=1, column=0, sticky="w")
        self.entry_pin_bt1.grid(row=1, column=1, sticky="w", padx=5)
        self.lb_pin_bt2.grid(row=1, column=2, sticky="w")
        self.entry_pin_bt2.grid(row=1, column=3, sticky="w", padx=5)
        self.lb_pin_joystick.grid(row=2, column=0, sticky="w")
        self.entry_pin_joystick.grid(row=2, column=1, sticky="w", padx=5)
        self.lb_pin_aservo.grid(row=2, column=2, sticky="w")
        self.entry_pin_aservo.grid(row=2, column=3, sticky="w", padx=5)
        self.lb_pin_joystick_x.grid(row=3, column=0, sticky="w")
        self.entry_pin_joystick_x.grid(row=3, column=1, sticky="w", padx=5)
        self.lb_pin_joystick_y.grid(row=3, column=2, sticky="w")
        self.entry_pin_joystick_y.grid(row=3, column=3, sticky="w", padx=5)

        self.entry_pin_bt1.insert(tk.END, self.data["button_left"])
        self.entry_pin_bt2.insert(tk.END, self.data["button_right"])
        self.entry_pin_joystick.insert(tk.END, self.data["button_joystick"])
        self.entry_pin_aservo.insert(tk.END, self.data["servo"])
        self.entry_pin_joystick_x.insert(tk.END, self.data["joystick_x"])
        self.entry_pin_joystick_y.insert(tk.END, self.data["joystick_y"])

        self.bind("<Alt-i>", lambda event: self.entry_pin_bt1.focus())
        self.bind("<Alt-d>", lambda event: self.entry_pin_bt2.focus())
        self.bind("<Alt-j>", lambda event: self.entry_pin_joystick.focus())
        self.bind("<Alt-s>", lambda event: self.entry_pin_aservo.focus())
        self.bind("<Alt-x>", lambda event: self.entry_pin_joystick_x.focus())
        self.bind("<Alt-y>", lambda event: self.entry_pin_joystick_y.focus())

    def show_for_arduinoboard(self):
        """
        Shows the window with the components needed to
        configure the arduino board which has an arduino board
        """
        self.data = self.application.controller.get_pin_data()

        self.lb_board.grid(row=0, column=0, sticky="w")
        self.lb_arduinoBoardComponent.grid(row=1, column=0, sticky="w")


class MenuBar(tk.Menu):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Menu.__init__(self, parent, *args, **kwargs)
        self.application = application

        file_menu = tk.Menu(self, tearoff=0)
        file_menu.add_command(label="Nuevo archivo",
                              command=self.create_file, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(
            label="Importar sketch", command=application.open_file, accelerator="Ctrl+O")
        file_menu.add_command(
            label="Guardar sketch", command=application.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(
            label="Salir", command=self.check_if_exit, accelerator="Alt+F4")
        self.add_cascade(label="Archivo", menu=file_menu)

        edit_menu = tk.Menu(self, tearoff=0)
        edit_menu.add_command(
            label="Deshacer", command=application.editor_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(
            label="Rehacer", command=application.editor_redo, accelerator="Ctrl+Y")
        self.add_cascade(label="Editar", menu=edit_menu)

        conf_menu = tk.Menu(self, tearoff=0)
        conf_menu.add_command(label="Configurar pines", command=application.open_pin_configuration,
                              accelerator="Ctrl+P")
        self.add_cascade(label="Configurar", menu=conf_menu)

        exec_menu = tk.Menu(self, tearoff=0)
        exec_menu.add_command(
            label="Ejecutar", command=application.execute, accelerator="F5")
        exec_menu.add_command(
            label="Detener", command=application.stop, accelerator="Ctrl+F5")
        exec_menu.add_separator()
        exec_menu.add_command(
            label="Ampliar", command=lambda event: application.zoom_in(), accelerator="Ctrl++")
        exec_menu.add_command(
            label="Reducir", command=lambda event: application.zoom_out(), accelerator="Ctrl+-")
        self.add_cascade(label="Ejecutar", menu=exec_menu)

        help_menu = tk.Menu(self, tearoff=0)
        help_menu.add_command(label="Manual de ayuda",
                              command=self.__launch_help, accelerator="Ctrl+H")
        help_menu.add_command(
            label="Acerca de", command=self.show_about, accelerator="Ctrl+A")
        self.add_cascade(label="Ayuda", menu=help_menu)

        self.bind_all("<Control-p>", application.open_pin_configuration)
        self.bind_all("<Control-n>", self.create_file)
        self.bind_all("<Control-o>", application.open_file)
        self.bind_all("<Control-s>", application.save_file)
        self.bind_all("<Control-h>", self.__launch_help)
        self.bind_all("<Control-a>", self.show_about)
        self.bind_all("<F5>", application.execute)
        self.bind_all("<Control-F5>", application.stop)
        self.bind_all("<Control-plus>", lambda event: application.zoom_in())
        self.bind_all("<Control-minus>", lambda event: application.zoom_out())

    def __launch_help(self, event=None):
        subprocess.Popen('manual-usuario.pdf', shell=True)

    def create_file(self, event=None):
        if messagebox.askyesno('Nuevo archivo',
                               '¿Seguro que quieres crear un nuevo archivo? Se perderá el sketch si no está guardado'):
            self.application.editor_frame.create_file()

    def check_if_exit(self):
        if messagebox.askyesno('Salir', '¿Seguro que quieres salir? Se perderá el sketch si no está guardado'):
            self.application.close()

    def show_about(self, event=None):
        messagebox.showinfo('Simulador de Software para robots',
                            str(
                                'Aplicación realizada como trabajo de fin de grado.\n'
                                + 'Autor inicial: Diego Fernández Suárez\n'
                                + 'Autora extensión: María Suárez Hevia\n'
                                + 'Tutor: Cristian González García\n'
                                + 'Versión actual: b-0.5'
                            ))


class DrawingFrame(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.application = application
        self.__load_images()

        self.hud_canvas = tk.Canvas(
            self, height=100, bg=DARK_BLUE, highlightthickness=1, highlightbackground="black")

        self.canvas_frame = tk.Frame(self, bg=BLUE)
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", bd=1,
                                relief=tk.SOLID, highlightthickness=0)
        self.joystick_frame = JoystickFrame(self.canvas_frame, application, bg=DARK_BLUE, highlightthickness=1,
                                            highlightbackground="black")
        self.buttons_gamification = ButtonsGamification(self.canvas_frame, application, bg=DARK_BLUE,
                                                        highlightthickness=1, highlightbackground="black")

        self.bottom_frame = tk.Frame(self, bg=BLUE)
        self.key_movement = tk.Checkbutton(self.bottom_frame, text="Movimiento con el teclado", fg="white",
                                           font=("Consolas", 12),
                                           bg=BLUE, activebackground=BLUE, selectcolor="black",
                                           command=application.toggle_keys, underline=0)
        self.key_drawing = tk.Checkbutton(self.bottom_frame, text="Dibujar", fg="white",
                                          font=("Consolas", 12),
                                         bg=BLUE, activebackground=BLUE, selectcolor="black",
                                         command=application.set_drawing, underline=0)
        self.zoom_frame = tk.Frame(self.bottom_frame, bg=BLUE)
        self.zoom_in_button = ImageButton(
            self.zoom_frame,
            {
                "blue": self.zoom_img,
                "white": self.zoom_whi_img,
                "yellow": self.zoom_yel_img
            },
            bg=BLUE,
            bd=0
        )
        self.zoom_label = tk.Label(
            self.zoom_frame, bg=BLUE, fg="white", font=("Consolas", 12))
        self.zoom_out_button = ImageButton(
            self.zoom_frame,
            {
                "blue": self.dezoom_img,
                "white": self.dezoom_whi_img,
                "yellow": self.dezoom_yel_img
            },
            bg=BLUE,
            bd=0
        )

        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<B1-Motion>", self.move)
        self.canvas.bind("<MouseWheel>", self.zoom)
        application.bind("<Alt-m>", self.__toggle_check_manually)
        self.zoom_in_button.configure(command=self.application.zoom_in)
        self.zoom_out_button.configure(command=self.application.zoom_out)
        self.key_movement.select()

        self.zoom_in_button.grid(row=0, column=0, padx=5, pady=5)
        self.zoom_label.grid(row=0, column=1, padx=5, pady=5)
        self.zoom_out_button.grid(row=0, column=2, padx=5, pady=5)

        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.key_movement.pack(anchor="w", side=tk.LEFT)
        self.key_drawing.pack(anchor="w", side=tk.LEFT)
        self.zoom_frame.pack(anchor="e", side=tk.RIGHT)

        self.hud_canvas.pack(fill=tk.X, expand=False)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.bottom_frame.pack(fill=tk.X)

        self.init_x = 0
        self.init_y = 0

    def __toggle_check_manually(self, event=None):
        self.key_movement.toggle()
        self.application.toggle_keys()

    def press(self, event):
        if isinstance(self.application.controller.robot_layer.robot, robots.ArduinoBoard):
            self.application.controller.robot_layer.draw_component(event.x, event.y)
        self.canvas.focus_force()
        self.init_x = event.x
        self.init_y = event.y
        self.canvas.scan_mark(event.x, event.y)

    def release(self, event):
        self.application.controller.robot_layer.drawing.dx += self.init_x - event.x
        self.application.controller.robot_layer.drawing.dy += self.init_y - event.y
        if self.application.controller.robot_layer.drawing.dx < 0:
            self.application.controller.robot_layer.drawing.dx = 0
        if self.application.controller.robot_layer.drawing.dx > 545:
            self.application.controller.robot_layer.drawing.dx = 545
        if self.application.controller.robot_layer.drawing.dy < 0:
            self.application.controller.robot_layer.drawing.dy = 0
        if self.application.controller.robot_layer.drawing.dy > 580:
            self.application.controller.robot_layer.drawing.dy = 580

    def move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def zoom(self, event):
        if event.delta == -120:
            self.application.controller.zoom_out()
        elif event.delta == 120:
            self.application.controller.zoom_in()

    def change_zoom_label(self, zoom_level):
        self.zoom_label.configure(text="{}%".format(zoom_level))

    def show_joystick(self):
        self.joystick_frame.pack(anchor="center", fill=tk.X)

    def hide_joystick(self):
        self.joystick_frame.pack_forget()

    def show_button_keys_movement(self):
        self.key_movement.pack(anchor="w", side=tk.LEFT)

    def hide_button_keys_movement(self):
        self.key_movement.pack_forget()

    def show_buttons_gamification(self):
        self.buttons_gamification.pack(anchor="center", fill=tk.X)

    def hide_buttons_gamification(self):
        self.buttons_gamification.pack_forget()

    def __load_images(self):
        self.zoom_img = tk.PhotoImage(file="buttons/zoom.png")
        self.zoom_whi_img = tk.PhotoImage(file="buttons/zoom_w.png")
        self.zoom_yel_img = tk.PhotoImage(file="buttons/zoom_y.png")
        self.dezoom_img = tk.PhotoImage(file="buttons/dezoom.png")
        self.dezoom_whi_img = tk.PhotoImage(file="buttons/dezoom_w.png")
        self.dezoom_yel_img = tk.PhotoImage(file="buttons/dezoom_y.png")


class ButtonsGamification(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.application = application

        self.button_tutorial = tk.Button(self, text="TUTORIAL", bg=BLUE, bd=0, fg=DARK_BLUE, font=("Consolas", 13))
        self.button_hints = tk.Button(self, text="PISTAS", bg=BLUE, bd=0, fg=DARK_BLUE, font=("Consolas", 13))
        self.button_delete = tk.Button(self, text="ELIMINAR", bg=BLUE, bd=0, fg=DARK_BLUE, font=("Consolas", 13))
        self.button_results = tk.Button(self, text="RESULTADOS", bg=BLUE, bd=0, fg=DARK_BLUE, font=("Consolas", 13))

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)

        self.button_tutorial.grid(row=1, column=0, padx=(0, 20))
        self.button_hints.grid(row=1, column=1, padx=(0, 20))
        self.button_delete.grid(row=1, column=2, padx=(0, 20))
        self.button_results.grid(row=1, column=3, padx=(0, 20))

        self.button_tutorial.bind("<ButtonPress>", self.show_tutorial)
        self.button_hints.bind("<ButtonPress>", self.show_help)
        self.button_delete.bind("<ButtonPress>", self.delete_elements)
        self.button_results.bind("<ButtonPress>", self.show_results)

    def show_tutorial(self, event):
        self.application.controller.show_tutorial()
        self.application.controller.console.logger.write_log('info',
                                                             "El usuario ha consultado el tutorial del desafío: "
                                                             + str(self.application.selector_bar.
                                                                   gamification_option_selector.current() + 1))

    def show_results(self, event):
        self.application.controller.show_results()

    def show_help(self, event):
        self.application.controller.show_help(self.application.selector_bar.gamification_option_selector.current())
        self.application.controller.console.logger.write_log('info', "El usuario ha consultado una pista del desafío: "
                                                             + str(self.application.selector_bar.
                                                                   gamification_option_selector.current() + 1))

    def delete_elements(self, event):
        self.application.controller.delete_elements()
        self.application.controller.console.logger.write_log('info', "El usuario ha borrado el progreso del desafío: "
                                                             + str(self.application.selector_bar.
                                                                   gamification_option_selector.current() + 1))


class JoystickFrame(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.application = application

        self.lb_joystick = tk.Label(
            self, text="Joystick", bg=DARK_BLUE, fg="white", font=("Consolas", 13))
        self.lb_x = tk.Label(self, text="X:", bg=DARK_BLUE,
                             fg="white", font=("Consolas", 12))
        self.x_dir = tk.Scale(self, from_=0, to=1023, orient=tk.HORIZONTAL, bg=DARK_BLUE, fg="white",
                              sliderrelief=tk.FLAT, highlightthickness=0)
        self.lb_y = tk.Label(self, text="Y:", bg=DARK_BLUE,
                             fg="white", font=("Consolas", 12))
        self.y_dir = tk.Scale(self, from_=0, to=1023, orient=tk.HORIZONTAL, bg=DARK_BLUE, fg="white",
                              sliderrelief=tk.FLAT, highlightthickness=0)
        self.j_button = tk.Button(
            self, text="Botón", bg=BLUE, bd=0, fg=DARK_BLUE, font=("Consolas", 13))

        self.x_dir.set(500)
        self.y_dir.set(500)

        self.x_dir.bind("<ButtonRelease-1>", self.__updatex)
        self.y_dir.bind("<ButtonRelease-1>", self.__updatey)
        self.j_button.bind("<ButtonPress>", self.__pressb)
        self.j_button.bind("<ButtonRelease>", self.__releaseb)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)
        self.columnconfigure(5, weight=1)

        self.lb_joystick.grid(row=1, column=0, padx=(0, 20))
        self.lb_x.grid(row=1, column=1, padx=(0, 5))
        self.x_dir.grid(row=1, column=2, padx=(0, 20), pady=5)
        self.lb_y.grid(row=1, column=3, padx=(0, 5))
        self.y_dir.grid(row=1, column=4, padx=(0, 20), pady=5)
        self.j_button.grid(row=1, column=5, padx=10)

    def __updatex(self, event):
        self.application.controller.update_joystick('dx', self.x_dir.get())

    def __updatey(self, event):
        self.application.controller.update_joystick('dy', self.y_dir.get())

    def __pressb(self, event):
        self.application.controller.update_joystick('button', 0)

    def __releaseb(self, event):
        self.application.controller.update_joystick('button', 1)


class EditorFrame(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.text = self.TextEditor(self, bd=1, relief=tk.SOLID, wrap="none", font=("consolas", 12), undo=True,
                                    autoseparators=True)
        self.line_bar = self.LineNumberBar(
            self, width=30, bg=BLUE, bd=0, highlightthickness=0)
        self.sb_x = tk.Scrollbar(self, orient=tk.HORIZONTAL,
                                 command=self.text.xview)
        self.sb_y = tk.Scrollbar(self, orient=tk.VERTICAL,
                                 command=self.text.yview)

        self.create_file()

        self.text.update_highlight()
        self.line_bar.attach(self.text)
        self.text.config(xscrollcommand=self.sb_x.set,
                         yscrollcommand=self.sb_y.set)

        self.line_bar.grid(row=0, column=0, sticky="nsw")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.sb_x.grid(row=1, column=1, sticky="sew")
        self.sb_y.grid(row=0, column=2, sticky="nse")

        self.text.bind("<<Change>>", self._on_change)
        self.text.bind("<Configure>", self._on_change)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def create_file(self):
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, "void setup(){\n")
        self.text.insert(tk.END, "}\n\n")
        self.text.insert(tk.END, "void loop(){\n")
        self.text.insert(tk.END, "}")

    def change_text(self, text):
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, text)

    def _on_change(self, event):
        self.line_bar.show_lines()

    class TextEditor(tk.Text):

        def __init__(self, *args, **kwargs):
            tk.Text.__init__(self, *args, **kwargs)

            self.keywords = self.__get_keywords("assets/colors.txt")
            self.comment_lines = []

            self._orig = self._w + "_orig"
            self.tk.call("rename", self._w, self._orig)
            self.tk.createcommand(self._w, self._proxy)
            self.__create_tags()

        def update_highlight(self):
            def step():
                i = 0
                while True:
                    keyword = self.keywords[i]
                    if len(keyword) == 3:
                        self.highlight_all_delimited(
                            r'%s' % keyword[0], r'%s' % keyword[1], keyword[2])
                    elif keyword[0][0:2] == '\\"' or keyword[0][0:2] == "\\'":
                        self.highlight_all(r'%s' % keyword[0], keyword[1], True)
                    elif keyword[0][0] == '\\':
                        self.highlight_all(r'%s' % keyword[0], keyword[1])
                    elif keyword[0][0:2] == '//':
                        self.highlight_all(r'%s' % keyword[0], keyword[1], True)
                    else:
                        self.highlight_all(r'\b%s\b' % keyword[0], keyword[1])
                    self.after(1, gen.__next__)
                    i += 1
                    if i == len(self.keywords):
                        i = 0
                        for match in self.comment_lines:
                            self.__remove_tags(match[0], match[1])
                        self.comment_lines = []
                    yield

            gen = step()
            gen.__next__()

        def highlight_all(self, pattern, tag, is_repaintable=False):
            for match in self.search_re(pattern, is_repaintable):
                self.highlight(tag, match[0], match[1])

        def highlight_all_delimited(self, pattern_s, pattern_e, tag):
            for match in self.search_re_delimited(pattern_s, pattern_e):
                self.highlight(tag, match[0], match[1])

        def highlight(self, tag, start, end):
            is_comment = False
            for comm in self.comment_lines:
                comm_start = tuple(map(int, comm[0].split('.')))
                comm_end = tuple(map(int, comm[1].split('.')))
                fl_start = tuple(map(int, start.split('.')))
                fl_end = tuple(map(int, end.split('.')))
                if (
                        comm_start[0] <= fl_start[0] <= comm_end[0]
                        and comm_start[0] <= fl_end[0] <= comm_end[0]
                ):
                    finished = False
                    if comm_start[0] == fl_start[0] == comm_end[0]:
                        if fl_end[0] == fl_start[0]:
                            finished = (
                                    comm_start[1] < fl_start[1] < comm_end[1]
                                    and comm_start[1] < fl_end[1] < comm_end[1]
                            )
                        else:
                            finished = True
                    elif comm_start[0] == fl_start[0]:
                        finished = comm_start[1] < fl_start[1]
                    elif comm_end[0] == fl_start[0]:
                        finished = fl_start[1] < comm_end[1]
                    elif comm_start[0] == fl_end[0]:
                        finished = comm_start[1] < fl_end[1]
                    elif comm_end[0] == fl_end[0]:
                        finished = fl_end[1] < comm_end[1]
                    else:
                        finished = True
                    if finished:
                        is_comment = True
                        break
            if not is_comment:
                self.__remove_tags(start, end)
                self.tag_add(tag, start, end)

        def search_re(self, pattern, is_repaintable):
            """
            Uses the python re library to match patterns.

            Arguments:
                pattern - The pattern to match.
            Return value:
                A list of tuples containing the start and end indices of the matches.
                e.g. [("0.4", "5.9"]
            """
            matches = []
            text = self.get("1.0", tk.END).splitlines()
            for i, line in enumerate(text):
                for match in re.finditer(pattern, line):
                    matches.append(
                        (f"{i + 1}.{match.start()}", f"{i + 1}.{match.end()}"))
            if is_repaintable:
                self.comment_lines.extend(matches)
            return matches

        def search_re_delimited(self, pattern_s, pattern_e):
            """
            Uses the python re library to match patterns.

            Arguments:
                pattern_s - The starting pattern to match.
                pattern_e - The ending pattern to match.
            Return value:
                A list of tuples containing the start and end indices of the matches.
                e.g. [("0.4", "5.9"]
            """
            matches = []
            text = self.get("1.0", tk.END).splitlines()
            start = end = -1
            for i, line in enumerate(text):
                for match in re.finditer(pattern_s, line):
                    if start == -1:
                        start = f"{i + 1}.{match.start()}"
                for match in re.finditer(pattern_e, line):
                    if end == -1:
                        end = f"{i + 1}.{match.end()}"
                if start != -1 and end != -1:
                    matches.append((start, end))
                    start = end = -1
            self.comment_lines = matches
            return matches

        def _proxy(self, *args):
            result = None
            command = (self._orig,) + args
            try:
                result = self.tk.call(command)
            except Exception:
                return result

            if (args[0] in ("insert", "replace", "delete")
                    or args[0:3] == ("mark", "set", "insert")
                    or args[0:2] == ("xview", "moveto")
                    or args[0:2] == ("xview", "scroll")
                    or args[0:2] == ("yview", "moveto")
                    or args[0:2] == ("yview", "scroll")):
                self.event_generate("<<Change>>", when="tail")

            return result

        def __create_tags(self):
            self.tag_configure("blue", foreground="#00979C")
            self.tag_configure("strblue", foreground="#005C5F")
            self.tag_configure("orange", foreground="#D35400")
            self.tag_configure("green", foreground="#728E00")
            self.tag_configure("gray", foreground="#95A5A6")
            self.tag_configure("dark", foreground="#434F54")

        def __remove_tags(self, start, end):
            self.tag_remove("blue", start, end)
            self.tag_remove("strblue", start, end)
            self.tag_remove("orange", start, end)
            self.tag_remove("green", start, end)
            self.tag_remove("gray", start, end)
            self.tag_remove("dark", start, end)

        def __get_keywords(self, file_name):
            keywords = []
            file = open(file_name, "r")
            lines = list(
                filter(lambda line: line != '',
                       map(lambda line: str(line).rstrip(), file.readlines())
                       )
            )
            for line in lines:
                line_elems = line.split('\t')
                if len(line_elems) == 2:
                    keywords.append((line_elems[0], line_elems[1]))
                elif len(line_elems) == 3:
                    keywords.append(
                        (line_elems[0], line_elems[1], line_elems[2]))
            return keywords

    class LineNumberBar(tk.Canvas):

        def __init__(self, *args, **kwargs):
            tk.Canvas.__init__(self, *args, **kwargs)
            self.editor = None

        def attach(self, editor):
            self.editor = editor

        def show_lines(self, *args):
            self.delete("all")

            i = self.editor.index("@0,0")
            while True:
                dline = self.editor.dlineinfo(i)
                if dline is None:
                    break
                line = str(i).split(".")[0]
                x = 28 - 9 * len(line)
                y = dline[1]
                self.create_text(x, y, anchor="nw", text=line,
                                 fill="white", font=('consolas', 12, 'bold'))
                i = self.editor.index("%s+1line" % i)


class ConsoleFrame(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.application = application

        self.output = tk.IntVar()
        self.warning = tk.IntVar()
        self.error = tk.IntVar()

        self.console_frame = tk.Frame(self, bg=DARK_BLUE)
        self.console = tk.Text(self.console_frame, bd=1, relief=tk.SOLID, font=(
            "consolas", 12), bg="black", fg="white")
        self.sb_y = tk.Scrollbar(
            self.console_frame, orient=tk.VERTICAL, command=self.console.yview)
        self.filter_frame = tk.Frame(self, bg=DARK_BLUE, padx=10)
        self.check_out = tk.Checkbutton(self.filter_frame, text="Output", fg="white", font=("Consolas", 12),
                                        bg=DARK_BLUE, activebackground=DARK_BLUE, selectcolor="black",
                                        variable=self.output, onvalue=1, offvalue=0,
                                        command=application.console_filter, underline=1)
        self.check_warning = tk.Checkbutton(self.filter_frame, text="Warning", fg="white", font=("Consolas", 12),
                                            bg=DARK_BLUE, activebackground=DARK_BLUE, selectcolor="black",
                                            variable=self.warning, onvalue=1, offvalue=0,
                                            command=application.console_filter, underline=0)
        self.check_error = tk.Checkbutton(self.filter_frame, text="Error", fg="white", font=("Consolas", 12),
                                          bg=DARK_BLUE, activebackground=DARK_BLUE, selectcolor="black",
                                          variable=self.error, onvalue=1, offvalue=0,
                                          command=application.console_filter, underline=3)
        self.input_frame = tk.Frame(self, bg=DARK_BLUE)
        self.input_entry = tk.Entry(self.input_frame, bd=1, relief=tk.SOLID, bg="black", insertbackground="white",
                                    fg="white", font=("Consolas", 12))
        self.input_button = tk.Button(self.input_frame, bd=0, bg=BLUE, fg=DARK_BLUE, text="Enviar",
                                      font=("Consolas", 12), command=self.__send_input, underline=0)
        self.twin_button = tk.Button(self.input_frame, bd=0, bg=BLUE, fg=DARK_BLUE, text="Twin",
                                     font=("Consolas", 12), command=self.__send_twin, underline=0)

        self.console.config(state=tk.DISABLED, yscrollcommand=self.sb_y.set)
        self.check_out.select()
        self.check_warning.select()
        self.check_error.select()

        self.check_out.grid(column=0, row=0)
        self.check_warning.grid(column=0, row=1)
        self.check_error.grid(column=0, row=2)

        self.input_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.input_entry.pack(fill=tk.X, expand=True)

        self.sb_y.pack(fill=tk.Y, side=tk.RIGHT)
        self.console.pack(fill=tk.BOTH, expand=True)

        self.filter_frame.pack(side=tk.RIGHT)
        self.input_frame.pack(fill=tk.X, side=tk.BOTTOM, expand=True, pady=5)
        self.console_frame.pack(fill=tk.BOTH, expand=True)

        self.application.bind("<Alt-u>", self.change_output)
        self.application.bind("<Alt-w>", self.change_warning)
        self.application.bind("<Alt-o>", self.change_error)
        self.application.bind("<Alt-e>", lambda event: self.__send_input())
        self.application.bind("<Alt-t>", lambda event: self.__send_twin())

    def show_twin_button(self):
        if not self.twin_button.winfo_ismapped():
            self.twin_button.pack(side=tk.RIGHT, padx=(5, 0), before=self.input_entry)

    def hide_twin_button(self):
        if self.twin_button.winfo_ismapped():
            self.twin_button.pack_forget()

    def change_output(self, event=None):
        self.check_out.toggle()
        self.__filter()

    def change_warning(self, event=None):
        self.check_warning.toggle()
        self.__filter()

    def change_error(self, event=None):
        self.check_error.toggle()
        self.__filter()

    def __filter(self):
        self.application.console_filter()

    def __send_input(self):
        self.application.controller.send_input(self.input_entry.get())

    def __send_twin(self):
        self.application.controller.send_twin_input(self.input_entry.get())


class ButtonBar(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.application = application

        self.exec_frame = tk.Frame(self, bg=kwargs["bg"])
        self.hist_frame = tk.Frame(self, bg=kwargs["bg"])
        self.utils_frame = tk.Frame(self, bg=kwargs["bg"])
        self.tooltip_hover = tk.Label(
            self, bg=kwargs["bg"], font=("consolas", 12), fg="white")

        self.__load_images()

        self.execute_button = ImageButton(
            self.exec_frame,
            images={
                "blue": self.exec_img,
                "white": self.exec_whi_img,
                "yellow": self.exec_yel_img
            },
            bg=kwargs["bg"],
            activebackground=DARK_BLUE,
            bd=0
        )
        self.stop_button = ImageButton(
            self.exec_frame,
            images={
                "blue": self.stop_img,
                "white": self.stop_whi_img,
                "yellow": self.stop_yel_img
            },
            bg=kwargs["bg"],
            activebackground=DARK_BLUE,
            bd=0
        )
        self.undo_button = ImageButton(
            self.hist_frame,
            images={
                "blue": self.undo_img,
                "white": self.undo_whi_img,
                "yellow": self.undo_yel_img
            },
            bg=kwargs["bg"],
            activebackground=DARK_BLUE,
            bd=0,
            command=self.application.editor_undo
        )
        self.redo_button = ImageButton(
            self.hist_frame,
            images={
                "blue": self.redo_img,
                "white": self.redo_whi_img,
                "yellow": self.redo_yel_img
            },
            bg=kwargs["bg"],
            activebackground=DARK_BLUE,
            bd=0,
            command=self.application.editor_redo
        )
        self.save_button = ImageButton(
            self.utils_frame,
            images={
                "blue": self.save_img,
                "white": self.save_whi_img,
                "yellow": self.save_yel_img
            },
            bg=kwargs["bg"],
            activebackground=DARK_BLUE,
            bd=0,
            command=self.application.save_file
        )
        self.import_button = ImageButton(
            self.utils_frame,
            images={
                "blue": self.import_img,
                "white": self.import_whi_img,
                "yellow": self.import_yel_img
            },
            bg=kwargs["bg"],
            activebackground=DARK_BLUE,
            bd=0,
            command=self.application.open_file
        )

        self.execute_button.set_tooltip_text(self.tooltip_hover, "Ejecutar")
        self.stop_button.set_tooltip_text(self.tooltip_hover, "Detener")
        self.undo_button.set_tooltip_text(self.tooltip_hover, "Deshacer")
        self.redo_button.set_tooltip_text(self.tooltip_hover, "Rehacer")
        self.save_button.set_tooltip_text(self.tooltip_hover, "Guardar")
        self.import_button.set_tooltip_text(self.tooltip_hover, "Importar")

        self.execute_button.configure(command=self.execute)
        self.stop_button.configure(command=self.stop)

        self.exec_frame.grid(row=0, column=0)
        self.hist_frame.grid(row=0, column=1)
        self.utils_frame.grid(row=0, column=2)
        self.tooltip_hover.grid(row=0, column=3)

        self.execute_button.grid(row=0, column=1, padx=5, pady=5)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5)
        self.undo_button.grid(row=0, column=1, padx=5, pady=5)
        self.redo_button.grid(row=0, column=2, padx=5, pady=5)
        self.save_button.grid(row=0, column=1, padx=5, pady=5)
        self.import_button.grid(row=0, column=2, padx=5, pady=5)

    def execute(self):
        self.execute_button.on_click()
        self.application.execute()
        self.execute_button.on_click_finish()

    def stop(self):
        self.stop_button.on_click()
        self.application.stop()
        self.stop_button.on_click_finish()

    def __load_images(self):
        self.exec_img = tk.PhotoImage(file="buttons/exec.png")
        self.exec_whi_img = tk.PhotoImage(file="buttons/exec_w.png")
        self.exec_yel_img = tk.PhotoImage(file="buttons/exec_y.png")
        self.import_img = tk.PhotoImage(file="buttons/import.png")
        self.import_whi_img = tk.PhotoImage(file="buttons/import_w.png")
        self.import_yel_img = tk.PhotoImage(file="buttons/import_y.png")
        self.redo_img = tk.PhotoImage(file="buttons/redo.png")
        self.redo_whi_img = tk.PhotoImage(file="buttons/redo_w.png")
        self.redo_yel_img = tk.PhotoImage(file="buttons/redo_y.png")
        self.save_img = tk.PhotoImage(file="buttons/save.png")
        self.save_whi_img = tk.PhotoImage(file="buttons/save_w.png")
        self.save_yel_img = tk.PhotoImage(file="buttons/save_y.png")
        self.stop_img = tk.PhotoImage(file="buttons/stop.png")
        self.stop_whi_img = tk.PhotoImage(file="buttons/stop_w.png")
        self.stop_yel_img = tk.PhotoImage(file="buttons/stop_y.png")
        self.undo_img = tk.PhotoImage(file="buttons/undo.png")
        self.undo_whi_img = tk.PhotoImage(file="buttons/undo_w.png")
        self.undo_yel_img = tk.PhotoImage(file="buttons/undo_y.png")


class ImageButton(tk.Button):

    def __init__(self, parent, images, *args, **kwargs):
        tk.Button.__init__(self, parent, *args, **kwargs, image=images["blue"])
        self.images = images

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        event.widget['image'] = self.images["white"]
        try:
            self.label.configure(text=self.tooltip)
        except AttributeError:
            pass

    def on_leave(self, event):
        event.widget['image'] = self.images["blue"]
        try:
            self.label.configure(text="")
        except AttributeError:
            pass

    def on_click(self):
        self.configure(image=self.images["yellow"])

    def on_click_finish(self):
        self.configure(image=self.images["blue"])

    def set_tooltip_text(self, label: tk.Label, tooltip):
        self.label = label
        self.tooltip = tooltip


class SelectorBar(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.lb_robot = tk.Label(self, text="Robot:", bg=DARK_BLUE, fg="white", font=(
            "Consolas", 13), underline=0)
        self.robot_selector = ttk.Combobox(self, state="readonly")
        self.lb_track = tk.Label(self, text="Circuito:", bg=DARK_BLUE, fg="white", font=(
            "Consolas", 13), underline=1)
        self.lb_gamification_option = tk.Label(self, text="Opción:", bg=DARK_BLUE, fg="white", font=(
            "Consolas", 13), underline=1)
        self.track_selector = ttk.Combobox(self, state="readonly")
        self.gamification_option_selector = ttk.Combobox(self, state="readonly")

        self.application = application
        self.all_robots = ["Robot móvil (2 infrarrojos)",
                           "Robot móvil (3 infrarrojos)",
                           "Robot móvil (4 infrarrojos)",
                           "Actuador lineal",
                           "Placa arduino"]
        self.robot_selector['values'] = self.all_robots
        self.robot_selector.current(0)
        self.track_selector['values'] = [
            "Circuito", "Laberinto", "Recta",
            "Obstáculo", "Recta y obstáculo",
            "Circuito con nodos", "Recorrido infinito"]
        self.track_selector.current(0)
        self.gamification_option_selector['values'] = [
            "Libre", "Desafío 1", "Desafío 2", "Desafío 3", "Desafío 4", "Desafío 5", "Desafío 6"]
        self.gamification_option_selector.current(0)

        # --- Modo gemelo digital (MQTT) ---
        self.twin_var = tk.BooleanVar(value=False)
        self.twin_check = tk.Checkbutton(
            self, text="Gemelo digital", variable=self.twin_var,
            command=application.toggle_digital_twin_mode,
            bg=DARK_BLUE, fg="white", activebackground=DARK_BLUE,
            activeforeground="white", selectcolor=DARK_BLUE,
            font=("Consolas", 13), underline=0)
        self.lb_theme = tk.Label(self, text="Tema:", bg=DARK_BLUE, fg="white",
                                 font=("Consolas", 13))
        self.theme_entry = tk.Entry(self, width=12, font=("Consolas", 13))
        self.connect_button = tk.Button(
            self, text="Conectar", command=application.mqtt_connect,
            bg=BLUE, fg="white", activebackground=BLUE, font=("Consolas", 11),
            underline=2)  # 'n' de Conectar (Alt-n); en Desconectar -> 'd' (Alt-d)
        self.control_button = tk.Button(
            self, text="Controlar", command=application.mqtt_toggle_control,
            bg=BLUE, fg="white", activebackground=BLUE, font=("Consolas", 11),
            underline=6)  # 'l' de controLar (Alt-l); en Liberar -> 'L'

        self.robot_selector.bind(
            "<<ComboboxSelected>>", application.change_robot)
        self.track_selector.bind(
            "<<ComboboxSelected>>", application.change_track)
        self.gamification_option_selector.bind(
            "<<ComboboxSelected>>", application.change_gamification_option)
        application.bind("<Alt-r>", lambda event: self.robot_selector.focus())
        application.bind("<Alt-i>", lambda event: self.track_selector.focus())
        application.bind("<Alt-o>", lambda event: self.gamification_option_selector.focus())
        application.bind("<Alt-g>", lambda event: self.twin_check.invoke())
        # Conectar = Alt-n, Desconectar = Alt-d (mismo boton, texto alterna)
        application.bind("<Alt-n>", lambda event: self.connect_button.invoke()
                         if self.connect_button.winfo_ismapped() else None)
        application.bind("<Alt-d>", lambda event: self.connect_button.invoke()
                         if self.connect_button.winfo_ismapped() else None)
        # Controlar/Liberar = Alt-l (mismo boton, texto alterna)
        application.bind("<Alt-l>", lambda event: self.control_button.invoke()
                         if self.control_button.winfo_ismapped() else None)

        self.lb_robot.grid(row=0, column=0)
        self.robot_selector.grid(row=0, column=1, padx=(5, 15))
        self.lb_track.grid(row=0, column=2)
        self.track_selector.grid(row=0, column=3, padx=(5, 10))
        self.twin_check.grid(row=0, column=4, padx=(15, 5))

    def hide_arduino_robot(self):
        # "Placa arduino" = arduinoBoard, no aplica en gemelo digital
        if self.robot_selector.current() == 4:
            self.robot_selector.current(0)
            self.application.change_robot(None)
        self.robot_selector['values'] = self.all_robots[:-1]

    def recover_arduino_robot(self):
        self.robot_selector['values'] = self.all_robots

    def hide_circuit_selector(self):
        if self.lb_track.winfo_ismapped():
            self.lb_track.grid_forget()
        if self.track_selector.winfo_ismapped():
            self.track_selector.grid_forget()

    def recover_circuit_selector(self):
        if not self.lb_track.winfo_ismapped():
            self.lb_track.grid(row=0, column=2)
        if not self.track_selector.winfo_ismapped():
            self.track_selector.grid(row=0, column=3, padx=(5, 10))

    def hide_gamification_option_selector(self):
        if self.lb_gamification_option.winfo_ismapped():
            self.lb_gamification_option.grid_forget()
        if self.gamification_option_selector.winfo_ismapped():
            self.gamification_option_selector.grid_forget()

    def recover_gamification_option_selector(self):
        if not self.lb_gamification_option.winfo_ismapped():
            self.lb_gamification_option.grid(row=0, column=2)
        if not self.gamification_option_selector.winfo_ismapped():
            self.gamification_option_selector.grid(row=0, column=3, padx=(5, 10))

    def show_twin_controls(self):
        self.lb_theme.grid(row=0, column=5)
        self.theme_entry.grid(row=0, column=6, padx=(5, 5))
        self.connect_button.grid(row=0, column=7, padx=(0, 5))

    def hide_twin_controls(self):
        self.hide_control_button()
        if self.connect_button.winfo_ismapped():
            self.connect_button.grid_forget()
        if self.theme_entry.winfo_ismapped():
            self.theme_entry.grid_forget()
        if self.lb_theme.winfo_ismapped():
            self.lb_theme.grid_forget()

    def set_connected(self, connected):
        self.connect_button.config(
            text="Desconectar" if connected else "Conectar",
            underline=0 if connected else 2)  # 'd' de Desconectar / 'n' de Conectar

    # El botón Controlar/Soltar solo aparece con el gemelo conectado: tomar el
    # control sin conexión no tiene sentido.
    def show_control_button(self):
        self.control_button.config(text="Controlar", underline=6)
        self.control_button.grid(row=0, column=8, padx=(0, 5))

    def hide_control_button(self):
        if self.control_button.winfo_ismapped():
            self.control_button.grid_forget()

    def set_controlling(self, controlling):
        self.control_button.config(
            text="Liberar" if controlling else "Controlar",
            underline=0 if controlling else 6)  # 'L' de Liberar / 'l' de controLar
