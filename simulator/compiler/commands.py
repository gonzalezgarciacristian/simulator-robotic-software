import json
import traceback
import importlib.util
import sys
import time
import output.console as console
import compiler.transpiler as transpiler
import libraries.standard as standard
import libraries.serial as serial
import robot_components.robot_state as state
import requests

module = None


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
        serial.cons = self.controller.console
        self.ready = True

class ExecutionInfo(object):
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)

class Compile(Command):

    def __init__(self, controller, username, lab, group):
        super().__init__(controller)
        self.username = username
        self.lab = lab
        self.group = group

    def execute(self):
        try:
            #aqui se obtienen los warns y los errores
            #login de uos
            #scikit learn
            warns, errors = transpiler.transpile(self.controller.get_code())

            errores = []
            warnings = []

            for e in errors:
                errores.append({
                    "columna": e.column,
                    "linea": e.line,
                    "mensaje": e.message,
                    "tipoError": e.r_type,
                    "error": e.to_string
                })

            for e in warns:
                warnings.append({
                    "columna": e.column,
                    "linea": e.line,
                    "mensaje": e.message,
                    "tipoError": e.r_type,
                    "error": e.to_string
                })

            infoeje = ExecutionInfo()
            infoeje.warns = warnings
            infoeje.errores = errores
            infoeje.codigo = self.controller.get_code()

            infoeje.username = self.username
            infoeje.lab = self.lab
            infoeje.group = self.group

            try:
                r = requests.post('http://147.189.171.97:8000/insertaEjecucion',
                                 headers={'Accept': 'application/json'}, json=infoeje.toJSON())

                print(r)
            except requests.exceptions.ConnectionError as ce:
                print(f'la excepción es {ce}')
                traceback.print_exc()
                self.controller.console.write_error(
                    console.Error("Error de conexión", 0, 0, "El sketch no se ha podido enviar correctamente y"
                                                             " se ha guardado la información de la ejecución en el "
                                                             "archivo executions.txt. Si es necesario"
                                                             " avisa a tu profesor"))

                with open('executions.txt', 'a') as file:
                    file.write(infoeje.toJSON())
                    file.write("--------------------------------------------------------")
                    file.close()



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
                module.setup()
            except Exception:
                self.controller.console.write_error(
                    console.Error("Error de ejecución", 0, 0, "El sketch no se ha podido ejecutar correctamente"))
        return True


class Loop(Command):

    def __init__(self, controller):
        super().__init__(controller)

    def execute(self):
        global module
        if not self.ready:
            self.prepare_exec()
        curr_time_ns = time.time_ns()
        if (
                not standard.state.exec_time_us > curr_time_ns / 1000
                and not standard.state.exec_time_ms > curr_time_ns / 1000000
                and not standard.state.exited and self.controller.executing
        ):
            try:
                module.loop()
            except Exception:
                self.controller.console.write_error(
                    console.Error("Error de ejecución", 0, 0, "El sketch no se ha podido ejecutar correctamente"))
                self.controller.executing = False
