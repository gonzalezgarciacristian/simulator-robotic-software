"""
Camera — Cámara virtual esférica para renderizado 3D.
"""
import math
import numpy as np


class Camera:

    DEFAULT_YAW = 45.0
    DEFAULT_PITCH = 30.0
    DEFAULT_DISTANCE = 700.0
    DEFAULT_FOCAL = 300.0
    FOV_DEGREES = 60.0  # ángulo de visión vertical de la proyección en perspectiva
    DEFAULT_ZOOM = 1.0
    PITCH_MIN = -89.0
    PITCH_MAX = 89.0
    ZOOM_MIN = 0.01
    ZOOM_MAX = 100.0
    KEYBOARD_SPEED = 2.0  # grados por tick
    PROJECTION_PERSPECTIVE = "perspective"
    PROJECTION_CABALLERA = "caballera"
    PROJECTION_ISOMETRICA = "isometrica"
    CABALLERA_ANGLE_DEG = 35.0
    CABALLERA_DEPTH_SCALE = 0.5

    def __init__(self):
        self.yaw = self.DEFAULT_YAW
        self.pitch = self.DEFAULT_PITCH
        self.distance = self.DEFAULT_DISTANCE
        self.focal_length = self.DEFAULT_FOCAL
        self.zoom = self.DEFAULT_ZOOM
        self.screen_offset_x = 0.0
        self.screen_offset_y = 0.0
        self.projection_mode = self.PROJECTION_PERSPECTIVE

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------

    def set_zoom_from_scale(self, scale):
        """Convierte un porcentaje de escala en una distancia orbital real.

        A diferencia del zoom optico, aqui el porcentaje representa un dolly:
        200% acerca la camara a la mitad de distancia; 50% la aleja al doble.
        """
        if scale and scale > 0:
            zoom_factor = scale / 100.0
            zoom_factor = max(self.ZOOM_MIN, min(self.ZOOM_MAX, zoom_factor))
            self.distance = self.DEFAULT_DISTANCE / zoom_factor
        self._sync_zoom_from_distance()

    def set_distance(self, distance):
        """Fija la distancia orbital y actualiza el porcentaje de zoom mostrado."""
        min_distance = self.DEFAULT_DISTANCE / self.ZOOM_MAX
        max_distance = self.DEFAULT_DISTANCE / self.ZOOM_MIN
        self.distance = max(min_distance, min(max_distance, float(distance)))
        self._sync_zoom_from_distance()

    def set_orientation(self, yaw=None, pitch=None):
        if yaw is not None:
            self.yaw = float(yaw) % 360.0
        if pitch is not None:
            self.pitch = max(self.PITCH_MIN, min(self.PITCH_MAX, float(pitch)))

    def set_projection_mode(self, projection_mode=None):
        if projection_mode == self.PROJECTION_CABALLERA:
            projection_mode = self.PROJECTION_PERSPECTIVE

        valid_modes = {
            self.PROJECTION_PERSPECTIVE,
            self.PROJECTION_ISOMETRICA,
        }
        if projection_mode in valid_modes:
            self.projection_mode = projection_mode
        else:
            self.projection_mode = self.PROJECTION_PERSPECTIVE

    def pan(self, dx, dy):
        self.screen_offset_x += dx
        self.screen_offset_y += dy

    def reset(self):
        self.yaw = self.DEFAULT_YAW
        self.pitch = self.DEFAULT_PITCH
        self.screen_offset_x = 0.0
        self.screen_offset_y = 0.0
        self.distance = self.DEFAULT_DISTANCE
        self.zoom = self.DEFAULT_ZOOM
        self.projection_mode = self.PROJECTION_PERSPECTIVE

    def keyboard_update(self, move_wasd):
        if not move_wasd:
            return
        if move_wasd.get('a') or move_wasd.get('A'):
            self.yaw = (self.yaw - self.KEYBOARD_SPEED) % 360.0
        if move_wasd.get('d') or move_wasd.get('D'):
            self.yaw = (self.yaw + self.KEYBOARD_SPEED) % 360.0
        if move_wasd.get('w') or move_wasd.get('W'):
            self.pitch = min(self.PITCH_MAX, self.pitch + self.KEYBOARD_SPEED)
        if move_wasd.get('s') or move_wasd.get('S'):
            self.pitch = max(self.PITCH_MIN, self.pitch - self.KEYBOARD_SPEED)

    # ------------------------------------------------------------------
    # Transformación geométrica
    # ------------------------------------------------------------------

    def get_position(self):
        """Posición de la cámara en coordenadas del mundo."""
        yaw_r = math.radians(self.yaw)
        pitch_r = math.radians(self.pitch)
        x = self.distance * math.cos(pitch_r) * math.sin(yaw_r)
        y = self.distance * math.cos(pitch_r) * math.cos(yaw_r)
        z = self.distance * math.sin(pitch_r)
        return np.array([x, y, z], dtype=float)

    def get_view_matrix(self):
        """
        Construye la matriz de vista (lookAt desde la posición de la cámara
        mirando al origen del mundo).
        """
        cam_pos = self.get_position()
        target = np.zeros(3)
        world_up = np.array([0.0, 0.0, 1.0])

        forward = target - cam_pos
        norm = np.linalg.norm(forward)
        if norm < 1e-9:
            forward = np.array([0.0, 0.0, -1.0])
        else:
            forward = forward / norm

        right = np.cross(forward, world_up)
        r_norm = np.linalg.norm(right)
        if r_norm < 1e-9:
            right = np.array([1.0, 0.0, 0.0])
        else:
            right = right / r_norm

        up = np.cross(right, forward)
        up = up / np.linalg.norm(up)

        # Matriz de rotación (view matrix 3x3)
        # Convención: R[2] = forward (hacia el target) → z_cam > 0 para puntos
        # delante de la cámara, compatible con el chequeo "z <= 0.01 → detrás".
        R = np.array([
            [right[0],    right[1],    right[2]  ],
            [up[0],       up[1],       up[2]     ],
            [forward[0],  forward[1],  forward[2]],
        ], dtype=float)
        return R, cam_pos

    def camera_space(self, point):
        """
        Transforma un punto 3D al espacio de cámara.
        Retorna [x_cam, y_cam, z_cam].
        """
        R, cam_pos = self.get_view_matrix()
        p = np.array(point, dtype=float) - cam_pos
        return R @ p

    def project(self, point, width, height):
        """
        Proyecta un punto 3D a coordenadas de pantalla 2D.
        Retorna (sx, sy) o None si está detrás de la cámara.
        """
        p_cs = self.camera_space(point)
        return self.project_camera_space(p_cs, width, height)

    def get_focal(self, viewport_height=None):
        """Focal en píxeles derivada del FOV vertical fijo y la altura del viewport.

        Con una focal constante el ángulo de visión dependía del tamaño del
        canvas (en ventanas grandes superaba los 130°, un gran angular extremo)
        y al acercar la cámara las piezas del brazo se estiraban hacia los
        bordes. Fijar el FOV mantiene la perspectiva natural con cualquier
        tamaño de ventana y nivel de zoom.
        """
        if not viewport_height or viewport_height <= 0:
            return self.focal_length
        half_fov = math.radians(self.FOV_DEGREES) / 2.0
        return (float(viewport_height) / 2.0) / math.tan(half_fov)

    def get_projection_scale(self, viewport_height=None):
        return self.get_focal(viewport_height) / max(self.distance, 1e-9)

    def project_camera_space(self, p_cs, width, height):
        """Proyecta coordenadas ya expresadas en el espacio de cámara."""
        z = p_cs[2]
        if z <= 0.01:
            return None
        cx = width / 2.0 + self.screen_offset_x
        cy = height / 2.0 + self.screen_offset_y

        if self.projection_mode == self.PROJECTION_ISOMETRICA:
            scale = self.get_projection_scale(height)
            sx = p_cs[0] * scale + cx
            sy = -p_cs[1] * scale + cy
            return sx, sy

        f = self.get_focal(height)
        sx = (p_cs[0] / z) * f + cx
        sy = (-p_cs[1] / z) * f + cy
        return sx, sy

    def _sync_zoom_from_distance(self):
        if self.distance <= 1e-9:
            self.zoom = self.ZOOM_MAX
            return
        self.zoom = self.DEFAULT_DISTANCE / self.distance
        self.zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, self.zoom))
