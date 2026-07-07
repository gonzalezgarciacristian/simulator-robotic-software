import os
import math
import re
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
import tkinter.ttk as ttk
import tkinter.font as tkfont
from PIL import Image, ImageDraw, ImageTk
import graphics.controller as controller
import files.files_reader as files
import subprocess
import robot_components.robots as robots

DARK_BLUE = "#006468"
BLUE = "#17a1a5"
WINDOW_BG = DARK_BLUE
SURFACE_BG = "#F7FAFA"
SURFACE_ALT_BG = "#E6F0F0"
SURFACE_HEADER_BG = BLUE
PANEL_BORDER = DARK_BLUE
TEXT_PRIMARY = "#173D3F"
TEXT_MUTED = "#6B7D7F"
TEXT_DISABLED = "#869396"
INPUT_BG = "#FFFFFF"
INPUT_DISABLED_BG = "#D7DDDF"
INPUT_DISABLED_BORDER = "#AAB4B7"
INPUT_FIXED_BG = "#DCEEF5"
INPUT_FIXED_BORDER = "#5F98A6"
INPUT_ACCENT_BG = "#D4EDE8"
PANEL_ACTION_BG = BLUE
PANEL_ACTION_FG = "white"
PANEL_ACTION_ACTIVE_BG = DARK_BLUE
PANEL_ACTION_DISABLED_BG = "#91979C"
PANEL_ACTION_DISABLED_FG = "#E7EAEC"
PANEL_ACTION_BORDER = "#083C3E"
PANEL_ACTION_DISABLED_BORDER = "#747A7F"
PANEL_CONFIRM_BG = "#18B36A"
PANEL_CONFIRM_ACTIVE_BG = "#129158"
PANEL_CONFIRM_DISABLED_BG = "#91979C"
PANEL_CONFIRM_BORDER = "#0A6A3F"


class FontScaler:
    """Conjunto de fuentes ``tkfont.Font`` que se reescalan por un factor común.

    Permite que un panel reflujie todas sus fuentes con una sola llamada
    (``apply(scale)``). Cada fuente recuerda su tamaño base de diseño y se
    recalcula respetando un mínimo legible. Como las fuentes son objetos
    compartidos, asignarlas a varios widgets y cambiar su tamaño actualiza
    todos a la vez de forma eficiente.
    """

    def __init__(self, family="Consolas"):
        self._family = family
        self._fonts = []  # (Font, base_size)

    def font(self, base_size, weight="normal", slant="roman"):
        f = tkfont.Font(family=self._family, size=base_size,
                        weight=weight, slant=slant)
        self._fonts.append((f, base_size))
        return f

    def apply(self, scale, minimum=7):
        scale = max(0.1, float(scale))
        for f, base in self._fonts:
            size = max(minimum, int(round(base * scale)))
            if f.cget("size") != size:
                f.configure(size=size)


class VScrollFrame(tk.Frame):
    """Contenedor con scroll vertical automático.

    El contenido se añade dentro de ``self.body``. La barra de scroll aparece
    sola cuando el contenido es más alto que el área visible y se oculta cuando
    cabe. La rueda del ratón desplaza el contenido (incluida sobre los hijos).
    """

    def __init__(self, parent, bg, **kwargs):
        tk.Frame.__init__(self, parent, bg=bg, **kwargs)
        self._bg = bg
        self._canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        self._vbar = tk.Scrollbar(self, orient=tk.VERTICAL,
                                  command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.body = tk.Frame(self._canvas, bg=bg)
        self._win = self._canvas.create_window((0, 0), window=self.body,
                                               anchor="nw")
        self._vbar_shown = False
        self.body.bind("<Configure>", self._on_body_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind_wheel(self)

    def _on_body_configure(self, _event=None):
        try:
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        except Exception:
            pass
        self._update_vbar()

    def _on_canvas_configure(self, event):
        try:
            self._canvas.itemconfigure(self._win, width=event.width)
        except Exception:
            pass
        self._update_vbar()

    def _update_vbar(self):
        try:
            need = self.body.winfo_reqheight() > self._canvas.winfo_height() + 1
        except Exception:
            return
        if need and not self._vbar_shown:
            self._vbar.pack(side=tk.RIGHT, fill=tk.Y, before=self._canvas)
            self._vbar_shown = True
        elif not need and self._vbar_shown:
            self._vbar.pack_forget()
            self._vbar_shown = False

    def _on_wheel(self, event):
        if not self._vbar_shown:
            return
        try:
            self._canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        except Exception:
            pass

    def bind_wheel(self, widget):
        """Propaga el desplazamiento con rueda a un widget y sus descendientes."""
        try:
            widget.bind("<MouseWheel>", self._on_wheel, add="+")
            for child in widget.winfo_children():
                self.bind_wheel(child)
        except Exception:
            pass


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

        # Área de contenido: PanedWindow horizontal [info | central+derecho] para
        # que el panel de info sea redimensionable con sash frente al viewport.
        self.content_area = tk.PanedWindow(
            self.vertical_pane, orient=tk.HORIZONTAL,
            sashpad=5, sashrelief="solid", bg=DARK_BLUE)

        # Panel izquierdo de información del brazo 3D (oculto por defecto)
        self.left_info_panel = Arm3DInfoPanel(self.content_area, self, bg=DARK_BLUE)
        self._left_info_visible = False

        # PanedWindow central+derecho
        self.center_right_pane = tk.PanedWindow(
            self.content_area, orient=tk.HORIZONTAL,
            sashpad=5, sashrelief="solid", bg=BLUE)

        self.drawing_frame = DrawingFrame(self.center_right_pane, self, bg=BLUE)

        # Notebook derecho: pestaña CÓDIGO y pestaña 3D opcional
        self.right_notebook = ttk.Notebook(self.center_right_pane)
        self.editor_frame = EditorFrame(self.right_notebook, bg=BLUE)
        self.arm3d_control_panel = Arm3DControlPanel(
            self.right_notebook, self, bg=DARK_BLUE,
            highlightthickness=1, highlightbackground="black")
        self.right_notebook.add(self.editor_frame, text="CÓDIGO")

        self.console_frame = ConsoleFrame(self.vertical_pane, self, bg=DARK_BLUE)

        self.identifier = None
        self.controller = controller.RobotsController(self)
        self.prepare_controller()
        self.keys_used = True
        self.file_manager = files.FileManager()

        self.menu_bar.pack(fill=tk.X)
        self.button_bar.pack(fill=tk.X, side="left", expand=True)
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

        # Notebook: CÓDIGO a la izquierda, CONTROL MANUAL a la derecha
        self.center_right_pane.add(self.drawing_frame, stretch="first", width=900, minsize=100)
        self.center_right_pane.add(self.right_notebook, width=320, minsize=120)

        # El panel central+derecho ocupa todo el área; el panel de info se
        # inserta a su izquierda solo cuando el Braccio está activo.
        self.content_area.add(self.center_right_pane, stretch="always", minsize=200)

        self.vertical_pane.add(self.content_area, stretch="first", minsize=100)
        self.vertical_pane.add(self.console_frame, stretch="never", height=200, minsize=100)

        self._setup_notebook_tab_scaling()

        self.bind("<KeyPress>", self.key_press)
        self.bind("<KeyRelease>", self.key_release)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.challenge = 0

    def _setup_notebook_tab_scaling(self):
        """Hace que la fuente de las pestañas (CÓDIGO / CONTROL MANUAL) se
        autoajuste al ancho del notebook para que no se trunquen."""
        self._nb_tab_font = tkfont.Font(family="Consolas", size=10)
        try:
            style = ttk.Style()
            style.configure("Arm3D.TNotebook.Tab",
                            font=self._nb_tab_font, padding=(3, 2))
            self.right_notebook.configure(style="Arm3D.TNotebook")
            self.right_notebook.bind("<Configure>", self._on_notebook_configure)
        except Exception:
            pass

    def _on_notebook_configure(self, event):
        # Fuente de las pestañas (CÓDIGO + CONTROL MANUAL) proporcional al ancho
        # del notebook: se reduce para que SIEMPRE quepan sin truncar (diseño
        # responsive) y crece hasta un tope cuando hay sitio. El divisor está
        # calibrado para que el texto quepa de verdad en ttk.
        try:
            size = max(7, min(11, int(round(event.width / 33.0))))
            if self._nb_tab_font.cget("size") != size:
                self._nb_tab_font.configure(size=size)
        except Exception:
            pass

    def prepare_controller(self):
        self.__update_robot()  # call first so the robot_layer is created
        self.controller.configure_layer(self.drawing_frame.canvas,
                                        self.drawing_frame.hud_canvas)  # call second so the canvas are initialized
        # call third so the console is initialized
        self.controller.configure_console(self.console_frame.console)
        # connect editor breakpoint handler now that controller exists
        self.editor_frame.attach_controller(self)
        # call last so all the three elements that are configured before are initialized
        self.__update_track()
        # if not, the track raises exception

    def execute(self):
        self.drawing_frame.canvas.focus_force()
        self.controller.execute(self.selector_bar.gamification_option_selector.current())

    def stop(self):
        self.controller.stop()

    def toggle_pause(self):
        """Alterna entre pausado y ejecutando (RF4.2.2)."""
        self.controller.toggle_pause()

    def step_once(self):
        """Ejecuta una sentencia más y vuelve a pausar (RF4.2.3)."""
        self.controller.step_once()


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
        if robot == 5:
            self.open_arm3d_configuration()
        else:
            PinConfigurationWindow(self, robot, self)

    def open_arm3d_configuration(self):
        """Abre la ventana modal de configuración del brazo 3D."""
        import graphics.layers as _layers
        if isinstance(self.controller.robot_layer, _layers.Arm3DLayer):
            Arm3DConfigurationWindow(self, self.controller.robot_layer.motor3d, self)

    def zoom_in(self):
        self.controller.zoom_in()

    def zoom_out(self):
        self.controller.zoom_out()

    def change_zoom_label(self, zoom_level):
        self.drawing_frame.change_zoom_label(zoom_level)

    def set_arm3d_mouse_drag_mode(self, mode):
        if hasattr(self, "drawing_frame"):
            self.drawing_frame.set_arm3d_mouse_mode(mode)
        if hasattr(self, "arm3d_control_panel"):
            self.arm3d_control_panel.set_mouse_drag_mode(mode)

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
        self.menu_bar.update_config_menu_label(robot)
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

    def _set_left_info_visible(self, visible):
        """Inserta o quita el panel de info como primer pane del PanedWindow
        (a la izquierda del viewport), con sash para redimensionarlo."""
        if visible and not self._left_info_visible:
            try:
                self.content_area.add(
                    self.left_info_panel, before=self.center_right_pane,
                    width=210, minsize=90, stretch="never")
            except Exception:
                self.content_area.add(self.left_info_panel)
            self._left_info_visible = True
        elif not visible and self._left_info_visible:
            self.content_area.forget(self.left_info_panel)
            self._left_info_visible = False

    def show_arm3d_panel(self, showing):
        if showing:
            self._set_arm3d_control_tab_visible(True)
            # Mostrar panel izquierdo de información
            self._set_left_info_visible(True)
            # Ocultar HUD clásico (la info va al panel izquierdo)
            self.drawing_frame.hide_hud()
            # Mostrar botones de vista de cámara
            self.drawing_frame.show_arm3d_camera_buttons()
            # Seleccionar pestaña CONTROL MANUAL en el notebook
            self.right_notebook.select(self.arm3d_control_panel)
            # Conectar el panel de info al HUD del brazo (con retardo para que la capa esté lista)
            self.after(150, self._connect_arm3d_info_panel)
        else:
            self._set_arm3d_control_tab_visible(False)
            self.set_arm3d_mouse_drag_mode(None)
            # Ocultar panel izquierdo
            self._set_left_info_visible(False)
            # Restaurar HUD clásico
            self.drawing_frame.show_hud()
            # Ocultar botones de cámara
            self.drawing_frame.hide_arm3d_camera_buttons()
            # Seleccionar pestaña CÓDIGO
            self.right_notebook.select(self.editor_frame)

    def _set_arm3d_control_tab_visible(self, visible):
        """Añade o elimina la pestaña CONTROL MANUAL según el robot activo."""
        control_tab = str(self.arm3d_control_panel)
        is_visible = control_tab in self.right_notebook.tabs()
        if visible and not is_visible:
            self.right_notebook.add(
                self.arm3d_control_panel, text="CONTROL MANUAL")
        elif not visible and is_visible:
            if self.right_notebook.select() == control_tab:
                self.right_notebook.select(self.editor_frame)
            self.right_notebook.forget(self.arm3d_control_panel)

    def _connect_arm3d_info_panel(self):
        """Conecta el panel de info izquierdo al HUD del brazo 3D cuando la capa está lista.
        También actualiza los límites de los sliders y sincroniza el estado de los toggles
        de trayectoria y rangos articulares con el scene 3D."""
        try:
            import graphics.layers as _layers
            if isinstance(self.controller.robot_layer, _layers.Arm3DLayer):
                self.controller.robot_layer.hud._info_panel = self.left_info_panel
                self.arm3d_control_panel.update_joint_limits()
                # Sincronizar toggles UI → escena (evita el desfase checkbox=True / show_trail=False)
                self.left_info_panel.apply_visual_toggles()
        except Exception:
            pass

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

    def key_press(self, event):
        self.drawing_frame.handle_global_key_press(event)
        pressed_key = event.char
        if pressed_key in self.move_WASD:
            self.move_WASD[pressed_key] = True

    def key_release(self, event):
        pressed_key = event.char
        if pressed_key in self.move_WASD:
            self.move_WASD[pressed_key] = False

    def abort_after(self):
        if self.identifier is not None:
            self.after_cancel(self.identifier)
            self.identifier = None

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
            frame_content, text="Pin servo derecho:", underline=10)
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
        self.bind("<Alt-d>", lambda event: self.entry_pin_se2.focus())
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
        self.bind("<Alt-d>", lambda event: self.entry_pin_se2.focus())
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
        self.bind("<Alt-d>", lambda event: self.entry_pin_se2.focus())
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


class Arm3DConfigurationWindow(tk.Toplevel):
    """
    Ventana modal de configuración del brazo 3D.
    Permite modificar DOF, tabla DH, tipos de articulación y límites.
    Importar/exportar configuración en JSON.
    """

    BRACCIO_TABLE_BASE_ROW = {
        "theta": 0.0,
        "d": 0.0,
        "a": 0.0,
        "alpha": 0.0,
    }
    BRACCIO_TABLE_DH_ROWS = [
        {"theta": -180.0, "d": 72.0, "a": -2.0, "alpha": 90.0},
        {"theta": 90.0, "d": 0.0, "a": 125.0, "alpha": 0.0},
        {"theta": 0.0, "d": 0.0, "a": 125.0, "alpha": 0.0},
        {"theta": -90.0, "d": 0.0, "a": 0.0, "alpha": 90.0},
        {"theta": 90.0, "d": -60.0, "a": 0.0, "alpha": 180.0},
        {"theta": -90.0, "d": 126.55, "a": 0.5, "alpha": 0.0},
    ]
    BRACCIO_SERVO_PINS = [11, 10, 9, 6, 5, 3]

    @classmethod
    def _braccio_table_defaults(cls):
        """Valores de tabla DH alineados con el Braccio exacto visible en escena."""
        return {
            "base": dict(cls.BRACCIO_TABLE_BASE_ROW),
            "dh_rows": [dict(row) for row in cls.BRACCIO_TABLE_DH_ROWS],
            "servo_pins": list(cls.BRACCIO_SERVO_PINS),
        }

    def _table_source_config(self):
        """Config visible en la tabla de edición, con ajuste especial para Braccio."""
        current = self.motor3d.get_model_config()
        preset_name = self._preset_var.get() if hasattr(self, "_preset_var") else None
        if preset_name == "braccio_tinkerkit":
            table_defaults = self._braccio_table_defaults()
            current = dict(current)
            current["base"] = table_defaults["base"]
            current["dh_rows"] = table_defaults["dh_rows"]
            current["servo_pins"] = table_defaults["servo_pins"]
        return current

    def __init__(self, parent, motor3d_api, application: MainApplication = None, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)
        self.title("Configuración Brazo 3D")
        self.focus_force()
        self.resizable(True, True)
        self.configure(bg=WINDOW_BG)
        self.application = application
        self.motor3d = motor3d_api
        self._parent_window = parent
        # Escala calculada para que el PEOR caso (DOF6 + leyenda) quepa
        # entero en la pantalla: así la ventana nunca se sale ni necesita scroll
        # (preferencia del usuario: encoger para que todo sea visible).
        self._ui_scale = self._compute_ui_scale()
        # Escala de diseño (la mayor): tope al que se vuelve cuando hay sitio.
        self._design_scale = self._ui_scale
        # Las fuentes se generan vía FontScaler con tamaño base = size*_ui_scale.
        # Al redimensionar la ventana se reconstruye el cuerpo a otra _ui_scale,
        # encogiendo proporcionalmente fuentes Y estructura (paddings) sin perder
        # el layout original.
        self._fonts = FontScaler()
        self._font_cache = {}
        self._font_scale = 1.0
        self._combo_style_name = "Arm3DConfig.TCombobox"
        self._configure_window_styles()

        # Cuerpo desplazable: el contenido vive en self._scroll_inner; así la
        # ventana nunca se sale de la pantalla (aparece scroll si hace falta) y
        # puede redimensionarse. Los botones se anclan fuera del scroll.
        self._build_scroll_container()
        self._build_config_body()

        # Anclar el cuerpo desplazable una vez los botones ya reservan su zona
        # inferior (pack: primero BOTTOM, luego el cuerpo rellena el resto).
        self._scroll_body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Aplicar estado inicial según el perfil activo (debe ir después de crear todos los widgets)
        self._apply_preset_display(self._computed_initial_preset)

        self._sync_scroll_layout()
        self._fit_window_to_content(center=True)
        # Enlazar el reflujo por redimensionado (reconstruye a otra escala).
        self._last_fit_scale = self._ui_scale
        self._resize_job = None
        self._last_win_size = None
        self.bind("<Configure>", self._on_window_configure)

    def _build_config_body(self):
        """Construye el cuerpo de la ventana (perfil/DOF/tutorial/tabla/botones).
        Aislado para poder reconstruirlo a otra escala (_ui_scale) al
        redimensionar, encogiendo TODO de forma proporcional."""
        body = self._scroll_inner

        # ---- Frame superior: perfil y DOF ----
        top_frame = tk.Frame(
            body, bg=SURFACE_BG, bd=1, relief=tk.SOLID,
            highlightthickness=1, highlightbackground=PANEL_BORDER
        )
        top_frame.pack(fill=tk.X, padx=self._s(18), pady=(self._s(14), self._s(8)))
        top_inner = tk.Frame(top_frame, bg=SURFACE_BG)
        top_inner.pack(fill=tk.X, padx=self._s(12), pady=self._s(8))

        top_inner.grid_columnconfigure(0, weight=3)
        top_inner.grid_columnconfigure(1, weight=1)
        top_inner.grid_columnconfigure(2, weight=2)

        profile_block = tk.Frame(top_inner, bg=SURFACE_BG)
        profile_block.grid(row=0, column=0, sticky="ew", padx=(0, self._s(14)))
        tk.Label(profile_block, text="Perfil", bg=SURFACE_BG, fg=DARK_BLUE,
                 font=self._font(10, "bold")).pack(anchor="w", pady=(0, self._s(4)))
        self._presets = self.motor3d.repository.list_builtin_presets()
        preset_names = ["Custom"] + sorted(self._presets.keys())
        current_preset = self.motor3d.active_preset_name
        initial_preset = current_preset if current_preset in self._presets else "Custom"
        self._computed_initial_preset = initial_preset
        self._preset_var = tk.StringVar(value=initial_preset)
        preset_combo = ttk.Combobox(
            profile_block,
            textvariable=self._preset_var,
            values=preset_names,
            state="readonly",
            width=self._s(18),
            style=self._combo_style_name,
        )
        preset_combo.pack(fill=tk.X)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        dof_block = tk.Frame(top_inner, bg=SURFACE_BG)
        dof_block.grid(row=0, column=1, sticky="ew", padx=(0, self._s(14)))
        tk.Label(dof_block, text="DOF", bg=SURFACE_BG, fg=DARK_BLUE,
                 font=self._font(10, "bold")).pack(anchor="w", pady=(0, self._s(4)))
        self._dof_var = tk.IntVar(value=self.motor3d.model.dof)
        self._dof_spin = tk.Spinbox(
            dof_block,
            from_=1,
            to=6,
            textvariable=self._dof_var,
            width=self._s(4),
            font=self._font(12),
            command=self._on_dof_change,
            bg=INPUT_BG,
            fg=TEXT_PRIMARY,
            buttonbackground=SURFACE_ALT_BG,
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1,
            highlightbackground=PANEL_BORDER,
            highlightcolor=DARK_BLUE,
            readonlybackground=INPUT_BG,
            disabledbackground=INPUT_DISABLED_BG,
            disabledforeground=TEXT_MUTED,
            insertbackground=TEXT_PRIMARY,
        )
        self._dof_spin.pack(fill=tk.X)

        visual_block = tk.Frame(top_inner, bg=SURFACE_BG)
        visual_block.grid(row=0, column=2, sticky="ew")
        tk.Label(visual_block, text="Modo visual", bg=SURFACE_BG, fg=DARK_BLUE,
                 font=self._font(10, "bold")).pack(anchor="w", pady=(0, self._s(4)))
        self._visual_var = tk.StringVar()
        self._MODES_SELECTABLE = ["auto_generic", "skeleton"]
        self._vis_combo = ttk.Combobox(
            visual_block,
            textvariable=self._visual_var,
            values=self._MODES_SELECTABLE,
            state="readonly",
            width=self._s(15),
            style=self._combo_style_name,
        )
        self._vis_combo.pack(fill=tk.X)
        self._vis_combo.bind("<<ComboboxSelected>>", self._on_visual_mode_selected)
        self._fps_counter_var = tk.BooleanVar(
            value=self.motor3d.model.visual.get('show_fps_counter', True)
        )
        tk.Checkbutton(
            visual_block,
            text="Mostrar FPS",
            variable=self._fps_counter_var,
            bg=SURFACE_BG,
            fg=TEXT_PRIMARY,
            selectcolor=INPUT_BG,
            activebackground=SURFACE_BG,
            activeforeground=TEXT_PRIMARY,
            font=self._font(9),
        ).pack(anchor="w", pady=(self._s(6), 0))

        self._base_row_widgets = []
        self._base_row_controls = []
        self._base_row_entries = {}

        help_section = tk.Frame(
            body, bg=SURFACE_BG, bd=1, relief=tk.SOLID,
            highlightthickness=1, highlightbackground=PANEL_BORDER
        )
        help_section.pack(fill=tk.X, padx=self._s(18), pady=(0, self._s(8)))
        help_frame = tk.Frame(help_section, bg=SURFACE_BG)
        help_frame.pack(fill=tk.X, padx=self._s(12), pady=(self._s(8), self._s(8)))
        self._help_frame = help_frame
        self._help_btn = tk.Button(
            help_frame,
            text="Abrir tutorial de tablas DH (PDF)",
            command=self._open_dh_tutorial,
            **self._action_button_options(),
        )
        self._help_btn.configure(anchor="w", justify="left", padx=self._s(16))
        self._help_btn.pack(fill=tk.X, pady=self._s(1))
        self._legend_frame = self._build_config_legend(help_frame)

        # ---- Tabla DH ----
        table_shell = tk.Frame(
            body, bg=SURFACE_BG, bd=1, relief=tk.SOLID,
            highlightthickness=1, highlightbackground=PANEL_BORDER
        )
        table_shell.pack(fill=tk.BOTH, expand=True, padx=self._s(18), pady=(0, self._s(8)))
        table_frame = tk.Frame(table_shell, bg=SURFACE_BG)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=self._s(10), pady=self._s(8))

        headers = [
            "J", "Theta (°)", "d (mm)", "a (mm)", "Alpha (°)",
            "Tipo", "Lim min", "Lim max", "Dir yaw", "Dir pitch", "Pin"
        ]
        for col, h in enumerate(headers):
            tk.Label(table_frame, text=h, font=self._font(11, "bold"), bg=SURFACE_HEADER_BG,
                     fg="white", relief=tk.SOLID, bd=1, padx=self._s(8),
                     pady=self._s(7)).grid(row=0, column=col, sticky="nsew", padx=self._s(2), pady=(0, self._s(4)))
        for col in range(len(headers)):
            table_frame.grid_columnconfigure(
                col, weight=1 if col in (1, 2, 3, 4, 6, 7, 8, 9) else 0
            )

        self._rows = []
        self._locked = False
        self._build_dh_rows(table_frame)

        self._table_frame = table_frame

        # ---- Botones inferiores (anclados fuera del scroll, siempre visibles) ----
        btn_frame = tk.Frame(
            self, bg=SURFACE_BG, bd=1, relief=tk.SOLID,
            highlightthickness=1, highlightbackground=PANEL_BORDER
        )
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=self._s(18), pady=(0, self._s(14)))
        self._btn_frame = btn_frame
        btn_inner = tk.Frame(btn_frame, bg=SURFACE_BG)
        btn_inner.pack(fill=tk.X, padx=self._s(12), pady=self._s(8))

        left_btn_frame = tk.Frame(btn_inner, bg=SURFACE_BG)
        left_btn_frame.pack(side=tk.LEFT, pady=self._s(2))
        right_btn_frame = tk.Frame(btn_inner, bg=SURFACE_BG)
        right_btn_frame.pack(side=tk.RIGHT, pady=self._s(2))

        self._btn_import = tk.Button(
            left_btn_frame,
            text="Importar JSON",
            command=self._import_json,
            **self._action_button_options(),
        )
        self._btn_import.pack(side=tk.LEFT, padx=(0, self._s(12)))
        self._btn_export = tk.Button(
            left_btn_frame,
            text="Exportar config",
            command=self._export_json,
            **self._action_button_options(),
        )
        self._btn_export.pack(side=tk.LEFT, padx=(0, self._s(4)))
        self._btn_cancel = tk.Button(
            right_btn_frame,
            text="Cancelar",
            command=self.destroy,
            **self._action_button_options(),
        )
        self._btn_cancel.pack(side=tk.RIGHT, padx=(self._s(12), 0))
        self._btn_save = tk.Button(
            right_btn_frame,
            text="Confirmar",
            command=self._save,
            **self._action_button_options("confirm"),
        )
        self._btn_save.pack(side=tk.RIGHT, padx=(0, self._s(4)))

    def _s(self, value, minimum=1):
        scale = getattr(self, "_ui_scale", 0.82)
        return max(minimum, int(round(value * scale)))

    def _font(self, size, *styles):
        # Tamaño de diseño (incorpora la escala estructural _ui_scale). El factor
        # vivo _font_scale lo aplica FontScaler.apply() al redimensionar.
        base = max(7, int(round(size * getattr(self, "_ui_scale", 0.82))))
        fonts = getattr(self, "_fonts", None)
        if fonts is None:
            # Fallback para instancias creadas con __new__ en pruebas.
            return ("Consolas", base, *styles)
        weight = "bold" if "bold" in styles else "normal"
        slant = "italic" if "italic" in styles else "roman"
        key = (base, weight, slant)
        f = self._font_cache.get(key)
        if f is None:
            f = fonts.font(base, weight, slant)
            self._font_cache[key] = f
        return f

    def _configure_window_styles(self):
        style = ttk.Style(self)
        style.configure(
            self._combo_style_name,
            padding=(self._s(8), self._s(4), self._s(8), self._s(4)),
            font=self._font(11),
            foreground=TEXT_PRIMARY,
            fieldbackground=INPUT_BG,
            background=SURFACE_ALT_BG,
            arrowcolor=TEXT_PRIMARY,
            bordercolor=PANEL_BORDER,
            lightcolor=PANEL_BORDER,
            darkcolor=PANEL_BORDER,
        )
        style.map(
            self._combo_style_name,
            fieldbackground=[("readonly", INPUT_BG), ("disabled", INPUT_DISABLED_BG)],
            foreground=[("readonly", TEXT_PRIMARY), ("disabled", TEXT_MUTED)],
            selectforeground=[("readonly", TEXT_PRIMARY)],
            selectbackground=[("readonly", INPUT_BG)],
            background=[("readonly", SURFACE_ALT_BG), ("disabled", INPUT_DISABLED_BG)],
            arrowcolor=[("disabled", TEXT_MUTED), ("readonly", TEXT_PRIMARY)],
        )

    # ------------------------------------------------------------------
    # Escalado adaptativo + cuerpo desplazable
    # ------------------------------------------------------------------
    # Tamaño del contenido del peor caso (DOF6 + leyenda) por unidad de
    # escala, medido empíricamente: contenido ≈ escala * (K_W, K_H). Sirve para
    # elegir una escala con la que TODO quepa en pantalla sin scroll.
    _CONTENT_K_W = 1010.0
    _CONTENT_K_H = 905.0

    def _compute_ui_scale(self):
        """Escala de la UI: la mayor posible (diseño compacto) con la que el peor
        caso de contenido quepa entero en la pantalla actual, en alto y ancho.
        """
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
        except Exception:
            return 0.82
        # Escala base por altura (≈0.82 en 1080p); y topes para que el peor caso
        # quepa dejando margen (88% alto, 92% ancho).
        base = screen_h / 1320.0
        fit_h = (screen_h * 0.88) / self._CONTENT_K_H
        fit_w = (screen_w * 0.92) / self._CONTENT_K_W
        return max(0.5, min(0.85, base, fit_h, fit_w))

    def _build_scroll_container(self):
        """Crea el contenedor desplazable (canvas + scrollbars + inner frame)."""
        body = tk.Frame(self, bg=WINDOW_BG)
        self._scroll_body = body
        canvas = tk.Canvas(body, bg=WINDOW_BG, bd=0, highlightthickness=0)
        vbar = tk.Scrollbar(body, orient=tk.VERTICAL, command=canvas.yview)
        hbar = tk.Scrollbar(body, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self._scroll_canvas = canvas
        self._scroll_vbar = vbar
        self._scroll_hbar = hbar
        self._vbar_visible = False
        self._hbar_visible = False
        inner = tk.Frame(canvas, bg=WINDOW_BG)
        self._scroll_inner = inner
        self._scroll_inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", self._on_scroll_inner_configure)
        canvas.bind("<Configure>", self._on_scroll_canvas_configure)
        for w in (canvas, inner):
            w.bind("<MouseWheel>", self._on_body_mousewheel)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _on_scroll_inner_configure(self, _event=None):
        # Se dispara solo cuando el contenido cambia de tamaño real (tras un
        # relayout natural de Tk): actualiza la región de scroll y la visibilidad
        # de las barras sin forzar un relayout síncrono costoso.
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        try:
            canvas.configure(scrollregion=canvas.bbox("all"))
            self._set_scrollbar_visibility(
                self._scroll_inner.winfo_reqheight() > canvas.winfo_height() + 1,
                self._scroll_inner.winfo_reqwidth() > canvas.winfo_width() + 1,
            )
        except Exception:
            pass

    def _on_scroll_canvas_configure(self, event):
        """Reevalúa scrollbars y estira el contenido al ancho del canvas.

        Estirar el contenido para que llene el ancho disponible (cuando sobra
        sitio) es BARATO: solo propaga el ``fill``/``grid`` de los frames ya
        existentes —no reconstruye widgets ni reenvuelve texto—, así que se hace
        en vivo durante el arrastre y el contenido rellena el hueco horizontal de
        inmediato. Lo costoso (~250 ms) es la reconstrucción a otra escala de
        fuente, que sigue ocurriendo solo al SOLTAR (debounce). Cuando el
        contenido es más ancho que el canvas se respeta su ancho natural y
        aparece scroll horizontal."""
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        try:
            content_w = self._scroll_inner.winfo_reqwidth()
            content_h = self._scroll_inner.winfo_reqheight()
            fill_w = max(event.width, content_w)
            if fill_w != getattr(self, "_last_fill_w", None):
                canvas.itemconfigure(self._scroll_inner_id, width=fill_w)
                canvas.configure(scrollregion=(0, 0, fill_w, content_h))
                self._last_fill_w = fill_w
            self._set_scrollbar_visibility(
                content_h > event.height + 1,
                content_w > event.width + 1,
            )
        except Exception:
            pass

    def _on_body_mousewheel(self, event):
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None or not getattr(self, "_vbar_visible", False):
            return
        try:
            delta = event.delta
        except Exception:
            return
        if not delta:
            return
        canvas.yview_scroll(-1 if delta > 0 else 1, "units")

    def _sync_scroll_layout(self, set_canvas_size=True):
        """Ajusta scrollregion, scrollbars y el estirado del contenido.

        ``set_canvas_size``: si True (init/DOF/tutorial) fija además el tamaño
        REQUERIDO del canvas al del contenido para que la ventana se abra/ajuste
        a su contenido. Durante el redimensionado (rebuild) se pasa False: la
        ventana ya tiene el tamaño que puso el usuario y fijar el tamaño del
        canvas haría que la ventana se encogiera al contenido (rompía el
        agrandado y la responsividad al ajustar el bloque superior)."""
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        try:
            self.update_idletasks()
            content_w = self._scroll_inner.winfo_reqwidth()
            content_h = self._scroll_inner.winfo_reqheight()
            btn_h = 0
            btn_frame = getattr(self, "_btn_frame", None)
            if btn_frame is not None:
                btn_h = btn_frame.winfo_reqheight()
            # Guardar el tamaño natural a fuente de diseño (factor 1.0) como
            # referencia para el preview y el cálculo de escala al redimensionar.
            if abs(getattr(self, "_font_scale", 1.0) - 1.0) < 0.02:
                self._built_nat_w = content_w
                self._built_nat_h = content_h + btn_h
            try:
                cap_w = int(self.winfo_screenwidth() * 0.94)
                cap_h = int(self.winfo_screenheight() * 0.90)
            except Exception:
                cap_w, cap_h = content_w, content_h
            view_w = min(content_w, cap_w)
            view_h = min(content_h, max(cap_h - btn_h, 200))
            need_v = content_h > view_h + 1
            need_h = content_w > view_w + 1
            self._set_scrollbar_visibility(need_v, need_h)
            # Estirar el contenido para llenar el ancho del canvas cuando sobra
            # sitio (evita el hueco a la derecha al agrandar). Se hace aquí, en
            # el "settle", no en cada píxel del arrastre, para no penalizar el
            # rendimiento. La región de scroll cubre el ancho real mostrado.
            cw = max(canvas.winfo_width(), 1)
            fill_w = max(cw, content_w)
            try:
                canvas.itemconfigure(self._scroll_inner_id, width=fill_w)
                self._last_fill_w = fill_w
            except Exception:
                pass
            if set_canvas_size:
                canvas.configure(
                    width=view_w, height=view_h,
                    scrollregion=(0, 0, fill_w, content_h),
                )
            else:
                canvas.configure(scrollregion=(0, 0, fill_w, content_h))
        except Exception:
            pass

    def _set_scrollbar_visibility(self, need_v, need_h):
        vbar = getattr(self, "_scroll_vbar", None)
        hbar = getattr(self, "_scroll_hbar", None)
        if vbar is not None and need_v != getattr(self, "_vbar_visible", False):
            if need_v:
                vbar.pack(side=tk.RIGHT, fill=tk.Y, before=self._scroll_canvas)
            else:
                vbar.pack_forget()
            self._vbar_visible = need_v
        if hbar is not None and need_h != getattr(self, "_hbar_visible", False):
            if need_h:
                hbar.pack(side=tk.BOTTOM, fill=tk.X, before=self._scroll_canvas)
            else:
                hbar.pack_forget()
            self._hbar_visible = need_h

    def _on_window_configure(self, event):
        """Redimensionado de la ventana.

        Reconstruir el cuerpo (ttk + tabla + texto con wrap) cuesta ~250 ms, y
        cualquier reescalado (incluso solo de fuentes) provoca ese relayout. Por
        eso NO se reescala durante el arrastre —la ventana solo se redimensiona,
        con su scroll, que es barato— y se reconstruye UNA sola vez a la escala
        adecuada cuando el arrastre se detiene (debounce), quedando proporcional
        y sin scroll.
        """
        if event.widget is not self:
            return
        size = (event.width, event.height)
        last = getattr(self, "_last_win_size", None)
        if last is not None and abs(size[0] - last[0]) < 8 and abs(size[1] - last[1]) < 8:
            return
        self._last_win_size = size
        if getattr(self, "_resize_job", None) is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
        self._resize_job = self.after(280, self._apply_resize_scale)

    def _apply_resize_scale(self):
        self._resize_job = None
        if not hasattr(self, "tk") or getattr(self, "_scroll_inner", None) is None:
            return
        # Escala el contenido para llenar la ventana de forma proporcional, tanto
        # al ENCOGER como al AGRANDAR (puede crecer por encima del diseño hasta un
        # tope). Se ajusta a la dimensión limitante para no necesitar scroll; el
        # hueco horizontal restante lo cubre el estirado del contenido.
        #
        # Se itera (máx. 2) re-midiendo el contenido real para converger sin
        # scroll. Esto solo ocurre al SOLTAR (debounce), una vez por gesto, no
        # durante el arrastre, por lo que no penaliza la fluidez.
        max_scale = max(0.95, self._design_scale)
        for _ in range(2):
            try:
                self.update_idletasks()
                nat_w = self._scroll_inner.winfo_reqwidth()
                nat_h = self._scroll_inner.winfo_reqheight()
                btn_frame = getattr(self, "_btn_frame", None)
                if btn_frame is not None:
                    nat_h += btn_frame.winfo_reqheight()
                win_w = self.winfo_width()
                win_h = self.winfo_height()
            except Exception:
                return
            if nat_w <= 1 or nat_h <= 1 or win_w <= 1:
                return
            ratio = min((win_w - 6) / nat_w, (win_h - 6) / nat_h)
            target = max(0.40, min(max_scale, self._ui_scale * ratio))
            if abs(target - self._ui_scale) < 0.02:
                break
            self._rebuild_config_body(target)

    def _rebuild_config_body(self, scale):
        """Reconstruye el cuerpo a otra escala conservando el estado editado."""
        try:
            cfg = self._snapshot_config_from_inputs(target_dof=self._dof_var.get())
            self.motor3d.set_model_config(cfg)
        except Exception:
            pass
        saved = {
            "preset": self._preset_var.get() if hasattr(self, "_preset_var") else "Custom",
            "dof": self._dof_var.get() if hasattr(self, "_dof_var") else 6,
            "visual": self._visual_var.get() if hasattr(self, "_visual_var") else None,
            "fps": self._fps_counter_var.get() if hasattr(self, "_fps_counter_var") else True,
        }
        self._ui_scale = scale
        self._fonts = FontScaler()
        self._font_cache = {}
        self._font_scale = 1.0
        self._configure_window_styles()
        try:
            for w in self._scroll_inner.winfo_children():
                w.destroy()
            if getattr(self, "_btn_frame", None) is not None:
                self._btn_frame.destroy()
        except Exception:
            pass
        self._build_config_body()
        # Reasegurar el orden de empaquetado: el _btn_frame (BOTTOM) recién creado
        # debe reservar su zona ANTES de que el cuerpo (TOP+expand) rellene el
        # resto; si no, el cuerpo lo aplasta y los botones desaparecen.
        try:
            self._scroll_body.pack_forget()
            self._scroll_body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        except Exception:
            pass
        try:
            self._dof_var.set(saved["dof"])
            if saved["visual"] is not None:
                self._visual_var.set(saved["visual"])
            self._fps_counter_var.set(saved["fps"])
            self._preset_var.set(saved["preset"])
        except Exception:
            pass
        self._apply_preset_display(saved["preset"])
        # Un único layout síncrono: ajusta scroll y captura el tamaño natural a
        # fuente de diseño. set_canvas_size=False: NO reajustar la ventana al
        # contenido (la ventana ya tiene el tamaño del usuario durante el
        # redimensionado; si no, se encogería tras cada rebuild).
        self._sync_scroll_layout(set_canvas_size=False)

    def _fit_window_to_content(self, center=False):
        if not hasattr(self, "tk"):
            return
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        # Recortar al tamaño de pantalla para que la ventana nunca se salga
        # (el scroll del cuerpo cubre el contenido que no quepa). Protegido por
        # try/except para no romper invocaciones de prueba con stubs.
        try:
            width = min(width, int(self.winfo_screenwidth() * 0.96))
            height = min(height, int(self.winfo_screenheight() * 0.94))
        except Exception:
            pass
        # El ANCHO se fija al del contenido: apenas puede encoger (las fuentes
        # tienen un mínimo legible y la tabla tiene 11 columnas), así que impedir
        # estrecharlo evita por completo la barra horizontal —incluso cuando
        # aparece la vertical, que se reserva su hueco dentro de este ancho—.
        # El ALTO sí puede encoger; si el contenido no cabe, aparece scroll
        # vertical pero los botones permanecen anclados y visibles.
        self.minsize(width, min(height, 360))

        if center:
            parent = getattr(self, "_parent_window", None)
            if parent is not None:
                x = parent.winfo_x() + (parent.winfo_width() - width) // 2
                y = parent.winfo_y() + (parent.winfo_height() - height) // 2
            else:
                x = self.winfo_x()
                y = self.winfo_y()
            self.geometry(f"{width}x{height}+{x}+{y}")
            return

        x = self.winfo_x()
        y = self.winfo_y()
        self.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def _base_transform_entry_behavior():
        """Campos DH de J0: editables, pero distinguidos del resto por ser base fija."""
        return ("fixed", False)

    @staticmethod
    def _base_metadata_entry_behavior():
        """Campos no aplicables en J0: tipo, límites y dirección, siempre bloqueados."""
        return ("disabled", True)

    def _servo_pins_for_table(self, config, dof):
        pins = list(config.get('servo_pins', []) or [])
        if not any(pin is not None for pin in pins):
            pins = list(self.BRACCIO_SERVO_PINS)
        normalized = [self._parse_pin_value(pin, allow_empty=True) for pin in pins[:dof]]
        while len(normalized) < dof:
            normalized.append(None)
        return normalized

    @staticmethod
    def _parse_pin_value(value, allow_empty=False):
        text = "" if value is None else str(value).strip()
        if not text:
            if allow_empty:
                return None
            raise ValueError
        if text.lower().startswith("a") and len(text) > 1:
            return int(text[1:]) + 14
        pin = int(text)
        if pin < 0:
            raise ValueError
        return pin

    @staticmethod
    def _joint_dh_entry_behavior(jtype, key):
        """Clasifica el aspecto y la editabilidad de cada parámetro DH."""
        if jtype == 'P' and key == 'theta':
            return ("disabled", True)
        if jtype == 'P' and key == 'd':
            return ("accent", False)
        if jtype == 'R' and key == 'theta':
            return ("accent", False)
        return ("standard", False)

    @staticmethod
    def _joint_direction_entry_behavior(jtype):
        """Yaw/pitch solo aplican a prismáticas con preorientación."""
        if jtype == 'P':
            return ("standard", False)
        return ("disabled", True)

    def _entry_options(self, variant="standard"):
        bg = INPUT_BG
        fg = TEXT_PRIMARY
        border = PANEL_BORDER
        if variant == "fixed":
            bg = INPUT_FIXED_BG
            fg = TEXT_PRIMARY
            border = INPUT_FIXED_BORDER
        elif variant == "disabled":
            bg = INPUT_DISABLED_BG
            fg = TEXT_DISABLED
            border = INPUT_DISABLED_BORDER
        elif variant == "accent":
            bg = INPUT_ACCENT_BG
            border = BLUE
        return {
            "bg": bg,
            "fg": fg,
            "bd": 1,
            "relief": tk.SOLID,
            "highlightthickness": 1,
            "highlightbackground": border,
            "highlightcolor": border,
            "disabledbackground": INPUT_DISABLED_BG,
            "disabledforeground": TEXT_DISABLED,
            "readonlybackground": bg,
            "insertbackground": TEXT_PRIMARY,
        }

    @staticmethod
    def _remember_semantic_state(widget, state):
        """Guarda el estado funcional del widget para restaurarlo tras bloquear/desbloquear."""
        try:
            widget._semantic_state = state
        except Exception:
            pass

    @staticmethod
    def _semantic_state_for_widget(widget):
        state = getattr(widget, "_semantic_state", None)
        if state:
            return state
        if isinstance(widget, ttk.Combobox):
            return "readonly"
        return "normal"

    def _apply_widget_state(self, widget, locked):
        target_state = "disabled" if locked else self._semantic_state_for_widget(widget)
        try:
            widget.configure(state=target_state)
        except Exception:
            pass

    def _build_config_legend(self, parent):
        """Añade una leyenda visual para interpretar los colores de la tabla."""
        legend_frame = tk.Frame(parent, bg=SURFACE_BG)
        legend_frame.pack(fill=tk.X, pady=(self._s(10), self._s(2)))

        items_frame = tk.Frame(legend_frame, bg=SURFACE_BG)
        items_frame.pack(fill=tk.X)

        legend_items = [
            ("Editable", "standard", "Parámetro general editable."),
            ("Activa", "accent", "Variable principal de la articulación actual."),
            ("Base fija", "fixed", "Parámetro de J0 editable, pero especial."),
            ("Bloqueada", "disabled", "No aplica o no puede editarse."),
        ]

        for idx, (title, variant, description) in enumerate(legend_items):
            item = tk.Frame(items_frame, bg=SURFACE_BG)
            item.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=(0, self._s(16)), pady=self._s(4))

            options = self._entry_options(variant)
            swatch = tk.Label(
                item,
                text="  ",
                width=self._s(3),
                relief=tk.SOLID,
                bd=1,
                bg=options["bg"],
                fg=options["fg"],
                highlightthickness=1,
                highlightbackground=options["highlightbackground"],
            )
            swatch.pack(side=tk.LEFT, padx=(0, self._s(8)))

            text_frame = tk.Frame(item, bg=SURFACE_BG)
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(
                text_frame,
                text=title,
                bg=SURFACE_BG,
                fg=TEXT_PRIMARY,
                font=self._font(10, "bold"),
            ).pack(anchor="w")
            tk.Label(
                text_frame,
                text=description,
                bg=SURFACE_BG,
                fg=TEXT_MUTED,
                font=self._font(9),
            ).pack(anchor="w")

        items_frame.grid_columnconfigure(0, weight=1)
        items_frame.grid_columnconfigure(1, weight=1)
        return legend_frame

    def _action_button_options(self, variant="secondary"):
        options = {
            "font": self._font(11, "bold"),
            "bd": 2,
            "relief": tk.SOLID,
            "highlightthickness": 1,
            "padx": self._s(14),
            "pady": self._s(6),
            "overrelief": tk.GROOVE,
        }
        if variant == "confirm":
            options.update({
                "bg": PANEL_CONFIRM_BG,
                "fg": "white",
                "activebackground": PANEL_CONFIRM_ACTIVE_BG,
                "activeforeground": "white",
                "disabledforeground": PANEL_ACTION_DISABLED_FG,
                "highlightbackground": PANEL_CONFIRM_BORDER,
                "highlightcolor": PANEL_CONFIRM_BORDER,
            })
        else:
            options.update({
                "bg": PANEL_ACTION_BG,
                "fg": PANEL_ACTION_FG,
                "activebackground": PANEL_ACTION_ACTIVE_BG,
                "activeforeground": PANEL_ACTION_FG,
                "disabledforeground": PANEL_ACTION_DISABLED_FG,
                "highlightbackground": PANEL_ACTION_BORDER,
                "highlightcolor": PANEL_ACTION_BORDER,
            })
        return options

    def _set_action_button_enabled(self, button, enabled=True, variant="secondary"):
        options = self._action_button_options(variant)
        if enabled:
            options.update({
                "state": "normal",
                "cursor": "hand2",
                "relief": tk.SOLID,
            })
        else:
            options.update({
                "state": "disabled",
                "cursor": "arrow",
                "relief": tk.GROOVE,
                "bg": PANEL_CONFIRM_DISABLED_BG if variant == "confirm" else PANEL_ACTION_DISABLED_BG,
                "highlightbackground": (
                    PANEL_CONFIRM_BORDER if variant == "confirm" else PANEL_ACTION_DISABLED_BORDER
                ),
                "highlightcolor": (
                    PANEL_CONFIRM_BORDER if variant == "confirm" else PANEL_ACTION_DISABLED_BORDER
                ),
            })
        button.configure(**options)

    def _build_dh_rows(self, table_frame):
        """Construye las filas editables de la tabla DH."""
        for widgets in self._rows:
            for w in widgets:
                try:
                    w.destroy()
                except Exception:
                    pass
        for w in self._base_row_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self._rows = []
        self._base_row_widgets = []
        self._base_row_controls = []
        self._base_row_entries = {}

        table_config = self._table_source_config()
        model = self.motor3d.model
        n = self._dof_var.get()
        base = dict(table_config.get('base', {'theta': 0.0, 'd': 0.0, 'a': 0.0, 'alpha': 0.0}))
        dh_rows = list(table_config.get('dh_rows', []))
        servo_pins = self._servo_pins_for_table(table_config, n)

        base_lbl = tk.Label(
            table_frame, text="0", font=self._font(11, "bold"),
            width=self._s(3), bg=SURFACE_BG, fg=TEXT_MUTED
        )
        base_lbl.grid(row=1, column=0, sticky="nsew", padx=self._s(2), pady=self._s(2))
        self._base_row_widgets.append(base_lbl)

        for col, key in enumerate(['theta', 'd', 'a', 'alpha']):
            variant, disabled = self._base_transform_entry_behavior()
            entry = tk.Entry(
                table_frame, font=self._font(11), width=self._s(9),
                **self._entry_options(variant)
            )
            entry.insert(0, str(round(float(base.get(key, 0.0)), 2)))
            self._remember_semantic_state(entry, "disabled" if disabled else "normal")
            if disabled:
                entry.configure(state="disabled")
            entry.grid(row=1, column=col + 1, sticky="nsew", padx=self._s(2), pady=self._s(2))
            self._base_row_entries[key] = entry
            self._base_row_widgets.append(entry)
            self._base_row_controls.append(entry)

        type_variant, type_disabled = self._base_metadata_entry_behavior()
        type_entry = tk.Entry(
            table_frame, font=self._font(11), width=self._s(4), justify="center",
            **self._entry_options(type_variant)
        )
        type_entry.insert(0, "F")
        self._remember_semantic_state(type_entry, "disabled" if type_disabled else "normal")
        if type_disabled:
            type_entry.configure(state="disabled")
        type_entry.grid(row=1, column=5, sticky="nsew", padx=self._s(2), pady=self._s(2))
        self._base_row_widgets.append(type_entry)

        for col in (6, 7, 8, 9, 10):
            meta_variant, meta_disabled = self._base_metadata_entry_behavior()
            lim_entry = tk.Entry(
                table_frame, font=self._font(11), width=self._s(7), justify="center",
                **self._entry_options(meta_variant)
            )
            lim_entry.insert(0, "--")
            self._remember_semantic_state(lim_entry, "disabled" if meta_disabled else "normal")
            if meta_disabled:
                lim_entry.configure(state="disabled")
            lim_entry.grid(row=1, column=col, sticky="nsew", padx=self._s(2), pady=self._s(2))
            self._base_row_widgets.append(lim_entry)

        note = tk.Label(table_frame, text="fija", font=self._font(9),
                        bg=SURFACE_BG, fg=TEXT_MUTED)
        note.grid(row=1, column=11, padx=self._s(2), pady=self._s(2))
        self._base_row_widgets.append(note)

        for i in range(n):
            grid_row = i + 2
            row_entries = []
            dh = dh_rows[i] if i < len(dh_rows) else {'theta': 0, 'd': 0, 'a': 100, 'alpha': 0}
            lims = model.joint_limits[i] if i < len(model.joint_limits) else (-90.0, 90.0)
            jtype = model.joint_types[i] if i < len(model.joint_types) else 'R'
            raw_pre_rotations = getattr(model, 'prismatic_pre_rotations', []) or []
            direction = raw_pre_rotations[i] if i < len(raw_pre_rotations) else {'yaw': 0.0, 'pitch': 0.0}
            servo_pin = servo_pins[i] if i < len(servo_pins) else None

            joint_lbl = tk.Label(
                table_frame, text=str(i + 1), font=self._font(11, "bold"),
                width=self._s(3), bg=SURFACE_BG, fg=TEXT_MUTED
            )
            joint_lbl.grid(row=grid_row, column=0, sticky="nsew", padx=self._s(2), pady=self._s(2))

            dh_entries = []
            for col, key in enumerate(['theta', 'd', 'a', 'alpha']):
                variant, disabled = self._joint_dh_entry_behavior(jtype, key)
                e = tk.Entry(
                    table_frame, font=self._font(11), width=self._s(9),
                    **self._entry_options(variant)
                )
                e.insert(0, str(round(float(dh.get(key, 0.0)), 2)))
                self._remember_semantic_state(e, "disabled" if disabled else "normal")
                if disabled:
                    e.configure(state="disabled")
                e.grid(row=grid_row, column=col + 1, sticky="nsew", padx=self._s(2), pady=self._s(2))
                dh_entries.append(e)
            row_entries.extend(dh_entries)

            direction_entries = []
            for offset, key in enumerate(('yaw', 'pitch')):
                direction_variant, direction_disabled = self._joint_direction_entry_behavior(jtype)
                direction_entry = tk.Entry(
                    table_frame, font=self._font(11), width=self._s(7),
                    **self._entry_options(direction_variant)
                )
                direction_entry.insert(0, str(round(float(direction.get(key, 0.0)), 2)))
                self._remember_semantic_state(direction_entry, "disabled" if direction_disabled else "normal")
                if direction_disabled:
                    direction_entry.configure(state="disabled")
                direction_entry.grid(row=grid_row, column=offset + 8, sticky="nsew", padx=self._s(2), pady=self._s(2))
                direction_entries.append(direction_entry)

            def _make_type_cb(combo, theta_e, d_e, a_e, direction_widgets, unit_widget):
                def _cb(_evt=None):
                    new_jt = combo.get()
                    if new_jt == 'P':
                        theta_e.configure(state='normal', **self._entry_options("disabled"))
                        theta_e.configure(state='disabled')
                        self._remember_semantic_state(theta_e, "disabled")
                        d_e.configure(state='normal', **self._entry_options("accent"))
                        self._remember_semantic_state(d_e, "normal")
                        unit_widget.configure(text="mm")
                        defaults = ('0.0', '0.0')
                        for idx, direction_e in enumerate(direction_widgets):
                            direction_e.configure(state='normal', **self._entry_options("standard"))
                            self._remember_semantic_state(direction_e, "normal")
                            if not str(direction_e.get()).strip():
                                direction_e.insert(0, defaults[idx])
                        try:
                            a_val = float(a_e.get())
                            d_val = float(d_e.get())
                            if (
                                not math.isclose(a_val, 0.0, abs_tol=1e-9)
                                and math.isclose(d_val, 0.0, abs_tol=1e-9)
                            ):
                                d_e.configure(state='normal')
                                d_e.delete(0, tk.END)
                                d_e.insert(0, str(a_val))
                                a_e.delete(0, tk.END)
                                a_e.insert(0, '0.0')
                                d_e.configure(**self._entry_options("accent"))
                        except (ValueError, tk.TclError):
                            pass
                    else:
                        theta_e.configure(state='normal', **self._entry_options("accent"))
                        self._remember_semantic_state(theta_e, "normal")
                        d_e.configure(state='normal', **self._entry_options("standard"))
                        self._remember_semantic_state(d_e, "normal")
                        a_e.configure(state='normal', **self._entry_options("standard"))
                        self._remember_semantic_state(a_e, "normal")
                        unit_widget.configure(text="deg")
                        for direction_e in direction_widgets:
                            direction_e.configure(state='normal', **self._entry_options("disabled"))
                            direction_e.configure(state='disabled')
                            self._remember_semantic_state(direction_e, "disabled")
                        try:
                            d_val = float(d_e.get())
                            a_val = float(a_e.get())
                            if (
                                not math.isclose(d_val, 0.0, abs_tol=1e-9)
                                and math.isclose(a_val, 0.0, abs_tol=1e-9)
                            ):
                                d_e.delete(0, tk.END)
                                d_e.insert(0, '0.0')
                                a_e.delete(0, tk.END)
                                a_e.insert(0, str(d_val))
                        except (ValueError, tk.TclError):
                            pass
                return _cb

            type_combo = ttk.Combobox(
                table_frame, values=["R", "P"], state="readonly", width=self._s(4),
                style=self._combo_style_name
            )
            type_combo.set(jtype)
            self._remember_semantic_state(type_combo, "readonly")
            type_combo.grid(row=grid_row, column=5, sticky="nsew", padx=self._s(2), pady=self._s(2))
            row_entries.append(type_combo)

            lim_unit = "mm" if jtype == 'P' else "deg"
            e_min = tk.Entry(
                table_frame, font=self._font(11), width=self._s(7),
                **self._entry_options("standard")
            )
            e_min.insert(0, str(round(float(lims[0]), 1)))
            e_min.grid(row=grid_row, column=6, sticky="nsew", padx=self._s(2), pady=self._s(2))

            e_max = tk.Entry(
                table_frame, font=self._font(11), width=self._s(7),
                **self._entry_options("standard")
            )
            e_max.insert(0, str(round(float(lims[1]), 1)))
            e_max.grid(row=grid_row, column=7, sticky="nsew", padx=self._s(2), pady=self._s(2))

            pin_entry = tk.Entry(
                table_frame, font=self._font(11), width=self._s(6),
                justify="center", **self._entry_options("standard")
            )
            if servo_pin is not None:
                pin_entry.insert(0, str(servo_pin))
            self._remember_semantic_state(pin_entry, "normal")
            pin_entry.grid(row=grid_row, column=10, sticky="nsew", padx=self._s(2), pady=self._s(2))

            unit_lbl = tk.Label(
                table_frame, text=lim_unit, font=self._font(9),
                bg=SURFACE_BG, fg=TEXT_MUTED
            )
            unit_lbl.grid(row=grid_row, column=11, padx=self._s(2), pady=self._s(2))

            type_combo.bind(
                "<<ComboboxSelected>>",
                _make_type_cb(
                    type_combo, dh_entries[0], dh_entries[1], dh_entries[2], direction_entries, unit_lbl
                )
            )

            row_entries.extend([e_min, e_max])
            row_entries.extend(direction_entries)
            row_entries.append(pin_entry)
            row_entries.extend([unit_lbl, joint_lbl])
            self._rows.append(row_entries)

        # Respetar el estado de bloqueo si ya estaba activo
        if self._locked:
            self._set_locked(True)

    def _apply_preset_display(self, name):
        """Actualiza el modo visual y el estado de bloqueo según el perfil indicado."""
        is_tinkerkit = (name == "braccio_tinkerkit")
        if hasattr(self, "_fps_counter_var"):
            self._fps_counter_var.set(
                self.motor3d.model.visual.get('show_fps_counter', True)
            )
        if is_tinkerkit:
            # braccio_exact es el modo propio del tinkerkit; mostrarlo aunque no sea seleccionable
            self._vis_combo.configure(values=["braccio_exact"] + self._MODES_SELECTABLE)
            self._visual_var.set("braccio_exact")
        else:
            self._vis_combo.configure(values=self._MODES_SELECTABLE)
            if name == "Custom":
                self._visual_var.set("auto_generic")
            else:
                # Modo guardado en el preset
                path = self._presets.get(name)
                saved_mode = "auto_generic"
                if path:
                    import json
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        m = data.get('visual', {}).get('mode', 'auto_generic')
                        saved_mode = m if m in self._MODES_SELECTABLE else 'auto_generic'
                    except Exception:
                        pass
                self._visual_var.set(saved_mode)
        self._set_locked(is_tinkerkit)

    def _set_locked(self, locked: bool):
        """Deshabilita o habilita todos los controles editables (perfil de solo lectura)."""
        self._locked = locked
        state_spin   = "disabled" if locked else "normal"
        state_combo  = "disabled" if locked else "readonly"
        self._dof_spin.configure(state=state_spin)
        self._vis_combo.configure(state=state_combo)
        self._set_action_button_enabled(self._btn_import, enabled=not locked)
        self._set_action_button_enabled(self._btn_export, enabled=True)
        self._set_action_button_enabled(self._btn_save, enabled=True, variant="confirm")
        # Aplicar a las filas de la tabla DH
        for row in self._rows:
            for widget in row:
                self._apply_widget_state(widget, locked)
        for widget in self._base_row_controls:
            self._apply_widget_state(widget, locked)

    def _on_preset_selected(self, _event=None):
        """Carga el preset seleccionado y repuebla DOF, modo visual y tabla DH."""
        name = self._preset_var.get()
        previous = self.motor3d.active_preset_name
        if name != "Custom":
            path = self._presets.get(name)
            if not path:
                return
            import json
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                tk.messagebox.showerror("Error", f"No se pudo leer el preset '{name}'.", parent=self)
                return
            dof = data.get('dof', self.motor3d.model.dof)
            self._dof_var.set(dof)
            self.motor3d.set_model_config(data)
            self._sync_arm3d_servo_pin_mapping()
            self._build_dh_rows(self._table_frame)
            self._refresh_base_row_entries()
        elif previous in self._presets:
            # Solo al pasar de un preset del sistema a Custom se descarta la
            # servo_calibration heredada (la tabla no la incluye) -> mapeo 1:1.
            # Un Custom ya existente o importado desde JSON conserva su calibración.
            config = self.motor3d.get_model_config()
            config['servo_calibration'] = []
            self.motor3d.set_model_config(config)
        self._apply_preset_display(name)
        self.motor3d.active_preset_name = name if name != "Custom" else None
        self.motor3d.model.preset_name = self.motor3d.active_preset_name
        self._clear_combo_focus()

    def _on_visual_mode_selected(self, _event=None):
        self._clear_combo_focus()

    def _sync_arm3d_servo_pin_mapping(self):
        controller = getattr(getattr(self, "application", None), "controller", None)
        layer = getattr(controller, "robot_layer", None)
        if hasattr(layer, "apply_servo_pin_mapping"):
            layer.apply_servo_pin_mapping()

    def _clear_combo_focus(self):
        def _clear():
            widget = self.focus_get()
            try:
                if widget is not None and hasattr(widget, "selection_clear"):
                    widget.selection_clear()
            except Exception:
                pass
            try:
                self.focus_set()
            except Exception:
                pass

        try:
            self.after_idle(_clear)
        except Exception:
            _clear()

    def _fps_counter_enabled(self):
        var = getattr(self, "_fps_counter_var", None)
        if var is not None:
            try:
                return bool(var.get())
            except Exception:
                pass
        try:
            return bool(self.motor3d.model.visual.get('show_fps_counter', True))
        except Exception:
            return True

    def _snapshot_config_from_inputs(self, target_dof=None):
        """Construye una configuración desde la GUI actual sin invalidar el flujo por errores parciales."""
        current = self.motor3d.get_model_config()
        n = len(self._rows)

        current_dh = list(current.get('dh_rows', []))
        current_types = list(current.get('joint_types', []))
        current_limits = list(current.get('joint_limits', []))
        current_dirs = list(current.get('prismatic_pre_rotations', []))
        current_pins = list(current.get('servo_pins', []))
        current_base = dict(current.get('base', {}))

        dh_rows = []
        joint_types = []
        joint_limits = []
        prismatic_pre_rotations = []
        servo_pins = []

        for i, row in enumerate(self._rows):
            prev_dh = current_dh[i] if i < len(current_dh) else {'theta': 0.0, 'd': 0.0, 'a': 100.0, 'alpha': 0.0}
            prev_type = current_types[i] if i < len(current_types) else 'R'
            prev_limits = current_limits[i] if i < len(current_limits) else (-90.0, 90.0)
            prev_dir = current_dirs[i] if i < len(current_dirs) else {'yaw': 0.0, 'pitch': 0.0}
            prev_pin = current_pins[i] if i < len(current_pins) else None

            parsed_dh = {}
            for col, key in enumerate(['theta', 'd', 'a', 'alpha']):
                try:
                    parsed_dh[key] = float(row[col].get())
                except (ValueError, TypeError):
                    parsed_dh[key] = float(prev_dh.get(key, 0.0 if key != 'a' else 100.0))
            dh_rows.append(parsed_dh)

            try:
                jtype = row[4].get()
            except Exception:
                jtype = prev_type
            joint_types.append(jtype if jtype in ('R', 'P') else prev_type)

            try:
                lim_min = float(row[5].get())
            except (ValueError, TypeError):
                lim_min = float(prev_limits[0])
            try:
                lim_max = float(row[6].get())
            except (ValueError, TypeError):
                lim_max = float(prev_limits[1])
            joint_limits.append((lim_min, lim_max))

            direction = {'yaw': 0.0, 'pitch': 0.0}
            if joint_types[-1] == 'P':
                try:
                    direction['yaw'] = float(row[7].get())
                except (ValueError, TypeError):
                    direction['yaw'] = float(prev_dir.get('yaw', 0.0))
                try:
                    direction['pitch'] = float(row[8].get())
                except (ValueError, TypeError):
                    direction['pitch'] = float(prev_dir.get('pitch', 0.0))
            prismatic_pre_rotations.append(direction)

            try:
                servo_pins.append(self._parse_pin_value(row[9].get(), allow_empty=True))
            except (ValueError, TypeError):
                servo_pins.append(self._parse_pin_value(prev_pin, allow_empty=True))

        base_row = {}
        for key, entry in self._base_row_entries.items():
            try:
                base_row[key] = float(entry.get())
            except (ValueError, TypeError):
                base_row[key] = float(current_base.get(key, 0.0))

        current['dof'] = target_dof if target_dof is not None else n
        current['dh_rows'] = dh_rows
        current['joint_types'] = joint_types
        current['joint_limits'] = joint_limits
        current['prismatic_pre_rotations'] = prismatic_pre_rotations
        current['servo_pins'] = servo_pins
        current['base'] = base_row
        current['visual'] = dict(current.get('visual', {}))
        current['visual']['mode'] = self._visual_var.get()
        current['visual']['show_fps_counter'] = self._fps_counter_enabled()
        return current

    def _on_dof_change(self):
        config = self._snapshot_config_from_inputs(target_dof=self._dof_var.get())
        self.motor3d.set_model_config(config)
        self._sync_arm3d_servo_pin_mapping()
        self._build_dh_rows(self._table_frame)
        self._refresh_base_row_entries()
        self._sync_scroll_layout()
        self._fit_window_to_content()

    def _refresh_base_row_entries(self):
        base_row = dict(self._table_source_config().get(
            'base',
            {'theta': 0.0, 'd': 0.0, 'a': 0.0, 'alpha': 0.0},
        ))
        for key, entry in self._base_row_entries.items():
            prev_state = str(entry.cget('state'))
            if prev_state == "disabled":
                entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, str(round(float(base_row.get(key, 0.0)), 2)))
            if prev_state == "disabled":
                entry.configure(state="disabled")

    def _open_dh_tutorial(self, event=None):
        path = None
        for candidate in (
            os.path.join("tutorials", "Tutorial_tablas_DH.pdf"),
            os.path.join("tutorials", "Tutorial.pdf"),
        ):
            candidate = os.path.abspath(candidate)
            if os.path.exists(candidate):
                path = candidate
                break

        if path is None:
            path = os.path.abspath(os.path.join("tutorials", "Tutorial_tablas_DH.pdf"))
            messagebox.showerror(
                "Tutorial DH no encontrado",
                "No se encontro el PDF de tablas DH:\n" + path,
            )
            return
        subprocess.Popen([path], shell=True)

    def _collect_config(self):
        """Lee los valores de la tabla y retorna (dict, None) o (None, mensaje_error).
        Resalta en rojo las entradas inválidas para dar feedback visual al usuario."""
        n = len(self._rows)
        dh_rows = []
        joint_types = []
        joint_limits = []
        prismatic_pre_rotations = []
        servo_pins = []
        base_row = {}
        errors = []

        # Limpiar resaltados previos
        for row in self._rows:
            for idx in (0, 1, 2, 3, 5, 6, 7, 8, 9):
                if idx >= len(row):
                    continue
                widget = row[idx]
                try:
                    widget.configure(highlightthickness=0)
                except Exception:
                    pass
        for widget in self._base_row_entries.values():
            try:
                widget.configure(highlightthickness=0)
            except Exception:
                pass

        def _mark_invalid(widget, msg):
            try:
                widget.configure(highlightthickness=2,
                                 highlightbackground="#FF4444",
                                 highlightcolor="#FF4444")
            except Exception:
                pass
            errors.append(msg)

        for i, row in enumerate(self._rows):
            joint_n = i + 1
            dh_ok = True
            parsed = {}
            for col, key in enumerate(['theta', 'd', 'a', 'alpha']):
                try:
                    parsed[key] = float(row[col].get())
                except ValueError:
                    _mark_invalid(row[col], f"J{joint_n}: '{key}' no es un número válido.")
                    dh_ok = False

            if dh_ok:
                # RF1.1.1.3: parametro DH 'a' con signo, limitado a +/-2000 mm.
                a = parsed['a']
                if abs(a) > 2000:
                    _mark_invalid(row[2], f"J{joint_n}: 'a' supera el limite fisico (+/-2000 mm).")
                    dh_ok = False

            if dh_ok:
                dh_rows.append({'theta': parsed['theta'], 'd': parsed['d'],
                                'a': parsed['a'], 'alpha': parsed['alpha']})
            else:
                dh_rows.append({'theta': 0, 'd': 0, 'a': 100, 'alpha': 0})  # placeholder

            jtype = row[4].get() if hasattr(row[4], 'get') else 'R'
            joint_types.append(jtype)

            direction = {'yaw': 0.0, 'pitch': 0.0}
            if jtype == 'P':
                direction_ok = True
                try:
                    direction['yaw'] = float(row[7].get())
                except ValueError:
                    _mark_invalid(row[7], f"J{joint_n}: Dir yaw no es un numero valido.")
                    direction_ok = False

                try:
                    direction['pitch'] = float(row[8].get())
                except ValueError:
                    _mark_invalid(row[8], f"J{joint_n}: Dir pitch no es un numero valido.")
                    direction_ok = False

                if direction_ok and abs(direction['pitch']) > 180.0:
                    _mark_invalid(row[8], f"J{joint_n}: Dir pitch debe quedar entre -180 y 180 grados.")

            prismatic_pre_rotations.append(direction)

            try:
                servo_pins.append(self._parse_pin_value(row[9].get(), allow_empty=True))
            except ValueError:
                _mark_invalid(row[9], f"J{joint_n}: pin no es valido.")
                servo_pins.append(None)

            lim_ok = True
            try:
                lim_min = float(row[5].get())
            except ValueError:
                _mark_invalid(row[5], f"J{joint_n}: límite mínimo no es un número válido.")
                lim_ok = False
                lim_min = -90.0

            try:
                lim_max = float(row[6].get())
            except ValueError:
                _mark_invalid(row[6], f"J{joint_n}: límite máximo no es un número válido.")
                lim_ok = False
                lim_max = 90.0

            if lim_ok and lim_min > lim_max:
                _mark_invalid(row[5], f"J{joint_n}: el límite mínimo no puede ser mayor que el máximo.")
                _mark_invalid(row[6], f"J{joint_n}: el límite mínimo no puede ser mayor que el máximo.")

            joint_limits.append((lim_min, lim_max))

        for key, entry in self._base_row_entries.items():
            try:
                base_row[key] = float(entry.get())
            except ValueError:
                _mark_invalid(entry, f"J0 fija: '{key}' no es un numero valido.")
                base_row[key] = 0.0

        # ---- Validación semántica por tipo de articulación ----
        for i, (jtype, _dh, (lim_min, lim_max)) in enumerate(
                zip(joint_types, dh_rows, joint_limits)):
            joint_n = i + 1
            row = self._rows[i]

            if jtype == 'P':
                # En DH la variable prismatica sigue yendo en `d`, pero `a` puede
                # representar un offset rigido lateral valido hacia el siguiente origen.
                continue

            else:  # R
                # Los limites de una R joint son angulos en grados.
                if abs(lim_min) > 360.0 or abs(lim_max) > 360.0:
                    _mark_invalid(row[5],
                        f"J{joint_n} (R): limites ({lim_min:.0f}deg..{lim_max:.0f}deg) "
                        f"superan +/-360deg - se introdujeron valores en mm por error?")

        seen_pins = {}
        for i, pin in enumerate(servo_pins):
            if pin is None:
                continue
            if pin in seen_pins:
                first_idx = seen_pins[pin]
                _mark_invalid(self._rows[i][9], f"J{i + 1}: el pin {pin} ya esta asignado a J{first_idx + 1}.")
                _mark_invalid(self._rows[first_idx][9], f"J{first_idx + 1}: pin duplicado.")
            else:
                seen_pins[pin] = i

        if errors:
            return None, "\n".join(errors)

        current = self.motor3d.get_model_config()
        current['dof'] = n
        current['dh_rows'] = dh_rows
        current['joint_types'] = joint_types
        current['joint_limits'] = joint_limits
        current['prismatic_pre_rotations'] = prismatic_pre_rotations
        current['servo_pins'] = servo_pins
        current['base'] = dict(base_row)
        current['visual'] = dict(current.get('visual', {}))
        current['visual']['mode'] = self._visual_var.get()
        current['visual']['show_fps_counter'] = self._fps_counter_enabled()

        return current, None

    def _save(self):
        config, error = self._collect_config()
        if error:
            tk.messagebox.showerror("Error de configuración", error, parent=self)
            return
        self.motor3d.set_model_config(config)
        self._sync_arm3d_servo_pin_mapping()
        # Actualizar active_preset_name para que la próxima apertura de config muestre el perfil correcto
        selected = self._preset_var.get()
        all_presets = self.motor3d.repository.list_builtin_presets()
        self.motor3d.active_preset_name = selected if selected in all_presets else None
        self.motor3d.model.preset_name = self.motor3d.active_preset_name
        self.motor3d.save_model_config()
        if self.application and hasattr(self.application, 'arm3d_control_panel'):
            self.application.arm3d_control_panel.refresh_from_model()
        self.destroy()

    def _import_json(self):
        from tkinter.filedialog import askopenfilename
        path = askopenfilename(filetypes=[("JSON config", "*.json")], parent=self)
        if path:
            ok = self.motor3d.load_model_config(path=path)
            if ok:
                self._sync_arm3d_servo_pin_mapping()
                self._dof_var.set(self.motor3d.model.dof)
                if hasattr(self, "_fps_counter_var"):
                    self._fps_counter_var.set(
                        self.motor3d.model.visual.get('show_fps_counter', True)
                    )
                self._build_dh_rows(self._table_frame)
                self._refresh_base_row_entries()
            else:
                tk.messagebox.showerror("Error", "No se pudo cargar el archivo JSON.", parent=self)

    def _export_json(self):
        from tkinter.filedialog import asksaveasfilename
        path = asksaveasfilename(defaultextension=".json",
                                 filetypes=[("JSON config", "*.json")], parent=self)
        if path:
            config, error = self._collect_config()
            if error:
                tk.messagebox.showerror("Error de configuración", error, parent=self)
                return
            self.motor3d.set_model_config(config)
            self._sync_arm3d_servo_pin_mapping()
            ok = self.motor3d.save_model_config(path=path)
            if not ok:
                tk.messagebox.showerror("Error", "No se pudo guardar el archivo.", parent=self)


class MenuBar(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        kwargs.setdefault("bg", "#f0f0f0")
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.application = application
        self._menu_buttons = []
        self._active_menu_button = None
        self._open_menu_button = None

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
        self._add_menu_button("Archivo", file_menu)

        edit_menu = tk.Menu(self, tearoff=0)
        edit_menu.add_command(
            label="Deshacer", command=application.editor_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(
            label="Rehacer", command=application.editor_redo, accelerator="Ctrl+Y")
        self._add_menu_button("Editar", edit_menu)

        conf_menu = tk.Menu(self, tearoff=0)
        conf_menu.add_command(label="Configurar pines", command=application.open_pin_configuration,
                              accelerator="Ctrl+P")
        self._config_menu = conf_menu
        self._config_pins_menu_index = 0
        self._add_menu_button("Configurar", conf_menu)

        exec_menu = tk.Menu(self, tearoff=0)
        exec_menu.add_command(
            label="Ejecutar", command=application.execute, accelerator="F5")
        exec_menu.add_command(
            label="Detener", command=application.stop, accelerator="Ctrl+F5")
        exec_menu.add_separator()
        exec_menu.add_command(
            label="Pausar / Reanudar", command=application.toggle_pause, accelerator="F8")
        exec_menu.add_command(
            label="Paso a paso", command=application.step_once, accelerator="F10")
        exec_menu.add_separator()
        exec_menu.add_command(
            label="Ampliar", command=lambda event: application.zoom_in(), accelerator="Ctrl++")
        exec_menu.add_command(
            label="Reducir", command=lambda event: application.zoom_out(), accelerator="Ctrl+-")
        self._add_menu_button("Ejecutar", exec_menu)

        help_menu = tk.Menu(self, tearoff=0)
        help_menu.add_command(label="Manual de ayuda",
                              command=self.__launch_help, accelerator="Ctrl+H")
        help_menu.add_command(
            label="Acerca de", command=self.show_about, accelerator="Ctrl+A")
        self._add_menu_button("Ayuda", help_menu)

        self.bind_all("<Control-p>", application.open_pin_configuration)
        self.bind_all("<Control-n>", self.create_file)
        self.bind_all("<Control-o>", application.open_file)
        self.bind_all("<Control-s>", application.save_file)
        self.bind_all("<Control-h>", self.__launch_help)
        self.bind_all("<Control-a>", self.show_about)
        self.bind_all("<F5>", application.execute)
        self.bind_all("<Control-F5>", application.stop)
        self.bind_all("<F8>", lambda e: application.toggle_pause())
        self.bind_all("<F10>", lambda e: application.step_once())
        self.bind_all("<Control-plus>", lambda event: application.zoom_in())
        self.bind_all("<Control-minus>", lambda event: application.zoom_out())
        self.bind("<Leave>", self._clear_menu_hover)

    def update_config_menu_label(self, robot_option=None):
        if robot_option is None:
            try:
                robot_option = self.application.selector_bar.robot_selector.current()
            except Exception:
                robot_option = None
        label = "Configurar brazo" if robot_option == 5 else "Configurar pines"
        try:
            self._config_menu.entryconfigure(self._config_pins_menu_index, label=label)
        except Exception:
            pass

    def _add_menu_button(self, label, menu):
        def activate(_event=None):
            self._highlight_menu_button(button)

        def deactivate(_event=None):
            if self._open_menu_button is not button:
                self._reset_menu_button(button)
                if self._active_menu_button is button:
                    self._active_menu_button = None

        def open_menu(_event=None):
            self._open_menu_button = button
            self._highlight_menu_button(button)
            x = button.winfo_rootx()
            y = button.winfo_rooty() + button.winfo_height()
            menu.tk_popup(x, y)
            self.after(50, lambda: self._watch_menu_closed(button, menu))

        def mark_closed(_event=None):
            if self._open_menu_button is button:
                self._open_menu_button = None
            self._reset_menu_button(button)
            if self._active_menu_button is button:
                self._active_menu_button = None

        def leave_menu(_event=None):
            if not self._is_pointer_over(button):
                self._open_menu_button = None
                self._reset_menu_button(button)
                if self._active_menu_button is button:
                    self._active_menu_button = None

        button = tk.Label(
            self,
            text=label,
            bg="#f0f0f0",
            fg="#000000",
            bd=0,
            padx=5,
            pady=1,
            highlightthickness=0,
        )
        button.bind("<Enter>", activate)
        button.bind("<Leave>", deactivate)
        button.bind("<ButtonPress-1>", open_menu)
        menu.bind("<Unmap>", mark_closed, add="+")
        menu.bind("<Leave>", leave_menu, add="+")
        button.pack(side=tk.LEFT)
        self._menu_buttons.append(button)

    def _highlight_menu_button(self, active_button):
        for button in self._menu_buttons:
            if button is active_button:
                button.configure(bg="#D9EAF7", fg="black")
            elif button is not self._open_menu_button:
                self._reset_menu_button(button)
        self._active_menu_button = active_button

    def _reset_menu_button(self, button):
        button.configure(bg="#f0f0f0", fg="#000000")

    def _clear_menu_hover(self, _event=None):
        if self._open_menu_button is not None:
            return
        for button in self._menu_buttons:
            self._reset_menu_button(button)
        self._active_menu_button = None

    def _watch_menu_closed(self, button, menu):
        if self._open_menu_button is not button:
            return
        if menu.winfo_ismapped():
            self.after(50, lambda: self._watch_menu_closed(button, menu))
            return
        self._open_menu_button = None
        self._reset_menu_button(button)
        if self._active_menu_button is button:
            self._active_menu_button = None

    def _is_pointer_over(self, target):
        widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        return widget is target

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
                                + 'Autor extensión 3D (Braccio): Nicolás Guerbartchouk Pérez\n'
                                + 'Tutor: Cristian González García\n'
                                + 'Versión actual: b-0.6'
                            ))


class Arm3DControlPanel(tk.Frame):
    """Panel de control manual del brazo robótico 3D — layout vertical para pestaña derecha.
    Muestra sliders J1-J6 (cinemática directa) y campos IK (X/Y/Z).
    Visible únicamente cuando el robot Braccio (opción 5) está seleccionado.
    """

    _MAX_DOF = 6

    def __init__(self, parent, application: 'MainApplication' = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.application = application
        self._syncing_sliders = False
        self._sliders_locked = False
        self._slider_sync_cache = []

        # Fuentes escalables: se reflujan en _on_configure según el ancho del
        # panel para que nada se recorte cuando el usuario estrecha la pestaña.
        self._fonts = FontScaler()
        self._f_section = self._fonts.font(10, "bold")
        self._f_label = self._fonts.font(9)
        self._f_value = self._fonts.font(9)
        self._f_ik = self._fonts.font(10)
        self._f_entry = self._fonts.font(10)
        self._f_button = self._fonts.font(10)
        self._f_status = self._fonts.font(9)
        self._last_font_scale = None

        # Cuerpo con scroll vertical automático para la pestaña Control Manual.
        self._scroll = VScrollFrame(self, bg=DARK_BLUE)
        self._scroll.pack(fill=tk.BOTH, expand=True)
        body = self._scroll.body

        # --- Cinemática Directa: sliders verticales ---
        tk.Label(body, text="Cinemática Directa",
                 bg=DARK_BLUE, fg="#00E5CC",
                 font=self._f_section).pack(anchor="w", padx=8, pady=(8, 2))

        sliders_container = tk.Frame(body, bg=DARK_BLUE)
        # Gutter derecho para que la columna de valores nunca quede pegada al
        # borde del panel/notebook (evita el recorte del último dígito).
        sliders_container.pack(fill=tk.X, padx=(6, 12))
        sliders_container.columnconfigure(1, weight=1)
        self._sliders_container = sliders_container

        self._sliders = []
        self._val_labels = []
        self._jlabels = []
        for i in range(self._MAX_DOF):
            jlbl = tk.Label(sliders_container, text=f"J{i + 1}",
                            bg=DARK_BLUE, fg="white", font=self._f_label,
                            width=4, anchor="e")
            jlbl.grid(row=i, column=0, padx=(4, 2), pady=1, sticky="e")

            slider = tk.Scale(
                sliders_container,
                from_=0, to=180,
                orient=tk.HORIZONTAL,
                bg=DARK_BLUE, fg="white",
                sliderrelief=tk.FLAT, highlightthickness=0,
                width=12, showvalue=False, resolution=0.1,
                command=lambda val, idx=i: self._on_slider(idx, val)
            )
            slider.set(90)
            slider.grid(row=i, column=1, padx=2, pady=1, sticky="ew")

            val_lbl = tk.Label(sliders_container, text=f"90{chr(176)}",
                               bg=DARK_BLUE, fg="white",
                               font=self._f_value, width=5, anchor="e")
            val_lbl.grid(row=i, column=2, padx=(2, 4), pady=1, sticky="e")

            self._sliders.append(slider)
            self._val_labels.append(val_lbl)
            self._jlabels.append(jlbl)
            self._slider_sync_cache.append({
                "visible": True,
                "range_state": None,
                "value": 90.0,
                "label": f"90{chr(176)}",
            })

        # --- Separador ---
        tk.Frame(body, bg=BLUE, height=1).pack(fill=tk.X, padx=6, pady=6)

        # --- Cinemática Inversa ---
        tk.Label(body, text="Cinemática Inversa",
                 bg=DARK_BLUE, fg="#00E5CC",
                 font=self._f_section).pack(anchor="w", padx=8, pady=(0, 4))

        ik_coords = tk.Frame(body, bg=DARK_BLUE)
        ik_coords.pack(fill=tk.X, padx=8)

        # Columnas de entrada con peso para que los campos X/Y/Z se expandan y
        # nunca queden recortados al estrechar el panel.
        for col_i, axis in enumerate(["X", "Y", "Z"]):
            tk.Label(ik_coords, text=f"{axis}:", bg=DARK_BLUE, fg="white",
                     font=self._f_ik).grid(row=0, column=col_i * 2, padx=(4, 1), sticky="e")
            ik_coords.grid_columnconfigure(col_i * 2 + 1, weight=1, uniform="ik")
        self._entry_x = tk.Entry(ik_coords, width=4, font=self._f_entry)
        self._entry_y = tk.Entry(ik_coords, width=4, font=self._f_entry)
        self._entry_z = tk.Entry(ik_coords, width=4, font=self._f_entry)
        self._entry_x.insert(0, "0")
        self._entry_y.insert(0, "0")
        self._entry_z.insert(0, "400")
        self._entry_x.grid(row=0, column=1, padx=(0, 4), sticky="ew")
        self._entry_y.grid(row=0, column=3, padx=(0, 4), sticky="ew")
        self._entry_z.grid(row=0, column=5, padx=(0, 4), sticky="ew")

        btn_frame = tk.Frame(body, bg=DARK_BLUE)
        btn_frame.pack(fill=tk.X, padx=8, pady=4)

        self._btn_ik = tk.Button(btn_frame, text="Confirmar Posición",
                                 bg=BLUE, bd=0, fg=DARK_BLUE,
                                 font=self._f_button, command=self._on_ik)
        self._btn_ik.pack(fill=tk.X, pady=(0, 3))

        self._btn_reset_cam = tk.Button(btn_frame, text="Reset Cámara",
                                        bg=BLUE, bd=0, fg=DARK_BLUE,
                                        font=self._f_button, command=self._on_reset_cam)
        self._btn_reset_cam.pack(fill=tk.X)

        self._lbl_ik_status = tk.Label(body, text="", bg=DARK_BLUE, fg="#aaffaa",
                                       font=self._f_status, wraplength=240, justify=tk.LEFT)
        self._lbl_ik_status.pack(anchor="w", padx=8, pady=2)

        # --- Separador ---
        tk.Frame(body, bg=BLUE, height=1).pack(fill=tk.X, padx=6, pady=4)

        # Reenlazar la rueda del ratón ahora que el contenido existe.
        self._scroll.bind_wheel(self._scroll.body)
        # Reflujo de fuentes según el ancho real del panel.
        self.bind("<Configure>", self._on_configure)

        # --- Toggles de visualización ---
    # ------------------------------------------------------------------ helpers

    def _on_configure(self, event):
        """Escala las fuentes del panel en función de su ancho disponible."""
        width = event.width
        if width <= 1:
            return
        # Ancho de diseño en el que las fuentes base encajan sin recortes.
        scale = max(0.6, min(1.15, width / 320.0))
        if self._last_font_scale is not None and abs(scale - self._last_font_scale) < 0.02:
            return
        self._last_font_scale = scale
        self._fonts.apply(scale)
        try:
            self._lbl_ik_status.configure(wraplength=max(80, width - 24))
        except Exception:
            pass

    def _get_model(self):
        layer = self._get_layer()
        if layer is not None:
            return layer.motor3d.model
        return None

    def _get_layer(self):
        try:
            import graphics.layers as _layers
            layer = self.application.controller.robot_layer
            if isinstance(layer, _layers.Arm3DLayer):
                return layer
        except Exception:
            pass
        return None

    def _get_motor3d(self):
        try:
            layer = self._get_layer()
            if layer is not None:
                return layer.motor3d
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------ handlers

    def _is_servo_mode(self):
        return True

    def _on_slider(self, joint_idx, val):
        if getattr(self, "_syncing_sliders", False) or getattr(self, "_sliders_locked", False):
            return
        try:
            float_val = float(val)
            model = self._get_model()
            jtype = model.joint_types[joint_idx] if (
                model and joint_idx < len(model.joint_types)) else 'R'
            servo = self._is_servo_mode()
            if jtype == 'P':
                dh_val = float_val
                self._val_labels[joint_idx].config(text=f"{int(round(float_val))}mm")
            elif servo:
                dh_val = float_val
            else:
                dh_val = float_val
            unit = "mm" if jtype == 'P' else chr(176)
            self._val_labels[joint_idx].config(text=f"{int(round(float_val))}{unit}")
            self.application.controller.update_arm3d_joint(joint_idx, dh_val)
        except Exception:
            pass

    def _on_ik(self):
        # Resetear borde de los entries
        for entry in (self._entry_x, self._entry_y, self._entry_z):
            entry.configure(highlightthickness=0)
        invalid = False
        parsed = []
        for entry in (self._entry_x, self._entry_y, self._entry_z):
            try:
                parsed.append(float(entry.get()))
            except ValueError:
                entry.configure(highlightthickness=2, highlightbackground="#FF4444",
                                highlightcolor="#FF4444")
                invalid = True
        if invalid:
            self._lbl_ik_status.config(text="Valores X/Y/Z inválidos", fg="#ff8888")
            return
        x, y, z = parsed
        converged, msg = self.application.controller.solve_arm3d_ik(x, y, z)
        if converged:
            self._lbl_ik_status.config(text=str(msg), fg="#aaffaa")
            self._sync_sliders_from_model()
        else:
            self._lbl_ik_status.config(text=str(msg), fg="#ffcc88")
            self._sync_sliders_from_model()

    def _on_reset_cam(self):
        self.application.controller.reset_arm3d_camera()

    def _on_mouse_drag_mode_change(self):
        if self.application is None or not hasattr(self, "_mouse_drag_mode_var"):
            return
        selected = self._mouse_drag_mode_var.get()
        mode = None if selected == "none" else selected
        self.application.set_arm3d_mouse_drag_mode(mode)

    def set_mouse_drag_mode(self, mode):
        if hasattr(self, "_mouse_drag_mode_var"):
            self._mouse_drag_mode_var.set("none" if mode in (None, "") else str(mode))

    def _sync_sliders_from_model(self):
        self.refresh_from_model()

    def update_joint_limits(self):
        self.refresh_from_model()

    def _ensure_slider_sync_cache(self):
        if not hasattr(self, "_slider_sync_cache"):
            self._slider_sync_cache = []
        while len(self._slider_sync_cache) < len(getattr(self, "_sliders", [])):
            self._slider_sync_cache.append({
                "visible": None,
                "range_state": None,
                "value": None,
                "label": None,
            })
        return self._slider_sync_cache

    def refresh_from_model(self):
        """Sincroniza todo el panel con el modelo actual: DOF, tipos, rangos y valores."""
        try:
            layer = self._get_layer()
            model = layer.motor3d.model if layer is not None else self._get_model()
            if model is None:
                return
            dof = model.dof
            servo = self._is_servo_mode()
            motion_locked = bool(
                layer is not None
                and getattr(layer, "is_motion_active", lambda: False)()
            )
            self._sliders_locked = motion_locked
            self._syncing_sliders = True
            cache = self._ensure_slider_sync_cache()
            for i, (slider, val_lbl, jlbl) in enumerate(
                    zip(self._sliders, self._val_labels, self._jlabels)):
                item_cache = cache[i]
                if i < dof:
                    if item_cache.get("visible") is not True:
                        jlbl.grid()
                        slider.grid()
                        val_lbl.grid()
                        item_cache["visible"] = True

                    jtype = model.joint_types[i] if i < len(model.joint_types) else 'R'
                    # Rango REAL alcanzable (para el Braccio la calibración puede
                    # exceder el joint_limits nominal); así el slider comanda el
                    # barrido completo del servo, no el recortado al nominal.
                    mn, mx = model.effective_joint_limits(i) if i < len(model.joint_limits) else (-90.0, 90.0)
                    raw_dh = model.joints[i] if i < len(model.joints) else 0.0

                    if jtype == 'P':
                        lim_min, lim_max = mn, mx
                        disp_val = raw_dh
                        unit = "mm"
                    elif servo:
                        if layer is not None and hasattr(layer, "_to_control_value"):
                            lim_a = layer._to_control_value(i, mn)
                            lim_b = layer._to_control_value(i, mx)
                            lim_min, lim_max = min(lim_a, lim_b), max(lim_a, lim_b)
                            disp_val = layer._to_control_value(i, raw_dh)
                        else:
                            lim_min, lim_max = mn + 90.0, mx + 90.0
                            disp_val = raw_dh + 90.0
                        unit = chr(176)
                    else:
                        lim_min, lim_max = mn, mx
                        disp_val = raw_dh
                        unit = chr(176)

                    state = "disabled" if motion_locked else "normal"
                    range_state = (round(lim_min, 4), round(lim_max, 4), state)
                    if item_cache.get("range_state") != range_state:
                        slider.configure(from_=lim_min, to=lim_max, state=state)
                        item_cache["range_state"] = range_state

                    prev_value = item_cache.get("value")
                    if prev_value is None or abs(float(prev_value) - float(disp_val)) >= 0.05:
                        if motion_locked:
                            slider.configure(state="normal")
                        slider.set(disp_val)
                        if motion_locked:
                            slider.configure(state="disabled")
                        item_cache["value"] = float(disp_val)

                    label_text = f"{int(round(disp_val))}{unit}"
                    if item_cache.get("label") != label_text:
                        val_lbl.config(text=label_text)
                        item_cache["label"] = label_text
                else:
                    if item_cache.get("visible") is not False:
                        jlbl.grid_remove()
                        slider.grid_remove()
                        val_lbl.grid_remove()
                        slider.configure(state="normal")
                        item_cache["visible"] = False
                        item_cache["range_state"] = None
            self._syncing_sliders = False
        except Exception:
            self._syncing_sliders = False
            pass


class Arm3DInfoPanel(tk.Frame):
    """Panel izquierdo de información en tiempo real del brazo robótico 3D.
    Muestra coordenadas XYZ del efector final, ángulos articulares J1-J6 con
    sus límites y estado de seguridad.
    Solo visible cuando el robot Braccio (opción 5) está activo.
    """

    _BASE_WIDTH = 210

    def __init__(self, parent, application=None, *args, **kwargs):
        kwargs.setdefault('bg', DARK_BLUE)
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.application = application

        # Cuerpo con scroll vertical automático: si el contenido no cabe en alto,
        # aparece la barra sola. El panel es redimensionable (sash del PanedWindow).
        self._scroll = VScrollFrame(self, bg=DARK_BLUE)
        self._scroll.pack(fill=tk.BOTH, expand=True)
        body = self._scroll.body

        # Fuentes escalables: se reescalan en _on_configure según el ancho real
        # del panel (al estrechar el sash encogen proporcionalmente).
        self._fonts = FontScaler()
        self._f_title = self._fonts.font(10, "bold")
        self._f_section = self._fonts.font(9, "bold")
        self._f_label = self._fonts.font(9)
        self._f_value = self._fonts.font(9)
        self._f_limit = self._fonts.font(8)
        self._f_status = self._fonts.font(9)
        self._f_toggle = self._fonts.font(9)
        self._last_scale = None

        # Título
        tk.Label(body, text="Brazo Robótico 3D",
                 bg=DARK_BLUE, fg="white",
                 font=self._f_title).pack(pady=(10, 4), padx=6, fill=tk.X)

        tk.Frame(body, bg=BLUE, height=1).pack(fill=tk.X, padx=4)

        # --- Efector final ---
        tk.Label(body, text="Efector Final",
                 bg=DARK_BLUE, fg="#00E5CC",
                 font=self._f_section).pack(anchor="w", padx=10, pady=(0, 2))

        ee_frame = tk.Frame(body, bg=DARK_BLUE)
        ee_frame.pack(fill=tk.X, padx=8)

        self._lbl_ee = {}
        for axis in ["X", "Y", "Z"]:
            row = tk.Frame(ee_frame, bg=DARK_BLUE)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"{axis}:", bg=DARK_BLUE, fg="white",
                     font=self._f_label, width=3, anchor="e").pack(side=tk.LEFT)
            val = tk.Label(row, text="--- mm", bg=DARK_BLUE, fg="#00E5CC",
                           font=self._f_value, anchor="w")
            val.pack(side=tk.LEFT, padx=4)
            self._lbl_ee[axis] = val

        tk.Frame(body, bg=BLUE, height=1).pack(fill=tk.X, padx=4, pady=6)

        # --- Articulaciones ---
        tk.Label(body, text="Articulaciones",
                 bg=DARK_BLUE, fg="white",
                 font=self._f_section).pack(anchor="w", padx=10, pady=(0, 2))

        joints_frame = tk.Frame(body, bg=DARK_BLUE)
        joints_frame.pack(fill=tk.X, padx=8)

        self._lbl_joints = []
        self._lbl_joint_limits = []
        for i in range(6):
            row = tk.Frame(joints_frame, bg=DARK_BLUE)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"J{i + 1}:", bg=DARK_BLUE, fg="white",
                     font=self._f_label, width=3, anchor="e").pack(side=tk.LEFT)
            val = tk.Label(row, text="---°", bg=DARK_BLUE, fg="white",
                           font=self._f_value, width=5, anchor="w")
            val.pack(side=tk.LEFT, padx=2)
            lim = tk.Label(row, text="[---,---]", bg=DARK_BLUE, fg="#AACCFF",
                           font=self._f_limit, anchor="w")
            lim.pack(side=tk.LEFT, padx=2)
            self._lbl_joints.append(val)
            self._lbl_joint_limits.append(lim)

        tk.Frame(body, bg=BLUE, height=1).pack(fill=tk.X, padx=4, pady=6)

        # --- Estado ---
        tk.Label(body, text="Estado",
                 bg=DARK_BLUE, fg="white",
                 font=self._f_section).pack(anchor="w", padx=10, pady=(0, 2))

        self._lbl_status = tk.Label(body, text="OK",
                                    bg=DARK_BLUE, fg="#aaffaa",
                                    font=self._f_status, wraplength=195,
                                    justify=tk.LEFT, anchor="w")
        self._lbl_status.pack(anchor="w", padx=10, pady=2)

        tk.Frame(body, bg=BLUE, height=1).pack(fill=tk.X, padx=4, pady=6)

        tk.Label(body, text="Visualización",
                 bg=DARK_BLUE, fg="white",
                 font=self._f_section).pack(anchor="w", padx=10, pady=(0, 2))

        toggles_frame = tk.Frame(body, bg=DARK_BLUE)
        toggles_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        self._trail_var = tk.BooleanVar(value=True)
        tk.Checkbutton(toggles_frame, text="Trayectoria",
                       variable=self._trail_var,
                       bg=DARK_BLUE, fg="white", selectcolor=DARK_BLUE,
                       font=self._f_toggle, activebackground=DARK_BLUE,
                       command=self._on_trail_toggle).pack(anchor="w")

        self._joint_ranges_var = tk.BooleanVar(value=False)
        tk.Checkbutton(toggles_frame, text="Rangos articulares",
                       variable=self._joint_ranges_var,
                       bg=DARK_BLUE, fg="white", selectcolor=DARK_BLUE,
                       font=self._f_toggle, activebackground=DARK_BLUE,
                       command=self._on_joint_ranges_toggle).pack(anchor="w")

        self._joint_axes_var = tk.BooleanVar(value=False)
        tk.Checkbutton(toggles_frame, text="Ejes XYZ",
                       variable=self._joint_axes_var,
                       bg=DARK_BLUE, fg="white", selectcolor=DARK_BLUE,
                       font=self._f_toggle, activebackground=DARK_BLUE,
                       command=self._on_joint_axes_toggle).pack(anchor="w")

        # Reenlazar la rueda del ratón ahora que el contenido existe.
        self._scroll.bind_wheel(self._scroll.body)
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event):
        """Reflujo: escala las fuentes según el ancho real del panel; el scroll
        vertical de VScrollFrame se encarga del desbordamiento en alto."""
        width = event.width
        if width <= 1:
            return
        scale = max(0.7, min(1.1, width / self._BASE_WIDTH))
        if self._last_scale is not None and abs(scale - self._last_scale) < 0.02:
            return
        self._last_scale = scale
        self._fonts.apply(scale)
        try:
            self._lbl_status.configure(wraplength=max(110, width - 18))
        except Exception:
            pass

    def apply_visual_toggles(self):
        self._on_trail_toggle()
        self._on_joint_ranges_toggle()
        self._on_joint_axes_toggle()

    def _on_trail_toggle(self):
        try:
            self.application.controller.toggle_arm3d_trail(self._trail_var.get())
        except Exception:
            pass

    def _on_joint_ranges_toggle(self):
        try:
            self.application.controller.toggle_arm3d_joint_ranges(self._joint_ranges_var.get())
        except Exception:
            pass

    def _on_joint_axes_toggle(self):
        try:
            self.application.controller.toggle_arm3d_joint_axes(self._joint_axes_var.get())
        except Exception:
            pass

    def update(self, dof, joints, end_effector, in_workspace, singular,
               safety_blocked, warning_message, joint_limits=None, joint_types=None):
        """Actualiza los valores mostrados. Llamado desde Arm3DHUD.update()."""
        # Efector actual
        if end_effector and len(end_effector) >= 3:
            for axis, val in zip(["X", "Y", "Z"], end_effector):
                self._lbl_ee[axis].config(text=f"{val:.0f} mm")
        else:
            for axis in ["X", "Y", "Z"]:
                self._lbl_ee[axis].config(text="--- mm")

        # Articulaciones con límites y unidades según tipo
        for i, (val_lbl, lim_lbl) in enumerate(zip(self._lbl_joints, self._lbl_joint_limits)):
            unit = "mm" if (joint_types and i < len(joint_types) and joint_types[i] == 'P') else "°"
            if joints and i < len(joints):
                val_lbl.config(text=f"{joints[i]:.0f}{unit}")
            else:
                val_lbl.config(text="---°")
            if joint_limits and i < len(joint_limits):
                mn, mx = joint_limits[i]
                lim_lbl.config(text=f"[{mn:.0f}{unit},{mx:.0f}{unit}]")
            else:
                lim_lbl.config(text="[---,---]")

        # Estado
        if safety_blocked:
            self._lbl_status.config(
                text=f"⚠ {warning_message or 'BLOQUEADO'}", fg="#FF6666")
        elif singular:
            self._lbl_status.config(text="⚠ Singularidad", fg="#FFAA00")
        elif not in_workspace:
            self._lbl_status.config(text="⚠ Fuera de rango", fg="#FFAA00")
        else:
            self._lbl_status.config(text="OK", fg="#aaffaa")


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

        # Presets de cámara 3D visibles solo para Braccio.
        self.cam_buttons_frame = tk.Frame(self.canvas_frame, bg=DARK_BLUE,
                                          highlightthickness=1, highlightbackground=BLUE)
        # Dos sub-filas (vistas / modos) que se apilan cuando el viewport es
        # estrecho para que la barra de cámara no se salga del lienzo.
        self._cam_views_row = tk.Frame(self.cam_buttons_frame, bg=DARK_BLUE)
        self._cam_modes_row = tk.Frame(self.cam_buttons_frame, bg=DARK_BLUE)
        self._cam_rows_stacked = None
        self._camera_view_buttons = {}
        self._camera_drag_buttons = {}
        self._selected_camera_view = None
        self._selected_camera_drag_mode = None
        # Fuente escalable e iconos en tiers: la barra encoge proporcionalmente.
        self._cam_font_scaler = FontScaler()
        self._cam_font = self._cam_font_scaler.font(8, "bold")
        self._cam_buttons = []          # (button, icon_key)
        self._cam_icon_size = 26
        for _text, _view, _icon_key in [
            ("Libre", None, "free"),
            ("Caballera", "caballera", "caballera"),
            ("Isométrica", "isometrica", "isometrica"),
        ]:
            button = tk.Button(
                self._cam_views_row,
                text=_text,
                image=self._cam_icons[_icon_key][26],
                compound=tk.TOP,
                justify=tk.CENTER,
                bg=DARK_BLUE,
                fg="white",
                font=self._cam_font,
                bd=0,
                padx=8,
                pady=4,
                activebackground=BLUE,
                activeforeground="white",
                highlightthickness=0,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda v=_view: self._on_cam_preset(v)
            )
            button.pack(side=tk.LEFT, padx=2, pady=2)
            self._camera_view_buttons[_view] = button
            self._cam_buttons.append((button, _icon_key))

        for _text, _mode, _icon_key in [
            ("Rotar", "rotate", "rotate"),
            ("Desplazar", "pan", "pan"),
            ("Zoom", "zoom", "zoom"),
        ]:
            button = tk.Button(
                self._cam_modes_row,
                text=_text,
                image=self._cam_icons[_icon_key][26],
                compound=tk.TOP,
                justify=tk.CENTER,
                bg=DARK_BLUE,
                fg="white",
                font=self._cam_font,
                bd=0,
                padx=8,
                pady=4,
                activebackground=BLUE,
                activeforeground="white",
                highlightthickness=0,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda m=_mode: self._on_cam_drag_mode(m)
            )
            button.pack(side=tk.LEFT, padx=2, pady=2)
            self._camera_drag_buttons[_mode] = button
            self._cam_buttons.append((button, _icon_key))
        self._layout_camera_rows(stacked=False)
        self._refresh_camera_button_selection()
        # Reflujo + escalado de la barra de cámara según el ancho del viewport.
        self.canvas_frame.bind("<Configure>", self._on_canvas_frame_configure)

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
            self.zoom_frame, bg=BLUE, fg="white", font=("Consolas", 12), width=5)
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
        self.canvas.bind("<ButtonPress-3>", self.press_right)
        self.canvas.bind("<ButtonRelease-3>", self.release_right)
        self.canvas.bind("<B3-Motion>", self.pan)
        self.canvas.bind("<MouseWheel>", self.zoom)
        application.bind("<Alt-m>", self.__toggle_check_manually)
        self.zoom_in_button.configure(command=self.application.zoom_in)
        self.zoom_out_button.configure(command=self.application.zoom_out)
        self.key_movement.select()

        self.zoom_in_button.grid(row=0, column=0, padx=5, pady=5)
        self.zoom_label.grid(row=0, column=1, padx=5, pady=5)
        self.zoom_out_button.grid(row=0, column=2, padx=5, pady=5)

        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.arm3d_mouse_mode_hint = tk.Label(
            self.canvas_frame,
            text="",
            bg=DARK_BLUE,
            fg="#D9F0F1",
            font=("Consolas", 8, "bold"),
            padx=8,
            pady=4,
        )

        self.key_movement.pack(anchor="w", side=tk.LEFT)
        self.key_drawing.pack(anchor="w", side=tk.LEFT)
        self.zoom_frame.pack(anchor="e", side=tk.RIGHT)

        # Layout de DrawingFrame con grid (permite show/hide de hud_canvas sin cambiar el orden)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.hud_canvas.grid(row=0, column=0, sticky="ew")
        self.canvas_frame.grid(row=1, column=0, sticky="nsew")
        self.bottom_frame.grid(row=2, column=0, sticky="ew")

        self.init_x = 0
        self.init_y = 0
        self._arm3d_mouse_mode = None
        self._arm3d_left_down = False
        self._arm3d_right_down = False

    def __toggle_check_manually(self, event=None):
        self.key_movement.toggle()
        self.application.toggle_keys()

    def set_arm3d_mouse_mode(self, mode):
        valid_modes = {None, "rotate", "pan", "zoom"}
        self._arm3d_mouse_mode = mode if mode in valid_modes else None
        self._selected_camera_drag_mode = self._arm3d_mouse_mode
        self._refresh_camera_button_selection()
        self._update_arm3d_mouse_mode_hint()

    def handle_global_key_press(self, event):
        if self._arm3d_mouse_mode is None:
            return
        if event.keysym in {"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"}:
            return
        self.application.set_arm3d_mouse_drag_mode(None)

    def _update_arm3d_mouse_mode_hint(self):
        labels = {
            "rotate": "Rotar",
            "pan": "Desplazar",
            "zoom": "Zoom",
        }
        label = labels.get(self._arm3d_mouse_mode)
        if not label:
            self.arm3d_mouse_mode_hint.place_forget()
            return
        # Texto y fuente según el ancho disponible; anclado arriba-izquierda para
        # no solaparse con la barra de cámara (abajo-derecha).
        try:
            width = self.canvas_frame.winfo_width()
        except Exception:
            width = 0
        if width and width < 360:
            text = f"Ratón: {label}"
            font = ("Consolas", 7, "bold")
        elif width and width < 520:
            text = f"Modo ratón: {label}"
            font = ("Consolas", 8, "bold")
        else:
            text = f"Modo ratón: {label} | pulsa una tecla para salir"
            font = ("Consolas", 8, "bold")
        self.arm3d_mouse_mode_hint.configure(text=text, font=font)
        self.arm3d_mouse_mode_hint.place(relx=0.0, rely=0.0, anchor="nw", x=8, y=8)

    def _handle_arm3d_mouse_drag(self, event):
        dx = event.x - self.init_x
        dy = event.y - self.init_y
        self.init_x = event.x
        self.init_y = event.y

        if self._arm3d_left_down and self._arm3d_right_down:
            self.application.controller.dolly_arm3d_camera(dy)
            return

        if self._arm3d_mouse_mode == "pan" and self._arm3d_left_down:
            self.application.controller.drag_arm3d_camera(dx, dy, pan=True)
            return

        if self._arm3d_mouse_mode == "zoom" and self._arm3d_left_down:
            self.application.controller.dolly_arm3d_camera(dy)
            return

        if self._arm3d_mouse_mode == "rotate" and self._arm3d_left_down:
            self.application.controller.drag_arm3d_camera(dx, dy)
            return

        if self._arm3d_right_down:
            self.application.controller.drag_arm3d_camera(dx, dy, pan=True)
            return

        self.application.controller.drag_arm3d_camera(dx, dy)

    def press(self, event):
        import graphics.layers as _layers
        layer = self.application.controller.robot_layer
        if isinstance(layer, _layers.Arm3DLayer):
            # El brazo 3D maneja el arrastre en move()
            self.canvas.focus_force()
            self.init_x = event.x
            self.init_y = event.y
            self._arm3d_left_down = True
            return
        if isinstance(layer.robot, robots.ArduinoBoard):
            layer.draw_component(event.x, event.y)
        self.canvas.focus_force()
        self.init_x = event.x
        self.init_y = event.y
        self.canvas.scan_mark(event.x, event.y)

    def release(self, event):
        import graphics.layers as _layers
        layer = self.application.controller.robot_layer
        if isinstance(layer, _layers.Arm3DLayer):
            self._arm3d_left_down = False
            return
        layer.drawing.dx += self.init_x - event.x
        layer.drawing.dy += self.init_y - event.y
        if layer.drawing.dx < 0:
            layer.drawing.dx = 0
        if layer.drawing.dx > 545:
            layer.drawing.dx = 545
        if layer.drawing.dy < 0:
            layer.drawing.dy = 0
        if layer.drawing.dy > 580:
            layer.drawing.dy = 580

    def move(self, event):
        import graphics.layers as _layers
        layer = self.application.controller.robot_layer
        if isinstance(layer, _layers.Arm3DLayer):
            self._handle_arm3d_mouse_drag(event)
            return
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def press_right(self, event):
        import graphics.layers as _layers
        if isinstance(self.application.controller.robot_layer, _layers.Arm3DLayer):
            self.canvas.focus_force()
            self.init_x = event.x
            self.init_y = event.y
            self._arm3d_right_down = True

    def release_right(self, event):
        import graphics.layers as _layers
        if isinstance(self.application.controller.robot_layer, _layers.Arm3DLayer):
            self._arm3d_right_down = False

    def pan(self, event):
        import graphics.layers as _layers
        if isinstance(self.application.controller.robot_layer, _layers.Arm3DLayer):
            self._handle_arm3d_mouse_drag(event)

    def zoom(self, event):
        if event.delta == -120:
            self.application.controller.zoom_out()
        elif event.delta == 120:
            self.application.controller.zoom_in()

    def change_zoom_label(self, zoom_level):
        try:
            zoom_text = f"{int(round(float(zoom_level)))}%"
        except (TypeError, ValueError):
            zoom_text = "0%"
        self.zoom_label.configure(text=zoom_text)

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

    def show_hud(self):
        """Muestra el HUD strip superior (canvas de estado 2D)."""
        self.hud_canvas.grid()

    def hide_hud(self):
        """Oculta el HUD strip superior (usado cuando el panel de info lateral está activo)."""
        self.hud_canvas.grid_remove()

    def show_arm3d_camera_buttons(self):
        """Muestra los botones de navegación de cámara 3D en el canvas."""
        self.cam_buttons_frame.place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)

    def hide_arm3d_camera_buttons(self):
        """Oculta los botones de navegación de cámara 3D."""
        self.cam_buttons_frame.place_forget()

    def _layout_camera_rows(self, stacked):
        """Coloca las dos sub-filas de la barra de cámara en una sola fila
        (lado a lado) o apiladas (vistas arriba, modos abajo)."""
        if stacked == self._cam_rows_stacked:
            return
        self._cam_rows_stacked = stacked
        self._cam_views_row.grid_forget()
        self._cam_modes_row.grid_forget()
        if stacked:
            self._cam_views_row.grid(row=0, column=0, sticky="e")
            self._cam_modes_row.grid(row=1, column=0, sticky="e")
        else:
            self._cam_views_row.grid(row=0, column=0)
            self._cam_modes_row.grid(row=0, column=1)

    def _apply_camera_scale(self, width):
        """Escala iconos, fuente y padding de los botones de cámara por tiers
        según el ancho del viewport (encoge de forma proporcional)."""
        if width >= 620:
            icon, fscale, pad = 26, 1.0, (8, 4)
        elif width >= 470:
            icon, fscale, pad = 22, 0.92, (6, 3)
        elif width >= 360:
            icon, fscale, pad = 18, 0.82, (4, 3)
        else:
            icon, fscale, pad = 14, 0.72, (3, 2)
        if icon == getattr(self, "_cam_icon_size", None):
            return
        self._cam_icon_size = icon
        for button, key in getattr(self, "_cam_buttons", []):
            try:
                button.configure(image=self._cam_icons[key][icon],
                                 padx=pad[0], pady=pad[1])
            except Exception:
                pass
        self._cam_font_scaler.apply(fscale, minimum=6)

    def _on_canvas_frame_configure(self, event):
        """Escala la barra de cámara y la apila en dos filas cuando el viewport
        es demasiado estrecho para mostrar los 6 botones en una sola fila."""
        self._apply_camera_scale(event.width)
        try:
            self.update_idletasks()
            one_row = (self._cam_views_row.winfo_reqwidth()
                       + self._cam_modes_row.winfo_reqwidth() + 12)
        except Exception:
            return
        if not self._cam_rows_stacked and event.width < one_row + 16:
            self._layout_camera_rows(stacked=True)
        elif self._cam_rows_stacked and event.width > one_row + 44:
            self._layout_camera_rows(stacked=False)
        self._update_arm3d_mouse_mode_hint()

    def _on_cam_preset(self, view_name):
        """Callback de los botones de preset de cámara."""
        self._selected_camera_view = view_name
        self._selected_camera_drag_mode = None
        self.set_arm3d_mouse_mode(None)
        self.application.set_arm3d_mouse_drag_mode(None)
        self.application.controller.set_arm3d_camera_view(view_name)

    def _on_cam_drag_mode(self, mode):
        """Callback de los botones de modo de arrastre de cámara."""
        self._selected_camera_view = None
        self._selected_camera_drag_mode = mode
        self.set_arm3d_mouse_mode(mode)
        if hasattr(self.application.controller, "unlock_arm3d_camera_view"):
            self.application.controller.unlock_arm3d_camera_view()
        else:
            self.application.controller.set_arm3d_camera_view(None)
        self.application.set_arm3d_mouse_drag_mode(mode)

    def _refresh_camera_button_selection(self):
        selected_bg = BLUE
        normal_bg = DARK_BLUE
        for view_name, button in getattr(self, "_camera_view_buttons", {}).items():
            bg = selected_bg if view_name == self._selected_camera_view else normal_bg
            button.configure(bg=bg, activebackground=selected_bg)
        for mode_name, button in getattr(self, "_camera_drag_buttons", {}).items():
            bg = selected_bg if mode_name == self._selected_camera_drag_mode else normal_bg
            button.configure(bg=bg, activebackground=selected_bg)

    def _render_camera_drag_icon(self, mode_name):
        icon_size = 26
        image = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        color = "#D9F0F1"
        accent = "#00E5CC"

        def _round_point(point):
            return (int(round(point[0])), int(round(point[1])))

        def _draw_arrow(start, end, line_color=color):
            draw.line([_round_point(start), _round_point(end)], fill=line_color, width=2)
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.hypot(dx, dy)
            if length < 1e-6:
                return
            ux = dx / length
            uy = dy / length
            px = -uy
            py = ux
            head = 3.4
            spread = 2.0
            back = (end[0] - ux * head, end[1] - uy * head)
            left = (back[0] + px * spread, back[1] + py * spread)
            right = (back[0] - px * spread, back[1] - py * spread)
            draw.polygon(
                [_round_point(end), _round_point(left), _round_point(right)],
                fill=line_color
            )

        if mode_name == "rotate":
            draw.arc((5, 5, 21, 21), start=25, end=315, fill=color, width=2)
            _draw_arrow((18, 6), (21, 9), color)
            draw.ellipse((11, 11, 15, 15), fill=accent)
            return image

        if mode_name == "pan":
            _draw_arrow((13, 13), (13, 4), color)
            _draw_arrow((13, 13), (22, 13), color)
            _draw_arrow((13, 13), (13, 22), color)
            _draw_arrow((13, 13), (4, 13), color)
            draw.ellipse((11, 11, 15, 15), fill=accent)
            return image

        if mode_name == "zoom":
            draw.ellipse((5, 5, 17, 17), outline=color, width=2)
            draw.line([(15, 15), (22, 22)], fill=color, width=2)
            draw.line([(8, 11), (14, 11)], fill=accent, width=2)
            draw.line([(11, 8), (11, 14)], fill=accent, width=2)
            return image

        return image

    def _render_camera_preset_icon(self, preset_name):
        icon_size = 26
        image = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        def _add(point, vector):
            return (point[0] + vector[0], point[1] + vector[1])

        def _scale(vector, factor):
            return (vector[0] * factor, vector[1] * factor)

        def _round_point(point):
            return (int(round(point[0])), int(round(point[1])))

        def _draw_line(start, end, color, width):
            draw.line([_round_point(start), _round_point(end)], fill=color, width=width)

        def _draw_arrow(start, end, color):
            _draw_line(start, end, color, 2)
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.hypot(dx, dy)
            if length < 1e-6:
                return
            ux = dx / length
            uy = dy / length
            px = -uy
            py = ux
            head = 3.2
            spread = 2.0
            back = (end[0] - ux * head, end[1] - uy * head)
            left = (back[0] + px * spread, back[1] + py * spread)
            right = (back[0] - px * spread, back[1] - py * spread)
            draw.polygon(
                [_round_point(end), _round_point(left), _round_point(right)],
                fill=color
            )

        if preset_name == "free":
            orbit_color = "#D9F0F1"
            draw.ellipse((4, 6, 21, 19), outline=orbit_color, width=2)
            _draw_arrow((18, 8), (21, 10), orbit_color)
            _draw_arrow((7, 17), (4, 15), orbit_color)
            draw.ellipse((11, 11, 14, 14), fill=orbit_color)
            return image

        if preset_name == "caballera":
            origin = (6.0, 20.0)
            basis_x = (9.0, 0.0)
            basis_y = (7.0, -7.0)
            basis_z = (0.0, -10.0)
        else:
            origin = (13.0, 12.0)
            basis_x = (7.0, 4.0)
            basis_y = (-7.0, 4.0)
            basis_z = (0.0, -10.0)

        box_color = "#E3F1F2"
        origin_x = _add(origin, basis_x)
        origin_y = _add(origin, basis_y)
        origin_z = _add(origin, basis_z)
        origin_xy = _add(origin_x, basis_y)
        origin_xz = _add(origin_x, basis_z)
        origin_yz = _add(origin_y, basis_z)

        for start, end in (
            (origin, origin_x),
            (origin, origin_y),
            (origin, origin_z),
            (origin_x, origin_xy),
            (origin_x, origin_xz),
            (origin_y, origin_xy),
            (origin_y, origin_yz),
            (origin_z, origin_xz),
            (origin_z, origin_yz),
        ):
            _draw_line(start, end, box_color, 1)

        _draw_arrow(origin, _add(origin, _scale(basis_x, 1.35)), "#F26D6D")
        _draw_arrow(origin, _add(origin, _scale(basis_y, 1.35)), "#74D67A")
        _draw_arrow(origin, _add(origin, _scale(basis_z, 1.35)), "#6FA8FF")
        draw.ellipse(
            (
                int(round(origin[0] - 1.5)),
                int(round(origin[1] - 1.5)),
                int(round(origin[0] + 1.5)),
                int(round(origin[1] + 1.5)),
            ),
            fill=box_color,
        )
        return image

    def __load_images(self):
        self.zoom_img = tk.PhotoImage(file="buttons/zoom.png")
        self.zoom_whi_img = tk.PhotoImage(file="buttons/zoom_w.png")
        self.zoom_yel_img = tk.PhotoImage(file="buttons/zoom_y.png")
        self.dezoom_img = tk.PhotoImage(file="buttons/dezoom.png")
        self.dezoom_whi_img = tk.PhotoImage(file="buttons/dezoom_w.png")
        self.dezoom_yel_img = tk.PhotoImage(file="buttons/dezoom_y.png")
        # Iconos de cámara en varios tamaños para encoger la barra de forma
        # proporcional cuando el viewport es estrecho.
        sources = {
            "free": self._render_camera_preset_icon("free"),
            "caballera": self._render_camera_preset_icon("caballera"),
            "isometrica": self._render_camera_preset_icon("isometrica"),
            "rotate": self._render_camera_drag_icon("rotate"),
            "pan": self._render_camera_drag_icon("pan"),
            "zoom": self._render_camera_drag_icon("zoom"),
        }
        self._cam_icon_sizes = (26, 22, 18, 14)
        self._cam_icons = {}
        for key, img in sources.items():
            tier = {}
            for sz in self._cam_icon_sizes:
                im = img if sz == img.width else img.resize((sz, sz), Image.LANCZOS)
                tier[sz] = ImageTk.PhotoImage(im)
            self._cam_icons[key] = tier
        self.cam_free_icon = self._cam_icons["free"][26]
        self.cam_caballera_icon = self._cam_icons["caballera"][26]
        self.cam_isometrica_icon = self._cam_icons["isometrica"][26]
        self.cam_rotate_icon = self._cam_icons["rotate"][26]
        self.cam_pan_icon = self._cam_icons["pan"][26]
        self.cam_zoom_icon = self._cam_icons["zoom"][26]


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
            self, width=55, bg=BLUE, bd=0, highlightthickness=0)
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

    def attach_controller(self, app):
        """Conecta el editor con la aplicación para el manejo de breakpoints."""
        self.line_bar.attach_controller(app)

    def set_current_exec_line(self, line_no: int):
        """Resalta la línea que se está ejecutando (llamado desde debug_line)."""
        self.line_bar.set_current_line(line_no)
        self.text.tag_remove("current_exec", "1.0", tk.END)
        self.text.tag_add("current_exec", f"{line_no}.0", f"{line_no}.end+1c")
        self.text.see(f"{line_no}.0")

    def clear_exec_line(self):
        """Elimina el resaltado de la línea en ejecución."""
        self.line_bar.clear_current_line()
        self.text.tag_remove("current_exec", "1.0", tk.END)

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
            # Línea de ejecución actual (paso a paso / breakpoint)
            self.tag_configure("current_exec", background="#4A4A00", foreground="white")
            self.tag_raise("current_exec")

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
        # Layout constants (canvas width = 55px)
        _DOT_CX   = 8    # x-center of breakpoint dot
        _NUM_X    = 53   # right edge for line number text

        def __init__(self, *args, **kwargs):
            tk.Canvas.__init__(self, *args, **kwargs)
            self.editor   = None
            self._app     = None
            self._breakpoints   = set()   # set of int line numbers
            self._current_line  = None    # int line being executed, or None
            self.bind("<Button-1>", self._on_click)

        def attach(self, editor):
            self.editor = editor

        def attach_controller(self, app):
            self._app = app

        # ------ public API ------

        def toggle_breakpoint(self, line_no: int):
            if line_no in self._breakpoints:
                self._breakpoints.discard(line_no)
            else:
                self._breakpoints.add(line_no)
            if self._app is not None:
                self._app.controller.set_breakpoints(self._breakpoints)
            self.show_lines()

        def clear_breakpoints(self):
            self._breakpoints.clear()
            if self._app is not None:
                self._app.controller.set_breakpoints(set())
            self.show_lines()

        def set_current_line(self, line_no: int):
            self._current_line = line_no
            self.show_lines()

        def clear_current_line(self):
            self._current_line = None
            self.show_lines()

        # ------ event handler ------

        def _on_click(self, event):
            if self.editor is None:
                return
            idx = self.editor.index(f"@0,{event.y}")
            line_no = int(idx.split(".")[0])
            self.toggle_breakpoint(line_no)

        # ------ drawing ------

        def show_lines(self, *args):
            self.delete("all")
            if self.editor is None:
                return
            i = self.editor.index("@0,0")
            while True:
                dline = self.editor.dlineinfo(i)
                if dline is None:
                    break
                line = int(str(i).split(".")[0])
                y, h = dline[1], dline[3]

                # Background highlight for currently executing line
                if line == self._current_line:
                    self.create_rectangle(
                        0, y, self._NUM_X + 4, y + h,
                        fill="#4A4A00", outline=""
                    )

                # Breakpoint red dot
                if line in self._breakpoints:
                    r  = max(4, h // 2 - 2)
                    cy = y + h // 2
                    self.create_oval(
                        self._DOT_CX - r, cy - r,
                        self._DOT_CX + r, cy + r,
                        fill="#CC0000", outline="#FF5555"
                    )

                # Line number (right-aligned)
                self.create_text(
                    self._NUM_X, y, anchor="ne",
                    text=str(line), fill="white",
                    font=('consolas', 12, 'bold')
                )
                i = self.editor.index(f"{i}+1line")


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
        self.input_entry.bind("<Return>", lambda event: self.__send_input())

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
        self.input_entry.delete(0, tk.END)


class ButtonBar(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.application = application

        self.exec_frame = tk.Frame(self, bg=kwargs["bg"])
        self.hist_frame = tk.Frame(self, bg=kwargs["bg"])
        self.utils_frame = tk.Frame(self, bg=kwargs["bg"])
        self.tooltip_hover = tk.Label(
            self, bg=kwargs["bg"], font=("consolas", 12), fg="white",
            width=18, anchor="w")
        self.tooltip_hover_right = tk.Label(
            self, bg=kwargs["bg"], font=("consolas", 12), fg="white",
            width=14, anchor="e")

        self.__load_images()

        _bg = kwargs["bg"]

        def _imgbtn(parent, base, **kw):
            return ImageButton(
                parent,
                images={
                    "blue":   getattr(self, f"{base}_img"),
                    "white":  getattr(self, f"{base}_whi_img"),
                    "yellow": getattr(self, f"{base}_yel_img"),
                },
                bg=_bg, activebackground=DARK_BLUE, bd=0, **kw
            )

        # --- exec group (order matches mockup: Play Pause Stop StepBack StepFwd Reset) ---
        self.execute_button    = _imgbtn(self.exec_frame, "exec")
        self.pause_button      = _imgbtn(self.exec_frame, "pause")
        self.stop_button         = _imgbtn(self.exec_frame, "stop")
        self.step_forward_button = _imgbtn(self.exec_frame, "step_forward")
        self.reset_button      = _imgbtn(self.exec_frame, "reset")

        # --- hist group ---
        self.undo_button = _imgbtn(self.hist_frame, "undo", command=self.application.editor_undo)
        self.redo_button = _imgbtn(self.hist_frame, "redo", command=self.application.editor_redo)

        # --- utils group ---
        self.save_button   = _imgbtn(self.utils_frame, "save",   command=self.application.save_file)
        self.import_button = _imgbtn(self.utils_frame, "import", command=self.application.open_file)

        # tooltips
        self.execute_button.set_tooltip_text(self.tooltip_hover, "Ejecutar")
        self.pause_button.set_tooltip_text(self.tooltip_hover, "Pausar / Reanudar")
        self.stop_button.set_tooltip_text(self.tooltip_hover, "Detener")
        self.step_forward_button.set_tooltip_text(self.tooltip_hover, "Paso adelante")
        self.reset_button.set_tooltip_text(self.tooltip_hover, "Reiniciar")
        self.undo_button.set_tooltip_text(self.tooltip_hover_right, "Deshacer")
        self.redo_button.set_tooltip_text(self.tooltip_hover_right, "Rehacer")
        self.save_button.set_tooltip_text(self.tooltip_hover_right, "Guardar")
        self.import_button.set_tooltip_text(self.tooltip_hover_right, "Importar")

        self.execute_button.configure(command=self.execute)
        self.pause_button.configure(command=self.pause)
        self.stop_button.configure(command=self.stop)
        self.step_forward_button.configure(command=self.step_forward)
        self.reset_button.configure(command=self.reset)

        self.status_badge = tk.Label(
            self,
            text="■  DETENIDO",
            bg="#555555", fg="white",
            font=("Consolas", 10, "bold"),
            padx=8, pady=3, relief="flat",
        )

        # Columna 3 es el separador elástico: empuja hist/utils a la derecha
        self.columnconfigure(3, weight=1)

        # Izquierda: controles de ejecución
        self.exec_frame.grid(row=0, column=0, sticky="w")
        self.status_badge.grid(row=0, column=1, padx=(12, 4), sticky="w")
        self.tooltip_hover.grid(row=0, column=2, padx=(4, 0), sticky="w")
        # Derecha: tooltip + controles del sketch
        self.tooltip_hover_right.grid(row=0, column=4, padx=(0, 4), sticky="e")
        self.hist_frame.grid(row=0, column=5, sticky="e")
        self.utils_frame.grid(row=0, column=6, sticky="e", padx=(0, 4))

        # exec group columns 0-5
        self.execute_button.grid(row=0, column=0, padx=5, pady=5)
        self.pause_button.grid(row=0, column=1, padx=5, pady=5)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5)
        self.step_forward_button.grid(row=0, column=3, padx=5, pady=5)
        self.reset_button.grid(row=0, column=4, padx=5, pady=5)

        self.undo_button.grid(row=0, column=0, padx=5, pady=5)
        self.redo_button.grid(row=0, column=1, padx=5, pady=5)
        self.save_button.grid(row=0, column=0, padx=5, pady=5)
        self.import_button.grid(row=0, column=1, padx=5, pady=5)

    def execute(self):
        self.execute_button.on_click()
        self.application.execute()
        self.execute_button.on_click_finish()

    def stop(self):
        self.stop_button.on_click()
        self.application.stop()
        self.stop_button.on_click_finish()

    def pause(self):
        self.application.toggle_pause()

    def step_forward(self):
        self.application.step_once()


    def reset(self):
        self.reset_button.on_click()
        self.application.stop()
        # Defer execute() to the next event-loop tick so stop() finaliza primero
        self.application.after(0, self.application.execute)
        self.reset_button.on_click_finish()

    # ------------------------------------------------------------------
    # Estado visual del simulador
    # ------------------------------------------------------------------
    _STATE_CFG = {
        "idle":    ("■  DETENIDO",   "#555555", "white"),
        "running": ("▶  EJECUTANDO", "#007A3D", "white"),
        "paused":  ("⏸  PAUSADO",   "#B8860B", "white"),
    }

    def update_state(self, state: str):
        """Actualiza el badge de estado y el resaltado de botones."""
        text, bg, fg = self._STATE_CFG.get(state, self._STATE_CFG["idle"])
        self.status_badge.configure(text=text, bg=bg, fg=fg)
        self.execute_button.set_active(state == "running")
        self.pause_button.set_active(state == "paused")

    def __load_images(self):
        for name in ("exec", "import", "redo", "save", "stop", "undo",
                     "pause", "step_forward", "reset"):
            setattr(self, f"{name}_img",     tk.PhotoImage(file=f"buttons/{name}.png"))
            setattr(self, f"{name}_whi_img", tk.PhotoImage(file=f"buttons/{name}_w.png"))
            setattr(self, f"{name}_yel_img", tk.PhotoImage(file=f"buttons/{name}_y.png"))


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

    def set_active(self, active: bool):
        """Mantiene el botón resaltado en amarillo mientras active=True."""
        self._active = active
        if active:
            self.configure(image=self.images["yellow"])
        else:
            self.configure(image=self.images["blue"])

    def on_leave(self, event):
        event.widget['image'] = self.images["yellow"] if getattr(self, '_active', False) else self.images["blue"]
        try:
            self.label.configure(text="")
        except AttributeError:
            pass

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

        self.robot_selector['values'] = ["Robot móvil (2 infrarrojos)",
                                         "Robot móvil (3 infrarrojos)",
                                         "Robot móvil (4 infrarrojos)",
                                         "Actuador lineal",
                                         "Placa arduino",
                                         "Brazo Robótico (Braccio)"]
        self.robot_selector.current(0)
        self.track_selector['values'] = [
            "Circuito", "Laberinto", "Recta",
            "Obstáculo", "Recta y obstáculo",
            "Circuito con nodos"]
        self.track_selector.current(0)
        self.gamification_option_selector['values'] = [
            "Libre", "Desafío 1", "Desafío 2", "Desafío 3", "Desafío 4", "Desafío 5", "Desafío 6"]
        self.gamification_option_selector.current(0)

        self.robot_selector.bind(
            "<<ComboboxSelected>>", application.change_robot)
        self.track_selector.bind(
            "<<ComboboxSelected>>", application.change_track)
        self.gamification_option_selector.bind(
            "<<ComboboxSelected>>", application.change_gamification_option)
        application.bind("<Alt-r>", lambda event: self.robot_selector.focus())
        application.bind("<Alt-i>", lambda event: self.track_selector.focus())
        application.bind("<Alt-o>", lambda event: self.gamification_option_selector.focus())

        self.lb_robot.grid(row=0, column=0)
        self.robot_selector.grid(row=0, column=1, padx=(5, 15))
        self.lb_track.grid(row=0, column=2)
        self.track_selector.grid(row=0, column=3, padx=(5, 10))

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
