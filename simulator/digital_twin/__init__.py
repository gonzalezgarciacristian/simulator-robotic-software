"""Modo gemelo digital (MQTT) del simulador.

Contiene la capa de conexión MQTT que permite que el simulador actúe como
gemelo digital de un robot:

- ``secure_config``  — lectura/escritura de configuración con valores cifrados.
- ``twin_identity``  — identidad estable por theme (clientID y temas pub/sub).
- ``mqtt_adapter``   — cliente MQTT (paho) con cola de eventos thread-safe.
"""
