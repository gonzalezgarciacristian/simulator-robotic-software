"""
ArmKinematicState — Estado cinemático completo del brazo robótico.
Parametrización Denavit-Hartenberg, configurable para 1-6 DOF.
"""
import math


class ArmKinematicState:

    MIN_DOF = 1
    MAX_DOF = 6
    VISUAL_MODES = ["auto_generic", "braccio_exact", "skeleton"]

    def __init__(self):
        self.dof = 0
        self.link_lengths = []
        self.joints = []
        self.joint_limits = []
        self.joint_types = []
        self.dh_rows = []
        self.prismatic_pre_rotations = []
        self.servo_pins = []
        self.servo_calibration = []
        self.base_row = {'theta': 0.0, 'd': 0.0, 'a': 0.0, 'alpha': 0.0}
        self.preset_name = None
        self.visual = {"mode": "auto_generic", "theme": "default", "sizes": {}}

    def configure(self, dof, link_lengths=None, joint_limits=None,
                  joint_types=None, joints=None, dh_rows=None,
                  visual=None, base=None, prismatic_pre_rotations=None,
                  servo_pins=None, servo_calibration=None):
        self.dof = max(self.MIN_DOF, min(self.MAX_DOF, int(dof)))
        n = self.dof

        self.link_lengths = list(link_lengths) if link_lengths else [100.0] * n
        self.link_lengths = self.link_lengths[:n]
        while len(self.link_lengths) < n:
            self.link_lengths.append(100.0)

        if joint_limits:
            self.joint_limits = [tuple(lim) for lim in joint_limits][:n]
        else:
            self.joint_limits = [(-90.0, 90.0)] * n
        while len(self.joint_limits) < n:
            self.joint_limits.append((-90.0, 90.0))

        raw_types = list(joint_types) if joint_types else []
        self.joint_types = [(t if t in ('R', 'P') else 'R') for t in raw_types][:n]
        while len(self.joint_types) < n:
            self.joint_types.append('R')

        if joints:
            self.joints = [float(j) for j in joints][:n]
        else:
            self.joints = [0.0] * n
        while len(self.joints) < n:
            self.joints.append(0.0)

        if dh_rows:
            self.dh_rows = [dict(row) for row in dh_rows][:n]
        else:
            self.dh_rows = [
                {'theta': 0.0, 'd': 0.0, 'a': float(self.link_lengths[i]), 'alpha': 0.0}
                for i in range(n)
            ]
        while len(self.dh_rows) < n:
            i = len(self.dh_rows)
            ll = self.link_lengths[i] if i < len(self.link_lengths) else 100.0
            self.dh_rows.append({'theta': 0.0, 'd': 0.0, 'a': float(ll), 'alpha': 0.0})

        raw_prismatic_rotations = list(prismatic_pre_rotations) if prismatic_pre_rotations else []
        self.prismatic_pre_rotations = [
            self._normalize_prismatic_pre_rotation(item)
            for item in raw_prismatic_rotations[:n]
        ]
        while len(self.prismatic_pre_rotations) < n:
            self.prismatic_pre_rotations.append({'yaw': 0.0, 'pitch': 0.0})

        raw_servo_pins = list(servo_pins) if servo_pins else []
        self.servo_pins = [
            self._normalize_servo_pin(pin)
            for pin in raw_servo_pins[:n]
        ]
        while len(self.servo_pins) < n:
            self.servo_pins.append(None)

        self.servo_calibration = self._normalize_servo_calibration(servo_calibration, n)
        self.base_row = self._normalize_base_row(base)

        if visual:
            self.visual = dict(visual)
        else:
            self.visual = {"mode": "auto_generic", "theme": "default", "sizes": {}}

        self._sync_link_lengths_from_dh()
        self._clamp_joints()

    def set_joint(self, index, value):
        if 0 <= index < self.dof:
            mn, mx = self.effective_joint_limits(index)
            self.joints[index] = max(mn, min(mx, float(value)))

    def set_dh(self, dh_rows):
        n = self.dof
        self.dh_rows = [dict(row) for row in dh_rows][:n]
        while len(self.dh_rows) < n:
            self.dh_rows.append({'theta': 0.0, 'd': 0.0, 'a': 100.0, 'alpha': 0.0})
        self._sync_link_lengths_from_dh()

    def set_limits(self, limits):
        n = self.dof
        self.joint_limits = [tuple(lim) for lim in limits][:n]
        while len(self.joint_limits) < n:
            self.joint_limits.append((-90.0, 90.0))
        self._clamp_joints()

    def is_at_limit(self, index, eps=1.0):
        if 0 <= index < self.dof:
            mn, mx = self.joint_limits[index]
            return self.joints[index] <= mn + eps or self.joints[index] >= mx - eps
        return False

    def max_reach(self):
        reach = 0.0
        for i, row in enumerate(self.dh_rows):
            a = abs(float(row.get('a', 0.0)))
            d = float(row.get('d', 0.0))
            max_abs_d = abs(d)

            if i < len(self.joint_types) and self.joint_types[i] == 'P':
                if i < len(self.joint_limits):
                    mn, mx = self.joint_limits[i]
                    max_abs_d = max(abs(d + float(mn)), abs(d + float(mx)))

            reach += a + max_abs_d

        return reach

    def to_dict(self):
        return {
            'dof': self.dof,
            'link_lengths': list(self.link_lengths),
            'joints': list(self.joints),
            'joint_limits': [list(lim) for lim in self.joint_limits],
            'joint_types': list(self.joint_types),
            'dh_rows': [dict(row) for row in self.dh_rows],
            'prismatic_pre_rotations': [dict(item) for item in self.prismatic_pre_rotations],
            'servo_pins': list(self.servo_pins),
            'servo_calibration': [
                [[float(x), float(y)] for x, y in points]
                for points in self.servo_calibration
            ],
            'base': dict(self.base_row),
            'preset_name': self.preset_name,
            'visual': dict(self.visual),
        }

    def load_dict(self, data):
        preset_name = data.get('preset_name')
        self.preset_name = preset_name if isinstance(preset_name, str) and preset_name else None
        self.configure(
            dof=data.get('dof', 1),
            link_lengths=data.get('link_lengths'),
            joint_limits=data.get('joint_limits'),
            joint_types=data.get('joint_types'),
            joints=data.get('joints'),
            dh_rows=data.get('dh_rows'),
            base=data.get('base'),
            visual=data.get('visual'),
            prismatic_pre_rotations=data.get('prismatic_pre_rotations'),
            servo_pins=data.get('servo_pins'),
            servo_calibration=data.get('servo_calibration'),
        )

    def _sync_link_lengths_from_dh(self):
        for i, row in enumerate(self.dh_rows):
            if i < len(self.link_lengths):
                self.link_lengths[i] = abs(row.get('a', self.link_lengths[i]))

    def _clamp_joints(self):
        for i in range(self.dof):
            mn, mx = self.effective_joint_limits(i)
            self.joints[i] = max(mn, min(mx, self.joints[i]))

    def effective_joint_limits(self, index):
        mn, mx = self.joint_limits[index]
        if index >= len(self.joint_types) or self.joint_types[index] != 'R':
            return mn, mx
        points = self.servo_calibration[index] if index < len(self.servo_calibration) else []
        if len(points) < 2:
            return mn, mx
        lo = self._interp_calibration(points, 0.0) - 90.0
        hi = self._interp_calibration(points, 180.0) - 90.0
        return (lo, hi) if lo <= hi else (hi, lo)

    @staticmethod
    def _interp_calibration(points, value):
        """Interpola linealmente digital→real sobre los puntos de calibración,
        recortando (clamp) a los extremos fuera del rango muestreado."""
        value = float(value)
        ordered = sorted((float(x), float(y)) for x, y in points)
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

    @staticmethod
    def _normalize_prismatic_pre_rotation(item):
        default = {'yaw': 0.0, 'pitch': 0.0}

        if isinstance(item, dict):
            source_yaw = item.get('yaw', 0.0)
            source_pitch = item.get('pitch', 0.0)
        elif isinstance(item, (list, tuple)):
            source_yaw = item[0] if len(item) > 0 else 0.0
            source_pitch = item[1] if len(item) > 1 else 0.0
        else:
            return dict(default)

        try:
            yaw = float(source_yaw)
        except (TypeError, ValueError):
            yaw = 0.0

        try:
            pitch = float(source_pitch)
        except (TypeError, ValueError):
            pitch = 0.0

        return {'yaw': yaw, 'pitch': pitch}

    @staticmethod
    def _normalize_servo_pin(pin):
        if pin is None or pin == "":
            return None
        try:
            return int(pin)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _normalize_servo_calibration(cls, calibration, dof):
        if not calibration:
            return []

        result = []
        for joint_points in list(calibration)[:dof]:
            points = []
            if isinstance(joint_points, (list, tuple)):
                for point in joint_points:
                    parsed = cls._normalize_calibration_point(point)
                    if parsed is not None:
                        points.append(parsed)
            result.append(points)

        while len(result) < dof:
            result.append([])
        return result

    @staticmethod
    def _normalize_calibration_point(point):
        if isinstance(point, dict):
            source_x = point.get('digital', point.get('servo'))
            source_y = point.get('real', point.get('measured'))
        elif isinstance(point, (list, tuple)) and len(point) >= 2:
            source_x, source_y = point[0], point[1]
        else:
            return None

        try:
            return float(source_x), float(source_y)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_base_row(base):
        default = {'theta': 0.0, 'd': 0.0, 'a': 0.0, 'alpha': 0.0}
        if not isinstance(base, dict):
            return dict(default)

        if any(k in base for k in ('theta', 'd', 'a', 'alpha')):
            row = {}
            for key in ('theta', 'd', 'a', 'alpha'):
                try:
                    row[key] = float(base.get(key, 0.0))
                except (TypeError, ValueError):
                    row[key] = 0.0
            return row

        raw_rpy = list(base.get('rpy', [])) if 'rpy' in base else []
        if raw_rpy:
            roll = math.radians(float(raw_rpy[0]) if len(raw_rpy) > 0 else 0.0)
            pitch = math.radians(float(raw_rpy[1]) if len(raw_rpy) > 1 else 0.0)
            yaw = math.radians(float(raw_rpy[2]) if len(raw_rpy) > 2 else 0.0)

            cr, sr = math.cos(roll), math.sin(roll)
            cp, sp = math.cos(pitch), math.sin(pitch)
            cy, sy = math.cos(yaw), math.sin(yaw)

            zx = cy * sp * cr + sy * sr
            zy = sy * sp * cr - cy * sr
            zz = cp * cr

            alpha = math.degrees(math.atan2(math.sqrt(zx * zx + zy * zy), zz))
            if abs(zx) > 1e-9 or abs(zy) > 1e-9:
                theta = math.degrees(math.atan2(zx, -zy))
            else:
                theta = math.degrees(yaw)

            row = dict(default)
            row['theta'] = theta
            row['alpha'] = alpha
            return row

        return dict(default)
