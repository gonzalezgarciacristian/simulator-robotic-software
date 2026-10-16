"""Configuración con valores cifrados.

Los ficheros de configuración del gemelo digital son ``.json`` con la estructura
en claro pero cada valor sensible cifrado con Fernet. Así se pueden localizar y
editar rápido sin exponer el dato real (IP, puerto, sufijo de identidad...).

La clave va fija en el código, igual que en ``output/console_gamification.py``:
es **ofuscación**, no seguridad fuerte (quien tenga el código puede descifrar).
"""

import base64
import json

from cryptography.fernet import Fernet

# Misma estrategia que el modo gamificación: clave fija en el binario.
_KEY = b'qpbwoA}91MY2J:{^k!hM>G%f+b5c@,mw'
_cipher = Fernet(base64.urlsafe_b64encode(_KEY))

# Ficheros relativos al cwd (Simulador/), junto a robot_data.json.
BROKER_FILE = "mqtt_broker.json"


def encrypt_value(text) -> str:
    """Cifra un valor suelto y lo devuelve como cadena (token Fernet)."""
    return _cipher.encrypt(str(text).encode()).decode()


def decrypt_value(token: str) -> str:
    """Descifra un token Fernet generado por :func:`encrypt_value`."""
    return _cipher.decrypt(token.encode()).decode()


def load_broker_config(path: str = BROKER_FILE):
    """Lee ``mqtt_broker.json`` y devuelve ``(ip, port)`` descifrados.

    Lanza excepción si el fichero no existe o no es válido; el llamante decide
    cómo informarlo.
    """
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    ip = decrypt_value(data["ip"])
    port = int(decrypt_value(data["port"]))
    return ip, port


def write_broker_config(ip: str, port, path: str = BROKER_FILE):
    """Genera ``mqtt_broker.json`` con ``ip``/``port`` cifrados (uso en deploy)."""
    data = {
        "ip": encrypt_value(ip),
        "port": encrypt_value(port),
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
    return path
