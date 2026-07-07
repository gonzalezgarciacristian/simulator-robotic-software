"""Performance benchmark tool for the TFG validation plan.

Run from the repository root:
    python -m simulator.performance_benchmark

The measurements map directly to the performance tests documented in the TFG:
PR-01 render FPS, PR-02 inverse kinematics time, PR-03 RSS memory and
PR-04 arm configuration change latency.
"""
from __future__ import annotations

import argparse
import csv
import ctypes
import datetime as _dt
import gc
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_DIR = Path(__file__).resolve().parent
if str(SIMULATOR_DIR) not in sys.path:
    sys.path.insert(0, str(SIMULATOR_DIR))

PR01_PERFORMANCE_SKETCH = """#include <Braccio.h>

const int STEP_DELAY_MS = 8;

void setup() {
  Braccio.begin();
}

void loop() {
  Braccio.ServoMovement(STEP_DELAY_MS, 90, 45, 180, 180, 90, 10);
  delay(80);
  Braccio.ServoMovement(STEP_DELAY_MS, 20, 165, 40, 15, 170, 73);
  delay(80);
  Braccio.ServoMovement(STEP_DELAY_MS, 170, 20, 175, 160, 10, 15);
  delay(80);
  Braccio.ServoMovement(STEP_DELAY_MS, 35, 140, 70, 45, 145, 65);
  delay(80);
  Braccio.ServoMovement(STEP_DELAY_MS, 150, 35, 160, 135, 30, 25);
  delay(80);
  Braccio.ServoMovement(STEP_DELAY_MS, 75, 120, 25, 170, 115, 73);
  delay(80);
  Braccio.ServoMovement(STEP_DELAY_MS, 120, 55, 145, 20, 60, 10);
  delay(80);
}
"""


@dataclass
class BenchmarkResult:
    test_id: str
    metric: str
    value: float
    unit: str
    threshold: str
    passed: bool
    details: dict


class _MockCanvas:
    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height

    def winfo_width(self):
        return self._width

    def winfo_height(self):
        return self._height

    def create_image(self, *_args, **_kwargs):
        return 1

    def itemconfig(self, *_args, **_kwargs):
        return None

    def update_idletasks(self):
        return None

    def update(self):
        return None


class _TkCanvas:
    def __init__(self, root, canvas):
        self.root = root
        self.canvas = canvas

    def __getattr__(self, name):
        return getattr(self.canvas, name)

    def update_idletasks(self):
        self.root.update_idletasks()

    def update(self):
        self.root.update()

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass


@contextmanager
def benchmark_canvas(mode: str, width: int, height: int):
    """Create a real Tk canvas when possible, otherwise use a headless mock."""
    if mode in {"auto", "tk"}:
        try:
            import tkinter as tk

            root = tk.Tk()
            root.title("S4R - Benchmark de rendimiento 3D")
            root.withdraw()
            canvas = tk.Canvas(root, width=width, height=height)
            canvas.pack()
            root.update_idletasks()
            wrapper = _TkCanvas(root, canvas)
            try:
                yield wrapper, "tk", None
            finally:
                wrapper.close()
            return
        except Exception as exc:
            if mode == "tk":
                raise RuntimeError("No se pudo crear un canvas Tkinter real") from exc
            fallback_error = str(exc)
    else:
        fallback_error = None

    canvas = _MockCanvas(width, height)
    with mock.patch("motor3d.rendering.robot3d_drawing.ImageTk") as image_tk:
        image_tk.PhotoImage.return_value = SimpleNamespace()
        yield canvas, "mock", fallback_error


def _load_braccio_api():
    from motor3d.api import Motor3DApi
    from motor3d.persistence.arm_config_repository import ArmConfigRepository

    api = Motor3DApi()
    repo = ArmConfigRepository()
    if not repo.load_builtin_preset(api.model, "braccio_tinkerkit", silent=True):
        raise RuntimeError("No se pudo cargar el preset braccio_tinkerkit")
    api._sync_active_preset_name()
    api._sync_camera_distance_for_model()
    api.scene.clear_trail()
    api.scene.update(track_trail=False)
    return api


def _make_two_dof_config():
    return {
        "dof": 2,
        "link_lengths": [200.0, 160.0],
        "joints": [0.0, 0.0],
        "joint_limits": [[-90.0, 90.0], [-75.0, 75.0]],
        "joint_types": ["R", "R"],
        "dh_rows": [
            {"theta": 0.0, "d": 120.0, "a": 0.0, "alpha": 90.0},
            {"theta": 0.0, "d": 0.0, "a": 200.0, "alpha": 0.0},
        ],
        "visual": {"mode": "auto_generic", "theme": "default", "sizes": {}},
    }


def _braccio_config():
    from motor3d.kinematics.arm_kinematic_state import ArmKinematicState
    from motor3d.persistence.arm_config_repository import ArmConfigRepository

    model = ArmKinematicState()
    repo = ArmConfigRepository()
    if not repo.load_builtin_preset(model, "braccio_tinkerkit", silent=True):
        raise RuntimeError("No se pudo cargar el preset braccio_tinkerkit")
    data = model.to_dict()
    data["preset_name"] = "braccio_tinkerkit"
    return data


def _fps_drop_sustained(frame_durations, max_frame_seconds=0.1, sustained_seconds=2.0):
    slow_run = 0.0
    worst_run = 0.0
    for duration in frame_durations:
        if duration > max_frame_seconds:
            slow_run += duration
            worst_run = max(worst_run, slow_run)
        else:
            slow_run = 0.0
    return worst_run >= sustained_seconds, worst_run


def _build_pr01_app_result(frame_times, start_time):
    elapsed = max(time.perf_counter() - start_time, 1e-9)
    frame_durations = [
        cur - prev for prev, cur in zip(frame_times, frame_times[1:])
    ]
    frames = len(frame_times)
    mean_fps = frames / elapsed
    sustained_drop, worst_slow_run = _fps_drop_sustained(frame_durations)
    min_frame_fps = 1.0 / max(frame_durations) if frame_durations else 0.0

    return BenchmarkResult(
        test_id="PR-01",
        metric="app_render_fps_mean",
        value=round(mean_fps, 3),
        unit="fps",
        threshold=">= 15 FPS medio y sin caidas < 10 FPS sostenidas mas de 2 s",
        passed=mean_fps >= 15.0 and not sustained_drop,
        details={
            "canvas_mode": "full_app",
            "duration_seconds": round(elapsed, 3),
            "frames": frames,
            "min_instant_fps": round(min_frame_fps, 3),
            "worst_slow_run_seconds": round(worst_slow_run, 3),
            "robot": "Brazo Robotico (Braccio)",
            "window": "MainApplication",
            "sketch": "PR01_PERFORMANCE_SKETCH",
        },
    )


def _run_render_fps_application_window(duration_seconds: float, result_path=None, force_exit=False):
    import graphics.gui as gui

    def _cancel_pending_after_callbacks(root):
        try:
            after_ids = root.tk.call("after", "info")
        except Exception:
            return
        for after_id in after_ids:
            try:
                root.after_cancel(after_id)
            except Exception:
                pass

    os.chdir(REPO_ROOT)
    app = gui.MainApplication()
    app.update_idletasks()
    app.selector_bar.robot_selector.current(5)
    app.change_robot(None)
    app.update_idletasks()

    layer = app.controller.robot_layer
    original_draw = layer.motor3d.draw
    frame_times = []
    state = {"result": None, "closed": False, "start": None}

    def _counting_draw(canvas):
        frame_times.append(time.perf_counter())
        return original_draw(canvas)

    layer.motor3d.draw = _counting_draw

    def _write_result(result):
        if result_path:
            Path(result_path).write_text(
                json.dumps(asdict(result), ensure_ascii=False),
                encoding="utf-8",
            )
        try:
            print(json.dumps(asdict(result), ensure_ascii=False), flush=True)
        except Exception:
            pass

    def _finish():
        if state["closed"]:
            return
        state["closed"] = True
        if state["result"] is None:
            state["result"] = _build_pr01_app_result(frame_times, state["start"])
            _write_result(state["result"])
        try:
            app.stop()
        except Exception:
            pass
        _cancel_pending_after_callbacks(app)
        try:
            app.update_idletasks()
        except Exception:
            pass
        try:
            app.quit()
        except Exception:
            pass
        try:
            app.destroy()
        except Exception:
            pass
        if force_exit:
            os._exit(0 if state["result"].passed else 1)

    def _force_finish():
        try:
            _finish()
        finally:
            try:
                app.quit()
            except Exception:
                pass

    try:
        app.protocol("WM_DELETE_WINDOW", _finish)
    except Exception:
        pass

    try:
        app.bind("<Escape>", lambda _event: _finish())
    except Exception:
        pass

    def _show_close_hint():
        try:
            app.title("Simulador Software para Robots - PR-01 cerrando automaticamente")
        except Exception:
            pass

    def _quit_only():
        try:
            app.quit()
        except Exception:
            pass

    try:
        app.editor_frame.change_text(PR01_PERFORMANCE_SKETCH)
    except Exception:
        app.editor_frame.text.delete("1.0", "end")
        app.editor_frame.text.insert("1.0", PR01_PERFORMANCE_SKETCH)
    app.update_idletasks()
    app.execute()

    state["start"] = time.perf_counter()
    app.after(0, _show_close_hint)
    app.after(max(1, int(duration_seconds * 1000)), _finish)
    app.after(max(1000, int(duration_seconds * 1000) + 1500), _force_finish)
    app.mainloop()
    _quit_only()
    _finish()
    return state["result"]


def run_render_fps_application(duration_seconds: float):
    result_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as fh:
            result_file = fh.name

        cmd = [
            sys.executable,
            "-m",
            "simulator.performance_benchmark",
            "--_pr01-app-child",
            "--duration",
            str(duration_seconds),
            "--_pr01-result-path",
            result_file,
        ]
        timeout_s = max(15.0, float(duration_seconds) + 12.0)
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.terminate()
            try:
                stdout, stderr = proc.communicate(timeout=3.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate(timeout=3.0)

        path = Path(result_file)
        if path.exists() and path.stat().st_size > 0:
            data = json.loads(path.read_text(encoding="utf-8"))
            details = dict(data.get("details", {}))
            details["process_exit_code"] = proc.returncode
            details["process_timed_out"] = timed_out
            return BenchmarkResult(
                test_id=data["test_id"],
                metric=data["metric"],
                value=float(data["value"]),
                unit=data["unit"],
                threshold=data["threshold"],
                passed=bool(data["passed"]),
                details=details,
            )

        return BenchmarkResult(
            test_id="PR-01",
            metric="app_render_fps_mean",
            value=0.0,
            unit="fps",
            threshold=">= 15 FPS medio y sin caidas < 10 FPS sostenidas mas de 2 s",
            passed=False,
            details={
                "canvas_mode": "full_app",
                "error": "El proceso de la aplicacion no escribio resultado PR-01.",
                "process_exit_code": proc.returncode,
                "process_timed_out": timed_out,
                "stdout_tail": (stdout or "")[-500:],
                "stderr_tail": (stderr or "")[-500:],
            },
        )
    finally:
        if result_file:
            try:
                Path(result_file).unlink(missing_ok=True)
            except Exception:
                pass


def _ik_targets(sample_count: int):
    from motor3d.kinematics.arm_kinematic_state import ArmKinematicState
    from motor3d.kinematics.kinematics_fk import forward_kinematics_chain
    from motor3d.persistence.arm_config_repository import ArmConfigRepository

    model = ArmKinematicState()
    repo = ArmConfigRepository()
    if not repo.load_builtin_preset(model, "braccio_tinkerkit", silent=True):
        raise RuntimeError("No se pudo cargar el preset braccio_tinkerkit")

    targets = []
    for sample in range(sample_count):
        phase = sample / max(1, sample_count - 1)
        joints = []
        for index, (mn, mx) in enumerate(model.joint_limits):
            center = (mn + mx) / 2.0
            amplitude = (mx - mn) * 0.20
            joints.append(center + amplitude * math.sin(phase * math.tau * 2.0 + index))
        model.joints[:] = joints
        targets.append(list(forward_kinematics_chain(model)["end_effector"]))
    return targets


def run_ik_timing(sample_count: int):
    from motor3d.kinematics.arm_kinematic_state import ArmKinematicState
    from motor3d.kinematics.kinematics_ik import solve_inverse_kinematics
    from motor3d.persistence.arm_config_repository import ArmConfigRepository

    model = ArmKinematicState()
    repo = ArmConfigRepository()
    if not repo.load_builtin_preset(model, "braccio_tinkerkit", silent=True):
        raise RuntimeError("No se pudo cargar el preset braccio_tinkerkit")

    targets = _ik_targets(sample_count)
    durations_ms = []
    converged_count = 0
    errors = []

    for target in targets:
        model.joints[:] = [0.0, 0.0, 0.0, 0.0, 0.0, -17.0]
        start = time.perf_counter()
        converged, error = solve_inverse_kinematics(
            model, target, max_iter=150, tolerance=1.0, alpha=0.65
        )
        durations_ms.append((time.perf_counter() - start) * 1000.0)
        converged_count += int(bool(converged))
        errors.append(float(error))

    mean_ms = statistics.fmean(durations_ms) if durations_ms else 0.0
    max_ms = max(durations_ms) if durations_ms else 0.0

    return BenchmarkResult(
        test_id="PR-02",
        metric="ik_solve_time_mean",
        value=round(mean_ms, 3),
        unit="ms",
        threshold="< 500 ms medio y ninguna invocacion > 1000 ms",
        passed=mean_ms < 500.0 and max_ms <= 1000.0,
        details={
            "samples": sample_count,
            "max_ms": round(max_ms, 3),
            "min_ms": round(min(durations_ms), 3) if durations_ms else 0.0,
            "converged": converged_count,
            "max_error_mm": round(max(errors), 3) if errors else 0.0,
        },
    )


def _current_rss_bytes():
    if os.name == "nt":
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32")
        psapi = ctypes.WinDLL("psapi")
        get_current_process = kernel32.GetCurrentProcess
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info = psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
            wintypes.DWORD,
        ]
        get_process_memory_info.restype = wintypes.BOOL
        ok = get_process_memory_info(
            get_current_process(), ctypes.byref(counters), counters.cb
        )
        if ok:
            return int(counters.WorkingSetSize)
        return 0

    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(rss * 1024 if sys.platform != "darwin" else rss)
    except Exception:
        return 0


def run_memory_idle(idle_seconds: float, canvas, canvas_mode: str):
    api = _load_braccio_api()
    api.draw(canvas)
    if canvas_mode == "tk":
        canvas.update()
    gc.collect()
    if idle_seconds > 0:
        time.sleep(idle_seconds)
    gc.collect()

    rss_mb = _current_rss_bytes() / (1024.0 * 1024.0)
    return BenchmarkResult(
        test_id="PR-03",
        metric="idle_rss",
        value=round(rss_mb, 3),
        unit="MB",
        threshold="< 500 MB",
        passed=0.0 < rss_mb < 500.0,
        details={
            "idle_seconds": idle_seconds,
            "canvas_mode": canvas_mode,
            "process": "benchmark process with Motor3DApi loaded",
        },
    )


def run_config_change(canvas, canvas_mode: str):
    api = _load_braccio_api()
    api.set_model_config(_make_two_dof_config())
    api.draw(canvas)
    if canvas_mode == "tk":
        canvas.update()

    target_config = _braccio_config()
    start = time.perf_counter()
    api.set_model_config(target_config)
    api.draw(canvas)
    if canvas_mode == "tk":
        canvas.update()
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    return BenchmarkResult(
        test_id="PR-04",
        metric="config_change_2_to_6_dof",
        value=round(elapsed_ms, 3),
        unit="ms",
        threshold="< 2000 ms",
        passed=elapsed_ms < 2000.0,
        details={
            "from_dof": 2,
            "to_dof": 6,
            "canvas_mode": canvas_mode,
        },
    )


def write_results(results, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"performance_results_{stamp}.json"
    csv_path = output_dir / f"performance_results_{stamp}.csv"

    payload = {
        "created_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "python": sys.version,
        "platform": sys.platform,
        "results": [asdict(result) for result in results],
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["test_id", "metric", "value", "unit", "threshold", "passed", "details"],
        )
        writer.writeheader()
        for result in results:
            row = asdict(result)
            row["details"] = json.dumps(row["details"], ensure_ascii=False)
            writer.writerow(row)

    return json_path, csv_path


def run_all(args):
    render_result = run_render_fps_application(args.duration)

    with benchmark_canvas(
        args.canvas,
        args.width,
        args.height,
    ) as (canvas, canvas_mode, fallback):
        results = [
            render_result,
            run_ik_timing(args.ik_samples),
            run_memory_idle(args.idle_seconds, canvas, canvas_mode),
            run_config_change(canvas, canvas_mode),
        ]

    output_paths = None
    if args.output_dir:
        output_paths = write_results(results, Path(args.output_dir))

    return results, canvas_mode, fallback, output_paths


def build_parser():
    parser = argparse.ArgumentParser(
        description="Ejecuta las pruebas de rendimiento PR-01..PR-04 del TFG."
    )
    parser.add_argument("--duration", type=float, default=60.0,
                        help="Segundos de medicion para PR-01 FPS (por defecto: 60).")
    parser.add_argument("--ik-samples", type=int, default=50,
                        help="Numero de puntos objetivo para PR-02 IK (por defecto: 50).")
    parser.add_argument("--idle-seconds", type=float, default=30.0,
                        help="Segundos de reposo antes de medir PR-03 RSS (por defecto: 30).")
    parser.add_argument("--canvas", choices=["auto", "tk", "mock"], default="auto",
                        help="Canvas usado por PR-03/PR-04: auto, tk o mock.")
    parser.add_argument("--width", type=int, default=800,
                        help="Anchura del canvas de benchmark.")
    parser.add_argument("--height", type=int, default=600,
                        help="Altura del canvas de benchmark.")
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "output" / "performance"),
                        help="Directorio de salida para JSON y CSV. Usa '' para no escribir.")
    parser.add_argument("--_pr01-app-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_pr01-result-path", default=None, help=argparse.SUPPRESS)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.ik_samples <= 0:
        parser.error("--ik-samples debe ser mayor que 0")
    if args.duration <= 0:
        parser.error("--duration debe ser mayor que 0")
    if args.idle_seconds < 0:
        parser.error("--idle-seconds no puede ser negativo")
    if args.output_dir == "":
        args.output_dir = None
    if args._pr01_app_child:
        result = _run_render_fps_application_window(
            args.duration,
            result_path=args._pr01_result_path,
            force_exit=True,
        )
        return 0 if result.passed else 1

    results, canvas_mode, fallback, output_paths = run_all(args)

    if fallback:
        print(f"Canvas real no disponible; usando mock headless ({fallback}).")
    print("Modo PR-01: app")
    print(f"Canvas usado: {canvas_mode}")
    for result in results:
        status = "OK" if result.passed else "FAIL"
        print(
            f"{result.test_id} {status}: {result.metric} = "
            f"{result.value} {result.unit} ({result.threshold})"
        )
    if output_paths:
        json_path, csv_path = output_paths
        print(f"JSON: {json_path}")
        print(f"CSV: {csv_path}")

    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
