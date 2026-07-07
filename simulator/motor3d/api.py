"""
Motor3DApi — Fachada principal del módulo de simulación 3D.
Arm3DLayer (en graphics) solo llama métodos de esta clase.
"""
import os
import math
from pathlib import Path

import numpy as np

from motor3d.kinematics.arm_kinematic_state import ArmKinematicState
from motor3d.kinematics.kinematics_fk import get_base_transform, forward_kinematics_chain
from motor3d.kinematics.kinematics_ik import solve_inverse_kinematics
from motor3d.kinematics.constraints_limits import clamp_model_joints
from motor3d.camera.camera import Camera
from motor3d.camera.camera_controller import CameraController
from motor3d.rendering.robot3d_drawing import Robot3DDrawing
from motor3d.rendering.scene3d import Scene3D
from motor3d.persistence.arm_config_repository import ArmConfigRepository
from motor3d.safety.safety_manager import SafetyManager


class Motor3DApi:

    DEFAULT_PRESET = 'braccio_tinkerkit'
    _RUNTIME_VISUAL_FLAGS = ('show_joint_ranges', 'show_joint_axes')
    AUTO_GENERIC_CAMERA_DISTANCE_FACTOR = 1.25
    # Umbral de error (mm) por debajo del cual la IK se reporta como "convergida".
    IK_REPORT_TOLERANCE_MM = 5.0
    API_IK_MAX_ITER = 600
    API_IK_ALPHA = 1.0

    def __init__(self):
        self.model = ArmKinematicState()
        self.camera = Camera()

        # Rutas
        _assets_dir = Path(os.path.dirname(__file__)) / '..' / 'assets'
        _assets_dir = _assets_dir.resolve()
        _stl_dir = _assets_dir / 'stl'
        _presets_dir = _assets_dir / 'presets'
        _autosave = _assets_dir / 'arm3d_last_config.json'

        self.autosave_path = _autosave
        self.default_preset_name = self.DEFAULT_PRESET
        self.active_preset_name = self.DEFAULT_PRESET

        self.repository = ArmConfigRepository(
            default_path=_autosave,
            presets_dir=_presets_dir,
        )
        self.camera_controller = CameraController(self.camera)
        self.safety_manager = SafetyManager()

        renderer = Robot3DDrawing(stl_dir=str(_stl_dir))
        self.scene = Scene3D(self.model, self.camera, renderer)
        self.renderer = renderer

        # Cargar preset por defecto
        loaded = self.repository.load_model(self.model, silent=True)
        if not loaded:
            self.repository.load_builtin_preset(self.model, self.DEFAULT_PRESET, silent=True)
        self._sync_active_preset_name()
        if self.model.dof == 0:
            self._load_fallback_config()

        self._sync_camera_distance_for_model()
        self.scene.update()

    # ------------------------------------------------------------------
    # Cámara
    # ------------------------------------------------------------------

    def set_zoom_from_scale(self, scale):
        self.camera.set_zoom_from_scale(scale)

    def keyboard_camera(self, move_wasd):
        self.camera_controller.keyboard_update(move_wasd)

    def pan_camera(self, dx, dy):
        self.camera_controller.pan(dx, dy)

    def dolly_camera(self, dy):
        self.camera_controller.dolly(dy)

    def drag_camera(self, dx, dy, pan=False):
        self.camera_controller.drag(dx, dy, pan=pan)

    def set_camera(self, yaw=None, pitch=None, projection_mode=None, distance=None):
        self.camera.set_orientation(yaw=yaw, pitch=pitch)
        if distance is not None:
            self.camera.set_distance(distance)
        if projection_mode is not None:
            self.camera.set_projection_mode(projection_mode)

    def reset_camera(self):
        self.camera.reset()
        self._sync_camera_distance_for_model()

    # ------------------------------------------------------------------
    # Articulaciones
    # ------------------------------------------------------------------

    def set_joint(self, index, value):
        """Fija el ángulo articular con clamping por límites y actualiza FK."""
        self.model.set_joint(index, value)
        self.scene.update()

    # ------------------------------------------------------------------
    # Trayectoria
    # ------------------------------------------------------------------

    def set_show_trail(self, show):
        self.scene.set_show_trail(show)

    def set_show_joint_ranges(self, show):
        if show:
            self.model.visual['show_joint_ranges'] = True
        else:
            self.model.visual.pop('show_joint_ranges', None)

    def set_show_joint_axes(self, show):
        if show:
            self.model.visual['show_joint_axes'] = True
        else:
            self.model.visual.pop('show_joint_axes', None)

    def set_show_fps_counter(self, show):
        if show:
            self.model.visual['show_fps_counter'] = True
        else:
            self.model.visual['show_fps_counter'] = False

    # ------------------------------------------------------------------
    # Cinemática Inversa
    # ------------------------------------------------------------------

    def solve_ik(self, x, y, z, track_trail=True):
        """
        Lanza la cinemática inversa hacia la posición (x, y, z).

        Returns:
            (converged: bool, message: str)
        """
        # La IK persigue la punta de la pinza cerrada (TCP, el punto medio entre
        # las garras), el mismo punto que muestra el panel, para CUALQUIER brazo.
        # El solver sigue refinando de forma agresiva (tolerancia interna ~1 mm),
        # pero el éxito se reporta hasta IK_REPORT_TOLERANCE_MM: errores de 1-5 mm
        # son visualmente exactos y no deben anunciarse como "objetivo no alcanzable".
        error = self._solve_ik_to_effective_tip([float(x), float(y), float(z)])
        self.scene.update(track_trail=track_trail)
        if error <= self.IK_REPORT_TOLERANCE_MM:
            return True, f"IK convergida (error={error:.1f} mm)"
        else:
            return False, (
                f"Mejor aproximación IK aplicada (error={error:.1f} mm) — "
                f"objetivo no alcanzable exactamente con la configuración actual"
            )

    def _effective_tip(self, model=None):
        """Devuelve (punta_efectiva, chain). La punta efectiva es el TCP que se
        muestra en el panel: para el Braccio es el centro de las garras cerradas
        (ya incluido en el extremo cinemático recalibrado); para un brazo genérico
        es el centro entre las puntas de la pinza decorativa. Cae al extremo DH si
        algo falla."""
        model = model or self.model
        chain = forward_kinematics_chain(model)
        try:
            tip = self.renderer.get_effective_end_effector(
                model, chain['positions'], chain)
        except Exception:
            tip = chain['end_effector']
        return [float(v) for v in tip], chain

    def _solve_ik_to_effective_tip(self, target):
        """Resuelve la IK para que la punta efectiva (TCP) alcance `target`.

        Si la punta coincide con el extremo cinemático (Braccio recalibrado, o
        brazo sin pinza), basta el solver DH estándar. Si la punta es la de la
        pinza decorativa de un brazo genérico —rígida respecto al penúltimo marco
        e independiente de la última articulación (el gripper)— se resuelve un
        modelo temporal con una fila DH fija hasta la punta, lo que la persigue
        de forma nativa y robusta sin offsets de herramienta ocultos."""
        tip, chain = self._effective_tip()
        ee = chain['end_effector']
        if self.model.dof >= 2 and math.dist(tip, ee) > 1.0:
            error = self._solve_via_reduced_model(target, tip, chain)
            if error is not None:
                return error
        solve_inverse_kinematics(
            self.model, list(target), max_iter=self.API_IK_MAX_ITER,
            tolerance=1.0, alpha=self.API_IK_ALPHA)
        tip2, _ = self._effective_tip()
        return math.dist(tip2, target)

    def _solve_via_reduced_model(self, target, tip, chain):
        """Persigue la punta de la pinza decorativa con un modelo temporal.

        Se elimina la última articulación de apertura y se añade una fila DH fija
        que lleva desde el penúltimo marco hasta el TCP de la pinza.
        """
        try:
            dof = self.model.dof
            t_parent = np.array(chain['matrices'][dof - 2], dtype=float)
            tip_local = np.linalg.inv(t_parent) @ np.array(
                [tip[0], tip[1], tip[2], 1.0])
            reduced = ArmKinematicState()
            data = self.model.to_dict()
            for key in ('dh_rows', 'joint_types', 'joint_limits', 'joints',
                        'servo_pins', 'servo_calibration', 'prismatic_pre_rotations'):
                if isinstance(data.get(key), list):
                    data[key] = data[key][:dof - 1]

            x, y, z = float(tip_local[0]), float(tip_local[1]), float(tip_local[2])
            data['dh_rows'].append({
                'theta': math.degrees(math.atan2(y, x)) if abs(x) > 1e-9 or abs(y) > 1e-9 else 0.0,
                'd': z,
                'a': math.hypot(x, y),
                'alpha': 0.0,
            })
            data['joint_types'].append('R')
            data['joint_limits'].append([0.0, 0.0])
            data['joints'].append(0.0)
            if isinstance(data.get('servo_pins'), list):
                data['servo_pins'].append(None)
            if isinstance(data.get('servo_calibration'), list):
                data['servo_calibration'].append([])
            if isinstance(data.get('prismatic_pre_rotations'), list):
                data['prismatic_pre_rotations'].append({'yaw': 0.0, 'pitch': 0.0})
            data['dof'] = dof
            reduced.load_dict(data)
            solve_inverse_kinematics(
                reduced, list(target), max_iter=self.API_IK_MAX_ITER,
                tolerance=1.0, alpha=self.API_IK_ALPHA)
            for i in range(dof - 1):
                self.model.set_joint(i, reduced.joints[i])
            tip2, _ = self._effective_tip()
            return math.dist(tip2, target)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------

    def get_model_config(self):
        self.model.preset_name = self.active_preset_name
        return self.model.to_dict()

    def set_model_config(self, config):
        visual_flags = self._capture_runtime_visual_flags()
        self.model.load_dict(config)
        self._restore_runtime_visual_flags(visual_flags)
        self._sync_active_preset_name()
        self.renderer._canvas_image_id = None
        self.scene.clear_trail()
        self._sync_camera_distance_for_model()
        self.scene.update()

    def save_model_config(self, path=None):
        self.model.preset_name = self.active_preset_name
        return self.repository.save_model(self.model, path=path or self.autosave_path)

    def load_model_config(self, path=None):
        visual_flags = self._capture_runtime_visual_flags()
        ok = self.repository.load_model(self.model, path=path or self.autosave_path)
        if ok:
            self._restore_runtime_visual_flags(visual_flags)
            self._sync_active_preset_name()
            self.scene.clear_trail()
            self._sync_camera_distance_for_model()
            self.scene.update()
        return ok

    def uses_legacy_servo_degrees(self):
        """True solo para el Braccio predefinido con numeración servo 0..180."""
        return (
            self.model.visual.get('mode') == 'braccio_exact'
            and self.active_preset_name == self.DEFAULT_PRESET
        )

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def draw(self, canvas):
        """Renderiza la escena completa en el canvas Tkinter."""
        self.scene.draw(canvas)

    # ------------------------------------------------------------------
    # Evaluación de seguridad (usado por Arm3DLayer)
    # ------------------------------------------------------------------

    def evaluate_safety(self):
        """Evalúa el estado de seguridad de la pose actual.

        El chequeo de workspace se hace sobre el efector cinemático
        (chain['end_effector'], el mismo punto que persigue la IK), no sobre el
        TCP visual: la geometría cosmética de la pinza se extiende más allá de la
        cadena y provocaba falsos "fuera de rango" en poses normales estiradas.
        """
        points = self._points_with_kinematic_end_effector()
        return self.safety_manager.evaluate(points, self.model.max_reach(), model=self.model)


    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _load_fallback_config(self):
        """Configuración mínima si no hay preset disponible."""
        self.model.configure(
            dof=3,
            link_lengths=[200.0, 200.0, 120.0],
            joint_limits=[(-90.0, 90.0)] * 3,
            joint_types=['R', 'R', 'R'],
            joints=[0.0, 0.0, 0.0],
            dh_rows=[
                {'theta': 0.0, 'd': 212.0, 'a': 0.0, 'alpha': 90.0},
                {'theta': 0.0, 'd': 0.0, 'a': 200.0, 'alpha': 0.0},
                {'theta': 0.0, 'd': 0.0, 'a': 200.0, 'alpha': 0.0},
            ],
            visual={'mode': 'auto_generic', 'theme': 'default', 'sizes': {}},
        )
        self.active_preset_name = None
        self.model.preset_name = None

    def _capture_runtime_visual_flags(self):
        visual = getattr(self.model, 'visual', {}) or {}
        return {
            key: bool(visual.get(key, False))
            for key in self._RUNTIME_VISUAL_FLAGS
        }

    def _restore_runtime_visual_flags(self, flags):
        if not isinstance(flags, dict):
            return
        for key in self._RUNTIME_VISUAL_FLAGS:
            if flags.get(key, False):
                self.model.visual[key] = True
            else:
                self.model.visual.pop(key, None)

    def _sync_active_preset_name(self):
        preset_name = getattr(self.model, 'preset_name', None)
        if preset_name == self.DEFAULT_PRESET and self.model.visual.get('mode') == 'braccio_exact':
            self.active_preset_name = preset_name
            self.model.preset_name = preset_name
            return
        if self.model.visual.get('mode') == 'braccio_exact':
            # Compatibilidad con presets/autosaves antiguos sin preset_name persistido.
            self.active_preset_name = self.DEFAULT_PRESET
            self.model.preset_name = self.DEFAULT_PRESET
            return
        self.active_preset_name = None
        self.model.preset_name = None

    def _sync_camera_distance_for_model(self):
        """Reencuadra la distancia orbital según el tamaño del modelo cargado."""
        self.camera.set_distance(self._recommended_camera_distance())

    def _recommended_camera_distance(self):
        """Evita arrancar con la cámara demasiado cerca de modelos genéricos grandes."""
        if self.model.visual.get('mode') == 'braccio_exact':
            return self.camera.DEFAULT_DISTANCE

        reach = max(0.0, float(self.model.max_reach()))
        if reach <= 0.0:
            return self.camera.DEFAULT_DISTANCE

        try:
            base_transform = get_base_transform(self.model)
            base_offset = math.sqrt(sum(float(v) * float(v) for v in base_transform[:3, 3]))
        except Exception:
            base_offset = 0.0

        extent = base_offset + reach
        return max(
            self.camera.DEFAULT_DISTANCE,
            extent * self.AUTO_GENERIC_CAMERA_DISTANCE_FACTOR,
        )

    def _points_with_effective_tcp(self):
        points = [list(p) for p in (self.scene.last_points or [])]
        tcp = self.scene.get_effective_end_effector()
        if tcp is None:
            return points
        if points:
            points[-1] = list(tcp)
        else:
            points = [list(tcp)]
        return points

    def _points_with_kinematic_end_effector(self):
        """Posiciones articulares con el último punto = efector cinemático.

        Es el extremo de la cadena DH, el mismo objetivo que resuelve la IK; se
        usa para el chequeo de alcance/workspace."""
        points = [list(p) for p in (self.scene.last_points or [])]
        chain = self.scene.last_chain
        ee = chain.get('end_effector') if chain else None
        if ee is None:
            return points
        if points:
            points[-1] = list(ee)
        else:
            points = [list(ee)]
        return points
