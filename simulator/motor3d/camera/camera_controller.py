"""
CameraController — Traduce eventos de entrada (ratón/teclado) en movimientos de cámara.
"""
import math


class CameraController:

    ROTATION_SENSITIVITY = 0.35  # grados por píxel
    DOLLY_SENSITIVITY = 0.012

    def __init__(self, camera):
        self._camera = camera

    def rotate_drag(self, dx, dy):
        """Actualiza yaw y pitch según el arrastre del ratón."""
        self._camera.yaw = (self._camera.yaw + dx * self.ROTATION_SENSITIVITY) % 360.0
        new_pitch = self._camera.pitch - dy * self.ROTATION_SENSITIVITY
        self._camera.pitch = max(self._camera.PITCH_MIN, min(self._camera.PITCH_MAX, new_pitch))

    def drag(self, dx, dy, pan=False):
        """Despacha arrastre a pan o rotación según el flag."""
        if pan:
            self.pan(dx, dy)
        else:
            self.rotate_drag(dx, dy)

    def pan(self, dx, dy):
        """Desplazamiento lateral del plano de proyección."""
        self._camera.pan(dx * 0.5, dy * 0.5)

    def dolly(self, dy):
        """Acerca o aleja la cámara orbital con un arrastre vertical."""
        factor = math.exp(dy * self.DOLLY_SENSITIVITY)
        self._camera.set_distance(self._camera.distance * factor)

    def keyboard_update(self, move_wasd):
        """Actualiza la cámara con el estado de las teclas WASD."""
        self._camera.keyboard_update(move_wasd)
