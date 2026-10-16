"""Resolucion de rutas para las pruebas, independiente del directorio de trabajo.

Los archivos de test viven en ``Simulador/simulator/`` mientras que los recursos
que consumen (``tests/`` y ``codes/``) estan en la raiz del proyecto ``Simulador/``.
Este modulo calcula esas rutas a partir de ``__file__`` para que las pruebas
funcionen sea cual sea el directorio desde el que se lancen, en lugar de depender
de rutas absolutas codificadas o de rutas relativas al CWD.
"""
import os
import sys

# .../Simulador/simulator  (directorio que contiene este archivo y el codigo fuente)
SIMULATOR_DIR = os.path.dirname(os.path.abspath(__file__))
# .../Simulador  (raiz del proyecto, contiene tests/ y codes/)
PROJECT_ROOT = os.path.dirname(SIMULATOR_DIR)

# Garantiza que los paquetes del simulador (compiler, graphics, libraries, ...)
# sean importables aunque las pruebas se lancen desde otro directorio.
if SIMULATOR_DIR not in sys.path:
    sys.path.insert(0, SIMULATOR_DIR)


def tests_path(*parts):
    """Ruta absoluta a un recurso dentro de ``Simulador/tests/``.

    Ejemplo: ``tests_path("grammar-tests", "ejemploArrays.txt")``.
    """
    return os.path.join(PROJECT_ROOT, "tests", *parts)


def codes_path(*parts):
    """Ruta absoluta a un recurso dentro de ``Simulador/codes/``.

    Ejemplo: ``codes_path("challenge1")``.
    """
    return os.path.join(PROJECT_ROOT, "codes", *parts)
