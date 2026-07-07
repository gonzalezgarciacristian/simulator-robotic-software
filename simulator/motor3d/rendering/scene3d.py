"""
Scene3D — Contenedor de la escena 3D en tiempo de ejecución.
Gestiona posiciones FK, trayectoria del efector y actualización de fotogramas.
"""
import math

from motor3d.kinematics.kinematics_fk import forward_kinematics_chain


class Scene3D:

    MAX_TRAIL_POINTS = 600
    TRAIL_JOINT_EPS = 1e-6

    def __init__(self, model, camera, drawing):
        self.model = model
        self.camera = camera
        self.drawing = drawing
        self.last_points = []
        self.last_chain = None
        self.show_trail = False
        self.trail_points = []
        self._trail_model = None
        self._trail_signature = None

    def update(self, track_trail=True):
        """
        Recalcula la cinemática directa y extiende la trayectoria si está activa.
        Debe llamarse antes de draw() en cada fotograma.
        """
        if self.model.dof == 0:
            return

        chain = forward_kinematics_chain(self.model)
        self.last_chain = chain
        self.last_points = chain.get('positions', [])

        if track_trail and self.show_trail:
            self._extend_trail(chain)

    def draw(self, canvas):
        """Delega el renderizado en Robot3DDrawing."""
        if self.model.dof == 0:
            return
        trail = self.trail_points if self.show_trail else None
        self.drawing.draw(
            canvas,
            self.camera,
            self.last_points,
            self.model,
            self.last_chain,
            trail,
        )

    def get_end_effector(self):
        """Retorna la posición 3D del efector final en la pose actual."""
        ee = self.get_effective_end_effector()
        if ee:
            return ee
        if self.last_chain:
            return self.last_chain.get('end_effector', [0.0, 0.0, 0.0])
        return [0.0, 0.0, 0.0]

    def get_effective_end_effector(self):
        """Retorna el TCP visual real cuando el modelo activo lo define."""
        try:
            return self.drawing.get_effective_end_effector(
                self.model, self.last_points, self.last_chain
            )
        except Exception:
            return None

    def set_show_trail(self, show):
        self.show_trail = bool(show)
        if not self.show_trail:
            self.clear_trail()

    def clear_trail(self):
        self.trail_points = []
        self._trail_model = None
        self._trail_signature = None

    # ------------------------------------------------------------------
    # Interpolación de trayectoria
    # ------------------------------------------------------------------

    def _extend_trail(self, chain):
        """Añade puntos a la trayectoria del efector interpolando en espacio articular.

        En lugar de interpolar linealmente en el espacio 3D del extremo (que
        produce cuerdas rectas fuera del arco real), interpola los ángulos
        articulares entre la pose anterior y la actual, recalcula FK para
        cada configuración intermedia y obtiene el TCP real del modelo visual.
        Esto garantiza que la trayectoria siga el arco cinemático correcto
        aunque el brazo se mueva rápido entre fotogramas.
        """
        # Verificar si la morfología del modelo cambió (resetear si sí)
        sig = tuple(r.get('a', 0) for r in self.model.dh_rows)
        if sig != self._trail_signature:
            self.trail_points = []
            self._trail_model = None
            self._trail_signature = sig

        cur_joints = list(self.model.joints)

        if not self.trail_points:
            ee = self.drawing.get_effective_end_effector(self.model, self.last_points, chain)
            if ee:
                self.trail_points.append(list(ee))
            if self._trail_model is None:
                self._trail_model = _clone_model_joints(self.model)
            else:
                self._trail_model.joints[:] = cur_joints
            return

        # Determinar número de pasos según variación angular máxima
        if self._trail_model is None:
            self._trail_model = _clone_model_joints(self.model)

        prev_joints = list(self._trail_model.joints)
        if prev_joints and len(prev_joints) == len(cur_joints):
            max_delta = max(abs(c - p) for c, p in zip(cur_joints, prev_joints))
        else:
            max_delta = 0.0

        if max_delta <= self.TRAIL_JOINT_EPS:
            return

        steps = max(1, min(8, math.ceil(max_delta / 5.0)))

        # Interpolación en espacio articular: cada paso recalcula FK + TCP
        for s in range(1, steps + 1):
            t = s / steps
            interp_joints = [
                prev_joints[k] + (cur_joints[k] - prev_joints[k]) * t
                for k in range(len(cur_joints))
            ]
            snap = _ModelJointSnap(self.model, interp_joints)
            interp_chain = forward_kinematics_chain(snap)
            interp_pts = interp_chain.get('positions', [])
            ee = self.drawing.get_effective_end_effector(snap, interp_pts, interp_chain)
            if ee:
                self.trail_points.append(list(ee))

        # Limitar longitud
        if len(self.trail_points) > self.MAX_TRAIL_POINTS:
            self.trail_points = self.trail_points[-self.MAX_TRAIL_POINTS:]

        # Guardar snapshot de joints para el próximo fotograma
        self._trail_model.joints[:] = cur_joints


def _clone_model_joints(model):
    """Crea un objeto ligero que almacena únicamente los ángulos articulares."""
    s = _ModelJointSnap(model, list(model.joints))
    return s


class _ModelJointSnap:
    """Proxy del modelo que sobreescribe únicamente los ángulos articulares.

    Permite calcular forward_kinematics_chain con joints intermedios sin
    modificar el modelo real. Delega dof y dh_rows al modelo base.
    """

    __slots__ = ('_base', 'joints')

    def __init__(self, base_model, joints):
        object.__setattr__(self, '_base', base_model)
        object.__setattr__(self, 'joints', list(joints))

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, '_base'), name)
