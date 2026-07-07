"""
Funciones de comprobacion de workspace y singularidades.
"""
import math

import numpy as np

from motor3d.kinematics.kinematics_fk import (
    forward_kinematics_chain,
    get_base_transform,
    get_joint_axis_world,
)

_SINGULAR_CONDITION_LIMIT = 1000.0
_SINGULAR_VALUE_EPS = 1.0


def in_workspace(points, max_reach):
    """
    Verifica si la posicion del efector final esta dentro del workspace del robot.

    Args:
        points   : lista de [x, y, z] de las articulaciones (posiciones FK).
        max_reach: alcance maximo del brazo en mm.

    Returns:
        True si la posicion es alcanzable, False si esta fuera del workspace.
    """
    if not points or len(points) < 2:
        return True

    end = points[-1]
    dist = math.sqrt(end[0] ** 2 + end[1] ** 2 + end[2] ** 2)
    return dist <= max_reach * 1.05


def near_singularity(points, model=None, threshold=5.0):
    """
    Detecta si la cadena cinematica esta cerca de una configuracion singular.

    Si se proporciona el modelo, usa el rango del Jacobiano de posicion del
    efector. Esta senal es mas representativa que la alineacion visual de
    eslabones, que en el Braccio aparece en muchas poses normales.

    Args:
        points   : lista de [x, y, z] de los origenes articulares (posiciones FK).
        model    : estado cinematico opcional para evaluar el Jacobiano.
        threshold: umbral en grados usado solo como fallback geometrico.

    Returns:
        True si se detecta singularidad, False si no.
    """
    if model is not None:
        return _near_singularity_by_jacobian(model)

    if len(points) < 3:
        return False

    threshold_rad = math.radians(threshold)

    for i in range(len(points) - 2):
        p0 = points[i]
        p1 = points[i + 1]
        p2 = points[i + 2]

        v1 = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]]
        v2 = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]

        n1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2)
        n2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2 + v2[2] ** 2)

        if n1 < 1e-6 or n2 < 1e-6:
            continue

        dot = (v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]) / (n1 * n2)
        dot = max(-1.0, min(1.0, dot))
        angle = math.acos(abs(dot))

        if angle < threshold_rad:
            return True

    return False


def _near_singularity_by_jacobian(model):
    chain = forward_kinematics_chain(model)
    jacobian = np.array(_position_jacobian(model, chain), dtype=float).T
    if jacobian.size == 0:
        return False

    expected_rank = min(3, int(getattr(model, 'dof', 0)))
    if expected_rank <= 0:
        return False

    singular_values = np.linalg.svd(jacobian, compute_uv=False)
    if len(singular_values) < expected_rank:
        return True

    relevant_values = singular_values[:expected_rank]
    min_singular_value = float(relevant_values[-1])
    max_singular_value = float(relevant_values[0])
    if min_singular_value < _SINGULAR_VALUE_EPS:
        return True
    return max_singular_value / min_singular_value > _SINGULAR_CONDITION_LIMIT


def _position_jacobian(model, chain):
    matrices = chain.get('matrices', [])
    positions = chain.get('positions', [])
    ee = chain.get('end_effector', [0.0, 0.0, 0.0])
    base_transform = get_base_transform(model)
    jacobian = []

    for i in range(model.dof):
        transform = matrices[i - 1] if i > 0 else base_transform
        axis = get_joint_axis_world(model, i, transform)

        if model.joint_types[i] == 'P':
            jacobian.append(axis)
            continue

        joint_pos = positions[i] if i < len(positions) else [0.0, 0.0, 0.0]
        rx = float(ee[0]) - float(joint_pos[0])
        ry = float(ee[1]) - float(joint_pos[1])
        rz = float(ee[2]) - float(joint_pos[2])

        jacobian.append([
            axis[1] * rz - axis[2] * ry,
            axis[2] * rx - axis[0] * rz,
            axis[0] * ry - axis[1] * rx,
        ])

    return jacobian
