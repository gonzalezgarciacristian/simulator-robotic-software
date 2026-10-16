import unittest

from path_helper import tests_path

from antlr4 import *
from compiler.ArduinoLexer import ArduinoLexer
from compiler.ArduinoParser import ArduinoParser
import compiler.ast_builder_visitor as ast_builder_visitor
import compiler.error_listener as error_listener
import compiler.warnings as warnings
import compiler.semantical_errors as semantical_analysis
import compiler.code_generator as code_generator
import libraries.libs as libraries


class TestBase(unittest.TestCase):

    def setUp(self) -> None:
        errors = []
        self.warns = []

        input = FileStream(fileName=self.file, encoding="utf-8")

        lexer = ArduinoLexer(input)
        listener = error_listener.CompilerErrorListener(False)
        lexer.removeErrorListeners()
        lexer.addErrorListener(listener)

        stream = CommonTokenStream(lexer)
        parser = ArduinoParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(listener)

        visitor = ast_builder_visitor.ASTBuilderVisitor()

        lib_manager = libraries.LibraryManager()
        warning_analysis = warnings.WarningAnalyzer()
        sem_analysis = semantical_analysis.Semantic(lib_manager)

        code_gen = code_generator.CodeGenerator(lib_manager)

        tree = parser.program()
        errors.extend(listener.errors)
        if len(errors) < 1:
            ast = visitor.visitProgram(tree)
            sem_analysis.execute(ast)
            try:
                errors.extend(sem_analysis.errors)
            except AttributeError:
                pass
            else:
                if len(errors) < 1:
                    code_gen.visit_program(ast, None)
                    warning_analysis.visit_program(ast, None)
                    self.warns = warning_analysis.warnings

    def tearDown(self):
        return super().tearDown()


class TestWarnings(TestBase):
    file = tests_path("warning-tests", "test.txt")

    def test_n_errors(self):
        self.assertEqual(6, len(self.warns))

    def test_error_type(self):
        self.assertEqual("Uso", self.warns[0].r_type)
        self.assertEqual("Uso", self.warns[1].r_type)
        self.assertEqual("Uso", self.warns[2].r_type)
        self.assertEqual("No implementado", self.warns[3].r_type)
        self.assertEqual("No implementado", self.warns[4].r_type)
        self.assertEqual("No implementado", self.warns[5].r_type)

    def test_error_msg(self):
        self.assertEqual(
            "No es recomendable el uso de bucles (do while), aunque sea correcto", self.warns[0].message)
        self.assertEqual(
            "No es recomendable el uso de bucles (for), aunque sea correcto", self.warns[1].message)
        self.assertEqual(
            "No es recomendable el uso de bucles (while), aunque sea correcto", self.warns[2].message)
        self.assertEqual(
            "La función reserve de String no está implementada, con lo que no cumplirá con su funcionalidad",
            self.warns[3].message)
        self.assertEqual(
            "La función randomSeed de Standard no está implementada, con lo que no cumplirá con su funcionalidad",
            self.warns[4].message)
        self.assertEqual("La función write de Serial no está implementada, con lo que no cumplirá con su funcionalidad",
                         self.warns[5].message)
