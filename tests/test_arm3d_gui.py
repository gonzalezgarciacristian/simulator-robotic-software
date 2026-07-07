import os
import sys
import tkinter as tk
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image


class DummyLogger:
    def __init__(self, calls):
        self.calls = calls

    def write_log(self, *args):
        self.calls.append(("log",) + args)


class DummyMotor3D:
    def __init__(self):
        self.repository = SimpleNamespace(list_builtin_presets=lambda: {})
        self.active_preset_name = None
        self.saved_config = None
        self.saved_path = None
        self.model = SimpleNamespace(
            dof=2,
            joint_limits=[(-90.0, 90.0), (0.0, 120.0)],
            joint_types=["R", "P"],
            joints=[15.0, 30.0],
            prismatic_pre_rotations=[
                {"yaw": 0.0, "pitch": 0.0},
                {"yaw": 30.0, "pitch": 45.0},
            ],
            servo_pins=[11, 10],
            visual={"mode": "auto_generic"},
            preset_name=None,
        )

    def get_model_config(self):
        return {
            "dof": self.model.dof,
            "base": {"theta": 5.0, "d": 6.0, "a": 7.0, "alpha": 8.0},
            "dh_rows": [
                {"theta": 10.0, "d": 20.0, "a": 30.0, "alpha": 40.0},
                {"theta": 1.0, "d": 2.0, "a": 3.0, "alpha": 4.0},
            ][: self.model.dof],
            "joint_types": list(self.model.joint_types[: self.model.dof]),
            "joint_limits": list(self.model.joint_limits[: self.model.dof]),
            "prismatic_pre_rotations": list(
                self.model.prismatic_pre_rotations[: self.model.dof]
            ),
            "servo_pins": list(self.model.servo_pins[: self.model.dof]),
            "visual": dict(self.model.visual),
        }

    def set_model_config(self, config):
        self.saved_config = config
        self.model.dof = config["dof"]
        self.model.joint_limits = list(config["joint_limits"])
        self.model.joint_types = list(config["joint_types"])
        self.model.prismatic_pre_rotations = list(config["prismatic_pre_rotations"])
        self.model.servo_pins = list(config["servo_pins"])
        self.model.visual = dict(config["visual"])

    def save_model_config(self, path=None):
        self.saved_path = path
        return True


@pytest.fixture(scope="session")
def tk_root():
    tcl_root = Path(sys.base_prefix) / "tcl"
    os.environ["TCL_LIBRARY"] = str(tcl_root / "tcl8.6")
    os.environ["TK_LIBRARY"] = str(tcl_root / "tk8.6")
    root = getattr(tk, "_default_root", None)
    owns_root = root is None
    if owns_root:
        root = tk.Tk()
        root.withdraw()
    yield root
    if owns_root:
        root.destroy()


@pytest.fixture
def tk_app(tk_root):
    root = tk_root
    calls = []
    root.calls = calls
    root.editor_frame = SimpleNamespace(
        create_file=lambda: calls.append(("create_file",)),
        clear_exec_line=lambda: calls.append(("clear_exec_line",)),
    )
    root.selector_bar = SimpleNamespace(
        gamification_option_selector=SimpleNamespace(current=lambda: 2)
    )
    root.open_file = lambda *args, **kwargs: calls.append(("open_file",))
    root.save_file = lambda *args, **kwargs: calls.append(("save_file",))
    root.editor_undo = lambda *args, **kwargs: calls.append(("editor_undo",))
    root.editor_redo = lambda *args, **kwargs: calls.append(("editor_redo",))
    root.open_pin_configuration = lambda *args, **kwargs: calls.append(
        ("open_pin_configuration",)
    )
    root.execute = lambda *args, **kwargs: calls.append(("execute",))
    root.stop = lambda *args, **kwargs: calls.append(("stop",))
    root.toggle_pause = lambda *args, **kwargs: calls.append(("toggle_pause",))
    root.step_once = lambda *args, **kwargs: calls.append(("step_once",))
    root.zoom_in = lambda *args, **kwargs: calls.append(("zoom_in",))
    root.zoom_out = lambda *args, **kwargs: calls.append(("zoom_out",))
    root.close = lambda *args, **kwargs: calls.append(("close",))
    root.console_filter = lambda *args, **kwargs: calls.append(("console_filter",))
    root.change_robot = lambda *args, **kwargs: calls.append(("change_robot",))
    root.change_track = lambda *args, **kwargs: calls.append(("change_track",))
    root.change_gamification_option = lambda *args, **kwargs: calls.append(
        ("change_gamification_option",)
    )
    root.toggle_keys = lambda *args, **kwargs: calls.append(("toggle_keys",))
    root.set_drawing = lambda *args, **kwargs: calls.append(("set_drawing",))
    root.set_arm3d_mouse_drag_mode = lambda mode: calls.append(
        ("set_arm3d_mouse_drag_mode", mode)
    )
    root.controller = SimpleNamespace(
        update_arm3d_joint=lambda idx, angle: calls.append(("joint", idx, angle)),
        solve_arm3d_ik=lambda x, y, z: (True, f"Target {x},{y},{z}"),
        reset_arm3d_camera=lambda: calls.append(("reset_arm3d_camera",)),
        toggle_arm3d_trail=lambda show: calls.append(("trail", show)),
        toggle_arm3d_joint_ranges=lambda show: calls.append(("joint_ranges", show)),
        toggle_arm3d_joint_axes=lambda show: calls.append(("joint_axes", show)),
        set_arm3d_camera_view=lambda view_name: calls.append(
            ("camera_view", view_name)
        ),
        unlock_arm3d_camera_view=lambda: calls.append(("unlock_camera_view",)),
        show_tutorial=lambda: calls.append(("show_tutorial",)),
        show_results=lambda: calls.append(("show_results",)),
        show_help=lambda challenge: calls.append(("show_help", challenge)),
        delete_elements=lambda: calls.append(("delete_elements",)),
        send_input=lambda text: calls.append(("send_input", text)),
        update_joystick=lambda axis, value: calls.append(("joystick", axis, value)),
        drag_arm3d_camera=lambda dx, dy, pan=False: calls.append(
            ("drag_camera", dx, dy, pan)
        ),
        dolly_arm3d_camera=lambda dy: calls.append(("dolly_camera", dy)),
        zoom_in=lambda: calls.append(("controller_zoom_in",)),
        zoom_out=lambda: calls.append(("controller_zoom_out",)),
        set_breakpoints=lambda values: calls.append(
            ("breakpoints", tuple(sorted(values)))
        ),
        robot_layer=None,
        console=SimpleNamespace(logger=DummyLogger(calls)),
        get_pin_data=lambda: {},
        save_pin_data=lambda data: calls.append(("save_pin_data", dict(data))),
    )
    yield root
    root.update_idletasks()
    for child in list(root.winfo_children()):
        try:
            child.destroy()
        except Exception:
            pass


def _patch_gui_images(monkeypatch, root):
    import graphics.gui as gui_mod

    original_photo = tk.PhotoImage

    def _blank_photo(*args, **kwargs):
        return original_photo(master=root, width=2, height=2)

    monkeypatch.setattr(gui_mod.tk, "PhotoImage", _blank_photo)
    monkeypatch.setattr(gui_mod.ImageTk, "PhotoImage", lambda *a, **k: _blank_photo())


def _patch_hud_images(monkeypatch, root):
    import graphics.huds as huds_mod

    original_photo = tk.PhotoImage

    monkeypatch.setattr(huds_mod.Image, "open", lambda *_a, **_k: Image.new("RGBA", (8, 8)))
    monkeypatch.setattr(
        huds_mod.ImageTk,
        "PhotoImage",
        lambda *a, **k: original_photo(master=root, width=2, height=2),
    )


def _full_pin_data():
    return {
        "servo_left": "2",
        "servo_right": "3",
        "light_mleft": "4",
        "light_left": "5",
        "light_right": "6",
        "light_mright": "7",
        "sound_trig": "8",
        "sound_echo": "9",
        "button_left": "10",
        "button_right": "11",
        "servo": "12",
        "button_joystick": "13",
        "joystick_x": "14",
        "joystick_y": "15",
    }


def _set_entry_value(entry, value):
    entry.delete(0, tk.END)
    entry.insert(0, value)


def test_pin_configuration_window_supports_variants_and_commit(monkeypatch, tk_app):
    import graphics.gui as gui_mod

    pin_data = _full_pin_data()
    saved = []
    tk_app.controller.get_pin_data = lambda: dict(pin_data)
    tk_app.controller.save_pin_data = lambda data: saved.append(dict(data))

    for option in range(5):
        window = gui_mod.PinConfigurationWindow(tk_app, option, tk_app)
        tk_app.update_idletasks()
        assert window.data == pin_data
        window.destroy()

    window = gui_mod.PinConfigurationWindow(tk_app, 3, tk_app)
    replacements = {
        "entry_pin_se1": "22",
        "entry_pin_se2": "23",
        "entry_pin_l1": "24",
        "entry_pin_l2": "25",
        "entry_pin_l3": "26",
        "entry_pin_l4": "27",
        "entry_pin_so1": "28",
        "entry_pin_so2": "29",
        "entry_pin_bt1": "30",
        "entry_pin_bt2": "31",
        "entry_pin_aservo": "32",
        "entry_pin_joystick": "33",
        "entry_pin_joystick_x": "34",
        "entry_pin_joystick_y": "35",
    }
    for attr, value in replacements.items():
        entry = getattr(window, attr)
        entry.delete(0, tk.END)
        entry.insert(tk.END, value)
    window.commit_data()

    assert saved[-1] == {
        "servo_left": "22",
        "servo_right": "23",
        "light_mleft": "24",
        "light_left": "25",
        "light_right": "26",
        "light_mright": "27",
        "sound_trig": "28",
        "sound_echo": "29",
        "button_left": "30",
        "button_right": "31",
        "servo": "32",
        "button_joystick": "33",
        "joystick_x": "34",
        "joystick_y": "35",
    }


def test_arm3d_configuration_window_constructor_and_tutorial_access(monkeypatch, tk_app):
    import graphics.gui as gui_mod

    popen_calls = []
    monkeypatch.setattr(
        gui_mod.subprocess,
        "Popen",
        lambda *args, **kwargs: popen_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        gui_mod.os.path,
        "exists",
        lambda path: os.path.basename(path) == "Tutorial_tablas_DH.pdf",
    )

    motor = DummyMotor3D()
    window = gui_mod.Arm3DConfigurationWindow(tk_app, motor, tk_app)

    assert len(window._rows) == 2
    config, error = window._collect_config()
    assert error is None
    assert config["dof"] == 2
    assert config["joint_types"] == ["R", "P"]
    assert config["servo_pins"] == [11, 10]

    assert "tablas DH" in window._help_btn.cget("text")
    window._open_dh_tutorial()
    assert popen_calls
    opened_path = popen_calls[-1][0][0][0]
    assert os.path.basename(opened_path) == "Tutorial_tablas_DH.pdf"

    window._dof_var.set(1)
    window._on_dof_change()
    assert motor.saved_config["dof"] == 1
    window.destroy()


def test_arm3d_configuration_window_swaps_near_zero_dh_values(tk_app):
    import graphics.gui as gui_mod

    motor = DummyMotor3D()
    window = gui_mod.Arm3DConfigurationWindow(tk_app, motor, tk_app)
    row = window._rows[0]

    theta_entry, d_entry, a_entry = row[0], row[1], row[2]
    type_combo = row[4]
    unit_label = row[10]

    a_entry.delete(0, tk.END)
    a_entry.insert(0, "25.0")
    d_entry.delete(0, tk.END)
    d_entry.insert(0, "1e-12")

    type_combo.set("P")
    type_combo.event_generate("<<ComboboxSelected>>")
    tk_app.update_idletasks()

    assert d_entry.get() == "25.0"
    assert a_entry.get() == "0.0"
    assert unit_label.cget("text") == "mm"
    assert theta_entry.cget("state") == "disabled"

    d_entry.delete(0, tk.END)
    d_entry.insert(0, "15.0")
    a_entry.delete(0, tk.END)
    a_entry.insert(0, "1e-12")

    type_combo.set("R")
    type_combo.event_generate("<<ComboboxSelected>>")
    tk_app.update_idletasks()

    assert d_entry.get() == "0.0"
    assert a_entry.get() == "15.0"
    assert unit_label.cget("text") == "deg"
    assert theta_entry.cget("state") == "normal"
    window.destroy()


def test_arm3d_servo_pin_mapping_routes_attach_to_configured_joint():
    from robot_components.robots import ArmHardwareRobot

    robot = ArmHardwareRobot()
    robot.set_servo_pin_mapping([2, 4, 7, 8, 12, 13])

    attached = robot.attach_servo_to_pin(4)

    assert attached is robot.servo_shoulder
    assert robot.servo_shoulder.pin == 4
    assert robot.board.get_pin_element(4) is robot.servo_shoulder


def test_arm3d_servo_attach_ignores_unconfigured_pin():
    from robot_components.robots import ArmHardwareRobot

    robot = ArmHardwareRobot()
    robot.set_servo_pin_mapping([2, 4, 7, 8, 12, 13])

    attached = robot.attach_servo_to_pin(99)

    assert attached is None
    assert all(servo.pin == -1 for servo in robot._joint_servos)
    assert robot.board.get_pin_element(99) is None


def test_braccio_uses_configured_servo_pins():
    from libraries.braccio import Braccio
    from robot_components.robots import ArmHardwareRobot

    robot = ArmHardwareRobot()
    robot.set_servo_pin_mapping([2, 4, 7, 8, 12, 13])
    braccio = Braccio(robot.board)

    assert braccio.begin() == Braccio.OK

    assert robot.servo_base.pin == 2
    assert robot.servo_shoulder.pin == 4
    assert robot.servo_elbow.pin == 7


def test_arm3d_configuration_window_helper_fallback_paths(tmp_path, tk_app):
    import graphics.gui as gui_mod

    calls = []
    window = gui_mod.Arm3DConfigurationWindow.__new__(gui_mod.Arm3DConfigurationWindow)
    window.tk = object()
    window.update_idletasks = lambda: calls.append("update")
    window.winfo_reqwidth = lambda: 320
    window.winfo_reqheight = lambda: 240
    window.minsize = lambda width, height: calls.append(("minsize", width, height))
    window.winfo_x = lambda: 11
    window.winfo_y = lambda: 17
    window.geometry = lambda spec: calls.append(("geometry", spec))

    gui_mod.Arm3DConfigurationWindow._fit_window_to_content(window, center=True)

    combo = gui_mod.ttk.Combobox(tk_app, values=["R", "P"], state="readonly")
    try:
        assert gui_mod.Arm3DConfigurationWindow._semantic_state_for_widget(combo) == "readonly"
    finally:
        combo.destroy()

    class BrokenWidget:
        def configure(self, **_kwargs):
            raise RuntimeError("boom")

    gui_mod.Arm3DConfigurationWindow._apply_widget_state(window, BrokenWidget(), locked=False)

    broken_preset = tmp_path / "broken.json"
    broken_preset.write_text("{invalid", encoding="utf-8")
    vis_values = []
    modes = []
    locks = []
    focus_ops = []
    window._vis_combo = SimpleNamespace(
        configure=lambda **kwargs: vis_values.append(tuple(kwargs["values"]))
    )
    window._visual_var = SimpleNamespace(
        set=lambda value: modes.append(value),
        get=lambda: "auto_generic",
    )
    window._MODES_SELECTABLE = ["auto_generic", "skeleton"]
    window._presets = {
        "broken": str(broken_preset),
        "braccio_tinkerkit": None,
    }
    window._set_locked = lambda locked: locks.append(locked)
    window.focus_get = lambda: SimpleNamespace(
        selection_clear=lambda: focus_ops.append("selection_cleared")
    )
    window.focus_set = lambda: focus_ops.append("focus_set")
    window.after_idle = lambda callback: (_ for _ in ()).throw(RuntimeError("no idle"))

    gui_mod.Arm3DConfigurationWindow._apply_preset_display(window, "broken")
    gui_mod.Arm3DConfigurationWindow._apply_preset_display(window, "braccio_tinkerkit")
    gui_mod.Arm3DConfigurationWindow._clear_combo_focus(window)

    assert ("geometry", "320x240+11+17") in calls
    assert modes[0] == "auto_generic"
    assert modes[-1] == "braccio_exact"
    assert vis_values[-1][0] == "braccio_exact"
    assert locks == [False, True]
    assert focus_ops == ["selection_cleared", "focus_set"]


def test_arm3d_configuration_window_preset_selection_paths(tmp_path):
    import graphics.gui as gui_mod

    broken_preset = tmp_path / "broken.json"
    broken_preset.write_text("{invalid", encoding="utf-8")
    valid_preset = tmp_path / "valid.json"
    valid_preset.write_text(
        '{"dof": 3, "visual": {"mode": "skeleton"}}',
        encoding="utf-8",
    )

    selected = {"name": "broken"}
    preset_display = []
    saved_configs = []
    rebuilt = []
    errors = []
    focus_calls = []
    dof_values = []
    model = SimpleNamespace(dof=2, preset_name="legacy")
    window = gui_mod.Arm3DConfigurationWindow.__new__(gui_mod.Arm3DConfigurationWindow)
    window._preset_var = SimpleNamespace(get=lambda: selected["name"])
    window._presets = {
        "broken": str(broken_preset),
        "valid": str(valid_preset),
    }
    window._dof_var = SimpleNamespace(set=lambda value: dof_values.append(value))
    window.motor3d = SimpleNamespace(
        model=model,
        active_preset_name="legacy",
        set_model_config=lambda config: saved_configs.append(config),
        get_model_config=lambda: {"servo_calibration": [{"pin": 1}]},
    )
    window._table_frame = object()
    window._build_dh_rows = lambda _frame: rebuilt.append("rows")
    window._refresh_base_row_entries = lambda: rebuilt.append("base")
    window._apply_preset_display = lambda name: preset_display.append(name)
    window._clear_combo_focus = lambda: focus_calls.append("clear")

    original_showerror = gui_mod.tk.messagebox.showerror
    gui_mod.tk.messagebox.showerror = lambda title, message, parent=None: errors.append(
        (title, message, parent)
    )
    try:
        gui_mod.Arm3DConfigurationWindow._on_preset_selected(window)
        assert errors and "No se pudo leer el preset 'broken'." in errors[-1][1]
        assert preset_display == []
        assert saved_configs == []

        selected["name"] = "valid"
        gui_mod.Arm3DConfigurationWindow._on_preset_selected(window)
        assert dof_values[-1] == 3
        assert saved_configs[-1]["visual"]["mode"] == "skeleton"
        assert rebuilt[-2:] == ["rows", "base"]
        assert preset_display[-1] == "valid"
        assert window.motor3d.active_preset_name == "valid"
        assert window.motor3d.model.preset_name == "valid"
        assert focus_calls[-1] == "clear"

        selected["name"] = "Custom"
        gui_mod.Arm3DConfigurationWindow._on_preset_selected(window)
        assert preset_display[-1] == "Custom"
        assert window.motor3d.active_preset_name is None
        assert window.motor3d.model.preset_name is None
    finally:
        gui_mod.tk.messagebox.showerror = original_showerror


def test_arm3d_configuration_window_refreshes_disabled_base_entries():
    import graphics.gui as gui_mod

    class EntrySpy:
        def __init__(self, state="normal"):
            self.state = state
            self.ops = []
            self.value = ""

        def cget(self, key):
            assert key == "state"
            return self.state

        def configure(self, **kwargs):
            self.ops.append(("configure", kwargs))
            if "state" in kwargs:
                self.state = kwargs["state"]

        def delete(self, *_args):
            self.ops.append(("delete",))
            self.value = ""

        def insert(self, _index, value):
            self.ops.append(("insert", value))
            self.value = value

    window = gui_mod.Arm3DConfigurationWindow.__new__(gui_mod.Arm3DConfigurationWindow)
    disabled = EntrySpy("disabled")
    normal = EntrySpy("normal")
    window._base_row_entries = {
        "theta": disabled,
        "d": normal,
    }
    window._table_source_config = lambda: {
        "base": {"theta": 1.234, "d": 2.0}
    }

    gui_mod.Arm3DConfigurationWindow._refresh_base_row_entries(window)

    assert disabled.value == "1.23"
    assert normal.value == "2.0"
    assert disabled.ops[0] == ("configure", {"state": "normal"})
    assert disabled.ops[-1] == ("configure", {"state": "disabled"})


def test_arm3d_configuration_window_collect_config_marks_invalid_inputs(tk_app):
    import graphics.gui as gui_mod

    motor = DummyMotor3D()
    window = gui_mod.Arm3DConfigurationWindow(tk_app, motor, tk_app)
    row_r = window._rows[0]
    row_p = window._rows[1]

    _set_entry_value(row_r[0], "bad")
    _set_entry_value(row_p[7], "yaw")
    _set_entry_value(row_p[8], "pitch")
    _set_entry_value(row_p[5], "min")
    _set_entry_value(row_p[6], "max")
    _set_entry_value(window._base_row_entries["theta"], "base")

    config, error = window._collect_config()

    assert config is None
    assert "J1" in error
    assert "Dir yaw" in error
    assert "Dir pitch" in error
    assert "J0 fija" in error
    assert int(row_r[0].cget("highlightthickness")) == 2
    assert int(row_p[7].cget("highlightthickness")) == 2
    assert int(row_p[8].cget("highlightthickness")) == 2
    assert int(row_p[5].cget("highlightthickness")) == 2
    assert int(row_p[6].cget("highlightthickness")) == 2
    assert int(window._base_row_entries["theta"].cget("highlightthickness")) == 2
    window.destroy()


def test_arm3d_configuration_window_collect_config_marks_semantic_limit_errors(tk_app):
    import graphics.gui as gui_mod

    motor = DummyMotor3D()
    window = gui_mod.Arm3DConfigurationWindow(tk_app, motor, tk_app)
    row_r = window._rows[0]
    row_p = window._rows[1]

    _set_entry_value(row_r[2], "2501")
    _set_entry_value(row_r[5], "500")
    _set_entry_value(row_r[6], "600")
    _set_entry_value(row_p[2], "-2501")
    _set_entry_value(row_p[7], "10")
    _set_entry_value(row_p[8], "190")
    _set_entry_value(row_p[5], "50")
    _set_entry_value(row_p[6], "40")

    config, error = window._collect_config()

    assert config is None
    assert "2000" in error
    assert "-180" in error
    assert "mayor" in error
    assert "+/-360deg" in error
    assert int(row_r[2].cget("highlightthickness")) == 2
    assert int(row_r[5].cget("highlightthickness")) == 2
    assert int(row_p[2].cget("highlightthickness")) == 2
    assert int(row_p[6].cget("highlightthickness")) == 2
    window.destroy()


def test_arm3d_configuration_window_save_updates_preset_and_refreshes_panel():
    import graphics.gui as gui_mod

    motor = DummyMotor3D()
    motor.repository = SimpleNamespace(list_builtin_presets=lambda: {"builtin": object()})
    refresh_calls = []

    window = gui_mod.Arm3DConfigurationWindow.__new__(gui_mod.Arm3DConfigurationWindow)
    window._collect_config = lambda: (motor.get_model_config(), None)
    window.motor3d = motor
    window._preset_var = SimpleNamespace(get=lambda: "builtin")
    window.application = SimpleNamespace(
        arm3d_control_panel=SimpleNamespace(
            refresh_from_model=lambda: refresh_calls.append("refresh")
        )
    )
    window.destroy = lambda: refresh_calls.append("destroy")

    gui_mod.Arm3DConfigurationWindow._save(window)

    assert motor.saved_config["dof"] == 2
    assert motor.active_preset_name == "builtin"
    assert motor.model.preset_name == "builtin"
    assert refresh_calls == ["refresh", "destroy"]


def test_arm3d_configuration_window_import_and_export_json_paths(monkeypatch, tmp_path):
    import graphics.gui as gui_mod
    import tkinter.filedialog as filedialog_mod

    errors = []
    dof_values = []
    layout_calls = []
    saved_configs = []
    save_paths = []
    load_result = {"ok": True}

    motor = DummyMotor3D()

    def _load_model_config(path=None):
        if load_result["ok"]:
            motor.model.dof = 4
            return True
        return False

    motor.load_model_config = _load_model_config
    motor.set_model_config = lambda config: saved_configs.append(config)
    motor.save_model_config = lambda path=None: save_paths.append(path) or False

    window = gui_mod.Arm3DConfigurationWindow.__new__(gui_mod.Arm3DConfigurationWindow)
    window.motor3d = motor
    window._dof_var = SimpleNamespace(set=lambda value: dof_values.append(value))
    window._table_frame = object()
    window._build_dh_rows = lambda frame: layout_calls.append(("rows", frame))
    window._refresh_base_row_entries = lambda: layout_calls.append(("base",))
    window._collect_config = lambda: ({"dof": 2, "visual": {"mode": "auto_generic"}}, None)

    monkeypatch.setattr(
        gui_mod.tk.messagebox,
        "showerror",
        lambda title, message, parent=None: errors.append((title, message, parent)),
    )
    monkeypatch.setattr(
        filedialog_mod,
        "askopenfilename",
        lambda **_kwargs: str(tmp_path / "preset.json"),
    )
    monkeypatch.setattr(
        filedialog_mod,
        "asksaveasfilename",
        lambda **_kwargs: str(tmp_path / "export.json"),
    )

    gui_mod.Arm3DConfigurationWindow._import_json(window)
    assert dof_values[-1] == 4
    assert layout_calls[-2:] == [("rows", window._table_frame), ("base",)]

    load_result["ok"] = False
    gui_mod.Arm3DConfigurationWindow._import_json(window)
    assert errors[-1][0] == "Error"

    gui_mod.Arm3DConfigurationWindow._export_json(window)
    assert saved_configs[-1]["dof"] == 2
    assert save_paths[-1].endswith("export.json")
    assert errors[-1][0] == "Error"

    window._collect_config = lambda: (None, "config broken")
    gui_mod.Arm3DConfigurationWindow._export_json(window)
    assert errors[-1][0].startswith("Error de configur")


def test_gui_panels_and_menus_construct_and_interact(monkeypatch, tk_app):
    import graphics.gui as gui_mod
    import graphics.layers as layers_mod

    _patch_gui_images(monkeypatch, tk_app)
    monkeypatch.setattr(gui_mod.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(gui_mod.messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(gui_mod.subprocess, "Popen", lambda *a, **k: tk_app.calls.append(("popen",)))

    class FakeArm3DLayer:
        def __init__(self):
            self.motor3d = DummyMotor3D()

    monkeypatch.setattr(layers_mod, "Arm3DLayer", FakeArm3DLayer)
    tk_app.controller.robot_layer = FakeArm3DLayer()

    menu = gui_mod.MenuBar(tk_app, tk_app)
    menu.create_file()
    menu.check_if_exit()
    menu.show_about()
    menu._MenuBar__launch_help()

    panel = gui_mod.Arm3DControlPanel(tk_app, tk_app, bg=gui_mod.DARK_BLUE)
    panel.refresh_from_model()
    panel._on_slider(1, "55")
    panel._on_ik()
    panel._on_reset_cam()
    panel.set_mouse_drag_mode("zoom")
    panel._on_mouse_drag_mode_change()

    info = gui_mod.Arm3DInfoPanel(tk_app, tk_app, bg=gui_mod.DARK_BLUE)
    info.update(
        2,
        [10.0, 20.0],
        [100.0, 200.0, 300.0],
        in_workspace=True,
        singular=False,
        safety_blocked=False,
        warning_message="",
        joint_limits=[(-90.0, 90.0), (0.0, 120.0)],
        joint_types=["R", "P"],
    )
    info.apply_visual_toggles()

    selector = gui_mod.SelectorBar(tk_app, tk_app, bg=gui_mod.DARK_BLUE)
    selector.hide_circuit_selector()
    selector.recover_circuit_selector()
    selector.hide_gamification_option_selector()
    selector.recover_gamification_option_selector()

    console = gui_mod.ConsoleFrame(tk_app, tk_app, bg=gui_mod.DARK_BLUE)
    console.change_output()
    console.change_warning()
    console.change_error()
    console.input_entry.insert(0, "42")
    console._ConsoleFrame__send_input()

    assert ("create_file",) in tk_app.calls
    assert ("close",) in tk_app.calls
    assert ("joint", 1, 55.0) in tk_app.calls
    assert ("reset_arm3d_camera",) in tk_app.calls
    assert ("camera_view", "zoom") not in tk_app.calls
    assert ("trail", True) in tk_app.calls
    assert ("joint_ranges", False) in tk_app.calls
    assert ("joint_axes", False) in tk_app.calls
    assert ("send_input", "42") in tk_app.calls


def test_drawing_editor_and_buttons_cover_widget_flows(monkeypatch, tk_app):
    import graphics.gui as gui_mod
    import graphics.layers as layers_mod

    _patch_gui_images(monkeypatch, tk_app)

    class FakeArm3DLayer:
        def __init__(self):
            self.motor3d = DummyMotor3D()

    monkeypatch.setattr(layers_mod, "Arm3DLayer", FakeArm3DLayer)
    tk_app.controller.robot_layer = FakeArm3DLayer()

    frame = gui_mod.DrawingFrame(tk_app, tk_app, bg=gui_mod.BLUE)
    frame.set_arm3d_mouse_mode("rotate")
    frame.handle_global_key_press(SimpleNamespace(keysym="a"))
    frame.show_joystick()
    frame.hide_joystick()
    frame.show_button_keys_movement()
    frame.hide_button_keys_movement()
    frame.show_buttons_gamification()
    frame.hide_buttons_gamification()
    frame.show_hud()
    frame.hide_hud()
    frame.show_arm3d_camera_buttons()
    frame.hide_arm3d_camera_buttons()
    frame.change_zoom_label("155.4")
    frame._on_cam_preset("caballera")
    frame._on_cam_drag_mode("zoom")
    assert frame._camera_view_buttons[None].cget("bg") == gui_mod.BLUE
    assert frame._camera_drag_buttons["zoom"].cget("bg") == gui_mod.BLUE
    frame.press(SimpleNamespace(x=10, y=20))
    frame.move(SimpleNamespace(x=30, y=45))
    frame.press_right(SimpleNamespace(x=30, y=45))
    frame.pan(SimpleNamespace(x=45, y=60))
    frame.release_right(SimpleNamespace(x=45, y=60))
    frame.release(SimpleNamespace(x=45, y=60))
    frame.zoom(SimpleNamespace(delta=120))
    frame.zoom(SimpleNamespace(delta=-120))

    gamification = gui_mod.ButtonsGamification(
        tk_app, tk_app, bg=gui_mod.DARK_BLUE
    )
    gamification.show_tutorial(None)
    gamification.show_help(None)
    gamification.show_results(None)
    gamification.delete_elements(None)

    joystick = gui_mod.JoystickFrame(tk_app, tk_app, bg=gui_mod.DARK_BLUE)
    joystick.x_dir.set(321)
    joystick.y_dir.set(654)
    joystick._JoystickFrame__updatex(None)
    joystick._JoystickFrame__updatey(None)
    joystick._JoystickFrame__pressb(None)
    joystick._JoystickFrame__releaseb(None)

    editor = gui_mod.EditorFrame(tk_app)
    editor.change_text("/* hi */\nint value = 1;\n")
    editor.attach_controller(tk_app)
    editor.set_current_exec_line(2)
    editor.clear_exec_line()
    assert editor.text.search_re(r"\bint\b", False)
    assert editor.text.search_re_delimited(r"/\*", r"\*/")
    editor.line_bar.toggle_breakpoint(2)
    editor.line_bar.set_current_line(2)
    editor.line_bar.clear_current_line()
    editor.line_bar.show_lines()

    button_bar = gui_mod.ButtonBar(tk_app, tk_app, bg=gui_mod.DARK_BLUE)
    original_after = tk_app.after
    tk_app.after = lambda delay, callback=None: (
        tk_app.calls.append(("after", delay)),
        callback() if callback is not None else None,
        "after-id",
    )[-1]
    try:
        button_bar.execute()
        button_bar.stop()
        button_bar.pause()
        button_bar.step_forward()
        button_bar.reset()
    finally:
        tk_app.after = original_after
    button_bar.update_state("running")
    button_bar.update_state("paused")

    assert ("set_arm3d_mouse_drag_mode", None) in tk_app.calls
    assert ("set_arm3d_mouse_drag_mode", "zoom") in tk_app.calls
    assert ("camera_view", "caballera") in tk_app.calls
    assert ("unlock_camera_view",) in tk_app.calls
    assert ("camera_view", None) not in tk_app.calls
    assert ("dolly_camera", 25) in tk_app.calls
    assert ("dolly_camera", 15) in tk_app.calls
    assert ("controller_zoom_in",) in tk_app.calls
    assert ("controller_zoom_out",) in tk_app.calls
    assert ("show_tutorial",) in tk_app.calls
    assert ("show_results",) in tk_app.calls
    assert ("delete_elements",) in tk_app.calls
    assert ("breakpoints", (2,)) in tk_app.calls


def test_huds_controller_and_screen_updater_paths(monkeypatch, tk_app):
    import compiler.commands as commands_mod
    import graphics.controller as controller_mod
    import graphics.huds as huds_mod
    import graphics.screen_updater as screen_mod

    _patch_hud_images(monkeypatch, tk_app)

    class CanvasSpy:
        def __init__(self):
            self.ops = []

        def delete(self, *args):
            self.ops.append(("delete", args))

        def create_text(self, *args, **kwargs):
            self.ops.append(("text", args, kwargs))

        def create_image(self, *args, **kwargs):
            self.ops.append(("image", args, kwargs))

    mobile = huds_mod.MobileHUD()
    mobile.set_canvas(CanvasSpy())
    mobile.set_wheel([50, 150, -250])
    mobile.set_circuit([True, False, True])
    mobile.set_detect_obstacle([40, -1])

    actuator = huds_mod.ActuatorHUD()
    actuator.set_canvas(CanvasSpy())
    actuator.set_pressed([True, False])
    actuator.set_direction(-150)
    actuator.set_direction(250)

    class DummyCmd:
        def __init__(self, controller):
            self.controller = controller
            self.rebooted = 0

        def execute(self):
            return True

        def compile(self, _code):
            return object()

        def reboot(self):
            self.rebooted += 1

    class DummyConsoleGamification:
        pass

    class DummyLayer:
        def __init__(self, *args):
            self.args = args
            self.stop_called = 0
            self.circuit = None
            self.drawing = SimpleNamespace(zoom_percentage=lambda: 133)
            self.motor3d = SimpleNamespace(
                set_show_trail=lambda show: tk_app.calls.append(("trail_toggle", show)),
                set_show_joint_ranges=lambda show: tk_app.calls.append(("ranges_toggle", show)),
                set_show_joint_axes=lambda show: tk_app.calls.append(("axes_toggle", show)),
            )

        def stop(self):
            self.stop_called += 1

        def set_joint_angle(self, joint_idx, angle):
            tk_app.calls.append(("set_joint_angle", joint_idx, angle))

        def solve_ik(self, x, y, z):
            tk_app.calls.append(("solve_ik", x, y, z))
            return True, "ok"

        def drag_camera(self, dx, dy, pan=False):
            tk_app.calls.append(("drag_camera_layer", dx, dy, pan))

        def dolly_camera(self, dy):
            tk_app.calls.append(("dolly_camera_layer", dy))

        def reset_camera(self):
            tk_app.calls.append(("reset_camera_layer",))

        def unlock_camera_view(self):
            tk_app.calls.append(("unlock_camera_view_layer",))

        def set_camera_view(self, view_name):
            tk_app.calls.append(("set_camera_view_layer", view_name))

        def set_circuit(self, circuit):
            self.circuit = circuit

    class DummyArm3DLayer(DummyLayer):
        pass

    monkeypatch.setattr(controller_mod.console_gamification, "ConsoleGamification", DummyConsoleGamification)
    monkeypatch.setattr(controller_mod.commands, "Compile", DummyCmd)
    monkeypatch.setattr(controller_mod.commands, "Setup", DummyCmd)
    monkeypatch.setattr(controller_mod.commands, "Loop", DummyCmd)
    monkeypatch.setattr(controller_mod.layers, "MobileRobotLayer", DummyLayer)
    monkeypatch.setattr(controller_mod.layers, "LinearActuatorLayer", DummyLayer)
    monkeypatch.setattr(controller_mod.layers, "ArduinoBoardLayer", DummyLayer)
    monkeypatch.setattr(controller_mod.layers, "Arm3DLayer", DummyArm3DLayer)

    state_calls = []
    view = SimpleNamespace(
        show_circuit_selector=lambda show: tk_app.calls.append(("show_circuit", show)),
        show_gamification_option_selector=lambda show: tk_app.calls.append(("show_gamification", show)),
        show_joystick=lambda show: tk_app.calls.append(("show_joystick_view", show)),
        show_button_keys_movement=lambda show: tk_app.calls.append(("show_keys_btn", show)),
        show_buttons_gamification=lambda show: tk_app.calls.append(("show_gamif_btn", show)),
        show_key_drawing=lambda show: tk_app.calls.append(("show_key_drawing", show)),
        show_arm3d_panel=lambda show: tk_app.calls.append(("show_arm3d_panel", show)),
        change_zoom_label=lambda value: tk_app.calls.append(("zoom_label", value)),
        abort_after=lambda: tk_app.calls.append(("abort_after",)),
        after=lambda delay, callback=None: (
            tk_app.calls.append(("view_after", delay)),
            callback() if callback is not None else None,
            "view-after-id",
        )[-1],
        button_bar=SimpleNamespace(update_state=lambda state: state_calls.append(state)),
        editor_frame=SimpleNamespace(clear_exec_line=lambda: tk_app.calls.append(("clear_exec_line",))),
        keys_used=False,
        move_WASD={"w": False, "a": False, "s": False, "d": False},
        open_arm3d_configuration=lambda: tk_app.calls.append(("open_arm3d_configuration",)),
        update_idletasks=lambda: tk_app.calls.append(("update_idletasks",)),
    )

    controller = controller_mod.RobotsController(view)
    controller.console = SimpleNamespace(
        write_output=lambda text: tk_app.calls.append(("write_output", text)),
        input=lambda text: tk_app.calls.append(("console_input", text)),
        filter_messages=lambda msgs: tk_app.calls.append(("filter_messages", tuple(msgs))),
    )

    for option in range(6):
        controller.change_robot(option)

    controller.robot_layer = DummyArm3DLayer()
    controller.arm3d = True
    controller.update_arm3d_joint(1, 42.0)
    assert controller.solve_arm3d_ik(1.0, 2.0, 3.0) == (True, "ok")
    controller.drag_arm3d_camera(4, 5, pan=True)
    controller.dolly_arm3d_camera(6)
    controller.reset_arm3d_camera()
    controller.toggle_arm3d_trail(True)
    controller.toggle_arm3d_joint_ranges(True)
    controller.toggle_arm3d_joint_axes(True)
    controller.set_arm3d_camera_view("isometrica")
    controller.unlock_arm3d_camera_view()
    controller.open_arm3d_config()
    controller.change_circuit(5)
    controller.send_input("hello")
    controller.filter_console({"info": True, "warning": False, "error": True})

    controller.robot_layer.robot = SimpleNamespace(
        joystick=SimpleNamespace(dx=None, dy=None, value=None)
    )
    controller.update_joystick("dx", 10)
    controller.update_joystick("dy", 20)
    controller.update_joystick("button", 0)

    controller.executing = True
    controller.toggle_pause()
    controller.step_once()
    controller.set_breakpoints({7})
    controller._notify_state("running")
    controller.paused = False
    controller.step_pending = False
    assert controller.debug_should_pause_at_line(7) is True
    controller.stop()

    monkeypatch.setattr(screen_mod.time, "time_ns", lambda: 20_000_000)
    screen_mod.layer = SimpleNamespace(
        move=lambda using_keys, move_wasd: tk_app.calls.append(
            ("screen_move", using_keys, dict(move_wasd))
        )
    )
    screen_mod.view = view
    screen_mod.last_update = 0
    screen_mod.refresh()
    screen_mod.update()

    paused_ctrl = SimpleNamespace(
        executing=True,
        paused=False,
        debug_should_pause_at_line=lambda line_no: line_no == 7,
    )
    screen_mod.controller = paused_ctrl
    screen_mod.view = SimpleNamespace(
        editor_frame=SimpleNamespace(
            set_current_exec_line=lambda line_no: tk_app.calls.append(
                ("exec_line", line_no)
            )
        ),
        after=lambda delay, callback=None: callback() if callback else None,
        update_idletasks=lambda: None,
        keys_used=False,
        move_WASD={},
    )
    with pytest.raises(commands_mod.ExecutionPaused):
        screen_mod.debug_line(7)

    assert state_calls
    assert ("set_joint_angle", 1, 42.0) in tk_app.calls
    assert ("trail_toggle", True) in tk_app.calls
    assert ("ranges_toggle", True) in tk_app.calls
    assert ("axes_toggle", True) in tk_app.calls
    assert ("screen_move", False, {"w": False, "a": False, "s": False, "d": False}) in tk_app.calls
    assert ("exec_line", 7) in tk_app.calls
