"""Pytest bootstrap local para los tests del simulador 3D."""
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_DIR = PROJECT_ROOT / "simulator"

for candidate in (PROJECT_ROOT, SIMULATOR_DIR):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)


@pytest.fixture(autouse=True)
def _ignore_arm3d_autosave(monkeypatch):
    """Aísla los tests del autosave local ``arm3d_last_config.json``.

    Al construirse, ``Motor3DApi`` carga ese fichero (``load_model`` con
    ``path=None`` y ``silent=True``); si existe en disco —porque el usuario
    ejecutó la app— sobrescribe el preset Braccio por defecto y hace fallar los
    tests de calibración, que asumen que un brazo recién creado es el Braccio.

    Aquí se neutraliza SOLO esa llamada concreta (``path=None`` + ``silent=True``,
    que es exclusiva del autosave). Las cargas con ruta explícita (presets,
    ficheros de prueba) y las que esperan el mensaje "archivo no encontrado"
    (``silent=False``) se mantienen intactas.
    """
    from motor3d.persistence.arm_config_repository import ArmConfigRepository

    original_load = ArmConfigRepository.load_model

    def _load_without_autosave(self, model, path=None, silent=False):
        if path is None and silent:
            return False
        return original_load(self, model, path=path, silent=silent)

    monkeypatch.setattr(ArmConfigRepository, "load_model", _load_without_autosave)
