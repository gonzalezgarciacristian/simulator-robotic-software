"""Cliente MQTT del gemelo digital (envoltorio sobre paho-mqtt).

Las callbacks de paho corren en su propio hilo de red, por lo que **no** tocan
Tkinter: solo encolan eventos en ``self.events`` (una ``queue.Queue``). El
controlador, desde el hilo de Tk, drena esa cola y actualiza consola/UI.

Eventos encolados (tuplas):
    ("connect", code)            code == 0 → conexión aceptada por el broker
    ("connect_fail",)            no se pudo establecer la conexión de red
    ("message", topic, payload)  mensaje de texto recibido
    ("suback", denied)           denied == True → tema ocupado (whitelist)
    ("disconnect", code)         code != 0 → desconexión inesperada
"""

import queue

import paho.mqtt.client as mqtt

# paho-mqtt 2.x exige indicar la versión de la API de callbacks; 1.x no la tiene.
try:
    from paho.mqtt.enums import CallbackAPIVersion
    _HAS_V2 = True
except Exception:  # pragma: no cover - depende de la versión instalada
    _HAS_V2 = False

import digital_twin.twin_identity as twin_identity

# Centinela de presencia: al conectar, el simulador lo publica en su topic de
# salida para que el broker lo registre como publicador del tema. No es una
# orden ni una trama de datos: el dispositivo que lo reciba lo descarta sin
# procesarlo. Debe coincidir con TwinNode::HOLA del firmware Arduino.
HELLO = "hello"


class MQTTAdapter:

    def __init__(self, theme, host, port, identity=None):
        self.theme = theme
        self.host = host
        self.port = port
        self.identity = identity or twin_identity.TwinIdentity()

        self.client_id = self.identity.client_id(theme)
        self.pub_topic = self.identity.pub_topic(theme)
        self.sub_topic = self.identity.sub_topic(theme)

        self.events = queue.Queue()

        if _HAS_V2:
            self._client = mqtt.Client(
                CallbackAPIVersion.VERSION2,
                client_id=self.client_id, clean_session=True)
        else:  # pragma: no cover - paho 1.x
            self._client = mqtt.Client(
                client_id=self.client_id, clean_session=True)

        # Registro de callbacks para paho
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_subscribe = self._on_subscribe
        self._client.on_disconnect = self._on_disconnect
        self._client.on_connect_fail = self._on_connect_fail

    # ------------------------------------------------------------------ API
    def connect_async(self):
        """Programa la conexión **sin bloquear** y arranca el bucle de red.

        La conexión real ocurre en el hilo de paho; el resultado llega por
        ``on_connect`` (aceptada o rechazada por el broker) o por
        ``on_connect_fail`` (no se pudo establecer la conexión de red).
        Solo lanza excepción ante argumentos inválidos (host vacío...).
        """
        self._client.connect_async(self.host, self.port, keepalive=60)
        self._client.loop_start()

    def disconnect(self, farewell=None):
        """Cierra la conexión. Si se indica ``farewell``, lo publica y espera a
        que salga **antes** de desconectar (último mensaje, p.ej. soltar el
        control con ``0,0``), para que el dispositivo lo reciba aunque luego se
        caiga el socket."""
        try:
            if farewell is not None:
                info = self._client.publish(self.pub_topic, farewell)
                self._wait_published(info)
            self._client.disconnect()
        finally:
            self._client.loop_stop()

    @staticmethod
    def _wait_published(info, timeout=1.0):
        """Bloquea hasta que el mensaje sale (o expira el tiempo). Tolera la
        diferencia de firma de ``wait_for_publish`` entre paho 1.x y 2.x."""
        try:
            info.wait_for_publish(timeout)
        except TypeError:  # paho 1.x: wait_for_publish() no admite timeout
            try:
                info.wait_for_publish()
            except Exception:
                pass
        except Exception:
            pass

    def publish_text(self, text):
        """Publica un texto en el tema de publicación (``s + theme``)."""
        self._client.publish(self.pub_topic, text)

    # ----------------------------------------- callbacks (hilo de red paho)
    # Firmas compatibles con paho 1.x y 2.x (parámetros extra con valor por
    # defecto o *args). Solo encolan; nunca tocan la GUI.
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        code = getattr(rc, "value", rc)
        if code == 0:
            client.subscribe(self.sub_topic)
        self.events.put(("connect", code))

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="replace")
        except Exception:
            payload = str(msg.payload)
        self.events.put(("message", msg.topic, payload))

    def _on_subscribe(self, client, userdata, mid, granted_qos, properties=None):
        codes = [getattr(q, "value", q) for q in granted_qos]
        denied = any(c >= 128 for c in codes)
        self.events.put(("suback", denied))

    def _on_disconnect(self, client, userdata, *args):
        # v1: (rc,)   ;   v2: (disconnect_flags, reason_code, properties)
        rc = args[0] if len(args) == 1 else (args[1] if len(args) >= 2 else 0)
        code = getattr(rc, "value", rc)
        self.events.put(("disconnect", code))

    def _on_connect_fail(self, client, userdata):
        # paho no pudo establecer la conexión de red (broker caído/inalcanzable).
        self.events.put(("connect_fail",))
