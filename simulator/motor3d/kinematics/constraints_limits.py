"""
Restricciones y límites articulares.
"""


def clamp_model_joints(model):
    """
    Restringe todos los ángulos articulares a los rangos permitidos definidos
    en model.joint_limits, modificando model.joints in-place.
    """
    for i in range(model.dof):
        mn, mx = model.effective_joint_limits(i)
        model.joints[i] = max(mn, min(mx, model.joints[i]))
