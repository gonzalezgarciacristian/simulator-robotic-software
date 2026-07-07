"""
Cinematica Inversa (Inverse Kinematics) con multiarranque y mejor-solucion.

El solver sigue trabajando con unidades internas mixtas:
  - juntas R en radianes
  - juntas P en milimetros

Mejoras respecto a la version basica:
  - conserva la mejor pose encontrada aunque no converja del todo
  - prueba varias semillas internas para escapar de configuraciones singulares
  - usa busqueda en linea simple para no aceptar pasos que empeoren el error
  - refina internamente hasta una tolerancia pequena para evitar que la UI
    se quede en soluciones "aceptables" pero visualmente pobres
"""
import math

from motor3d.kinematics.constraints_limits import clamp_model_joints
from motor3d.kinematics.kinematics_fk import (
    forward_kinematics_chain,
    get_base_transform,
    get_joint_axis_world,
)

_RAD_TO_DEG = 180.0 / math.pi
_DEG_TO_RAD = math.pi / 180.0
_COL_EPS = 1e-9
_IMPROVEMENT_EPS = 1e-6
_INTERNAL_REFINEMENT_TOL_MM = 5.0
_LINE_SEARCH_SCALES = (1.0, 0.5, 0.25, 0.1)


def _position_jacobian_native(model, chain):
    """
    Jacobiano posicional expresado en las unidades internas del solver.

    Para juntas R:
        d p / d q(rad) = z x (p_ee - p_joint)

    Para juntas P:
        d p / d q(mm) = z
    donde z es el eje local de la articulacion en coordenadas del mundo.
    """
    matrices = chain.get('matrices', [])
    positions = chain.get('positions', [])
    ee = chain.get('end_effector', [0.0, 0.0, 0.0])
    base_T = get_base_transform(model)
    J = []

    for i in range(model.dof):
        T_prev = matrices[i - 1] if i > 0 else base_T
        axis = get_joint_axis_world(model, i, T_prev)

        if model.joint_types[i] == 'P':
            J.append(axis)
            continue

        joint_pos = positions[i] if i < len(positions) else [0.0, 0.0, 0.0]
        rx = float(ee[0]) - float(joint_pos[0])
        ry = float(ee[1]) - float(joint_pos[1])
        rz = float(ee[2]) - float(joint_pos[2])

        J.append([
            axis[1] * rz - axis[2] * ry,
            axis[2] * rx - axis[0] * rz,
            axis[0] * ry - axis[1] * rx,
        ])

    return J


def _max_step_native(jtype, limits):
    """Cota suave por iteracion para evitar saltos grandes e inestables."""
    mn, mx = float(limits[0]), float(limits[1])
    span = abs(mx - mn)
    if jtype == 'P':
        return max(5.0, min(40.0, span * 0.25 if span > 0.0 else 10.0))
    return math.radians(max(2.0, min(15.0, span * 0.25 if span > 0.0 else 5.0)))


def _to_internal_joint(value, jtype):
    return float(value) if jtype == 'P' else math.radians(float(value))


def _from_internal_joint(value, jtype):
    return float(value) if jtype == 'P' else float(value) * _RAD_TO_DEG


def _apply_internal_joints(model, joints_internal, types):
    model.joints[:] = [
        _from_internal_joint(q, jtype)
        for q, jtype in zip(joints_internal, types)
    ]


def _current_internal_state(model, limits, types):
    joints_internal = []
    limits_internal = []
    for q, (mn, mx), jtype in zip(model.joints, limits, types):
        joints_internal.append(_to_internal_joint(q, jtype))
        limits_internal.append((
            _to_internal_joint(mn, jtype),
            _to_internal_joint(mx, jtype),
        ))
    return joints_internal, limits_internal


def _clamp_internal_state(joints_internal, limits_internal):
    clamped = []
    for q, (mn, mx) in zip(joints_internal, limits_internal):
        clamped.append(max(mn, min(mx, float(q))))
    return clamped


def _neutral_internal_value(limit_pair):
    mn, mx = float(limit_pair[0]), float(limit_pair[1])
    if mn <= 0.0 <= mx:
        return 0.0
    return 0.5 * (mn + mx)


def model_last_revolute_index(types):
    for idx in range(len(types) - 1, -1, -1):
        if types[idx] == 'R':
            return idx
    return -1


def _build_seed_states(joints_internal, limits_internal, types):
    """
    Genera varias semillas internas para evitar quedar atrapado en poses singulares.

    Se prioriza:
      1. pose actual
      2. pose neutra (0 o centro del rango)
      3. centro exacto de limites
      4. dos poses "plegadas" simetricas para sacar al brazo de ejes degenerados
    """
    seeds = []

    def _add(seed):
        seed = tuple(round(float(v), 9) for v in _clamp_internal_state(seed, limits_internal))
        if seed not in seeds:
            seeds.append(seed)

    current = list(joints_internal)
    neutral = [_neutral_internal_value(lim) for lim in limits_internal]
    mid = [0.5 * (lim[0] + lim[1]) for lim in limits_internal]

    _add(current)
    _add(neutral)
    _add(mid)

    folded_a = []
    folded_b = []
    current_fold_a = []
    current_fold_b = []
    for i, ((mn, mx), jtype) in enumerate(zip(limits_internal, types)):
        base = neutral[i]
        span = abs(mx - mn)
        if jtype == 'P':
            delta = max(10.0, min(40.0, span * 0.15 if span > 0.0 else 10.0))
        else:
            span_deg = abs(span * _RAD_TO_DEG)
            delta_deg = max(8.0, min(20.0, span_deg * 0.12 if span_deg > 0.0 else 10.0))
            delta = delta_deg * _DEG_TO_RAD

        if i == 0:
            sign = 0.0
        elif i == 1:
            sign = -1.0
        elif i in (2, 3):
            sign = 1.0
        elif i == 4:
            sign = 0.5
        else:
            sign = 0.0

        folded_a.append(base + sign * delta)
        folded_b.append(base - sign * delta)

        current_base = joints_internal[i]
        current_sign = sign
        if i == model_last_revolute_index(types):
            current_sign = 0.0
        current_fold_a.append(current_base + current_sign * delta)
        current_fold_b.append(current_base - current_sign * delta)

    _add(folded_a)
    _add(folded_b)
    _add(current_fold_a)
    _add(current_fold_b)
    return [list(seed) for seed in seeds]


def _evaluate_state(model, target, joints_internal, types):
    _apply_internal_joints(model, joints_internal, types)
    chain = forward_kinematics_chain(model)
    ee = chain['end_effector']
    ex = float(target[0]) - float(ee[0])
    ey = float(target[1]) - float(ee[1])
    ez = float(target[2]) - float(ee[2])
    error = math.sqrt(ex ** 2 + ey ** 2 + ez ** 2)
    return chain, (ex, ey, ez), error


def _solve_from_seed(model, target, seed_internal, limits, limits_internal, types,
                     max_iter, tolerance, alpha, max_reach):
    joints_internal = _clamp_internal_state(seed_internal, limits_internal)
    stop_tolerance = min(float(tolerance), _INTERNAL_REFINEMENT_TOL_MM)
    rot_norm_scale = alpha / (max_reach ** 2 + 1e-6)

    chain, error_vec, error = _evaluate_state(model, target, joints_internal, types)
    best_error = error
    best_joints = list(joints_internal)

    for _ in range(max_iter):
        if error + _IMPROVEMENT_EPS < best_error:
            best_error = error
            best_joints = list(joints_internal)

        if error <= stop_tolerance:
            break

        J = _position_jacobian_native(model, chain)
        deltas = [0.0] * model.dof

        for i in range(model.dof):
            col = J[i]
            grad = col[0] * error_vec[0] + col[1] * error_vec[1] + col[2] * error_vec[2]
            if types[i] == 'P':
                col_norm_sq = col[0] * col[0] + col[1] * col[1] + col[2] * col[2]
                if col_norm_sq <= _COL_EPS:
                    continue
                step = alpha * grad / (col_norm_sq + _COL_EPS)
            else:
                step = rot_norm_scale * grad

            max_step = _max_step_native(types[i], limits[i])
            deltas[i] = max(-max_step, min(max_step, step))

        if max(abs(delta) for delta in deltas) <= 1e-9:
            break

        accepted = False
        best_candidate = None

        for scale in _LINE_SEARCH_SCALES:
            candidate = [
                joints_internal[i] + deltas[i] * scale
                for i in range(model.dof)
            ]
            candidate = _clamp_internal_state(candidate, limits_internal)
            cand_chain, cand_error_vec, cand_error = _evaluate_state(model, target, candidate, types)

            if best_candidate is None or cand_error < best_candidate[3]:
                best_candidate = (candidate, cand_chain, cand_error_vec, cand_error)

            if cand_error + _IMPROVEMENT_EPS < error:
                joints_internal = candidate
                chain = cand_chain
                error_vec = cand_error_vec
                error = cand_error
                accepted = True
                break

        if not accepted:
            if best_candidate is not None and best_candidate[3] + _IMPROVEMENT_EPS < best_error:
                joints_internal, chain, error_vec, error = best_candidate
                if error + _IMPROVEMENT_EPS < best_error:
                    best_error = error
                    best_joints = list(joints_internal)
            break

    _apply_internal_joints(model, best_joints, types)
    clamp_model_joints(model)
    chain = forward_kinematics_chain(model)
    ee = chain['end_effector']
    final_error = math.sqrt(
        (float(ee[0]) - float(target[0])) ** 2
        + (float(ee[1]) - float(target[1])) ** 2
        + (float(ee[2]) - float(target[2])) ** 2
    )
    return best_joints, final_error


def solve_inverse_kinematics(model, target, max_iter=150, tolerance=25.0, alpha=0.65):
    """
    Calcula los angulos/desplazamientos articulares para alcanzar la posicion objetivo.

    Caracteristicas:
      - trabaja con unidades internas mixtas (rad/mm)
      - busca una solucion precisa dentro de una sola llamada
      - si el objetivo no es alcanzable, deja aplicada la mejor aproximacion hallada

    Args:
        model     : ArmKinematicState - se modifica in-place con la mejor pose encontrada.
        target    : [x, y, z] - posicion objetivo del efector final (mm).
        max_iter  : numero maximo de iteraciones por semilla.
        tolerance : error aceptable en mm.
        alpha     : tasa de aprendizaje adimensional.

    Returns:
        (converged: bool, final_error: float)
    """
    tx, ty, tz = float(target[0]), float(target[1]), float(target[2])
    target = (tx, ty, tz)

    dof = model.dof
    limits = [model.effective_joint_limits(i) for i in range(dof)]
    types = model.joint_types
    joints_internal, limits_internal = _current_internal_state(model, limits, types)
    max_reach = max(1.0, float(model.max_reach()))

    seed_states = _build_seed_states(joints_internal, limits_internal, types)

    best_global_error = float('inf')
    best_global_joints = list(joints_internal)

    for seed in seed_states:
        seed_best_joints, seed_error = _solve_from_seed(
            model,
            target,
            seed,
            limits,
            limits_internal,
            types,
            max_iter=max_iter,
            tolerance=tolerance,
            alpha=alpha,
            max_reach=max_reach,
        )
        if seed_error + _IMPROVEMENT_EPS < best_global_error:
            best_global_error = seed_error
            best_global_joints = list(seed_best_joints)

    _apply_internal_joints(model, best_global_joints, types)
    clamp_model_joints(model)
    chain = forward_kinematics_chain(model)
    ee = chain['end_effector']
    final_err = math.sqrt(
        (float(ee[0]) - tx) ** 2
        + (float(ee[1]) - ty) ** 2
        + (float(ee[2]) - tz) ** 2
    )
    return final_err <= tolerance, final_err
