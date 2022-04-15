import tkinter as tk
import tkinter.ttk as ttk
from robots import DrawingTool


DARK_BLUE = "#006468"
BLUE = "#17a1a5"


class MainApplication(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("Simulador Software para Robots")
        self.geometry("1280x720")

        self.menu_bar = MenuBar(self)
        self.tools_frame = tk.Frame(self, bg=DARK_BLUE)
        self.button_bar = ButtonBar(self.tools_frame, self, bg=DARK_BLUE)
        self.robot_selector = ttk.Combobox(self.tools_frame, values=["Robot móvil", "Actuador lineal"], state="readonly")
        self.robot_selector.current(0)
        self.drawing_tool = DrawingTool(self.robot_selector.get())
        self.vertical_pane = tk.PanedWindow(
            orient=tk.VERTICAL, sashpad=5, sashrelief="solid", bg=DARK_BLUE)
        self.horizontal_pane = tk.PanedWindow(
            self.vertical_pane, orient=tk.HORIZONTAL, sashpad=5, sashrelief="solid", bg=BLUE)
        self.drawing_frame = DrawingFrame(
            self.horizontal_pane, self, bg=BLUE)
        self.editor_frame = EditorFrame(self.horizontal_pane, bg=BLUE)
        self.console_frame = ConsoleFrame(self.vertical_pane, bg=DARK_BLUE)

        self.drawing_tool.set_canvas(self.drawing_frame.canvas)
        self.drawing_tool.choose_robot(self.robot_selector.get())

        self.config(menu=self.menu_bar)
        self.button_bar.pack(fill=tk.X, side="left")
        self.robot_selector.pack(side="right", padx=15)
        self.movement = {
            "w": False,
            "a": False,
            "s": False,
            "d": False
        }
        self.identifier = None

        self.tools_frame.pack(fill=tk.X)
        self.vertical_pane.pack(fill="both", expand=True)

        self.horizontal_pane.add(
            self.drawing_frame, stretch="first", width=500, minsize=100)
        self.horizontal_pane.add(self.editor_frame, minsize=100)
        self.vertical_pane.add(self.horizontal_pane, stretch="first", minsize=100)
        self.vertical_pane.add(self.console_frame, stretch="never", height=200, minsize=100)

        self.robot_selector.bind("<<ComboboxSelected>>", self.change_robot)
        self.bind("<KeyPress>", self.key_press)
        self.bind("<KeyRelease>", self.key_release)

    def change_robot(self, event):
        self.stop_move()
        self.drawing_tool.choose_robot(self.robot_selector.get())

    def key_press(self, event):
        pressed_key = event.char
        if pressed_key in self.movement:
            self.movement[pressed_key] = True

    def key_release(self, event):
        pressed_key = event.char
        if pressed_key in self.movement:
            self.movement[pressed_key] = False

    def move(self):
        self.drawing_tool.move(self.movement)
        self.identifier = self.after(10, self.move)

    def stop_move(self):
        if self.identifier != None:
            self.after_cancel(self.identifier)


class MenuBar(tk.Menu):

    def __init__(self, parent, application: MainApplication=None, *args, **kwargs):
        tk.Menu.__init__(self, parent, *args, **kwargs)

        self.add_cascade(label="Archivo")
        self.add_cascade(label="Editar")
        self.add_cascade(label="Ver")
        self.add_cascade(label="Ayuda")


class DrawingFrame(tk.Frame):

    def __init__(self, parent, application: MainApplication=None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.application = application
        self.__load_images()

        self.canvas = tk.Canvas(self, bg="white", bd=1,
                                relief=tk.SOLID, highlightthickness=0)
        self.hud_canvas = tk.Canvas(self, height=100, bg=BLUE, highlightthickness=0)
        self.hud_canvas.create_text(50, 25, text="HUD", font=("Consolas", 25))
        self.zoom_frame = tk.Frame(self, bg=BLUE)
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
        self.zoom_label = tk.Label(self.zoom_frame, bg=BLUE, fg="white", font=("Consolas", 12))

        self.zoom_label.configure(text="{}%".format(self.application.drawing_tool.zoom_percent))

        self.canvas.bind("<ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<B1-Motion>", self.scroll_move)
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.zoom_in_button.configure(command=self.zoom_in)
        self.zoom_out_button.configure(command=self.zoom_out)

        self.zoom_in_button.grid(row=0, column=0, padx=5, pady=5)
        self.zoom_label.grid(row=0, column=1, padx=5, pady=5)
        self.zoom_out_button.grid(row=0, column=2, padx=5, pady=5)

        self.hud_canvas.pack(fill=tk.X, expand=False)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.zoom_frame.pack(anchor="e")

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def zoom(self, event):
        if event.delta == -120:
            self.zoom_out()
        elif event.delta == 120:
            self.zoom_in()

    def zoom_in(self):
        self.application.drawing_tool.zoom_in()
        self.__update_components_after_zoom()

    def zoom_out(self):
        self.application.drawing_tool.zoom_out()
        self.__update_components_after_zoom()

    def __update_components_after_zoom(self):
        self.__change_zoom_label()

    def __change_zoom_label(self):
        self.zoom_label.configure(text="{}%".format(self.application.drawing_tool.zoom_percent))

    def __load_images(self):
        self.zoom_img = tk.PhotoImage(file="simulator/gui/buttons/zoom.png")
        self.zoom_whi_img = tk.PhotoImage(file="simulator/gui/buttons/zoom_w.png")
        self.zoom_yel_img = tk.PhotoImage(file="simulator/gui/buttons/zoom_y.png")
        self.dezoom_img = tk.PhotoImage(file="simulator/gui/buttons/dezoom.png")
        self.dezoom_whi_img = tk.PhotoImage(file="simulator/gui/buttons/dezoom_w.png")
        self.dezoom_yel_img = tk.PhotoImage(file="simulator/gui/buttons/dezoom_y.png")


class EditorFrame(tk.Frame):

    def __init__(self, parent, application: MainApplication=None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.text = self.TextEditor(self, bd=1, relief=tk.SOLID, wrap="none", font=("consolas", 12))
        self.line_bar = self.LineNumberBar(self, width=30, bg=BLUE, bd=0, highlightthickness=0)
        self.sb_x = tk.Scrollbar(self, orient=tk.HORIZONTAL,
                                 command=self.text.xview)
        self.sb_y = tk.Scrollbar(self, orient=tk.VERTICAL,
                                 command=self.text.yview)

        self.text.insert(tk.END, "La zona del código\n")
        self.text.insert(tk.END, "La zona del código\n")
        self.text.insert(tk.END, "La zona del código")
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

    def _on_change(self, event):
        self.line_bar.show_lines()

    class TextEditor(tk.Text):

        def __init__(self, *args, **kwargs):
            tk.Text.__init__(self, *args, **kwargs)

            self._orig = self._w + "_orig"
            self.tk.call("rename", self._w, self._orig)
            self.tk.createcommand(self._w, self._proxy)

        def _proxy(self, *args):
            result = None
            command = (self._orig,) + args
            try:
                result = self.tk.call(command)
            except Exception:
                return result

            if (args[0] in ("insert", "replace", "delete") or
                    args[0:3] == ("mark", "set", "insert") or
                    args[0:2] == ("xview", "moveto") or
                    args[0:2] == ("xview", "scroll") or
                    args[0:2] == ("yview", "moveto") or
                    args[0:2] == ("yview", "scroll")
                ):
                self.event_generate("<<Change>>", when="tail")

            return result

    class LineNumberBar(tk.Canvas):

        def __init__(self, *args, **kwargs):
            tk.Canvas.__init__(self, *args, **kwargs)

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
                self.create_text(x, y, anchor="nw", text=line, fill="white", font=('consolas', 12, 'bold'))
                i = self.editor.index("%s+1line" % i)


class ConsoleFrame(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.console = tk.Text(self, bd=1, relief=tk.SOLID, font=("consolas", 12), bg="black", fg="white")
        self.filter_frame = tk.Frame(self, bg=DARK_BLUE, padx=10)
        self.check_out = tk.Checkbutton(self.filter_frame, text="Output", fg="white", font=("Consolas", 12), bg=DARK_BLUE, activebackground=DARK_BLUE)
        self.check_warning = tk.Checkbutton(self.filter_frame, text="Warning", fg="white", font=("Consolas", 12), bg=DARK_BLUE, activebackground=DARK_BLUE)
        self.check_error = tk.Checkbutton(self.filter_frame, text="Error", fg="white", font=("Consolas", 12), bg=DARK_BLUE, activebackground=DARK_BLUE)

        self.console.insert(tk.END, "Esto sería la consola")
        self.console.config(state=tk.DISABLED)

        self.check_out.grid(column=0, row=0)
        self.check_warning.grid(column=0, row=1)
        self.check_error.grid(column=0, row=2)
        self.filter_frame.pack(side=tk.RIGHT)
        self.console.pack(fill=tk.BOTH, expand=True)


class ButtonBar(tk.Frame):

    def __init__(self, parent, application: MainApplication = None, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.application = application

        self.exec_frame = tk.Frame(self, bg=kwargs["bg"])
        self.hist_frame = tk.Frame(self, bg=kwargs["bg"])
        self.utils_frame = tk.Frame(self, bg=kwargs["bg"])
        self.tooltip_hover = tk.Label(self, bg=kwargs["bg"], font=("consolas", 12), fg="white")

        self.__load_images()

        self.execute_button = ImageButton(
            self.exec_frame, 
            images = 
            {
                "blue": self.exec_img, 
                "white": self.exec_whi_img,
                "yellow": self.exec_yel_img
            }, 
            bg=kwargs["bg"], 
            bd=0
        )
        self.stop_button = ImageButton(
            self.exec_frame,
            images = 
            {
                "blue": self.stop_img, 
                "white": self.stop_whi_img,
                "yellow": self.stop_yel_img
            }, 
            bg=kwargs["bg"], 
            bd=0
        )
        self.undo_button = ImageButton(
            self.hist_frame,
            images = 
            {
                "blue": self.undo_img, 
                "white": self.undo_whi_img,
                "yellow": self.undo_yel_img
            }, 
            bg=kwargs["bg"], 
            bd=0
        )
        self.redo_button = ImageButton(
            self.hist_frame, 
            images = 
            {
                "blue": self.redo_img, 
                "white": self.redo_whi_img,
                "yellow": self.redo_yel_img
            }, 
            bg=kwargs["bg"], 
            bd=0
        )
        self.save_button = ImageButton(
            self.utils_frame,
            images = 
            {
                "blue": self.save_img, 
                "white": self.save_whi_img,
                "yellow": self.save_yel_img
            }, 
            bg=kwargs["bg"], 
            bd=0
        )
        self.import_button = ImageButton(
            self.utils_frame, 
            images = 
            {
                "blue": self.import_img, 
                "white": self.import_whi_img,
                "yellow": self.import_yel_img
            }, 
            bg=kwargs["bg"], 
            bd=0
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
        self.application.drawing_tool.execute()
        self.application.move()

    def stop(self):
        self.application.drawing_tool.stop_execute()
        self.application.stop_move()

    def __load_images(self):
        self.exec_img = tk.PhotoImage(file="simulator/gui/buttons/exec.png")
        self.exec_whi_img = tk.PhotoImage(file="simulator/gui/buttons/exec_w.png")
        self.exec_yel_img = tk.PhotoImage(file="simulator/gui/buttons/exec_y.png")
        self.import_img = tk.PhotoImage(file="simulator/gui/buttons/import.png")
        self.import_whi_img = tk.PhotoImage(file="simulator/gui/buttons/import_w.png")
        self.import_yel_img = tk.PhotoImage(file="simulator/gui/buttons/import_y.png")
        self.redo_img = tk.PhotoImage(file="simulator/gui/buttons/redo.png")
        self.redo_whi_img = tk.PhotoImage(file="simulator/gui/buttons/redo_w.png")
        self.redo_yel_img = tk.PhotoImage(file="simulator/gui/buttons/redo_y.png")
        self.save_img = tk.PhotoImage(file="simulator/gui/buttons/save.png")
        self.save_whi_img = tk.PhotoImage(file="simulator/gui/buttons/save_w.png")
        self.save_yel_img = tk.PhotoImage(file="simulator/gui/buttons/save_y.png")
        self.stop_img = tk.PhotoImage(file="simulator/gui/buttons/stop.png")
        self.stop_whi_img = tk.PhotoImage(file="simulator/gui/buttons/stop_w.png")
        self.stop_yel_img = tk.PhotoImage(file="simulator/gui/buttons/stop_y.png")
        self.undo_img = tk.PhotoImage(file="simulator/gui/buttons/undo.png")
        self.undo_whi_img = tk.PhotoImage(file="simulator/gui/buttons/undo_w.png")
        self.undo_yel_img = tk.PhotoImage(file="simulator/gui/buttons/undo_y.png")


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

    def on_click(self): # A futuro si se quiere
        self.configure(image=self.images["yellow"])

    def set_tooltip_text(self, label:tk.Label, tooltip):
        self.label = label
        self.tooltip = tooltip


def main():
    app = MainApplication()
    app.mainloop()


if __name__ == "__main__":
    main()
