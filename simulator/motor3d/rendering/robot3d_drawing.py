"""
Robot3DDrawing — Motor de renderizado 3D.
Pipeline: NumPy vectorizado → PIL rasterización → Tkinter PhotoImage (un único blit).

BraccioVisualModel  — Carga mallas STL del Braccio; anima con matrices FK.
GenericDhVisualModel — Geometría procedural para cualquier cadena DH.
MeshAsset           — Contenedor de triángulos + color base.
"""
import math
import os
import struct
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from motor3d.kinematics.kinematics_fk import get_base_transform, get_joint_axis_world

try:
    from PIL import Image, ImageDraw, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False


# ---------------------------------------------------------------------------
# Constantes de renderizado
# ---------------------------------------------------------------------------
_LIGHT_DIR = np.array([0.35, -0.45, 1.0], dtype=float)
_LIGHT_DIR = _LIGHT_DIR / np.linalg.norm(_LIGHT_DIR)

_ARC_COLOR = (0, 150, 130)
_ARC_STEPS = 32
_FAST_ARC_STEPS = 14
_TRAIL_SEGMENT_MM = 25.0
_FAST_TRAIL_SEGMENT_MM = 55.0
_TRAIL_MAX_PIECES = 12
_FAST_TRAIL_MAX_PIECES = 5
_VIEWPORT_CULL_MARGIN = 64.0
_AMBIENT = 0.30


# ---------------------------------------------------------------------------
# MeshAsset
# ---------------------------------------------------------------------------
class MeshAsset:
    """Contenedor de triángulos en coordenadas de modelo + color base."""

    def __init__(self, triangles, color=(180, 180, 180)):
        """
        Args:
            triangles: array numpy (N, 3, 3) — N triángulos, cada uno con 3 vértices xyz.
            color    : (R, G, B) entero 0-255.
        """
        self.triangles = np.asarray(triangles, dtype=float)
        self.color = color

    def is_empty(self):
        return self.triangles.size == 0


# ---------------------------------------------------------------------------
# Lectura de STL
# ---------------------------------------------------------------------------
def _load_stl(path):
    """
    Lee un archivo STL (binario o ASCII) y retorna array numpy (N, 3, 3).
    Retorna array vacío si el archivo no existe o hay error.
    """
    if not os.path.isfile(path):
        return np.zeros((0, 3, 3), dtype=float)
    try:
        with open(path, 'rb') as f:
            header = f.read(80)
            if header is None:
                return np.zeros((0, 3, 3), dtype=float)
            # Intentar STL binario
            count_data = f.read(4)
            if len(count_data) < 4:
                return np.zeros((0, 3, 3), dtype=float)
            n_tris = struct.unpack('<I', count_data)[0]
            expected = n_tris * 50
            remaining = f.read(expected)
            if len(remaining) == expected and n_tris > 0:
                # Es STL binario
                tris = []
                offset = 0
                for _ in range(n_tris):
                    # 3 floats normal + 9 floats verts + 2 bytes attr
                    vals = struct.unpack_from('<12f', remaining, offset)
                    v0 = [vals[3], vals[4], vals[5]]
                    v1 = [vals[6], vals[7], vals[8]]
                    v2 = [vals[9], vals[10], vals[11]]
                    tris.append([v0, v1, v2])
                    offset += 50
                return np.array(tris, dtype=float)
    except Exception:
        pass

    # Intentar STL ASCII
    try:
        tris = []
        with open(path, 'r', errors='replace') as f:
            content = f.read()
        lines = content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('facet normal'):
                verts = []
                i += 1
                while i < len(lines) and len(verts) < 3:
                    vl = lines[i].strip()
                    if vl.startswith('vertex'):
                        parts = vl.split()
                        verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    i += 1
                if len(verts) == 3:
                    tris.append(verts)
            else:
                i += 1
        if tris:
            return np.array(tris, dtype=float)
    except Exception:
        pass

    return np.zeros((0, 3, 3), dtype=float)


# ---------------------------------------------------------------------------
# BraccioVisualModel
# ---------------------------------------------------------------------------
class BraccioVisualModel:
    """
    Modelo visual específico del TinkerKit Braccio.
    Carga 7 mallas STL y las anima mediante transformaciones de articulación.
    """

    REQUIRED_DOF = 6
    STL_NAMES = [
        'braccio_base.stl',
        'braccio_shoulder.stl',
        'braccio_elbow.stl',
        'braccio_wrist_pitch.stl',
        'braccio_wrist_roll.stl',
        'braccio_left_gripper.stl',
        'braccio_right_gripper.stl',
    ]
    # Colores por pieza (RGB)
    PIECE_COLORS = [
        (80, 80, 80),    # base
        (60, 120, 200),  # shoulder
        (60, 120, 200),  # elbow
        (60, 120, 200),  # wrist pitch
        (60, 120, 200),  # wrist roll
        (220, 80, 60),   # gripper L
        (220, 80, 60),   # gripper R
    ]

    # Los STL del Braccio ya están en mm — no se aplica escala.
    STL_SCALE = 1.0

    # Offsets visuales extraídos del URDF braccio_arm.urdf.
    # Formato: (xyz_mm [x, y, z], rpy [roll, pitch, yaw] en radianes).
    # Las coordenadas xyz están en mm (valores URDF en metros × 1000).
    # R = Rz(yaw) @ Ry(pitch) @ Rx(roll) — convención URDF estándar.
    VISUAL_OFFSETS = [
        # piece 0 — braccio_base_link: rpy="0 0 π"  xyz="0 0.004 0"
        ([0.0, 4.0, 0.0],   [0.0, 0.0, math.pi]),
        # piece 1 — shoulder_link:    rpy="0 0 0"   xyz="-0.0045 0.0055 -0.026"
        ([-4.5, 5.5, -26.0], [0.0, 0.0, 0.0]),
        # piece 2 — elbow_link:       rpy="0 0 0"   xyz="-0.0045 0.005 -0.025"
        ([-4.5, 5.0, -25.0], [0.0, 0.0, 0.0]),
        # piece 3 — wrist_pitch_link: rpy="0 0 0"   xyz="0.003 -0.0004 -0.024"
        ([3.0, -0.4, -24.0], [0.0, 0.0, 0.0]),
        # piece 4 — wrist_roll_link:  rpy="0 0 0"   xyz="0.006 0 0"
        ([6.0, 0.0, 0.0],   [0.0, 0.0, 0.0]),
        # piece 5 — left_gripper_link:  rpy="0 π/2 0"  xyz="0 -0.012 0"
        ([0.0, -12.0, 0.0], [0.0, math.pi / 2, 0.0]),
        # piece 6 — right_gripper_link: rpy="0 π/2 0"  xyz="0 -0.012 0.010"
        ([0.0, -12.0, 10.0], [0.0, math.pi / 2, 0.0]),
    ]

    def __init__(self, stl_dir):
        self._stl_dir = stl_dir
        self._assets = []
        self._loaded = False
        self._offset_matrices = [
            self._build_offset_matrix(xyz, rpy)
            for xyz, rpy in self.VISUAL_OFFSETS
        ]
        self._load_assets()

    @staticmethod
    def _Raxis(axis, angle):
        """
        Matriz de rotación 4×4 alrededor de un eje arbitrario por angle radianes.
        Rodrigues' rotation formula.
        """
        ax = np.array(axis, dtype=float)
        norm = np.linalg.norm(ax)
        if norm < 1e-9:
            return np.eye(4, dtype=float)
        ax = ax / norm
        c, s = math.cos(angle), math.sin(angle)
        t = 1.0 - c
        x, y, z = ax
        R = np.array([
            [t*x*x + c,     t*x*y - s*z,  t*x*z + s*y],
            [t*x*y + s*z,   t*y*y + c,    t*y*z - s*x],
            [t*x*z - s*y,   t*y*z + s*x,  t*z*z + c  ],
        ], dtype=float)
        T = np.eye(4, dtype=float)
        T[:3, :3] = R
        return T

    @staticmethod
    def _build_offset_matrix(xyz_mm, rpy):
        """
        Construye una matriz homogénea 4×4 desde un origen visual URDF.
        También usada para orígenes articulares (joint origins).

        Args:
            xyz_mm : [x, y, z] desplazamiento en mm.
            rpy    : [roll, pitch, yaw] en radianes.
                     Convención URDF: R = Rz(yaw) @ Ry(pitch) @ Rx(roll).

        Returns:
            np.ndarray shape (4, 4).
        """
        roll, pitch, yaw = rpy
        cr, sr = math.cos(roll),  math.sin(roll)
        cp, sp = math.cos(pitch), math.sin(pitch)
        cy, sy = math.cos(yaw),   math.sin(yaw)

        Rx = np.array([[1, 0,   0  ],
                       [0, cr, -sr ],
                       [0, sr,  cr ]], dtype=float)
        Ry = np.array([[ cp, 0, sp],
                       [  0, 1,  0],
                       [-sp, 0, cp]], dtype=float)
        Rz = np.array([[cy, -sy, 0],
                       [sy,  cy, 0],
                       [ 0,   0, 1]], dtype=float)

        R = Rz @ Ry @ Rx
        T = np.eye(4, dtype=float)
        T[:3, :3] = R
        T[:3, 3]  = xyz_mm
        return T

    def _load_assets(self):
        self._assets = []
        for i, name in enumerate(self.STL_NAMES):
            path = os.path.join(self._stl_dir, name)
            tris = _load_stl(path)
            if tris.size > 0:
                tris = tris * self.STL_SCALE
            color = self.PIECE_COLORS[i] if i < len(self.PIECE_COLORS) else (150, 150, 150)
            self._assets.append(MeshAsset(tris, color))
        self._loaded = any(not a.is_empty() for a in self._assets)

    def supports_model(self, model):
        return model.dof >= self.REQUIRED_DOF and self._loaded

    # Offset del TCP en el frame local de T_wrist_r (en mm), calculado como
    # el punto medio entre las puntas de ambas garras cuando el gripper está
    # totalmente cerrado (servo=73° → q_urdf=1.274 rad).
    # Derivado del centroide de los vértices extremos de los STL de la pinza.
    _TCP_IN_WRIST_R = np.array([1.57, -0.50, 126.55, 1.0])

    def get_effective_end_effector(self, model, points, chain):
        """
        Devuelve el TCP calculado con la cadena URDF:
        la posición de la punta de las garras cuando están cerradas,
        independiente del estado real de apertura del gripper (joint[5]).

        El TCP se define como el punto medio de las puntas de ambas garras
        en posición cerrada, expresado en el frame de T_wrist_r:
        offset = [1.57, -0.50, 126.55] mm.
        """
        try:
            q = [(model.joints[i] + 90.0) * math.pi / 180.0
                 for i in range(min(5, model.dof))]   # solo joints 0-4; gripper no afecta TCP
            while len(q) < 5:
                q.append(math.pi / 2)

            _T = self._build_offset_matrix
            _R = self._Raxis
            base_T = get_base_transform(model)

            T_base    = base_T @ _R([0, 0, 1], q[0])
            T_shoulder = T_base @ _T([0.0, -2.0, 72.0], [-math.pi / 2, 0.0, 0.0]) \
                         @ _R([1, 0, 0], q[1])
            T_elbow   = T_shoulder @ _T([0.0, 0.0, 125.0], [-math.pi / 2, 0.0, 0.0]) \
                        @ _R([1, 0, 0], q[2])
            T_wrist_p = T_elbow @ _T([0.0, 0.0, 125.0], [-math.pi / 2, 0.0, 0.0]) \
                        @ _R([1, 0, 0], q[3])
            T_pre_wr  = T_wrist_p @ _T([0.0, 0.0, 60.0], [0.0, 0.0, math.pi / 2])
            T_wrist_r = T_pre_wr @ _R([0, 0, -1], q[4])

            # TCP = punta de las garras cerradas en frame T_wrist_r
            tcp = T_wrist_r @ self._TCP_IN_WRIST_R
            return [float(tcp[0]), float(tcp[1]), float(tcp[2])]
        except Exception:
            # Fallback al efector DH si algo falla
            if chain and chain.get('end_effector'):
                return chain['end_effector']
            return list(points[-1]) if points else [0.0, 0.0, 0.0]

    def get_joint_frames(self, model, chain=None):
        """
        Retorna la lista de marcos articulares en el sistema URDF
        (idéntico al de iter_triangles) para que _collect_joint_arcs dibuje
        los arcos en las posiciones correctas del modelo renderizado.

        Cada elemento: {'pos': [x,y,z], 'axis': np.array, 'xref': np.array, 'r_arc': float}

        La dirección de referencia (xref) corresponde a joints[i]=0 (posición neutro DH),
        calculada como el eje del marco AFTER transform @ Rjoint(q_urdf=π/2) que es
        perpendicular al eje de rotación — equivalente a -T_pre[:3,1] para las
        articulaciones con eje X, y [1,0,0] para la rotación de base (eje Z).
        """
        q = [(model.joints[i] + 90.0) * math.pi / 180.0
             for i in range(min(6, model.dof))]
        while len(q) < 6:
            q.append(math.pi / 2)

        _T = self._build_offset_matrix
        _R = self._Raxis
        base_T = get_base_transform(model)

        frames = []

        # Joint 0 — base, rotación alrededor de Z del mundo
        T_base = base_T @ _R([0, 0, 1], q[0])
        frames.append({
            'pos': base_T[:3, 3].tolist(),
            'axis': base_T[:3, 2].copy(),
            'xref': np.array([1.0, 0.0, 0.0]),   # X world = dirección a q0=0
            'r_arc': 80.0,
        })
        frames[0]['xref'] = base_T[:3, 0].copy()

        # Joint 1 — hombro, rotación alrededor de X
        T_pre_shoulder = T_base @ _T([0.0, -2.0, 72.0], [-math.pi / 2, 0.0, 0.0])
        T_shoulder = T_pre_shoulder @ _R([1, 0, 0], q[1])
        frames.append({
            'pos': T_pre_shoulder[:3, 3].tolist(),
            'axis': T_pre_shoulder[:3, 0].copy(),
            'xref': -T_pre_shoulder[:3, 1].copy(),   # dirección del eslabón a q1=0
            'r_arc': 60.0,
        })

        # Joint 2 — codo, rotación alrededor de X
        T_pre_elbow = T_shoulder @ _T([0.0, 0.0, 125.0], [-math.pi / 2, 0.0, 0.0])
        T_elbow = T_pre_elbow @ _R([1, 0, 0], q[2])
        frames.append({
            'pos': T_pre_elbow[:3, 3].tolist(),
            'axis': T_pre_elbow[:3, 0].copy(),
            'xref': -T_pre_elbow[:3, 1].copy(),
            'r_arc': 55.0,
        })

        # Joint 3 — muñeca pitch, rotación alrededor de X
        T_pre_wrist_p = T_elbow @ _T([0.0, 0.0, 125.0], [-math.pi / 2, 0.0, 0.0])
        T_wrist_p = T_pre_wrist_p @ _R([1, 0, 0], q[3])
        frames.append({
            'pos': T_pre_wrist_p[:3, 3].tolist(),
            'axis': T_pre_wrist_p[:3, 0].copy(),
            'xref': -T_pre_wrist_p[:3, 1].copy(),
            'r_arc': 45.0,
        })

        # Joint 4 — muñeca roll, rotación alrededor de -Z
        T_pre_wrist_r = T_wrist_p @ _T([0.0, 0.0, 60.0], [0.0, 0.0, math.pi / 2])
        T_wrist_r = T_pre_wrist_r @ _R([0, 0, -1], q[4])
        frames.append({
            'pos': T_pre_wrist_r[:3, 3].tolist(),
            'axis': -T_pre_wrist_r[:3, 2].copy(),   # -Z de T_pre_wrist_r
            'xref': -T_pre_wrist_r[:3, 1].copy(),   # dirección a q4=0
            'r_arc': 30.0,
        })

        # Joint 5 — pinza (gripper_joint URDF), rotación alrededor de −Y
        # Se usa el origen articular del dedo derecho (gripper_joint):
        #   xyz=(10,0,30)mm, rpy=(0,−0.2967,0) desde wrist_roll
        # La dirección de referencia debe coincidir con el dedo que se DIBUJA: la
        # malla del gripper lleva un origen visual rpy=(0,π/2,0) que la gira 90°
        # respecto al marco articular, de modo que el dedo visible apunta según
        # +Z de T_pre_right_g (no −X). Sin esta corrección el arco quedaba 90°
        # desfasado respecto a la posición real del dedo en ambos extremos.
        T_pre_right_g = T_wrist_r @ _T([10.0, 0.0, 30.0], [0.0, -0.2967, 0.0])
        frames.append({
            'pos': T_pre_right_g[:3, 3].tolist(),
            'axis': -T_pre_right_g[:3, 1].copy(),   # eje −Y (URDF axis=-Y)
            'xref': T_pre_right_g[:3, 2].copy(),     # dirección del dedo visible
            'r_arc': 50.0,
        })

        return frames[:model.dof]

    def iter_triangles(self, model, points, chain):
        """
        Genera (triangles_world, color) para cada pieza.

        Construye su PROPIA cadena cinemática directamente desde los datos del
        URDF braccio_arm.urdf, independiente de las matrices FK del DH.
        (Según §8.9 de la Guía: "NO depende de las matrices DH de la cadena FK")

        Conversión de ángulos:
            q_urdf = (joint_deg + 90.0) * pi / 180
            → servo=0  → q=0,    servo=90 → q=π/2,  servo=180 → q=π
            Validado con límites URDF: shoulder [0.262, 2.880] ≡ servo [15°,165°]

        Yields: (np.array shape (N,3,3), (R,G,B))
        """
        if model.dof < self.REQUIRED_DOF:
            return

        # Ángulos URDF a partir de los ángulos DH del modelo
        q = [(model.joints[i] + 90.0) * math.pi / 180.0
             for i in range(min(6, model.dof))]
        while len(q) < 6:
            q.append(math.pi / 2)

        # ------------------------------------------------------------------
        # Cadena cinemática URDF (todos los offsets xyz en mm, rpy en rad)
        # ------------------------------------------------------------------
        _T = self._build_offset_matrix   # alias corto
        _R = self._Raxis
        base_T = get_base_transform(model)

        # Pieza 0: braccio_base_link
        #   base_joint: parent=base_link(world), origin=(0,0,0), axis=+Z
        T_base = base_T @ _R([0, 0, 1], q[0])

        # Pieza 1: shoulder_link
        #   shoulder_joint: origin xyz=(0,-2,72)mm rpy=(-π/2,0,0), axis=+X
        T_shoulder = T_base \
                     @ _T([0.0, -2.0, 72.0], [-math.pi / 2, 0.0, 0.0]) \
                     @ _R([1, 0, 0], q[1])

        # Pieza 2: elbow_link
        #   elbow_joint: origin xyz=(0,0,125)mm rpy=(-π/2,0,0), axis=+X
        T_elbow = T_shoulder \
                  @ _T([0.0, 0.0, 125.0], [-math.pi / 2, 0.0, 0.0]) \
                  @ _R([1, 0, 0], q[2])

        # Pieza 3: wrist_pitch_link
        #   wrist_pitch_joint: origin xyz=(0,0,125)mm rpy=(-π/2,0,0), axis=+X
        T_wrist_p = T_elbow \
                    @ _T([0.0, 0.0, 125.0], [-math.pi / 2, 0.0, 0.0]) \
                    @ _R([1, 0, 0], q[3])

        # Pieza 4: wrist_roll_link
        #   wrist_roll_joint: origin xyz=(0,0,60)mm rpy=(0,0,π/2), axis=-Z
        T_wrist_r = T_wrist_p \
                    @ _T([0.0, 0.0, 60.0], [0.0, 0.0, math.pi / 2]) \
                    @ _R([0, 0, -1], q[4])

        # Pieza 5: left_gripper_link (sub_gripper_joint, mimic de gripper_joint)
        #   origin xyz=(-10,0,30)mm rpy=(0,3.4383,0), axis=+Y
        T_left_g = T_wrist_r \
                   @ _T([-10.0, 0.0, 30.0], [0.0, 3.4383, 0.0]) \
                   @ _R([0, 1, 0], q[5])

        # Pieza 6: right_gripper_link (gripper_joint)
        #   origin xyz=(10,0,30)mm rpy=(0,-0.2967,0), axis=-Y
        T_right_g = T_wrist_r \
                    @ _T([10.0, 0.0, 30.0], [0.0, -0.2967, 0.0]) \
                    @ _R([0, -1, 0], q[5])

        link_transforms = [
            T_base, T_shoulder, T_elbow, T_wrist_p,
            T_wrist_r, T_left_g, T_right_g,
        ]

        for piece_idx, asset in enumerate(self._assets):
            if asset.is_empty() or piece_idx >= len(link_transforms):
                continue

            # T_final = T_link_world @ T_visual_origin (URDF <visual><origin>)
            T_final = link_transforms[piece_idx] @ self._offset_matrices[piece_idx]

            tris = asset.triangles          # (N, 3, 3) ya en mm
            N = tris.shape[0]
            verts = tris.reshape(-1, 3)
            verts_h = np.hstack([verts, np.ones((verts.shape[0], 1))])
            verts_w = (T_final @ verts_h.T).T
            yield verts_w[:, :3].reshape(N, 3, 3), asset.color


# ---------------------------------------------------------------------------
# Utilidades de geometría
# ---------------------------------------------------------------------------

def _axis_aligned_transform(direction):
    """Matriz 4×4 identidad con columna Z = normalize(direction).
    Se usa para orientar cilindros a lo largo de un vector arbitrario."""
    z = np.array(direction, dtype=float)
    n = np.linalg.norm(z)
    if n < 1e-9:
        return np.eye(4)
    z = z / n
    ref = np.array([0.0, 1.0, 0.0]) if abs(z[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x = np.cross(ref, z)
    x = x / np.linalg.norm(x)
    y = np.cross(z, x)
    T = np.eye(4, dtype=float)
    T[:3, 0] = x
    T[:3, 1] = y
    T[:3, 2] = z
    return T


# ---------------------------------------------------------------------------
# GenericDhVisualModel
# ---------------------------------------------------------------------------
class GenericDhVisualModel:
    """
    Modelo visual genérico para cualquier cadena DH (1-6 DOF).
    Cada articulación se representa como una carcasa discoidea + núcleo cilíndrico
    (similar a un cuerpo de servo), y cada eslabón como una sección rectangular.
    """

    # Dimensiones mínimas en mm — aseguran visibilidad a zoom normal
    MIN_RADIUS = 25.0
    MAX_RADIUS = 55.0
    MIN_LINK_W = 18.0
    MAX_LINK_W = 44.0
    JOINT_STEPS = 12
    GRIPPER_MAX_OPEN_DEG = 32.0

    def supports_model(self, model):
        return model.dof >= 1

    def get_effective_end_effector(self, model, points, chain):
        dims = self._resolve_dimensions(model)
        gripper = self._get_gripper_geometry(model, chain, dims)
        if gripper is not None:
            return gripper['tcp'].tolist()
        if chain and chain.get('end_effector'):
            return chain['end_effector']
        if points:
            return points[-1]
        return [0.0, 0.0, 0.0]

    def _joint_neutral_xref(self, model, index, parent_transform):
        """Dirección de referencia para q=0 respetando el theta fijo DH."""
        row = model.dh_rows[index] if index < len(model.dh_rows) else {}
        theta_deg = float(row.get('theta', 0.0))
        theta_rad = math.radians(theta_deg)

        x_parent = np.asarray(parent_transform[:3, 0], dtype=float)
        y_parent = np.asarray(parent_transform[:3, 1], dtype=float)
        return math.cos(theta_rad) * x_parent + math.sin(theta_rad) * y_parent

    @staticmethod
    def _safe_normalize(vector, fallback):
        vec = np.asarray(vector, dtype=float)
        norm = np.linalg.norm(vec)
        if norm < 1e-9:
            vec = np.asarray(fallback, dtype=float)
            norm = np.linalg.norm(vec)
            if norm < 1e-9:
                return np.array([1.0, 0.0, 0.0], dtype=float)
        return vec / norm

    @staticmethod
    def _rotate_about_axis(vector, axis, angle):
        vec = np.asarray(vector, dtype=float)
        ax = np.asarray(axis, dtype=float)
        ax_norm = np.linalg.norm(ax)
        if ax_norm < 1e-9:
            return vec
        ax = ax / ax_norm
        c = math.cos(angle)
        s = math.sin(angle)
        return (
            vec * c
            + np.cross(ax, vec) * s
            + ax * np.dot(ax, vec) * (1.0 - c)
        )

    def _is_gripper_joint(self, model, joint_idx, seg_len, radius):
        jtype = model.joint_types[joint_idx] if joint_idx < len(model.joint_types) else 'R'
        if joint_idx != model.dof - 1 or model.dof < 2 or jtype == 'P':
            return False
        if seg_len < radius * 2.8:
            return True
        mn, mx = model.joint_limits[joint_idx] if joint_idx < len(model.joint_limits) else (-90.0, 90.0)
        return float(mx) <= 10.0 and float(mn) < float(mx)

    def _gripper_ratio(self, model, joint_idx):
        jval = model.joints[joint_idx] if joint_idx < len(model.joints) else 0.0
        mn, mx = model.joint_limits[joint_idx] if joint_idx < len(model.joint_limits) else (0.0, 90.0)
        if mx <= mn:
            return 0.5
        return max(0.0, min(1.0, (jval - mn) / (mx - mn)))

    def _get_gripper_geometry(self, model, chain, dims):
        if not chain or 'matrices' not in chain or model.dof <= 0:
            return None

        positions = chain.get('positions', [])
        matrices = chain.get('matrices', [])
        if len(positions) < model.dof + 1:
            return None

        joint_idx = model.dof - 1
        p0 = np.asarray(positions[joint_idx], dtype=float)
        p1 = np.asarray(positions[joint_idx + 1], dtype=float)
        seg_len = float(np.linalg.norm(p1 - p0))
        radius = dims['radius']
        if not self._is_gripper_joint(model, joint_idx, seg_len, radius):
            return None

        base_T = get_base_transform(model)
        T_prev = matrices[joint_idx - 1] if joint_idx > 0 else base_T
        row = model.dh_rows[joint_idx] if joint_idx < len(model.dh_rows) else {}

        hinge_axis = self._safe_normalize(T_prev[:3, 2], [0.0, 0.0, 1.0])
        forward = self._joint_neutral_xref(model, joint_idx, T_prev)
        forward = np.asarray(forward, dtype=float) - hinge_axis * np.dot(forward, hinge_axis)
        forward = self._safe_normalize(forward, T_prev[:3, 0])

        a_offset = float(row.get('a', 0.0))
        d_offset = float(row.get('d', 0.0))
        closed_offset = forward * a_offset + hinge_axis * d_offset
        tcp = p0 + closed_offset
        visual_span = float(np.linalg.norm(closed_offset))
        closed_dir = self._safe_normalize(closed_offset, forward)

        open_axis = hinge_axis - closed_dir * np.dot(hinge_axis, closed_dir)
        if np.linalg.norm(open_axis) < 1e-9:
            open_axis = forward - closed_dir * np.dot(forward, closed_dir)
        open_axis = self._safe_normalize(open_axis, T_prev[:3, 1])
        side = self._safe_normalize(np.cross(open_axis, closed_dir), np.cross(hinge_axis, forward))

        palm_radius = min(visual_span * 0.09, radius * 0.38)
        palm_depth = min(visual_span * 0.10, radius * 0.50)
        # Pinza estilizada: la longitud viene de la fila DH, pero el grosor queda
        # acotado para que escalas grandes no generen mordazas desproporcionadas.
        finger_width = min(visual_span * 0.055, radius * 0.24)
        bridge_half_span = finger_width * 0.58
        hinge_dist = min(visual_span * 0.24, radius * 1.25)
        finger_len = max(0.0, visual_span - hinge_dist)
        knuckle_radius = finger_width * 0.42

        wrist_center = p0 + closed_dir * (palm_depth * 0.50)
        hinge_center = p0 + closed_dir * hinge_dist
        bridge_center = hinge_center
        neck_start = p0 + closed_dir * palm_depth
        neck_end = hinge_center
        neck_width = finger_width * 1.05

        # Cada dedo se separa del eje un ángulo igual al valor articular: los dedos
        # quedan paralelos (cerrados, a lo largo de 'closed_dir') en jval=0 y se abren
        # a medida que jval se aleja de 0. Así cada límite acota el recorrido de su
        # dedo y el límite más cercano a 0 controla cuánto puede cerrarse la pinza
        # (si no llega a 0 queda un hueco; si lo cruza, se cerraría de más).
        jval_g = float(model.joints[joint_idx]) if joint_idx < len(model.joints) else 0.0
        fingers = []
        for sign in (+1.0, -1.0):
            hinge = hinge_center + side * sign * bridge_half_span
            angle = math.radians(-sign * jval_g)
            finger_dir = self._rotate_about_axis(closed_dir, open_axis, angle)
            finger_dir = self._safe_normalize(finger_dir, closed_dir)
            root = hinge.copy()
            tip = root + finger_dir * finger_len
            fingers.append({
                'sign': sign,
                'hinge': hinge,
                'root': root,
                'tip': tip,
                'dir': finger_dir,
            })

        return {
            'joint_idx': joint_idx,
            'palm_radius': palm_radius,
            'palm_depth': palm_depth,
            'finger_width': finger_width,
            'bridge_half_span': bridge_half_span,
            'knuckle_radius': knuckle_radius,
            'neck_start': neck_start,
            'neck_end': neck_end,
            'neck_width': neck_width,
            'wrist_center': wrist_center,
            'bridge_center': bridge_center,
            'forward': closed_dir,
            'side': side,
            'hinge_axis': open_axis,
            'tcp': tcp,
            'fingers': fingers,
        }

    def get_joint_frames(self, model, chain=None):
        frames = []
        matrices = chain.get('matrices', []) if chain else []
        positions = chain.get('positions', []) if chain else []
        base_T = get_base_transform(model)
        # Radio mínimo visible (fuera del disco de la articulación): garantiza que
        # el arco de rango se dibuje también en articulaciones con a=0 (p. ej. la
        # base que gira sobre una columna 'd'), cuyo eslabón propio mide 0.
        dims = self._resolve_dimensions(model)
        arc_floor = dims['radius'] * 1.8
        for i in range(model.dof):
            T = matrices[i - 1] if i > 0 else base_T
            pos = positions[i] if i < len(positions) else [0.0, 0.0, 0.0]
            a_len = abs(model.link_lengths[i]) if i < len(model.link_lengths) else 100.0
            r_arc = max(a_len * 0.4, arc_floor)
            frames.append({
                'pos': pos,
                'axis': T[:3, 2].copy(),
                'xref': self._joint_neutral_xref(model, i, T),
                'r_arc': r_arc,
            })

        # Como el Braccio, se marca el rango de UN solo dedo (el +): el arco sigue
        # a ese dedo, que se separa del eje 'forward' un ángulo -jval. Sobre el
        # rango articular [mn, mx] el dedo barre [-mx, -mn]; así cada límite mueve
        # su borde (el cercano a 0 controla el cierre, el lejano la apertura). El
        # arco se centra en la base de ese dedo para que lo siga.
        grip = self._get_gripper_geometry(model, chain, dims) if chain else None
        if grip is not None:
            gi = grip['joint_idx']
            if gi < len(frames):
                mn_g, mx_g = model.joint_limits[gi]
                plus = next((f for f in grip['fingers'] if f['sign'] > 0), None)
                if plus is not None:
                    frames[gi]['pos'] = list(np.asarray(plus['hinge'], dtype=float))
                frames[gi]['axis'] = np.asarray(grip['hinge_axis'], dtype=float)
                frames[gi]['xref'] = np.asarray(grip['forward'], dtype=float)
                frames[gi]['arc_angles'] = (float(-mx_g), float(-mn_g))
        return frames

    def _get_prismatic_geometry(self, model, joint_idx, chain):
        """
        Separa la geometría de una junta prismática DH en:
          - deslizamiento real sobre z_i
          - soporte rígido restante hasta el siguiente origen

        En DH modificada, el vector p0->p1 incluye tanto Tz(d+q) como Tx(a).
        Por eso no debe usarse directamente como eje del actuador cuando `a != 0`.
        """
        if not chain or 'matrices' not in chain:
            return None

        positions = chain.get('positions', [])
        matrices = chain.get('matrices', [])
        if joint_idx < 0 or joint_idx >= model.dof or len(positions) < joint_idx + 2:
            return None

        p0 = np.asarray(positions[joint_idx], dtype=float)
        p1 = np.asarray(positions[joint_idx + 1], dtype=float)

        base_T = get_base_transform(model)
        T_prev = matrices[joint_idx - 1] if joint_idx > 0 else base_T
        axis_dir = np.asarray(get_joint_axis_world(model, joint_idx, T_prev), dtype=float)

        span = p1 - p0
        slide_extent = float(np.dot(span, axis_dir))
        slide_end = p0 + axis_dir * slide_extent
        support_vec = p1 - slide_end

        return {
            'base': p0,
            'joint_end': p1,
            'axis_dir': axis_dir,
            'slide_end': slide_end,
            'slide_len': float(np.linalg.norm(slide_end - p0)),
            'support_vec': support_vec,
            'support_len': float(np.linalg.norm(support_vec)),
        }

    def iter_triangles(self, model, points, chain):
        """
        Genera triángulos de la geometría procedural del brazo.

        Cada articulación:
          - R: disco exterior (eje de rotación = col-Z del frame anterior) + hub cilíndrico.
          - P: housing fijo en p0 + vástago sobre z_i; cualquier offset fijo restante
            se dibuja como soporte rígido separado.
          - Último joint + eslabón muy corto → pinza de dos dedos que abre/cierra.
        Yields: (np.array shape (N,3,3), (R,G,B))
        """
        if not chain or 'matrices' not in chain:
            return

        matrices = chain['matrices']
        positions = chain.get('positions', [])
        if len(positions) < 2:
            return

        dims = self._resolve_dimensions(model)
        r  = dims['radius']
        lw = dims['link_w']
        base_T = get_base_transform(model)
        gripper = self._get_gripper_geometry(model, chain, dims)

        for i in range(model.dof):
            p0 = np.array(positions[i],     dtype=float)
            p1 = np.array(positions[i + 1], dtype=float)

            # Frame anterior: define el eje de rotación REAL del joint i (col Z)
            T_prev = matrices[i - 1] if i > 0 else base_T
            # Transform alineado con la direccion del eslabon (p0 -> p1)
            T_link = _axis_aligned_transform(p1 - p0)

            jtype    = model.joint_types[i] if i < len(model.joint_types) else 'R'
            at_limit = model.is_at_limit(i)
            seg_len  = float(np.linalg.norm(p1 - p0))

            if at_limit:
                actuator_color = (230, 80, 30)
            elif jtype == 'P':
                actuator_color = (55, 185, 90)
            else:
                actuator_color = (55, 115, 205)

            housing_color = (58, 62, 75)
            link_color    = (140, 145, 162)

            # ---- Pinza: último joint con eslabón muy corto ----
            is_gripper = gripper is not None and i == gripper['joint_idx']

            if is_gripper:
                palm = _make_cylinder(
                    gripper['wrist_center'],
                    _axis_aligned_transform(gripper['forward']),
                    gripper['palm_radius'],
                    gripper['palm_depth'] * 0.92,
                    self.JOINT_STEPS,
                )
                if palm.size > 0:
                    yield palm, housing_color

                neck = _make_link_prism(
                    gripper['neck_start'],
                    gripper['neck_end'],
                    gripper['neck_width'],
                )
                if neck.size > 0:
                    yield neck, housing_color

                bridge = _make_link_prism(
                    gripper['bridge_center'] - gripper['side'] * gripper['bridge_half_span'],
                    gripper['bridge_center'] + gripper['side'] * gripper['bridge_half_span'],
                    gripper['finger_width'] * 1.12,
                )
                if bridge.size > 0:
                    yield bridge, housing_color

                hinge_transform = _axis_aligned_transform(gripper['hinge_axis'])
                for finger in gripper['fingers']:
                    knuckle = _make_cylinder(
                        finger['hinge'],
                        hinge_transform,
                        gripper['knuckle_radius'],
                        gripper['finger_width'] * 1.10,
                        self.JOINT_STEPS,
                    )
                    if knuckle.size > 0:
                        yield knuckle, housing_color

                    prism  = _make_link_prism(
                        finger['root'],
                        finger['tip'],
                        gripper['finger_width'],
                    )
                    if prism.size > 0:
                        yield prism, actuator_color

            elif jtype == 'P':
                prism_geom = self._get_prismatic_geometry(model, i, chain)
                if prism_geom is None:
                    continue

                axis_transform = _axis_aligned_transform(prism_geom['axis_dir'])
                # Brida de conexión (flange) en p0
                flange = _make_cylinder(p0, T_prev, r, r * 0.30, self.JOINT_STEPS)
                if flange.size > 0:
                    yield flange, (90, 110, 130)
                # Housing fijo alineado con el eje real de la prismática (z_i)
                housing_h = r * 1.6
                housing = _make_cylinder(p0, axis_transform, r * 0.58, housing_h, self.JOINT_STEPS)
                if housing.size > 0:
                    yield housing, housing_color
                # Vástago móvil: solo representa el desplazamiento sobre z_i
                if prism_geom['slide_len'] > r * 0.4:
                    rod_center = (prism_geom['base'] + prism_geom['slide_end']) * 0.5
                    rod = _make_cylinder(
                        rod_center,
                        axis_transform,
                        r * 0.20,
                        prism_geom['slide_len'],
                        self.JOINT_STEPS,
                    )
                    if rod.size > 0:
                        yield rod, actuator_color
                # Offset fijo restante (por ejemplo `a`) hasta el siguiente origen.
                if prism_geom['support_len'] > lw * 0.35:
                    support = _make_link_prism(
                        prism_geom['slide_end'],
                        prism_geom['joint_end'],
                        lw * 0.82,
                    )
                    if support.size > 0:
                        yield support, link_color

            else:
                # R: carcasa discoidea + hub actuador
                disc = _make_cylinder(p0, T_prev, r,        r * 0.40, self.JOINT_STEPS)
                if disc.size > 0:
                    yield disc, housing_color
                hub_h = min(r * 1.6, max(r * 0.8, seg_len * 0.25))
                hub = _make_cylinder(p0, T_link, r * 0.38, hub_h, self.JOINT_STEPS)
                if hub.size > 0:
                    yield hub, actuator_color
                # Seccion de eslabon: el destino ya combina d y a de la fila DH.
                prism = _make_link_prism(p0, p1, lw)
                if prism.size > 0:
                    yield prism, link_color

        # Indicador del efector final (punto objetivo de la IK): esfera pequeña.
        ee = np.array(self.get_effective_end_effector(model, positions, chain), dtype=float)
        sphere = _make_sphere_approx(ee, max(4.0, r * 0.26))
        if sphere.size > 0:
            yield sphere, (220, 180, 50)

    def _resolve_dimensions(self, model):
        """Calcula radio y ancho de eslabón usando |a| + |d| de cada fila DH."""
        seg_lengths = []
        for row in model.dh_rows:
            a = abs(float(row.get('a', 0)))
            d = abs(float(row.get('d', 0)))
            seg = math.sqrt(a * a + d * d)
            if seg > 1.0:
                seg_lengths.append(seg)
        avg_len = sum(seg_lengths) / len(seg_lengths) if seg_lengths else 100.0
        r  = max(self.MIN_RADIUS, min(self.MAX_RADIUS, avg_len * 0.12))
        lw = max(self.MIN_LINK_W, min(self.MAX_LINK_W, avg_len * 0.09))
        return {'radius': r, 'link_w': lw}


# ---------------------------------------------------------------------------
# Funciones de geometría procedural
# ---------------------------------------------------------------------------

def _make_cylinder(center, transform_mat, radius, height, steps):
    """Genera triángulos de un cilindro orientado según los ejes de transform_mat."""
    if radius <= 1e-9 or height <= 1e-9 or steps < 3:
        return np.zeros((0, 3, 3))

    tris = []
    angles = [2 * math.pi * k / steps for k in range(steps)]
    # Usar la columna Z de la matriz de transformación como eje del cilindro
    ax = transform_mat[:3, 2]
    norm = np.linalg.norm(ax)
    if norm < 1e-9:
        ax = np.array([0.0, 0.0, 1.0])
    else:
        ax = ax / norm

    # Ortogonal al eje
    ref = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(ax, ref)) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    u = np.cross(ax, ref)
    u = u / np.linalg.norm(u)
    v = np.cross(ax, u)

    c = np.array(center, dtype=float)
    top = c + ax * height * 0.5
    bot = c - ax * height * 0.5

    for k in range(steps):
        a0, a1 = angles[k], angles[(k + 1) % steps]
        p0b = bot + radius * (math.cos(a0) * u + math.sin(a0) * v)
        p1b = bot + radius * (math.cos(a1) * u + math.sin(a1) * v)
        p0t = top + radius * (math.cos(a0) * u + math.sin(a0) * v)
        p1t = top + radius * (math.cos(a1) * u + math.sin(a1) * v)
        tris.append(np.array([[p0b, p1b, p0t]]))
        tris.append(np.array([[p1b, p1t, p0t]]))
        tris.append(np.array([[top, p0t, p1t]]))
        tris.append(np.array([[bot, p1b, p0b]]))

    if tris:
        return np.vstack(tris)
    return np.zeros((0, 3, 3))


def _make_link_prism(p0, p1, width):
    """Genera triángulos de un prisma cuadrado entre dos puntos."""
    if width <= 1e-9:
        return np.zeros((0, 3, 3))

    p0 = np.array(p0, dtype=float)
    p1 = np.array(p1, dtype=float)
    axis = p1 - p0
    length = np.linalg.norm(axis)
    if length < 1e-6:
        return np.zeros((0, 3, 3))
    axis = axis / length

    ref = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(axis, ref)) > 0.9:
        ref = np.array([0.0, 1.0, 0.0])
    u = np.cross(axis, ref)
    u = u / np.linalg.norm(u) * (width / 2)
    v = np.cross(axis, u)
    v_n = np.linalg.norm(v)
    if v_n > 1e-9:
        v = v / v_n * (width / 2)

    corners_b = [p0 + u + v, p0 - u + v, p0 - u - v, p0 + u - v]
    corners_t = [p1 + u + v, p1 - u + v, p1 - u - v, p1 + u - v]

    faces = []
    for i in range(4):
        j = (i + 1) % 4
        faces.append([corners_b[i], corners_b[j], corners_t[i]])
        faces.append([corners_b[j], corners_t[j], corners_t[i]])

    faces.append([corners_b[0], corners_b[1], corners_b[2]])
    faces.append([corners_b[0], corners_b[2], corners_b[3]])
    faces.append([corners_t[0], corners_t[2], corners_t[1]])
    faces.append([corners_t[0], corners_t[3], corners_t[2]])

    return np.array(faces, dtype=float)


def _make_sphere_approx(center, radius, steps=6):
    """Aproximación de esfera con un icosaedro simplificado."""
    c = np.array(center, dtype=float)
    tris = []
    for i in range(steps):
        phi0 = math.pi * i / steps - math.pi / 2
        phi1 = math.pi * (i + 1) / steps - math.pi / 2
        for j in range(steps * 2):
            theta0 = 2 * math.pi * j / (steps * 2)
            theta1 = 2 * math.pi * (j + 1) / (steps * 2)

            def pt(phi, theta):
                return c + radius * np.array([
                    math.cos(phi) * math.cos(theta),
                    math.cos(phi) * math.sin(theta),
                    math.sin(phi)
                ])

            p00 = pt(phi0, theta0)
            p01 = pt(phi0, theta1)
            p10 = pt(phi1, theta0)
            p11 = pt(phi1, theta1)
            tris.append([p00, p01, p10])
            tris.append([p01, p11, p10])

    return np.array(tris, dtype=float)


def _tint_color(color, factor):
    return (
        min(255, int(color[0] * factor)),
        min(255, int(color[1] * factor)),
        min(255, int(color[2] * factor)),
    )


def _resolve_render_worker_count():
    """Devuelve el numero de workers para preparar mallas 3D."""
    raw = os.environ.get('S4R_ARM3D_RENDER_WORKERS', 'auto').strip().lower()
    if raw in ('0', '1', 'off', 'false', 'no'):
        return 1
    if raw and raw != 'auto':
        try:
            return max(1, min(32, int(raw)))
        except ValueError:
            pass
    cpu_count = os.cpu_count() or 1
    if cpu_count <= 2:
        return 1
    return max(1, min(2, cpu_count - 1))


def _resolve_min_worker_triangles():
    raw = os.environ.get('S4R_ARM3D_RENDER_MIN_TRIS', '').strip()
    if not raw:
        return 1500
    try:
        return max(1, int(raw))
    except ValueError:
        return 1500


def _prepare_mesh_draw_chunk(all_tris, colors, shaded_flags, projection):
    """Proyecta, filtra e ilumina un bloque de triangulos."""
    if all_tris.size == 0:
        return None

    n_tris = all_tris.shape[0]
    r_view = projection['R_view']
    cam_pos = projection['cam_pos']
    f = projection['f']
    cx = projection['cx']
    cy = projection['cy']
    width = projection.get('width')
    height = projection.get('height')
    cull_margin = projection.get('cull_margin', _VIEWPORT_CULL_MARGIN)

    verts = all_tris.reshape(n_tris * 3, 3)
    verts_cam = (verts - cam_pos) @ r_view.T

    z_cam = verts_cam[:, 2]
    behind = (z_cam <= 0.01).reshape(n_tris, 3).any(axis=1)

    mode = projection.get('mode')
    if mode == 'isometrica':
        scale = projection['ortho_scale']
        sx = verts_cam[:, 0] * scale + cx
        sy = -verts_cam[:, 1] * scale + cy
    else:
        z_safe = np.where(z_cam > 0.01, z_cam, 1.0)
        sx = (verts_cam[:, 0] / z_safe) * f + cx
        sy = (-verts_cam[:, 1] / z_safe) * f + cy
    pts2d = np.stack([sx, sy], axis=1).reshape(n_tris, 3, 2)
    if width and height:
        min_xy = pts2d.min(axis=1)
        max_xy = pts2d.max(axis=1)
        offscreen = (
            (max_xy[:, 0] < -cull_margin)
            | (min_xy[:, 0] > float(width) + cull_margin)
            | (max_xy[:, 1] < -cull_margin)
            | (min_xy[:, 1] > float(height) + cull_margin)
        )
    else:
        offscreen = np.zeros(n_tris, dtype=bool)

    v0 = all_tris[:, 0, :]
    v1 = all_tris[:, 1, :]
    v2 = all_tris[:, 2, :]
    e1 = v1 - v0
    e2 = v2 - v0
    normals = np.cross(e1, e2)
    n_norms = np.linalg.norm(normals, axis=1)
    degen = n_norms < 1e-9
    n_norms_safe = np.where(degen, 1.0, n_norms)
    normals = normals / n_norms_safe[:, np.newaxis]

    view_dirs = cam_pos - v0
    vd_norms = np.linalg.norm(view_dirs, axis=1)
    vd_safe = np.where(vd_norms < 1e-9, 1.0, vd_norms)
    view_dirs = view_dirs / vd_safe[:, np.newaxis]
    facing = np.einsum('ij,ij->i', normals, view_dirs) > 0

    centroids_cam = ((v0 + v1 + v2) / 3.0 - cam_pos) @ r_view.T
    depths = centroids_cam[:, 2]

    mask = ~behind & ~degen & facing & ~offscreen
    visible = np.nonzero(mask)[0]
    if visible.size == 0:
        return None

    light_dot = np.einsum('ij,j->i', normals[visible], _LIGHT_DIR)
    shade = _AMBIENT + (1.0 - _AMBIENT) * np.maximum(0.0, light_dot)
    shade = np.where(shaded_flags[visible], shade, 1.0)

    rgb = np.minimum(
        255,
        (colors[visible].astype(float) * shade[:, np.newaxis]).astype(np.int16),
    ).astype(np.uint8)

    return pts2d[visible], depths[visible], rgb


# ---------------------------------------------------------------------------
# Robot3DDrawing
# ---------------------------------------------------------------------------
class Robot3DDrawing:
    """
    Motor de renderizado 3D principal.
    Pipeline: NumPy vectorizado → PIL rasterización → Tkinter PhotoImage.
    """

    STATIC_TAG = "arm3d_static"
    DYNAMIC_TAG = "arm3d_dynamic"
    TRAIL_TAG = "arm3d_trail"

    BG_COLOR = (30, 30, 35)
    GRID_COLOR = (60, 60, 70)
    AXIS_COLORS = {'x': (220, 60, 60), 'y': (60, 200, 60), 'z': (60, 60, 220)}
    TRAIL_COLOR = (0, 220, 180)
    GRID_SIZE = 400.0
    GRID_STEP = 100.0
    GRID_HALF_WIDTH = 2.0
    GRID_Z_OFFSET = -1.0

    drawing_width = 800
    drawing_height = 600

    def __init__(self, stl_dir=None):
        if stl_dir is None:
            stl_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'stl')
            stl_dir = os.path.normpath(stl_dir)

        self.braccio_visual = BraccioVisualModel(stl_dir)
        self.generic_visual = GenericDhVisualModel()
        self.visual_model = None
        self._last_draw_key = None
        self._photo = None
        self._canvas_image_id = None
        self._mesh_worker_count = _resolve_render_worker_count()
        self._mesh_worker_min_tris = _resolve_min_worker_triangles()
        self._mesh_executor = None
        self._grid_mesh_cache = None
        self._fast_quality = False

    def __del__(self):
        executor = getattr(self, '_mesh_executor', None)
        if executor is not None:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                executor.shutdown(wait=False)
            except Exception:
                pass

    def resolve_visual_model(self, model):
        """Selecciona el modelo visual según la configuración (Patrón Estrategia)."""
        visual_mode = model.visual.get('mode', 'auto_generic')
        if visual_mode == 'braccio_exact' and self.braccio_visual.supports_model(model):
            return self.braccio_visual
        return self.generic_visual

    def set_fast_quality(self, enabled):
        """Reduce detalle no estructural durante interacciones para mantener FPS."""
        self._fast_quality = bool(enabled)

    def _trail_quality(self):
        if self._fast_quality:
            return _FAST_TRAIL_SEGMENT_MM, _FAST_TRAIL_MAX_PIECES
        return _TRAIL_SEGMENT_MM, _TRAIL_MAX_PIECES

    def _active_arc_steps(self):
        return _FAST_ARC_STEPS if self._fast_quality else _ARC_STEPS

    def get_effective_end_effector(self, model, points3d, chain):
        vm = self.resolve_visual_model(model)
        return vm.get_effective_end_effector(model, points3d, chain)

    def draw(self, canvas, camera, points3d, model, chain, trail=None):
        """
        Renderiza la escena completa en el canvas Tkinter.

        Args:
            canvas : tk.Canvas
            camera : Camera
            points3d: lista de [x,y,z] posiciones articulares
            model  : ArmKinematicState
            chain  : resultado de forward_kinematics_chain
            trail  : lista de [x,y,z] puntos de trayectoria o None
        """
        if not _PIL_OK or canvas is None:
            return

        try:
            w = canvas.winfo_width()
            h = canvas.winfo_height()
        except Exception:
            w, h = self.drawing_width, self.drawing_height

        if w < 10 or h < 10:
            w, h = self.drawing_width, self.drawing_height

        img = Image.new('RGB', (w, h), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        projection = self._build_projection_context(camera, w, h)

        # Ejes del mundo como overlay sencillo
        self._draw_axes(draw, projection)

        # Colectar mallas agrupadas por color (evita crear 10k+ tuplas Python)
        vm = self.resolve_visual_model(model)
        self.visual_model = vm
        mesh_groups = []
        grid_mesh = self._build_grid_mesh()
        if grid_mesh.size != 0:
            mesh_groups.append((grid_mesh, self.GRID_COLOR, False))
        for tris_world, color in vm.iter_triangles(model, points3d, chain):
            if tris_world.size == 0:
                continue
            mesh_groups.append((tris_world, color, True))

        # Renderizado vectorizado del mesh y la trayectoria con orden de profundidad.
        self._render_mesh_vectorized(draw, projection, mesh_groups, trail)

        # Arcos de rango articular — encima del mesh para que sean visibles
        if points3d and chain and model.visual.get('show_joint_ranges', False):
            for line in self._collect_joint_arcs(model, points3d, chain, projection):
                draw.line(line, fill=_ARC_COLOR, width=1)

        # Esqueleto de puntos
        if model.visual.get('mode') == 'skeleton':
            self._render_skeleton(draw, points3d, model, projection)

        # Ejes locales XYZ de cada articulación
        if points3d and chain and model.visual.get('show_joint_axes', False):
            self._draw_joint_axes(draw, model, chain, projection)

        # Blit a canvas
        self._blit(canvas, img)

    def _blit(self, canvas, img):
        """Sube la imagen PIL al canvas Tkinter con un único create_image."""
        photo = ImageTk.PhotoImage(img)
        self._photo = photo
        if self._canvas_image_id is None:
            try:
                self._canvas_image_id = canvas.create_image(0, 0, anchor='nw', image=photo)
            except Exception:
                self._canvas_image_id = None
        else:
            try:
                canvas.itemconfig(self._canvas_image_id, image=photo)
            except Exception:
                try:
                    self._canvas_image_id = canvas.create_image(0, 0, anchor='nw', image=photo)
                except Exception:
                    pass

    def _build_projection_context(self, camera, w, h):
        """Precalcula la proyección de cámara compartida por todo el frame."""
        R_view, cam_pos = camera.get_view_matrix()
        projection = {
            'R_view': R_view,
            'cam_pos': cam_pos,
            'f': camera.get_focal(h),
            'cx': w / 2.0 + camera.screen_offset_x,
            'cy': h / 2.0 + camera.screen_offset_y,
            'width': w,
            'height': h,
            'mode': camera.projection_mode,
            'ortho_scale': camera.get_projection_scale(h),
            'target_depth': camera.distance,
            'cull_margin': _VIEWPORT_CULL_MARGIN,
        }
        return projection

    def _project_camera_space(self, p_cs, projection):
        """Proyecta coordenadas ya transformadas al espacio de cámara."""
        z = p_cs[2]
        if z <= 0.01:
            return None
        mode = projection.get('mode')
        if mode == 'isometrica':
            scale = projection['ortho_scale']
            sx = p_cs[0] * scale + projection['cx']
            sy = -p_cs[1] * scale + projection['cy']
            return sx, sy
        sx = (p_cs[0] / z) * projection['f'] + projection['cx']
        sy = (-p_cs[1] / z) * projection['f'] + projection['cy']
        return sx, sy

    def _project_point(self, point, projection):
        """Proyecta un punto 3D usando la cámara ya resuelta para este frame."""
        p_world = np.asarray(point, dtype=float) - projection['cam_pos']
        p_cs = projection['R_view'] @ p_world
        return self._project_camera_space(p_cs, projection)

    def _mesh_groups_to_arrays(self, mesh_groups):
        """Convierte grupos de malla en arrays contiguos para el pipeline."""
        valid_groups = [entry for entry in mesh_groups if entry[0].size != 0]
        if not valid_groups:
            return None

        total = sum(entry[0].shape[0] for entry in valid_groups)
        if total == 0:
            return None

        all_tris = np.empty((total, 3, 3), dtype=float)
        colors = np.empty((total, 3), dtype=np.uint8)
        shaded_flags = np.empty(total, dtype=bool)

        offset = 0
        for entry in valid_groups:
            tris, color = entry[0], entry[1]
            shaded = entry[2] if len(entry) >= 3 else True
            n_tris = tris.shape[0]
            end = offset + n_tris
            all_tris[offset:end] = tris
            colors[offset:end] = color
            shaded_flags[offset:end] = bool(shaded)
            offset = end

        return all_tris, colors, shaded_flags

    def _get_mesh_executor(self):
        if self._mesh_executor is None:
            self._mesh_executor = ThreadPoolExecutor(
                max_workers=self._mesh_worker_count,
                thread_name_prefix='arm3d-render',
            )
        return self._mesh_executor

    def _prepare_mesh_draw_items(self, all_tris, colors, shaded_flags, projection):
        """Prepara triangulos visibles, usando workers cuando compensa."""
        n_tris = all_tris.shape[0]
        if (
                self._mesh_worker_count <= 1
                or n_tris < self._mesh_worker_min_tris
        ):
            result = _prepare_mesh_draw_chunk(all_tris, colors, shaded_flags, projection)
            return [] if result is None else [result]

        chunk_count = min(self._mesh_worker_count, n_tris)
        chunk_size = int(math.ceil(n_tris / chunk_count))
        executor = self._get_mesh_executor()
        futures = []
        for start in range(0, n_tris, chunk_size):
            end = min(n_tris, start + chunk_size)
            futures.append(executor.submit(
                _prepare_mesh_draw_chunk,
                all_tris[start:end],
                colors[start:end],
                shaded_flags[start:end],
                projection,
            ))

        results = []
        try:
            for future in futures:
                item = future.result()
                if item is not None:
                    results.append(item)
        except Exception:
            for future in futures:
                future.cancel()
            result = _prepare_mesh_draw_chunk(all_tris, colors, shaded_flags, projection)
            return [] if result is None else [result]
        return results

    def _prepare_trail_draw_items(self, trail, projection):
        if trail is None:
            return []
        try:
            trail_len = len(trail)
        except TypeError:
            return []
        if trail_len < 2:
            return []

        points = np.asarray(trail, dtype=float)
        if points.ndim != 2 or points.shape[1] < 3:
            return []
        points = points[:, :3]
        if points.shape[0] < 2:
            return []

        r_view = projection['R_view']
        cam_pos = projection['cam_pos']
        f = projection['f']
        cx = projection['cx']
        cy = projection['cy']
        mode = projection.get('mode')
        n_points = points.shape[0]
        items = []
        segment_mm, max_pieces = self._trail_quality()
        cam_points = (points - cam_pos) @ r_view.T
        visible = cam_points[:, 2] > 0.01

        if mode == 'isometrica':
            scale = projection['ortho_scale']
            sx_all = cam_points[:, 0] * scale + cx
            sy_all = -cam_points[:, 1] * scale + cy
        else:
            z_safe = np.where(visible, cam_points[:, 2], 1.0)
            sx_all = (cam_points[:, 0] / z_safe) * f + cx
            sy_all = (-cam_points[:, 1] / z_safe) * f + cy
        projected = np.stack([sx_all, sy_all], axis=1)

        def project_camera_pair(cam0, cam1):
            if cam0[2] <= 0.01 or cam1[2] <= 0.01:
                return None
            if mode == 'isometrica':
                scale = projection['ortho_scale']
                p0 = (cam0[0] * scale + cx, -cam0[1] * scale + cy)
                p1 = (cam1[0] * scale + cx, -cam1[1] * scale + cy)
            else:
                p0 = ((cam0[0] / cam0[2]) * f + cx, (-cam0[1] / cam0[2]) * f + cy)
                p1 = ((cam1[0] / cam1[2]) * f + cx, (-cam1[1] / cam1[2]) * f + cy)
            return p0, p1

        for i in range(n_points - 1):
            p_start = points[i]
            p_end = points[i + 1]
            segment = p_end - p_start
            length = float(np.linalg.norm(segment))
            if length < 1e-9:
                continue
            pieces = max(1, min(max_pieces, int(math.ceil(length / segment_mm))))

            if pieces == 1:
                if not visible[i] or not visible[i + 1]:
                    continue
                p0 = (float(projected[i, 0]), float(projected[i, 1]))
                p1 = (float(projected[i + 1, 0]), float(projected[i + 1, 1]))

                alpha = i / max(1, n_points - 1)
                brightness = 0.25 + 0.75 * alpha
                color = (
                    min(255, int(self.TRAIL_COLOR[0] * brightness)),
                    min(255, int(self.TRAIL_COLOR[1] * brightness)),
                    min(255, int(self.TRAIL_COLOR[2] * brightness)),
                )
                width_px = 1 if brightness < 0.6 else 2
                items.append((
                    float((cam_points[i, 2] + cam_points[i + 1, 2]) * 0.5),
                    [p0, p1],
                    color,
                    width_px,
                ))
                continue

            cam_start = cam_points[i]
            cam_segment = cam_points[i + 1] - cam_start

            for piece in range(pieces):
                t0 = piece / pieces
                t1 = (piece + 1) / pieces
                cam0 = cam_start + cam_segment * t0
                cam1 = cam_start + cam_segment * t1
                pair = project_camera_pair(cam0, cam1)
                if pair is None:
                    continue
                p0, p1 = pair

                alpha = (i + t0) / max(1, n_points - 1)
                brightness = 0.25 + 0.75 * alpha
                color = (
                    min(255, int(self.TRAIL_COLOR[0] * brightness)),
                    min(255, int(self.TRAIL_COLOR[1] * brightness)),
                    min(255, int(self.TRAIL_COLOR[2] * brightness)),
                )
                width = 1 if brightness < 0.6 else 2
                items.append((
                    float((cam0[2] + cam1[2]) * 0.5),
                    [(float(p0[0]), float(p0[1])), (float(p1[0]), float(p1[1]))],
                    color,
                    width,
                ))

        return items

    def _draw_prepared_mesh(self, draw, prepared_chunks, trail_items=None):
        """Dibuja en PIL los triángulos y segmentos ya proyectados por profundidad."""
        trail_items = trail_items or []
        if not prepared_chunks and not trail_items:
            return

        pts2d = depths = rgb = mesh_order = None
        if prepared_chunks:
            pts2d = np.concatenate([chunk[0] for chunk in prepared_chunks], axis=0)
            depths = np.concatenate([chunk[1] for chunk in prepared_chunks], axis=0)
            rgb = np.concatenate([chunk[2] for chunk in prepared_chunks], axis=0)
            mesh_order = np.argsort(-depths)

        if trail_items:
            trail_items = sorted(trail_items, key=lambda item: -item[0])

        mesh_pos = 0
        trail_pos = 0
        mesh_count = 0 if mesh_order is None else len(mesh_order)
        trail_count = len(trail_items)

        while mesh_pos < mesh_count or trail_pos < trail_count:
            if trail_pos < trail_count:
                trail_depth = trail_items[trail_pos][0]
            else:
                trail_depth = None

            if mesh_pos < mesh_count:
                mesh_idx = mesh_order[mesh_pos]
                mesh_depth = depths[mesh_idx]
            else:
                mesh_idx = None
                mesh_depth = None

            if trail_depth is not None and (mesh_depth is None or trail_depth > mesh_depth):
                self._draw_trail_item(draw, trail_items[trail_pos])
                trail_pos += 1
            else:
                self._draw_mesh_item(draw, pts2d[mesh_idx], rgb[mesh_idx])
                mesh_pos += 1

    @staticmethod
    def _draw_mesh_item(draw, pts, color):
        try:
            draw.polygon(
                [pts[0, 0], pts[0, 1], pts[1, 0], pts[1, 1], pts[2, 0], pts[2, 1]],
                fill=(int(color[0]), int(color[1]), int(color[2])),
            )
        except Exception:
            pass

    @staticmethod
    def _draw_trail_item(draw, item):
        try:
            _depth, points, color, width = item
            draw.line(points, fill=color, width=width)
        except Exception:
            pass

    def _render_mesh_vectorized(self, draw, projection, mesh_groups, trail=None):
        """
        Pipeline de renderizado vectorizado con NumPy.

        Recibe mesh_groups = lista de (np.array (N,3,3), color_rgb[, shaded]).
        Proyecta todos los vértices de una vez, calcula normales y shading
        en bulk, aplica back-face culling y ordena por profundidad (painter's)
        antes de llamar a draw.polygon — eliminando los bucles Python por vértice.
        """
        has_trail = trail is not None and len(trail) >= 2
        if not mesh_groups and not has_trail:
            return

        prepared = []
        if mesh_groups:
            arrays = self._mesh_groups_to_arrays(mesh_groups)
            if arrays is not None:
                all_tris, colors, shaded_flags = arrays
                prepared = self._prepare_mesh_draw_items(
                    all_tris, colors, shaded_flags, projection
                )

        trail_items = self._prepare_trail_draw_items(trail, projection)
        self._draw_prepared_mesh(draw, prepared, trail_items)

    def _render_mesh(self, draw, camera, all_tris, w, h):
        """Wrapper de compatibilidad — redirige al pipeline vectorizado."""
        if not all_tris:
            return
        # Agrupar la lista legacy (tri, color[, shaded]) en el formato que espera el pipeline
        groups = {}
        order = []
        for entry in all_tris:
            if len(entry) >= 3:
                tri, color, shaded = entry[0], entry[1], entry[2]
            else:
                tri, color = entry
                shaded = True
            key = color
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append((tri, shaded))
        mesh_groups = []
        for key in order:
            arr = np.array([tri for tri, _shaded in groups[key]])
            shaded = groups[key][0][1]
            mesh_groups.append((arr, key, shaded))
        projection = self._build_projection_context(camera, w, h)
        self._render_mesh_vectorized(draw, projection, mesh_groups)

    def _render_skeleton(self, draw, points3d, model, projection):
        """Renderizado simplificado con líneas y círculos."""
        if not points3d or len(points3d) < 2:
            return
        prev = None
        for i, p in enumerate(points3d):
            proj = self._project_point(p, projection)
            if proj is None:
                prev = None
                continue
            if prev is not None:
                draw.line([prev, proj], fill=(200, 200, 200), width=3)
            r = 6 if i > 0 else 10
            color = (220, 80, 30) if model.is_at_limit(i - 1) and i > 0 else (60, 180, 220)
            draw.ellipse([proj[0] - r, proj[1] - r, proj[0] + r, proj[1] + r], fill=color)
            prev = proj

    def _build_grid_segment_mesh(self, start, end):
        """Convierte un segmento del suelo en una tira 3D de dos caras."""
        p0 = np.asarray(start, dtype=float)
        p1 = np.asarray(end, dtype=float)
        direction = p1 - p0
        length = np.linalg.norm(direction[:2])
        if length < 1e-9:
            return np.empty((0, 3, 3), dtype=float)

        side = np.array([-direction[1], direction[0], 0.0], dtype=float)
        side_norm = np.linalg.norm(side[:2])
        if side_norm < 1e-9:
            return np.empty((0, 3, 3), dtype=float)
        side = side / side_norm * self.GRID_HALF_WIDTH

        c0 = p0 + side
        c1 = p0 - side
        c2 = p1 - side
        c3 = p1 + side

        front = np.array([
            [c0, c1, c2],
            [c0, c2, c3],
        ], dtype=float)
        back = front[:, ::-1, :]
        return np.concatenate([front, back], axis=0)

    def _build_grid_mesh(self):
        """Construye la rejilla del suelo como pequeños segmentos 3D ordenables por profundidad."""
        if self._grid_mesh_cache is not None:
            return self._grid_mesh_cache

        size = self.GRID_SIZE
        step = self.GRID_STEP
        z = self.GRID_Z_OFFSET
        tris = []

        x_values = np.arange(-size, size + step, step, dtype=float)
        y_values = np.arange(-size, size + step, step, dtype=float)

        for x in x_values:
            for y0, y1 in zip(y_values[:-1], y_values[1:]):
                seg = self._build_grid_segment_mesh(
                    [x, y0, z],
                    [x, y1, z],
                )
                if seg.size != 0:
                    tris.append(seg)

        for y in y_values:
            for x0, x1 in zip(x_values[:-1], x_values[1:]):
                seg = self._build_grid_segment_mesh(
                    [x0, y, z],
                    [x1, y, z],
                )
                if seg.size != 0:
                    tris.append(seg)

        if not tris:
            self._grid_mesh_cache = np.empty((0, 3, 3), dtype=float)
        else:
            self._grid_mesh_cache = np.concatenate(tris, axis=0)
        return self._grid_mesh_cache

    def _draw_grid(self, draw, projection):
        """Dibuja la rejilla del plano Z=0."""
        size = 400
        step = 100
        color = self.GRID_COLOR
        for x in range(-size, size + step, step):
            p0 = self._project_point([float(x), float(-size), 0.0], projection)
            p1 = self._project_point([float(x), float(size), 0.0], projection)
            if p0 and p1:
                draw.line([p0, p1], fill=color, width=1)
        for y in range(-size, size + step, step):
            p0 = self._project_point([float(-size), float(y), 0.0], projection)
            p1 = self._project_point([float(size), float(y), 0.0], projection)
            if p0 and p1:
                draw.line([p0, p1], fill=color, width=1)

    def _draw_axes(self, draw, projection):
        """Dibuja los ejes de coordenadas XYZ con etiquetas."""
        origin = [0.0, 0.0, 0.0]
        length = 120.0
        axes = {
            'x': ([length, 0.0, 0.0], self.AXIS_COLORS['x']),
            'y': ([0.0, length, 0.0], self.AXIS_COLORS['y']),
            'z': ([0.0, 0.0, length], self.AXIS_COLORS['z']),
        }
        p0 = self._project_point(origin, projection)
        if p0 is None:
            return
        for label, (end, color) in axes.items():
            p1 = self._project_point(end, projection)
            if p1:
                draw.line([p0, p1], fill=color, width=2)
                try:
                    draw.text((p1[0] + 3, p1[1] - 8), label.upper(), fill=color)
                except Exception:
                    pass

    def _draw_trail(self, draw, trail, projection):
        """Dibuja la trayectoria del efector final.

        Proyecta cada punto 3D al espacio pantalla.  El segmento entre un punto
        que proyecta y el siguiente que NO proyecta (detrás de la cámara) se
        descarta, evitando líneas erróneas que cruzan la pantalla.

        El color varía de teal tenue (puntos más antiguos) a teal brillante
        (puntos más recientes).  Se usa un mínimo de brillo del 25 % para que
        los puntos antiguos siempre sean visibles.
        """
        if not trail or len(trail) < 2:
            return

        # Proyectar con índice original para respetar la continuidad
        projected = []  # lista de (screen_xy | None)
        for p in trail:
            projected.append(self._project_point(p, projection))

        n = len(projected)
        for i in range(n - 1):
            p0 = projected[i]
            p1 = projected[i + 1]
            # Descartar segmentos con algún extremo detrás de la cámara
            if p0 is None or p1 is None:
                continue
            # alpha = 0 → punto más antiguo, alpha = 1 → punto más reciente
            alpha = i / max(1, n - 1)
            brightness = 0.25 + 0.75 * alpha
            r = min(255, int(self.TRAIL_COLOR[0] * brightness))
            g = min(255, int(self.TRAIL_COLOR[1] * brightness))
            b = min(255, int(self.TRAIL_COLOR[2] * brightness))
            width = 1 if brightness < 0.6 else 2
            try:
                draw.line([p0, p1], fill=(r, g, b), width=width)
            except Exception:
                pass

    def _resolve_joint_basis(self, frame):
        """Construye una base ortonormal local (X, Y, Z) a partir del frame articular."""
        center = np.asarray(frame['pos'], dtype=float)
        axis = np.asarray(frame['axis'], dtype=float)
        u_raw = np.asarray(frame['xref'], dtype=float)

        axis_n = np.linalg.norm(axis)
        if axis_n < 1e-9:
            return None
        axis = axis / axis_n

        u_raw = u_raw - np.dot(u_raw, axis) * axis
        u_n = np.linalg.norm(u_raw)
        if u_n < 1e-9:
            return None
        u = u_raw / u_n

        v_raw = np.cross(axis, u)
        v_n = np.linalg.norm(v_raw)
        if v_n < 1e-9:
            return None
        v = v_raw / v_n
        u = np.cross(v, axis)

        return center, axis, u, v

    @staticmethod
    def _rotate_vector_about_axis(vector, axis, angle):
        vec = np.asarray(vector, dtype=float)
        ax = np.asarray(axis, dtype=float)
        ax_n = np.linalg.norm(ax)
        if ax_n < 1e-9:
            return vec
        ax = ax / ax_n
        c = math.cos(angle)
        s = math.sin(angle)
        return (
            vec * c
            + np.cross(ax, vec) * s
            + ax * np.dot(ax, vec) * (1.0 - c)
        )

    @staticmethod
    def _joint_arc_anchor_direction(frames, joint_idx, center, axis):
        for candidate in frames[joint_idx + 1:]:
            try:
                delta = np.asarray(candidate['pos'], dtype=float) - center
            except Exception:
                continue
            planar = delta - axis * np.dot(delta, axis)
            planar_n = np.linalg.norm(planar)
            if planar_n > 1e-6:
                return planar / planar_n
        return None

    def _draw_joint_axes(self, draw, model, chain, projection):
        """Dibuja los ejes XYZ locales de cada articulación usando sus frames renderizados."""
        vm = self.resolve_visual_model(model)
        frames = vm.get_joint_frames(model, chain)

        for frame in frames[:model.dof]:
            basis = self._resolve_joint_basis(frame)
            if basis is None:
                continue

            center, axis_z, axis_x, axis_y = basis
            p0 = self._project_point(center.tolist(), projection)
            if p0 is None:
                continue

            axis_len = float(np.clip(frame.get('r_arc', 40.0) * 0.65, 24.0, 72.0))
            axes = (
                (axis_x, self.AXIS_COLORS['x']),
                (axis_y, self.AXIS_COLORS['y']),
                (axis_z, self.AXIS_COLORS['z']),
            )
            for axis_dir, color in axes:
                p1 = self._project_point((center + axis_len * axis_dir).tolist(), projection)
                if p1 is None:
                    continue
                try:
                    draw.line([p0, p1], fill=color, width=2)
                except Exception:
                    pass

    @staticmethod
    def _interp_servo_calibration(points, value):
        """Interpola linealmente digital→real sobre los puntos de calibración,
        recortando (clamp) a los extremos fuera del rango muestreado."""
        ordered = sorted((float(x), float(y)) for x, y in points)
        if not ordered:
            return None
        if value <= ordered[0][0]:
            return ordered[0][1]
        if value >= ordered[-1][0]:
            return ordered[-1][1]
        for (x0, y0), (x1, y1) in zip(ordered, ordered[1:]):
            if x0 <= value <= x1:
                if x1 == x0:
                    return y1
                return y0 + (y1 - y0) * (value - x0) / (x1 - x0)
        return ordered[-1][1]

    def _servo_reachable_joint_range(self, model, joint_idx):
        return model.effective_joint_limits(joint_idx)

    def _collect_joint_arcs(self, model, points3d, chain, projection):
        """Retorna lista de segmentos 2D que representan los arcos de rango articular.

        Delega la obtención de las posiciones y ejes articulares al modelo visual
        activo (vm.get_joint_frames), de modo que los arcos coincidan con el
        modelo 3D renderizado — tanto para el Braccio exacto (URDF) como para
        el modelo genérico DH.

        Para cada articulación rotacional i:
          - center = pivote en coordenadas mundo (del modelo visual)
          - axis   = eje de rotación en coordenadas mundo
          - ref    = dirección actual de la primera geometría hija separada
                     del eje, o la referencia local si no hay geometría hija
          - Segmentos de arco [mn, mx] grados + líneas radiales.
        """
        lines = []
        vm = self.resolve_visual_model(model)
        frames = vm.get_joint_frames(model, chain)

        for i in range(model.dof):
            if model.joint_types[i] != 'R':
                continue
            if i >= len(frames):
                continue

            frame = frames[i]
            basis = self._resolve_joint_basis(frame)
            if basis is None:
                continue
            center, axis, u, _v = basis

            # Normalizar eje
            axis_n = np.linalg.norm(axis)
            if axis_n < 1e-9:
                continue
            axis = axis / axis_n

            # Por defecto el arco barre el rango articular [mn, mx]. Si el frame
            # define 'arc_angles' (p. ej. la pinza, que barre su apertura desde
            # la referencia 'forward'), se usan esos ángulos locales.
            mn, mx = frame.get('arc_angles', self._servo_reachable_joint_range(model, i))
            r_arc = frame['r_arc']
            ref_dir = self._joint_arc_anchor_direction(frames, i, center, axis)
            current_angle = float(frame.get('arc_current_angle', model.joints[i]))
            if ref_dir is None:
                ref_dir = u
                current_angle = 0.0

            # Puntos del arco con índice original (para descartar saltos si algún punto
            # queda detrás de la cámara sin crear segmentos erróneos que cruzan la pantalla)
            projected = []
            arc_steps = self._active_arc_steps()
            for k in range(arc_steps + 1):
                angle_deg = mn + (mx - mn) * k / arc_steps
                arc_dir = self._rotate_vector_about_axis(
                    ref_dir, axis, math.radians(angle_deg - current_angle))
                p3d = [
                    center[0] + r_arc * arc_dir[0],
                    center[1] + r_arc * arc_dir[1],
                    center[2] + r_arc * arc_dir[2],
                ]
                projected.append(self._project_point(p3d, projection))

            for k in range(len(projected) - 1):
                p0 = projected[k]
                p1 = projected[k + 1]
                if p0 is not None and p1 is not None:
                    lines.append([p0, p1])

            # Líneas radiales del centro al inicio y fin del arco
            c_proj = self._project_point(list(center), projection)
            if c_proj:
                if projected[0] is not None:
                    lines.append([c_proj, projected[0]])
                if projected[-1] is not None:
                    lines.append([c_proj, projected[-1]])

        return lines
