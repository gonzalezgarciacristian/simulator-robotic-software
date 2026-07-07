"""
ArmConfigRepository — Persistencia de configuraciones de brazos en JSON.
"""
import json
import os
from pathlib import Path


class ArmConfigRepository:

    DEFAULT_FILENAME = 'arm3d_last_config.json'

    def __init__(self, default_path=None, presets_dir=None):
        if default_path is None:
            default_path = Path(os.path.dirname(__file__)) / '..' / '..' / 'assets' / self.DEFAULT_FILENAME
        self.default_path = Path(default_path).resolve()

        if presets_dir is None:
            presets_dir = Path(os.path.dirname(__file__)) / '..' / '..' / 'assets' / 'presets'
        self.presets_dir = Path(presets_dir).resolve()

    def save_model(self, model, path=None):
        """
        Serializa y escribe la configuración del modelo en JSON.

        Args:
            model: ArmKinematicState
            path : Path opcional; si None usa self.default_path.

        Returns:
            True si se guardó correctamente, False si hubo error.
        """
        target = Path(path).resolve() if path else self.default_path
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w', encoding='utf-8') as f:
                json.dump(model.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ArmConfigRepository] Error al guardar: {e}")
            return False

    def load_model(self, model, path=None, silent=False):
        """
        Carga una configuración desde JSON y la aplica al modelo.

        Args:
            model : ArmKinematicState
            path  : Path opcional; si None usa self.default_path.
            silent: Si True, no imprime errores.

        Returns:
            True si se cargó correctamente, False si hubo error.
        """
        target = Path(path).resolve() if path else self.default_path
        try:
            with open(target, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data = self._migrate(data)
            model.load_dict(data)
            return True
        except FileNotFoundError:
            if not silent:
                print(f"[ArmConfigRepository] Archivo no encontrado: {target}")
            return False
        except Exception as e:
            if not silent:
                print(f"[ArmConfigRepository] Error al cargar: {e}")
            return False

    def load_builtin_preset(self, model, name, silent=False):
        """
        Carga un preset predefinido desde el directorio de presets.

        Args:
            model : ArmKinematicState
            name  : nombre del preset (sin extensión .json)
            silent: Si True, no imprime errores.
        """
        path = self.get_builtin_preset_path(name)
        if path is None:
            if not silent:
                print(f"[ArmConfigRepository] Preset no encontrado: {name}")
            return False
        return self.load_model(model, path=path, silent=silent)

    def get_builtin_preset_path(self, name):
        """Resuelve la ruta absoluta de un preset por nombre."""
        if not name.endswith('.json'):
            name = name + '.json'
        candidate = self.presets_dir / name
        if candidate.is_file():
            return candidate
        return None

    def list_builtin_presets(self):
        """
        Devuelve un diccionario {nombre: ruta} de presets .json disponibles.
        """
        result = {}
        if not self.presets_dir.is_dir():
            return result
        for p in sorted(self.presets_dir.glob('*.json')):
            result[p.stem] = p
        return result

    @staticmethod
    def _migrate(data):
        """Aplica migraciones de formato a datos antiguos."""
        # Versión futura: añadir migraciones aquí
        return data
