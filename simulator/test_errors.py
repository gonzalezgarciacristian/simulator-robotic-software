import unittest

from path_helper import tests_path

from antlr4 import *
from compiler.ArduinoLexer import ArduinoLexer
from compiler.ArduinoParser import ArduinoParser
from compiler.ast import *
from compiler.ast_builder_visitor import ASTBuilderVisitor
from compiler.error_listener import CompilerErrorListener
from compiler.semantical_errors import Semantic
from libraries.libs import LibraryManager


class TestBaseErrors(unittest.TestCase):

    def setUp(self):
        input = FileStream(fileName=self.file, encoding="utf-8")
        lexer = ArduinoLexer(input)
        error_listener = CompilerErrorListener(False)
        lexer.removeErrorListeners()
        lexer.addErrorListener(error_listener)
        stream = CommonTokenStream(lexer)
        parser = ArduinoParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(error_listener)
        visitor = ASTBuilderVisitor()
        lib_manager = LibraryManager()
        semantic = Semantic(lib_manager)
        tree = parser.program()
        self.syntax_errors = error_listener.errors
        if len(self.syntax_errors) < 1:
            self.ast = visitor.visitProgram(tree)
            semantic.execute(self.ast)
        try:
            self.semantic_errors = semantic.errors
        except AttributeError:
            pass

    def tearDown(self):
        return super().tearDown()

    def print_errors(self):
        for error in self.semantic_errors:
            print(error.to_string())


class TestSyntaxErrors(TestBaseErrors):
    file = tests_path("error-tests", "lex-syn.txt")

    def test_number_of_errors(self):
        self.assertEqual(len(self.syntax_errors), 5)

    def test_type_of_errors(self):
        self.assertEqual(self.syntax_errors[0].r_type, "Sintaxis")
        self.assertEqual(self.syntax_errors[1].r_type, "Sintaxis")
        self.assertEqual(self.syntax_errors[2].r_type, "Léxico")
        self.assertEqual(self.syntax_errors[3].r_type, "Sintaxis")
        self.assertEqual(self.syntax_errors[4].r_type, "Sintaxis")

    def test_error_messages(self):
        self.assertEqual(self.syntax_errors[0].message,
                         "El valor introducido en esta posición no es válido: ;")
        self.assertEqual(self.syntax_errors[1].message,
                         "Falta(n) caracter(es): ';'")
        self.assertEqual(self.syntax_errors[2].message,
                         "Caracter(es) inválido(s)")
        self.assertEqual(self.syntax_errors[3].message,
                         "El valor introducido en esta posición no es válido: \"panda;")
        self.assertEqual(self.syntax_errors[4].message,
                         "Código no válido")


class TestSetupLoopErrors(TestBaseErrors):
    file = tests_path("error-tests", "setup-loop.txt")

    def test_number_of_errors(self):
        self.assertEqual(len(self.semantic_errors), 2)

    def test_r_type(self):
        self.assertEqual(self.semantic_errors[0].r_type, "Declaración")
        self.assertEqual(self.semantic_errors[1].r_type, "Declaración")

    def test_error_message(self):
        self.assertEqual(
            self.semantic_errors[0].message, "No hay función setup")
        self.assertEqual(
            self.semantic_errors[1].message, "No hay función loop")


class TestTypeErrors(TestBaseErrors):
    file = tests_path("error-tests", "types.txt")

    def test_number_of_errors(self):
        self.assertEqual(len(self.semantic_errors), 30)

    def test_r_type(self):
        for err in self.semantic_errors[:-2]:
            self.assertEqual(err.r_type, "Tipos")
        self.assertEqual(
            self.semantic_errors[28].r_type, "Tipo de función setup")
        self.assertEqual(
            self.semantic_errors[29].r_type, "Tipo de función loop")

    def test_error_message(self):
        self.assertEqual(
            self.semantic_errors[0].message, "El tipo de la variable es numérico, pero su valor no")
        self.assertEqual(
            self.semantic_errors[1].message, "El tipo de la variable es numérico, pero su valor no")
        self.assertEqual(self.semantic_errors[2].message,
                         "El tipo de la variable es char, pero su valor no es char o int")
        self.assertEqual(
            self.semantic_errors[3].message, "El tipo del array es numérico, pero su valor no")
        self.assertEqual(
            self.semantic_errors[4].message, "El tipo de la variable y del valor no coincide")
        self.assertEqual(
            self.semantic_errors[5].message, "El tipo de la variable es numérico, pero su valor no")
        self.assertEqual(
            self.semantic_errors[6].message, "El tipo de la variable es numérico, pero su valor no")
        self.assertEqual(
            self.semantic_errors[7].message, "El tipo de la variable es numérico, pero su valor no")
        self.assertEqual(
            self.semantic_errors[8].message, "El resultado de la condición debe ser int o boolean")
        self.assertEqual(
            self.semantic_errors[9].message, "El resultado de la condición debe ser int o boolean")
        self.assertEqual(
            self.semantic_errors[10].message, "La variable del for debe ser int (en Arduino realmente no)")
        self.assertEqual(
            self.semantic_errors[11].message, "El resultado de la condición debe ser int o boolean")
        self.assertEqual(
            self.semantic_errors[12].message, "El incremento del for debe ser int")
        self.assertEqual(self.semantic_errors[13].message,
                         "La sentencia case debe de tener una expresión del tipo marcado en switch")
        self.assertEqual(
            self.semantic_errors[14].message, "El resultado de la condición debe ser int o boolean")
        self.assertEqual(
            self.semantic_errors[15].message, "El tipo del parámetro y del valor no coincide")
        self.assertEqual(
            self.semantic_errors[16].message, "El tipo de retorno es numérico, pero su valor no")
        self.assertEqual(
            self.semantic_errors[17].message, "La expresión no es de tipo numérico")
        self.assertEqual(
            self.semantic_errors[18].message, "La expresión debe ser tipo int o boolean")
        self.assertEqual(
            self.semantic_errors[19].message, "La expresión debe ser tipo int")
        self.assertEqual(
            self.semantic_errors[20].message, "La expresión izquierda debe ser int o boolean")
        self.assertEqual(
            self.semantic_errors[21].message, "La expresión derecha debe ser int o boolean")
        self.assertEqual(
            self.semantic_errors[22].message, "El tipo de la izquierda debe ser numérico")
        self.assertEqual(
            self.semantic_errors[23].message, "El tipo de la derecha debe ser numérico")
        self.assertEqual(
            self.semantic_errors[24].message, "El tipo de la variable es numérico, pero su valor no")
        self.assertEqual(
            self.semantic_errors[25].message, "El tipo de retorno y del valor no coincide")
        self.assertEqual(
            self.semantic_errors[26].message, "Las funciones de tipo void no deben retornar valor")
        self.assertEqual(
            self.semantic_errors[27].message, "Las funciones de tipo no void deben retornar valor")
        self.assertEqual(
            self.semantic_errors[28].message, "La función setup debe ser de tipo void")
        self.assertEqual(
            self.semantic_errors[29].message, "La función loop debe ser de tipo void")


class TestDeclarationErrors(TestBaseErrors):
    file = tests_path("error-tests", "declarations.txt")

    def test_number_of_errors(self):
        self.assertEqual(len(self.semantic_errors), 12)

    def test_r_type(self):
        for err in self.semantic_errors:
            self.assertEqual(err.r_type, "Declaración")

    def test_error_message(self):
        self.assertEqual(
            self.semantic_errors[0].message, "La variable ya ha sido declarada")
        self.assertEqual(
            self.semantic_errors[1].message, "El array ya ha sido declarado")
        self.assertEqual(
            self.semantic_errors[2].message, "La macro ya ha sido declarada")
        self.assertEqual(
            self.semantic_errors[3].message, "La variable ya ha sido declarada")
        self.assertEqual(
            self.semantic_errors[4].message, "El array ya ha sido declarado")
        self.assertEqual(
            self.semantic_errors[5].message, "La macro ya ha sido declarada")
        self.assertEqual(
            self.semantic_errors[6].message, "La función ya ha sido declarada")
        self.assertEqual(
            self.semantic_errors[7].message, "La función no se ha declarado")
        self.assertEqual(
            self.semantic_errors[8].message, "La variable no está declarada")
        self.assertEqual(
            self.semantic_errors[9].message, "La variable no está declarada")
        self.assertEqual(
            self.semantic_errors[10].message, "El array no está declarado")
        self.assertEqual(
            self.semantic_errors[11].message, "La variable no está declarada")


class TestFlowErrors(TestBaseErrors):
    file = tests_path("error-tests", "flow.txt")

    def test_number_of_errors(self):
        self.assertEqual(len(self.semantic_errors), 8)

    def test_r_types(self):
        for error in self.semantic_errors:
            self.assertEqual(error.r_type, "Mal uso de identificador")

    def test_error_messages(self):
        self.assertEqual(
            self.semantic_errors[0].message, "Continue debe ser usado dentro de un bucle")
        self.assertEqual(
            self.semantic_errors[1].message, "Break debe ser usado dentro de un bucle o en case switch")
        self.assertEqual(
            self.semantic_errors[2].message, "Continue debe usarse en bucles")
        self.assertEqual(
            self.semantic_errors[3].message, "Break debe usarse en bucles o en case switch")
        self.assertEqual(
            self.semantic_errors[4].message, "Continue debe usarse en bucles")
        self.assertEqual(
            self.semantic_errors[5].message, "Break debe usarse en bucles o en case switch")
        self.assertEqual(
            self.semantic_errors[6].message, "Continue debe usarse en bucles")
        self.assertEqual(
            self.semantic_errors[7].message, "La sentencia return debe de estar al final de la función")


class TestArrayAccessErrors(TestBaseErrors):
    file = tests_path("error-tests", "arrays.txt")

    def test_number_of_errors(self):
        self.assertEqual(len(self.semantic_errors), 24)

    def test_r_type(self):
        self.assertEqual(self.semantic_errors[0].r_type, "Declaración")
        self.assertEqual(self.semantic_errors[1].r_type, "Tamaños")
        self.assertEqual(self.semantic_errors[2].r_type, "Declaración")
        self.assertEqual(self.semantic_errors[3].r_type, "Tipos")
        self.assertEqual(self.semantic_errors[4].r_type, "Declaración")
        self.assertEqual(self.semantic_errors[5].r_type, "Índice")
        self.assertEqual(self.semantic_errors[6].r_type, "Tipos")
        self.assertEqual(self.semantic_errors[7].r_type, "Declaración")
        self.assertEqual(self.semantic_errors[8].r_type, "Tamaños")
        self.assertEqual(self.semantic_errors[9].r_type, "Tamaños")
        self.assertEqual(self.semantic_errors[10].r_type, "Tamaños")
        self.assertEqual(self.semantic_errors[11].r_type, "Declaración")
        self.assertEqual(self.semantic_errors[12].r_type, "Índice")
        self.assertEqual(self.semantic_errors[13].r_type, "Índice")
        self.assertEqual(self.semantic_errors[14].r_type, "Índice")
        self.assertEqual(self.semantic_errors[15].r_type, "Índice")
        self.assertEqual(self.semantic_errors[16].r_type, "Índice")
        self.assertEqual(self.semantic_errors[17].r_type, "Índice")
        self.assertEqual(self.semantic_errors[18].r_type, "Tamaños")
        self.assertEqual(self.semantic_errors[19].r_type, "Tamaños")
        self.assertEqual(self.semantic_errors[20].r_type, "Tamaños")
        self.assertEqual(self.semantic_errors[21].r_type, "Tamaños")
        self.assertEqual(self.semantic_errors[22].r_type, "Tamaños")
        self.assertEqual(self.semantic_errors[23].r_type, "Tamaños")

    def test_error_message(self):
        self.assertEqual(
            self.semantic_errors[0].message, "El array ya ha sido declarado")
        self.assertEqual(
            self.semantic_errors[1].message, "No se ha introducido el tamaño del array")
        self.assertEqual(
            self.semantic_errors[2].message, "El array ya ha sido declarado")
        self.assertEqual(
            self.semantic_errors[3].message, "El tipo del array es char, pero su valor no es char o int")
        self.assertEqual(
            self.semantic_errors[4].message, "El array no está declarado")
        self.assertEqual(self.semantic_errors[5].message,
                         "El tipo del índice debe ser int (o cualquiera que sea compatible)")
        self.assertEqual(
            self.semantic_errors[6].message, "El tipo de la variable y del valor no coincide")
        self.assertEqual(
            self.semantic_errors[7].message, "El array no está declarado")
        self.assertEqual(
            self.semantic_errors[8].message, "El índice sobrepasa el tamaño del array")
        self.assertEqual(
            self.semantic_errors[9].message, "El índice sobrepasa el tamaño del array")
        self.assertEqual(
            self.semantic_errors[10].message, "El índice sobrepasa el tamaño del array")
        self.assertEqual(
            self.semantic_errors[11].message, "El array no está declarado")
        self.assertEqual(self.semantic_errors[12].message,
                         "El tipo del índice debe ser int (o cualquiera que sea compatible)")
        self.assertEqual(self.semantic_errors[13].message,
                         "El tipo del índice debe ser int (o cualquiera que sea compatible)")
        self.assertEqual(self.semantic_errors[14].message,
                         "El tipo del índice debe ser int (o cualquiera que sea compatible)")
        self.assertEqual(self.semantic_errors[15].message,
                         "El tipo del índice debe ser int (o cualquiera que sea compatible)")
        self.assertEqual(self.semantic_errors[16].message,
                         "El tipo del índice debe ser int (o cualquiera que sea compatible)")
        self.assertEqual(self.semantic_errors[17].message,
                         "El tipo del índice debe ser int (o cualquiera que sea compatible)")
        self.assertEqual(
            self.semantic_errors[18].message, "El índice sobrepasa el tamaño del array")
        self.assertEqual(
            self.semantic_errors[19].message, "El índice sobrepasa el tamaño del array")
        self.assertEqual(
            self.semantic_errors[20].message, "El índice sobrepasa el tamaño del array")
        self.assertEqual(
            self.semantic_errors[21].message, "El índice sobrepasa el tamaño del array")
        self.assertEqual(
            self.semantic_errors[22].message, "El índice sobrepasa el tamaño del array")
        self.assertEqual(
            self.semantic_errors[23].message, "El índice sobrepasa el tamaño del array")


class TestLibraryFunctionErrors(TestBaseErrors):
    file = tests_path("error-tests", "library-function.txt")

    def test_number_of_errors(self):
        self.assertEqual(len(self.semantic_errors), 5)

    def test_r_types(self):
        self.assertEqual(self.semantic_errors[0].r_type, "Declaración")
        self.assertEqual(self.semantic_errors[1].r_type, "Parámetros")
        self.assertEqual(self.semantic_errors[2].r_type, "Declaración")
        self.assertEqual(self.semantic_errors[3].r_type, "Parámetros")
        self.assertEqual(self.semantic_errors[4].r_type, "Tipos")

    def test_error_messages(self):
        self.assertEqual(
            self.semantic_errors[0].message, "La función no se ha declarado")
        self.assertEqual(self.semantic_errors[1].message,
                         "El número de parámetros no coincide con los de la definición")
        self.assertEqual(
            self.semantic_errors[2].message, "La función no se ha declarado")
        self.assertEqual(self.semantic_errors[3].message,
                         "El número de parámetros no coincide con los de la definición")
        self.assertEqual(
            self.semantic_errors[4].message, "El tipo del parámetro y del valor no coincide")


class TestPositiveCases(TestBaseErrors):
    file = tests_path("error-tests", "mobile-ok.txt")

    def test_number_of_errors(self):
        self.assertEqual(len(self.semantic_errors), 0)

        self.file = tests_path("error-tests", "labyrinth-ok.txt")
        self.setUp()
        self.assertEqual(len(self.semantic_errors), 0)

        self.file = tests_path("error-tests", "pruebas-ok.txt")
        self.setUp()
        self.assertEqual(len(self.semantic_errors), 0)

        self.file = tests_path("error-tests", "blinking-ok.txt")
        self.setUp()
        self.assertEqual(len(self.semantic_errors), 0)

        self.file = tests_path("error-tests", "mixed-ok.txt")
        self.setUp()
        self.assertEqual(len(self.semantic_errors), 0)
