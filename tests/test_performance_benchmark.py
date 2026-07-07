import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from performance_benchmark import (  # noqa: E402
    PR01_PERFORMANCE_SKETCH,
    _fps_drop_sustained,
    _make_two_dof_config,
    build_parser,
    run_config_change,
    run_ik_timing,
    run_memory_idle,
)


class _Canvas:
    def winfo_width(self):
        return 320

    def winfo_height(self):
        return 240

    def create_image(self, *_args, **_kwargs):
        return 1

    def itemconfig(self, *_args, **_kwargs):
        return None


def test_two_dof_config_matches_pr04_starting_point():
    config = _make_two_dof_config()

    assert config["dof"] == 2
    assert len(config["joints"]) == 2
    assert config["visual"]["mode"] == "auto_generic"


def test_sustained_fps_drop_detection_uses_two_second_window():
    assert _fps_drop_sustained([0.11] * 18)[0] is False
    assert _fps_drop_sustained([0.11] * 19)[0] is True
    assert _fps_drop_sustained([0.11] * 10 + [0.02] + [0.11] * 10)[0] is False


def test_argument_defaults_match_tfg_plan():
    args = build_parser().parse_args([])

    assert args.duration == 60.0
    assert args.ik_samples == 50
    assert args.idle_seconds == 30.0
    assert args.canvas == "auto"
    assert "Braccio.ServoMovement" in PR01_PERFORMANCE_SKETCH


def test_benchmark_smoke_headless(monkeypatch):
    monkeypatch.setattr(
        "motor3d.rendering.robot3d_drawing.ImageTk.PhotoImage",
        lambda *_args, **_kwargs: object(),
    )

    ik = run_ik_timing(1)
    memory = run_memory_idle(0.0, _Canvas(), "mock")
    config = run_config_change(_Canvas(), "mock")

    assert ik.test_id == "PR-02"
    assert memory.test_id == "PR-03"
    assert config.test_id == "PR-04"
    assert ik.value >= 0.0
    assert memory.value >= 0.0
    assert config.value >= 0.0
