import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from graphics.layers import Arm3DLayer  # noqa: E402


class _Model:
    def __init__(self):
        self.visual = {"show_fps_counter": True}


class _Motor3D:
    def __init__(self):
        self.model = _Model()
        self.calls = []

    def set_show_fps_counter(self, show):
        self.calls.append(bool(show))
        self.model.visual["show_fps_counter"] = bool(show)


class _Canvas:
    def __init__(self):
        self.deleted = []
        self.items = []
        self._next_id = 1

    def delete(self, tag):
        self.deleted.append(tag)

    def winfo_width(self):
        return 640

    def create_text(self, *args, **kwargs):
        item_id = self._next_id
        self._next_id += 1
        self.items.append(("text", args, kwargs, item_id))
        return item_id

    def bbox(self, _item_id):
        return (560, 8, 628, 28)

    def create_rectangle(self, *args, **kwargs):
        item_id = self._next_id
        self._next_id += 1
        self.items.append(("rect", args, kwargs, item_id))
        return item_id

    def tag_lower(self, *_args):
        return None


def _layer_with_canvas():
    layer = Arm3DLayer.__new__(Arm3DLayer)
    layer.motor3d = _Motor3D()
    layer._canvas = _Canvas()
    layer._fps_last_frame_time = None
    layer._fps_display_value = 0.0
    layer._request_fast_render = lambda *_args, **_kwargs: None
    return layer


def test_fps_counter_draws_canvas_overlay_when_enabled():
    layer = _layer_with_canvas()

    layer._draw_fps_counter()

    kinds = [item[0] for item in layer._canvas.items]
    assert kinds == ["text", "rect"]
    assert layer._canvas.deleted == ["arm3d_fps_counter"]


def test_fps_counter_toggle_removes_overlay_when_disabled():
    layer = _layer_with_canvas()

    layer.set_fps_counter(False)
    layer._draw_fps_counter()

    assert layer.motor3d.calls == [False]
    assert layer._canvas.items == []
    assert layer._canvas.deleted == ["arm3d_fps_counter", "arm3d_fps_counter"]
