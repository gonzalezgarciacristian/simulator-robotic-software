import sys
import os

# Garantiza que (1) el directorio raíz del proyecto sea el cwd para que las rutas
# relativas a assets/, buttons/ y robot_data.json funcionen, y (2) simulator/ esté
# en sys.path para que los imports como "import graphics.gui" resuelvan correctamente.
# Esto permite ejecutar el simulador desde cualquier directorio:
#   python simulator/main.py   (desde la raíz)
#   python main.py             (desde simulator/)
if getattr(sys, 'frozen', False):
    # Ejecutable PyInstaller: los datos empaquetados (buttons/, assets/,
    # robot_data.json) se extraen en sys._MEIPASS (carpeta _internal en modo
    # onedir). El cwd debe apuntar ahí para que las rutas relativas resuelvan.
    _PROJECT_ROOT = sys._MEIPASS
    os.chdir(_PROJECT_ROOT)
    if _PROJECT_ROOT not in sys.path:
        sys.path.insert(0, _PROJECT_ROOT)
else:
    _SIMULATOR_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT  = os.path.dirname(_SIMULATOR_DIR)
    os.chdir(_PROJECT_ROOT)
    if _SIMULATOR_DIR not in sys.path:
        sys.path.insert(0, _SIMULATOR_DIR)

import graphics.gui as gui


def main():
    app = gui.MainApplication()
    app.mainloop()


if __name__ == '__main__':
    main()
