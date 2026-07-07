# coding: utf-8

import sys

sys.path.append(".")
sys.path.append("./simulator")

from antlr4 import *
from compiler.ArduinoLexer import ArduinoLexer
from compiler.ArduinoParser import ArduinoParser
import compiler.ast_builder_visitor as ast_builder_visitor
import compiler.error_listener as error_listener
import compiler.warnings as warnings
import compiler.semantical_errors as semantical_analysis
import compiler.code_generator as code_generator
import libraries.libs as libraries


def transpile(code):
    errors = []
    warns = []
    ast = None
    input = InputStream(code)

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
            if not errors:
                code_gen.visit_program(ast, None)
                warning_analysis.visit_program(ast, None)
                warns = warning_analysis.warnings

    return warns, errors, ast


def test():
    test_code = open('tests/grammar-tests/ejemPeque.txt', 'r').read()
    arbol = transpile(test_code)
    visitor = ast_builder_visitor.ASTBuilderVisitor()
    ast = visitor.visitProgram(arbol)
    lib_manager = libraries.LibraryManager()
    warning_analysis = warnings.WarningAnalyzer()
    sem_analysis = semantical_analysis.Semantic(lib_manager)
    return sem_analysis.execute(ast)

