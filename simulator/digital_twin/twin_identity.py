"""Identidad estable del gemelo digital por theme.

Para un ``theme`` introducido por el usuario se construye:

- ``client_id`` = ``"o" + theme + sufijo``
- tema de publicación = ``"s" + theme``
- tema de suscripción = ``"p" + theme``

El ``sufijo`` replica el ``__TIME__[6]+__TIME__[7]`` de Arduino: los 2 últimos
dígitos de ``int(time.time())`` capturados **la primera vez** que aparece un
theme. Se persiste cifrado en ``mqtt_identity.json`` para poder reutilizarlo al
reconectar con el mismo theme (el whitelist del broker solo deja reconectar al
mismo clientID). Ver FASE_0.md para el razonamiento completo.
"""

import json
import os
import time

import digital_twin.secure_config as secure_config

IDENTITY_FILE = "mqtt_identity.json"


class TwinIdentity:

    def __init__(self, path: str = IDENTITY_FILE):
        self.path = path

    def _load(self) -> dict:
        """Devuelve el mapa ``{theme: sufijo}`` con los sufijos descifrados."""
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                raw = json.load(file)
        except (json.JSONDecodeError, OSError):
            return {}
        data = {}
        for theme, token in raw.items():
            try:
                data[theme] = secure_config.decrypt_value(token)
            except Exception:
                # Entrada corrupta: se ignora (se regenerará si hace falta).
                continue
        return data

    def _save(self, data: dict):
        """Guarda el mapa cifrando cada sufijo."""
        raw = {theme: secure_config.encrypt_value(suffix)
               for theme, suffix in data.items()}
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(raw, file, indent=2)

    def get_or_create(self, theme: str) -> str:
        """Devuelve el sufijo del theme; lo genera y persiste si es nuevo."""
        data = self._load()
        if theme not in data:
            data[theme] = "{:02d}".format(int(time.time()) % 100)
            self._save(data)
        return data[theme]

    def client_id(self, theme: str) -> str:
        return "o" + theme + self.get_or_create(theme)

    def pub_topic(self, theme: str) -> str:
        return "s" + theme

    def sub_topic(self, theme: str) -> str:
        return "p" + theme
