"""
Cinemática Directa (Forward Kinematics) mediante parametrización Denavit-Hartenberg.

Convención clásica DH:
    Articulación R: T_i = Rz(theta_i + q_i) * Tz(d_i)   * Tx(a_i) * Rx(alpha_i)
    Articulación P: T_i = Rz(theta_i)       * Tz(d_i+qi) * Tx(a_i) * Rx(alpha_i)
"""
import math
import numpy as np

_AXIS_EPS = 1e-9


def get_base_transform(model):
    """Retorna la transformacion fija del joint 0 implicito de la base."""
    base = getattr(model, 'base_row', None)
    if isinstance(base, dict):
        theta = math.radians(float(base.get('theta', 0.0)))
        d = float(base.get('d', 0.0))
        a = float(base.get('a', 0.0))
        alpha = math.radians(float(base.get('alpha', 0.0)))
        return _dh_transform(theta, d, a, alpha)

    raw_rpy = getattr(model, 'base_rpy', [0.0, 0.0, 0.0]) or [0.0, 0.0, 0.0]
    roll = math.radians(float(raw_rpy[0]) if len(raw_rpy) > 0 else 0.0)
    pitch = math.radians(float(raw_rpy[1]) if len(raw_rpy) > 1 else 0.0)
    yaw = math.radians(float(raw_rpy[2]) if len(raw_rpy) > 2 else 0.0)

    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)

    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, cr, -sr],
        [0.0, sr, cr],
    ], dtype=float)
    Ry = np.array([
        [cp, 0.0, sp],
        [0.0, 1.0, 0.0],
        [-sp, 0.0, cp],
    ], dtype=float)
    Rz = np.array([
        [cy, -sy, 0.0],
        [sy, cy, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=float)

    T = np.eye(4, dtype=float)
    T[:3, :3] = Rz @ Ry @ Rx
    return T


def get_prismatic_pre_rotation(model, joint_idx):
    rotations = getattr(model, 'prismatic_pre_rotations', None) or []
    if 0 <= joint_idx < len(rotations):
        item = rotations[joint_idx]
        if isinstance(item, dict):
            return {
                'yaw': float(item.get('yaw', 0.0)),
                'pitch': float(item.get('pitch', 0.0)),
            }
    return {'yaw': 0.0, 'pitch': 0.0}


def get_prismatic_axis_local(model, joint_idx):
    orient = get_prismatic_pre_rotation(model, joint_idx)
    yaw = math.radians(orient['yaw'])
    pitch = math.radians(orient['pitch'])
    axis = _rotation_z_transform(yaw) @ _rotation_y_transform(pitch) @ np.array([0.0, 0.0, 1.0, 0.0])
    return _normalize_vector(axis[:3].tolist())


def get_joint_axis_world(model, joint_idx, T_prev):
    if joint_idx < len(model.joint_types) and model.joint_types[joint_idx] == 'P':
        axis_local = np.array(get_prismatic_axis_local(model, joint_idx), dtype=float)
        axis_world = T_prev[:3, :3] @ axis_local
        return _normalize_vector(axis_world.tolist())

    return _normalize_vector([
        float(T_prev[0, 2]),
        float(T_prev[1, 2]),
        float(T_prev[2, 2]),
    ])


def forward_kinematics_chain(model):
    """
    Calcula la cadena cinemática completa.

    Args:
        model: ArmKinematicState con los parámetros DH y ángulos articulares.

    Returns:
        Dict con:
            'matrices'    — lista de matrices 4x4 acumuladas (una por articulación)
            'positions'   — lista de [x, y, z] del origen de cada articulación
            'end_effector'— [x, y, z] del efector final DH
    """
    T = get_base_transform(model)
    matrices = []
    positions = [[float(T[0, 3]), float(T[1, 3]), float(T[2, 3])]]

    for i in range(model.dof):
        row = model.dh_rows[i]
        jtype = model.joint_types[i] if i < len(model.joint_types) else 'R'
        theta = math.radians(float(row.get('theta', 0.0)))
        d = float(row.get('d', 0.0))
        a = float(row.get('a', 0.0))
        alpha = math.radians(float(row.get('alpha', 0.0)))

        if jtype == 'P':
            orient = get_prismatic_pre_rotation(model, i)
            q = float(model.joints[i])
            Ti = _rotation_z_transform(math.radians(orient['yaw']))
            Ti = Ti @ _rotation_y_transform(math.radians(orient['pitch']))
            Ti = Ti @ _translation_transform(0.0, 0.0, q)
            Ti = Ti @ _dh_transform(theta, d, a, alpha)
        else:
            q = math.radians(model.joints[i])
            Ti = _dh_transform(theta + q, d, a, alpha)
        T = T @ Ti
        matrices.append(T.copy())
        positions.append([float(T[0, 3]), float(T[1, 3]), float(T[2, 3])])

    end_effector = [float(T[0, 3]), float(T[1, 3]), float(T[2, 3])]

    return {
        'matrices': matrices,
        'positions': positions,
        'end_effector': end_effector,
    }


def _dh_transform(theta, d, a, alpha):
    """
    Calcula la matriz de transformación DH para un eslabón.

    T = Rz(theta) * Tz(d) * Tx(a) * Rx(alpha)

    Resultado explícito:
        [cos(θ), -sin(θ)*cos(α),  sin(θ)*sin(α),  a*cos(θ)]
        [sin(θ),  cos(θ)*cos(α), -cos(θ)*sin(α),  a*sin(θ)]
        [0,       sin(α),         cos(α),           d      ]
        [0,       0,              0,                1      ]
    """
    ct = math.cos(theta)
    st = math.sin(theta)
    ca = math.cos(alpha)
    sa = math.sin(alpha)
    return np.array([
        [ct, -st * ca,  st * sa, a * ct],
        [st,  ct * ca, -ct * sa, a * st],
        [0.0, sa,       ca,      d     ],
        [0.0, 0.0,      0.0,     1.0   ]
    ], dtype=float)


def _translation_transform(tx, ty, tz):
    return np.array([
        [1.0, 0.0, 0.0, float(tx)],
        [0.0, 1.0, 0.0, float(ty)],
        [0.0, 0.0, 1.0, float(tz)],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=float)


def _rotation_z_transform(angle):
    ca = math.cos(angle)
    sa = math.sin(angle)
    return np.array([
        [ca, -sa, 0.0, 0.0],
        [sa,  ca, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=float)


def _rotation_y_transform(angle):
    ca = math.cos(angle)
    sa = math.sin(angle)
    return np.array([
        [ca,  0.0, sa, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [-sa, 0.0, ca, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ], dtype=float)


def _normalize_vector(vec, fallback=None):
    values = []
    for idx in range(3):
        try:
            values.append(float(vec[idx]))
        except (IndexError, TypeError, ValueError):
            values.append(0.0)

    norm = math.sqrt(sum(value * value for value in values))
    if norm <= _AXIS_EPS:
        base = fallback or [0.0, 0.0, 1.0]
        return [float(base[0]), float(base[1]), float(base[2])]

    return [value / norm for value in values]
