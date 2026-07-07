import traceback
import importlib.util
import sys
import time
import threading
import output.console as console
import compiler.transpiler as transpiler
import libraries.standard as standard
import libraries.serial as serial
import robot_components.robot_state as state

module = None


class ExecutionPaused(Exception):
    """Lanzada por screen_updater.debug_line() al alcanzar un breakpoint o en modo paso a paso."""
    pass


def _import_module():
    global module
    spec = importlib.util.spec_from_file_location('temp.script_arduino', 'temp/script_arduino.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['temp.script_arduino'] = module
    spec.loader.exec_module(module)


class Command:

    def __init__(self, controller):
        self.controller = controller
        self.ready = False

    def execute(self):
        """
        Executes a command object
        """
        pass

    def reboot(self):
        self.ready = False

    def prepare_exec(self):
        standard.board = self.controller.robot_layer.robot.board
        standard.state = state.State()
        standard._stop_event.clear()
        standard.reset_runtime_watchdog()
        serial.cons = self.controller.console
        self.ready = True


class Compile(Command):

    def __init__(self, controller):
        super().__init__(controller)
        self.ast = None

    def execute(self):
        try:
            warns, errors, self.ast = transpiler.transpile(self.controller.get_code())
            if len(errors) > 0:
                self.print_errors(errors)
                return False
            elif len(warns) > 0:
                self.print_warnings(warns)
                return True
            return True
        except Exception as e:
            print(f'la excepción es {e}')
            traceback.print_exc()
            self.controller.console.write_error(
                console.Error("Error de compilación", 0, 0, "El sketch no se ha podido compilar correctamente"))

    def compile(self, code):
        try:
            warns, errors, ast = transpiler.transpile(code)
            if len(errors) > 0:
                self.print_errors(errors)
                return None
            elif len(warns) > 0:
                self.print_warnings(warns)
                return ast
            return ast
        except Exception as e:
            print(f'la excepción es {e}')
            traceback.print_exc()
            self.controller.console.write_error(
                console.Error("Error de compilación", 0, 0, "El sketch no se ha podido compilar correctamente"))

    def print_warnings(self, warnings):
        for warning in warnings:
            self.controller.console.write_warning(warning)

    def print_errors(self, errors):
        for error in errors:
            self.controller.console.write_error(error)


class Setup(Command):

    def __init__(self, controller):
        super().__init__(controller)

    def execute(self):
        global module
        if not self.ready:
            self.prepare_exec()
            _import_module()
        curr_time_ns = time.time_ns()
        if (
                not standard.state.exec_time_us > curr_time_ns / 1000
                and not standard.state.exec_time_ms > curr_time_ns / 1000000
        ):
            try:
                standard._stop_event.clear()
                standard.reset_runtime_watchdog()
                module.setup()
            except ExecutionPaused:
                return True
            except standard.ExecutionInterrupted:
                return True
            except Exception:
                traceback.print_exc()
                self.controller.console.write_error(
                    console.Error("Error de ejecución", 0, 0, "El sketch no se ha podido ejecutar correctamente"))
                return False
        return True


class Loop(Command):
    """
    Ejecuta module.loop() en un hilo de fondo para que delay() pueda hacer
    time.sleep() real sin bloquear el hilo principal de Tkinter.
    """

    def __init__(self, controller):
        super().__init__(controller)
        self._thread = None
        self._old_thread = None
        self._stop_flag = False

    def execute(self):
        global module
        if not self.controller.executing and self._thread is not None:
            return
        if not self.ready:
            self.prepare_exec()
        # Arrancar el hilo solo si no hay ya uno vivo
        if self._thread is None or not self._thread.is_alive():
            self._stop_flag = False
            standard._stop_event.clear()  # asegura que delay() funcione con normalidad
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def _run(self):
        """Cuerpo del hilo: repite loop() mientras la simulación esté activa."""
        try:
            standard.reset_runtime_watchdog()
            while not self._stop_flag:
                if not self.controller.executing:
                    break
                if standard.state and standard.state.exited:
                    break
                # Respetar bloqueo de seguridad (fuera de workspace)
                layer = self.controller.robot_layer
                import graphics.layers as _layers
                if (self.controller.arm3d
                        and isinstance(layer, _layers.Arm3DLayer)
                        and layer.safety_blocked):
                    time.sleep(0.02)
                    continue
                try:
                    module.loop()
                    time.sleep(0.001)
                except ExecutionPaused:
                    pass  # Simulación detenida mientras el hilo estaba bloqueado en debug_line
                except standard.ExecutionInterrupted:
                    break
                except Exception:
                    traceback.print_exc()
                    self.controller.executing = False
                    self._stop_flag = True
                    self.controller._notify_state("idle")
                    break
        except Exception:
            traceback.print_exc()
            self.controller.executing = False
            self._stop_flag = True
            self.controller._notify_state("idle")

    def reboot(self):
        standard._stop_event.set()   # despierta cualquier delay() bloqueado
        self._stop_flag = True
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=0.5)  # delay() ya no bloquea → 500 ms es más que suficiente
        # Guardar referencia si el hilo sigue vivo (código sin delay en bucle infinito)
        if self._thread is not None and self._thread.is_alive():
            self._old_thread = self._thread  # se abandona como daemon; morirá con el proceso
        self._thread = None
        super().reboot()
