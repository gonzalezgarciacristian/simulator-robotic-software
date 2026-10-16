import unittest

from path_helper import tests_path

from antlr4 import *
from compiler.ArduinoLexer import ArduinoLexer
from compiler.ArduinoParser import ArduinoParser
from compiler.ast import *
from compiler.ast_builder_visitor import ASTBuilderVisitor
from compiler.error_listener import CompilerErrorListener


class TestBaseAST(unittest.TestCase):

    def setUp(self):
        input = FileStream(fileName=self.file, encoding="utf-8")
        lexer = ArduinoLexer(input)
        stream = CommonTokenStream(lexer)
        parser = ArduinoParser(stream)
        visitor = ASTBuilderVisitor()
        tree = parser.program()
        self.ast = visitor.visitProgram(tree)

    def tearDown(self):
        return super().tearDown()


class TestInclude(TestBaseAST):
    file = tests_path("file-tests", "include.txt")

    def test_file_name(self):
        includes = self.ast.includes
        self.assertEqual(includes[0].file_name, "LibreriaDelIDE.h")
        self.assertEqual(includes[1].file_name, "ArchivoRandom.h")
        self.assertEqual(includes[2].file_name, "EstoEsUnaLibreria.h")
        self.assertEqual(includes[3].file_name, "iostream.h")


class TestGlobalDefinition(TestBaseAST):
    file = tests_path("file-tests", "g-def.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_type(self):
        self.assertTrue(
            isinstance(self.code[0].declaration.type,
                       IntTypeNode), "No es del tipo int"
        )
        self.assertTrue(
            isinstance(self.code[1].declaration.type,
                       StringTypeNode), "No es del tipo string"
        )
        self.assertTrue(
            isinstance(self.code[2].declaration.type,
                       DoubleTypeNode), "No es del tipo double"
        )
        self.assertTrue(
            isinstance(self.code[3].declaration.type,
                       BooleanTypeNode), "No es del tipo Boolean"
        )
        self.assertTrue(
            isinstance(self.code[4].declaration.type,
                       CharTypeNode), "No es del tipo char"
        )
        self.assertTrue(
            isinstance(self.code[5].declaration.type,
                       CharTypeNode), "No es del tipo char"
        )
        # define no prueba el tipo porque no tiene
        self.assertTrue(
            isinstance(self.code[7].declaration.type,
                       DoubleTypeNode), "No es del tipo double"
        )
        # define no prueba el tipo porque no tiene
        self.assertTrue(
            isinstance(self.code[9].declaration.type,
                       StringTypeNode), "No es del tipo string"
        )

    def test_var_name(self):
        self.assertEqual(self.code[0].declaration.var_name, "num")
        self.assertEqual(self.code[1].declaration.var_name, "saludo")
        self.assertEqual(self.code[2].declaration.var_name, "notas")
        self.assertEqual(self.code[3].declaration.var_name, "interruptores")
        self.assertEqual(self.code[4].declaration.var_name, "iniciales")
        self.assertEqual(self.code[5].declaration.var_name, "mensaje")
        self.assertEqual(self.code[6].macro.macro_name, "ledPin")
        self.assertEqual(self.code[7].declaration.var_name, "gravity")
        self.assertEqual(self.code[8].macro.macro_name, "arrayPins")
        self.assertEqual(self.code[9].declaration.var_name, "nombres")

    def test_is_constant(self):
        self.assertEqual(self.code[0].declaration.is_const, False)
        self.assertEqual(self.code[1].declaration.is_const, False)
        self.assertEqual(self.code[2].declaration.is_const, False)
        self.assertEqual(self.code[3].declaration.is_const, False)
        self.assertEqual(self.code[4].declaration.is_const, False)
        self.assertEqual(self.code[5].declaration.is_const, False)
        self.assertEqual(self.code[7].declaration.is_const, True)
        self.assertEqual(self.code[9].declaration.is_const, True)

    def test_value(self):
        self.assertEqual(self.code[0].declaration.expr, None)
        self.assertEqual(self.code[1].declaration.expr.value, "hola")
        self.assertEqual(self.code[6].macro.expr.value, 4)
        self.assertEqual(self.code[7].declaration.expr.value, 9.8)

    def test_array_index(self):
        self.assertEqual(self.code[2].declaration.size[0], 25)
        self.assertEqual(self.code[3].declaration.size[0], 5)
        self.assertEqual(self.code[4].declaration.size[0], 5)
        self.assertEqual(self.code[5].declaration.size[0], 10)
        self.assertEqual(self.code[9].declaration.size[0], 3)

    def test_array_elements(self):
        self.assertEqual(self.code[2].declaration.elements, [])
        self.assertEqual(
            list(
                map(
                    lambda elem: elem.value,
                    self.code[5].declaration.elements)
            ), ['T', 'r', 'a', 'e', ' ', 's', 'o', 'p', 'a', '\0']
        )
        self.assertEqual(
            list(
                map(
                    lambda elem: elem.value,
                    self.code[3].declaration.elements)
            ), [True, False, False, True, False]
        )
        self.assertEqual(
            list(
                map(
                    lambda elem: elem.value,
                    self.code[4].declaration.elements)
            ), ['E', 'A', 'M', 'A', 'P']
        )
        self.assertEqual(
            list(
                map(
                    lambda elem: elem.value,
                    self.code[8].macro.elements)
            ), [1, 3, 7, 10]
        )


class TestFunctionDefinition(TestBaseAST):
    file = tests_path("file-tests", "f-def.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_type(self):
        self.assertTrue(
            isinstance(self.code[0].function.type, VoidTypeNode),
            "El tipo no es void"
        )
        self.assertTrue(
            isinstance(self.code[1].function.type, VoidTypeNode),
            "El tipo no es void"
        )
        self.assertTrue(
            isinstance(self.code[2].function.type, IntTypeNode),
            "El tipo no es int"
        )
        self.assertTrue(
            isinstance(self.code[3].function.type, StringTypeNode),
            "El tipo no es string"
        )

    def test_name(self):
        self.assertEqual(self.code[0].function.name, "setup")
        self.assertEqual(self.code[1].function.name, "loop")
        self.assertEqual(self.code[2].function.name, "factorial")
        self.assertEqual(self.code[3].function.name, "outputPrint")

    def test_args(self):
        self.assertEqual(len(self.code[0].function.args), 0)
        self.assertEqual(
            list(
                map(
                    lambda arg: arg.var_name,
                    self.code[0].function.args
                )
            ), []
        )
        self.assertEqual(len(self.code[1].function.args), 0)
        self.assertEqual(
            list(
                map(
                    lambda arg: arg.var_name,
                    self.code[1].function.args
                )
            ), []
        )
        self.assertEqual(len(self.code[2].function.args), 1)
        self.assertEqual(
            list(
                map(
                    lambda arg: arg.var_name,
                    self.code[2].function.args
                )
            ), ["n"]
        )
        self.assertEqual(len(self.code[3].function.args), 2)
        self.assertEqual(
            list(
                map(
                    lambda arg: arg.var_name,
                    self.code[3].function.args
                )
            ), ["message", "b"]
        )

    def test_sentences(self):
        self.assertEqual(len(self.code[0].function.sentences), 0)
        self.assertEqual(len(self.code[1].function.sentences), 0)
        self.assertEqual(len(self.code[2].function.sentences), 0)
        self.assertEqual(len(self.code[3].function.sentences), 3)
        self.assertTrue(
            isinstance(
                self.code[3].function.sentences[0], DeclarationNode
            ), "No es una definicion"
        )
        self.assertTrue(
            isinstance(
                self.code[3].function.sentences[1], FunctionCallNode
            ), "No es una llamada"
        )
        self.assertTrue(
            isinstance(
                self.code[3].function.sentences[2], ReturnNode
            ), "No es un return"
        )


class TestTerminals(TestBaseAST):
    file = tests_path("file-tests", "terminals.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_class(self):
        self.assertTrue(isinstance(self.code[0].declaration.expr, BooleanNode))
        self.assertTrue(isinstance(self.code[1].declaration.expr, BooleanNode))
        self.assertTrue(isinstance(self.code[2].declaration.expr, IntNode))
        self.assertTrue(isinstance(self.code[3].declaration.expr, FloatNode))
        self.assertTrue(isinstance(self.code[4].declaration.expr, CharNode))
        self.assertTrue(isinstance(self.code[5].declaration.expr, StringNode))
        self.assertTrue(isinstance(self.code[6].declaration.expr, IDNode))
        self.assertTrue(isinstance(self.code[7].declaration.expr, HexNode))
        self.assertTrue(isinstance(self.code[8].declaration.expr, BinaryNode))
        self.assertTrue(isinstance(self.code[9].declaration.expr, OctalNode))

    def test_values(self):
        self.assertEqual(self.code[0].declaration.expr.value, True)
        self.assertEqual(self.code[1].declaration.expr.value, False)
        self.assertEqual(self.code[2].declaration.expr.value, 10)
        self.assertEqual(self.code[3].declaration.expr.value, 29.29)
        self.assertEqual(self.code[4].declaration.expr.value, 'D')
        self.assertEqual(self.code[5].declaration.expr.value, "Diego")
        self.assertEqual(self.code[6].declaration.expr.value, "c")
        self.assertEqual(hex(self.code[7].declaration.expr.value), "0xaf66")
        self.assertEqual(bin(self.code[8].declaration.expr.value), "0b1101")
        self.assertEqual(oct(self.code[9].declaration.expr.value), "0o767")

    def test_type_class(self):
        self.assertTrue(isinstance(
            self.code[0].declaration.type, BooleanTypeNode))
        self.assertTrue(isinstance(
            self.code[1].declaration.type, BooleanTypeNode))
        self.assertTrue(isinstance(self.code[2].declaration.type, IntTypeNode))
        self.assertTrue(isinstance(
            self.code[3].declaration.type, FloatTypeNode))
        self.assertTrue(isinstance(
            self.code[4].declaration.type, CharTypeNode))
        self.assertTrue(isinstance(
            self.code[5].declaration.type, StringTypeNode))
        self.assertTrue(isinstance(
            self.code[6].declaration.type, StringTypeNode))
        self.assertTrue(isinstance(self.code[7].declaration.type, IntTypeNode))
        self.assertTrue(isinstance(self.code[8].declaration.type, IntTypeNode))
        self.assertTrue(isinstance(self.code[9].declaration.type, IntTypeNode))


class TestFunctionCall(TestBaseAST):
    file = tests_path("file-tests", "f-calls.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_name(self):
        self.assertEqual(self.code[0].function.sentences[0].name.value, "f")
        self.assertEqual(
            self.code[0].function.sentences[1].name.value, "print")
        self.assertEqual(
            self.code[0].function.sentences[2].name.member.value, "toUpperCase")
        self.assertEqual(
            self.code[0].function.sentences[3].name.member.value, "toLowerCase")
        self.assertEqual(
            self.code[0].function.sentences[4].name.value, "params")

    def test_parameters(self):
        self.assertEqual(
            len(
                self.code[0].function.sentences[0].parameters
            ), 0
        )
        self.assertEqual(
            len(
                self.code[0].function.sentences[1].parameters
            ), 1
        )
        self.assertEqual(
            self.code[0].function.sentences[1].parameters[0].value, "hola")
        self.assertEqual(
            len(
                self.code[0].function.sentences[2].parameters
            ), 0
        )
        self.assertEqual(
            len(
                self.code[0].function.sentences[3].parameters
            ), 0
        )
        self.assertEqual(
            len(
                self.code[0].function.sentences[4].parameters
            ), 3
        )
        self.assertEqual(
            list(
                map(
                    lambda param: param.value,
                    self.code[0].function.sentences[4].parameters
                )
            ), [1, "hola", True]
        )

    def test_clase(self):
        self.assertEqual(
            type(self.code[0].function.sentences[0]), FunctionCallNode)
        self.assertEqual(
            type(self.code[0].function.sentences[1]), FunctionCallNode)
        self.assertEqual(
            self.code[0].function.sentences[2].name.element.value, "mensaje")
        self.assertEqual(
            self.code[0].function.sentences[3].name.element.element.value, "persona")
        self.assertEqual(
            self.code[0].function.sentences[3].name.element.member.value, "nombre")
        self.assertEqual(
            type(self.code[0].function.sentences[4]), FunctionCallNode)


class TestConditionals(TestBaseAST):
    file = tests_path("file-tests", "conditionals.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_condition(self):
        condition = self.code[0].function.sentences[0].condition
        self.assertEqual(
            str(condition.left.value)
            + condition.op
            + str(condition.right.value), "i>2"
        )
        condition = self.code[0].function.sentences[1].condition
        self.assertEqual(
            str(condition.left.value)
            + condition.op
            + str(condition.right.value), "d<29.69"
        )
        condition = self.code[0].function.sentences[2].condition
        self.assertEqual(condition.value, True)
        self.assertEqual(
            self.code[0].function.sentences[2].else_expr[0].condition.value, False
        )
        self.assertEqual(
            self.code[0].function.sentences[3].expression.value, "var"
        )

    def test_if_expr(self):
        self.assertEqual(
            self.code[0].function.sentences[0].if_expr[0].name.value, "doThis"
        )
        self.assertEqual(
            self.code[0].function.sentences[1].if_expr[0].name.value, "doThat"
        )
        self.assertEqual(
            self.code[0].function.sentences[2].if_expr[0].name.value, "doAlgo"
        )
        self.assertEqual(
            self.code[0].function.sentences[2].else_expr[0].if_expr[0].name.value, "print"
        )

    def test_else_expr(self):
        self.assertEqual(
            self.code[0].function.sentences[1].else_expr[0].name.value, "print"
        )
        self.assertEqual(
            self.code[0].function.sentences[2].else_expr[0].if_expr[0] is not None, True
        )
        self.assertEqual(
            self.code[0].function.sentences[2].else_expr[0].else_expr[0].name.value, "prueba"
        )

    def test_cases(self):
        cases = self.code[0].function.sentences[3].cases
        self.assertEqual(cases[0].type, "case")
        self.assertEqual(cases[0].expression.value, 1)
        self.assertEqual(cases[0].sentences[0].name.value, "print")
        self.assertEqual(cases[1].type, "case")
        self.assertEqual(cases[1].expression.value, 2)
        self.assertEqual(cases[1].sentences[0].name.value, "println")
        self.assertEqual(cases[2].type, "default")
        self.assertEqual(cases[2].expression, None)
        self.assertEqual(cases[2].sentences[0].name.value, "exit")


class TestBucles(TestBaseAST):
    file = tests_path("file-tests", "loops.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_while(self):
        condition = self.code[0].function.sentences[0].expression
        self.assertEqual(
            str(condition.left.value)
            + condition.op
            + str(condition.right.value), "i<f"
        )
        self.assertEqual(
            list(
                map(
                    lambda sent: sent.name.value,
                    self.code[0].function.sentences[0].sentences
                )
            ), ["yada", "heeh"]
        )

    def test_do_while(self):
        condition = self.code[0].function.sentences[1].expression
        self.assertEqual(
            str(condition.left.value)
            + condition.op
            + str(condition.right.value), "b||c"
        )
        self.assertEqual(
            list(
                map(
                    lambda sent: sent.name.value,
                    self.code[0].function.sentences[1].sentences
                )
            ), ["print"]
        )

    def test_for(self):
        self.assertEqual(
            self.code[0].function.sentences[2].assignment.var_name, "i")
        condition = self.code[0].function.sentences[2].condition
        self.assertEqual(
            str(condition.left.value)
            + condition.op
            + str(condition.right.value), "i<100"
        )
        expression = self.code[0].function.sentences[2].expression
        self.assertEqual(
            str(expression.left.value)
            + expression.op
            + str(expression.right.value), "i*=2"
        )
        self.assertEqual(
            list(
                map(
                    lambda sent: sent.name.value,
                    self.code[0].function.sentences[2].sentences
                )
            ), ["println"]
        )


class TestAsignations(TestBaseAST):
    file = tests_path("file-tests", "assignments.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_var_name(self):
        self.assertEqual(self.code[0].function.sentences[0].var_name, "i")
        self.assertEqual(self.code[0].function.sentences[1].var.value, "i")
        self.assertEqual(self.code[0].function.sentences[2].var_name, "x")
        self.assertEqual(self.code[0].function.sentences[3].var.value, "x")

    def test_expression(self):
        self.assertEqual(
            self.code[0].function.sentences[1].expr.name.value, "analogRead")
        self.assertEqual(self.code[0].function.sentences[3].expr.value, 2000)

    def test_left(self):
        for i in range(4, len(self.code[0].function.sentences)):
            self.assertEqual(
                self.code[0].function.sentences[i].left.value, "x")

    def test_op(self):
        self.assertEqual(self.code[0].function.sentences[4].op, "%=")
        self.assertEqual(self.code[0].function.sentences[5].op, "&=")
        self.assertEqual(self.code[0].function.sentences[6].op, "*=")
        self.assertEqual(self.code[0].function.sentences[7].op, "+=")
        self.assertEqual(self.code[0].function.sentences[8].op, "-=")
        self.assertEqual(self.code[0].function.sentences[9].op, "/=")
        self.assertEqual(self.code[0].function.sentences[10].op, "^=")
        self.assertEqual(self.code[0].function.sentences[11].op, "|=")

    def test_right(self):
        self.assertEqual(self.code[0].function.sentences[4].right.value, 10)
        self.assertEqual(
            bin(self.code[0].function.sentences[5].right.value), "0b1100")
        self.assertEqual(self.code[0].function.sentences[6].right.value, 5)
        self.assertEqual(self.code[0].function.sentences[7].right.value, 200)
        self.assertEqual(self.code[0].function.sentences[8].right.value, 100)
        self.assertEqual(self.code[0].function.sentences[9].right.value, 25)
        self.assertEqual(
            bin(self.code[0].function.sentences[10].right.value), "0b1010")
        self.assertEqual(
            bin(self.code[0].function.sentences[11].right.value), "0b1001")


class TestBitwise(TestBaseAST):
    file = tests_path("file-tests", "bitwise.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_class(self):
        for i in range(1, len(self.code[0].function.sentences) - 1):
            self.assertTrue(isinstance(
                self.code[0].function.sentences[i], BitwiseExpressionNode))

    def test_left(self):
        self.assertEqual(self.code[0].function.sentences[1].left.value, "i")
        self.assertEqual(self.code[0].function.sentences[2].left.value, "i")
        self.assertEqual(self.code[0].function.sentences[3].left.value, "i")
        self.assertEqual(self.code[0].function.sentences[4].left.value, "i")
        self.assertEqual(self.code[0].function.sentences[5].left.value, "i")

    def test_right(self):
        self.assertEqual(self.code[0].function.sentences[1].op, "<<")
        self.assertEqual(self.code[0].function.sentences[2].op, ">>")
        self.assertEqual(self.code[0].function.sentences[3].op, "^")
        self.assertEqual(self.code[0].function.sentences[4].op, "|")
        self.assertEqual(self.code[0].function.sentences[5].op, "&")

    def test_right(self):
        self.assertEqual(self.code[0].function.sentences[1].right.value, 2)
        self.assertEqual(self.code[0].function.sentences[2].right.value, 7)
        self.assertEqual(self.code[0].function.sentences[3].right.value, 50)
        self.assertEqual(self.code[0].function.sentences[4].right.value, 25)
        self.assertEqual(self.code[0].function.sentences[5].right.value, 215)

    def test_expression(self):
        self.assertEqual(
            self.code[0].function.sentences[6].expr.expression.value, "i")


class TestLocalDefinition(TestBaseAST):
    file = tests_path("file-tests", "local-def.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_types(self):
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[0].type,
                BooleanTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[1].type,
                BooleanTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[2].type,
                ByteTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[3].type,
                CharTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[4].type,
                DoubleTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[5].type,
                FloatTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[6].type,
                IntTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[7].type,
                LongTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[8].type,
                ShortTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[9].type,
                Size_tTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[10].type,
                StringTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[11].type,
                UCharTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[12].type,
                UIntTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[13].type,
                ULongTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[14].type,
                WordTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[15].type,
                DoubleTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[16].type,
                StringTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[17].type,
                CharTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[18].type,
                IntTypeNode
            )
        )
        self.assertTrue(
            isinstance(
                self.code[0].function.sentences[19].type,
                IntTypeNode
            )
        )

    def test_var_name(self):
        self.assertEqual(self.code[0].function.sentences[0].var_name, "b")
        self.assertEqual(self.code[0].function.sentences[1].var_name, "bo")
        self.assertEqual(self.code[0].function.sentences[2].var_name, "by")
        self.assertEqual(self.code[0].function.sentences[3].var_name, "c")
        self.assertEqual(self.code[0].function.sentences[4].var_name, "d")
        self.assertEqual(self.code[0].function.sentences[5].var_name, "f")
        self.assertEqual(self.code[0].function.sentences[6].var_name, "i")
        self.assertEqual(self.code[0].function.sentences[7].var_name, "l")
        self.assertEqual(self.code[0].function.sentences[8].var_name, "s")
        self.assertEqual(self.code[0].function.sentences[9].var_name, "size")
        self.assertEqual(self.code[0].function.sentences[10].var_name, "str")
        self.assertEqual(self.code[0].function.sentences[11].var_name, "uc")
        self.assertEqual(self.code[0].function.sentences[12].var_name, "ui")
        self.assertEqual(self.code[0].function.sentences[13].var_name, "ul")
        self.assertEqual(self.code[0].function.sentences[14].var_name, "w")
        self.assertEqual(self.code[0].function.sentences[15].var_name, "cIni")
        self.assertEqual(self.code[0].function.sentences[16].var_name, "str")
        self.assertEqual(self.code[0].function.sentences[17].var_name, "ch")
        self.assertEqual(
            self.code[0].function.sentences[18].var_name, "arraySimple")
        self.assertEqual(
            self.code[0].function.sentences[19].var_name, "arrayDoble")

    def test_value(self):
        self.assertEqual(self.code[0].function.sentences[1].expr.value, True)
        self.assertEqual(self.code[0].function.sentences[3].expr.value, 'd')
        self.assertEqual(self.code[0].function.sentences[4].expr.value, 29.73)
        self.assertEqual(self.code[0].function.sentences[6].expr.value, 1615)
        self.assertEqual(
            self.code[0].function.sentences[10].expr.value, "Diegui")
        self.assertEqual(
            self.code[0].function.sentences[15].expr.value, 29.456)
        self.assertEqual(self.code[0].function.sentences[17].expr.value, 'c')

    def test_elements(self):
        self.assertEqual(
            list(
                map(
                    lambda elem: elem.value,
                    self.code[0].function.sentences[18].elements
                )
            ), [1, 2, 3, 4, 5]
        )

    def test_is_constant(self):
        self.assertEqual(self.code[0].function.sentences[1].is_const, False)
        self.assertEqual(self.code[0].function.sentences[3].is_const, False)
        self.assertEqual(self.code[0].function.sentences[4].is_const, False)
        self.assertEqual(self.code[0].function.sentences[6].is_const, False)
        self.assertEqual(self.code[0].function.sentences[10].is_const, False)
        self.assertEqual(self.code[0].function.sentences[15].is_const, True)


class TestIncDec(TestBaseAST):
    file = tests_path("file-tests", "incdec.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_var(self):
        self.assertEqual(self.code[0].function.sentences[0].var.value, "i")
        self.assertEqual(self.code[0].function.sentences[1].var.value, "a")
        self.assertEqual(self.code[0].function.sentences[2].var.value, "z")
        self.assertEqual(self.code[0].function.sentences[3].var.value, "w")

    def test_op(self):
        self.assertEqual(self.code[0].function.sentences[0].op, "++")
        self.assertEqual(self.code[0].function.sentences[1].op, "--")
        self.assertEqual(self.code[0].function.sentences[2].op, "++")
        self.assertEqual(self.code[0].function.sentences[3].op, "--")


class TestSpecials(TestBaseAST):
    file = tests_path("file-tests", "specials.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_specials(self):
        self.assertTrue(isinstance(
            self.code[0].function.sentences[0], BreakNode))
        self.assertTrue(isinstance(
            self.code[0].function.sentences[1], ContinueNode))
        self.assertTrue(isinstance(
            self.code[0].function.sentences[2], ReturnNode))
        self.assertEqual(
            self.code[0].function.sentences[2].expression.value, 1)
        self.assertTrue(isinstance(
            self.code[0].function.sentences[3], ReturnNode))
        self.assertEqual(self.code[0].function.sentences[3].expression, None)


class TestAritmetic(TestBaseAST):
    file = tests_path("file-tests", "aritmetics.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_left(self):
        self.assertEqual(self.code[0].function.sentences[0].left.value, 225)
        self.assertEqual(self.code[0].function.sentences[1].left.value, "i")
        self.assertEqual(self.code[0].function.sentences[2].left.value, "i")
        self.assertEqual(self.code[0].function.sentences[3].left.value, 255)
        self.assertEqual(self.code[0].function.sentences[4].left.value, "f")
        self.assertEqual(self.code[0].function.sentences[5].left.value, "f")
        self.assertEqual(
            self.code[0].function.sentences[5].right.left.value, "a")

    def test_op(self):
        self.assertEqual(self.code[0].function.sentences[0].op, "%")
        self.assertEqual(self.code[0].function.sentences[1].op, "*")
        self.assertEqual(self.code[0].function.sentences[2].op, "+")
        self.assertEqual(self.code[0].function.sentences[3].op, "-")
        self.assertEqual(self.code[0].function.sentences[4].op, "/")
        self.assertEqual(self.code[0].function.sentences[5].op, "+")
        self.assertEqual(self.code[0].function.sentences[5].right.op, "/")

    def test_right(self):
        self.assertEqual(self.code[0].function.sentences[0].right.value, 350)
        self.assertEqual(self.code[0].function.sentences[1].right.value, "f")
        self.assertEqual(self.code[0].function.sentences[2].right.value, "a")
        self.assertEqual(self.code[0].function.sentences[3].right.value, "x")
        self.assertEqual(self.code[0].function.sentences[4].right.value, 30)
        self.assertEqual(
            self.code[0].function.sentences[5].right.right.value, 5)


class TestBoolean(TestBaseAST):
    file = tests_path("file-tests", "boolean.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_left(self):
        self.assertEqual(self.code[0].function.sentences[0].left.value, "x")
        self.assertEqual(self.code[0].function.sentences[1].left.value, "z")
        self.assertEqual(self.code[0].function.sentences[2].left.value, "x")
        self.assertEqual(self.code[0].function.sentences[3].left.value, 200)
        self.assertEqual(self.code[0].function.sentences[4].left.value, 0)
        self.assertEqual(self.code[0].function.sentences[5].left.value, 199)
        self.assertEqual(self.code[0].function.sentences[6].left.value, True)
        sent = self.code[0].function.sentences[7].left
        self.assertEqual(
            str(sent.left.value)
            + sent.op
            + str(sent.right.value),
            "x>29"
        )
        self.assertEqual(
            self.code[0].function.sentences[8].expression.value, "var")

    def test_op(self):
        self.assertEqual(self.code[0].function.sentences[0].op, ">")
        self.assertEqual(self.code[0].function.sentences[1].op, "<")
        self.assertEqual(self.code[0].function.sentences[2].op, ">=")
        self.assertEqual(self.code[0].function.sentences[3].op, "<=")
        self.assertEqual(self.code[0].function.sentences[4].op, "==")
        self.assertEqual(self.code[0].function.sentences[5].op, "!=")
        self.assertEqual(self.code[0].function.sentences[6].op, "&&")
        self.assertEqual(self.code[0].function.sentences[7].op, "||")
        self.assertEqual(self.code[0].function.sentences[7].right.op, "&&")

    def test_right(self):
        self.assertEqual(self.code[0].function.sentences[0].right.value, "y")
        self.assertEqual(self.code[0].function.sentences[1].right.value, "w")
        self.assertEqual(self.code[0].function.sentences[2].right.value, 200)
        self.assertEqual(self.code[0].function.sentences[3].right.value, "y")
        self.assertEqual(self.code[0].function.sentences[4].right.value, 1)
        self.assertEqual(self.code[0].function.sentences[5].right.value, 200)
        self.assertEqual(self.code[0].function.sentences[6].right.value, False)
        sent = self.code[0].function.sentences[7].right
        self.assertEqual(
            str(sent.left.left.value) + sent.left.op
            + str(sent.left.right.value)
            + sent.op
            + str(sent.right.left.value) + sent.right.op
            + str(sent.right.right.value),
            "y!=0&&z<w"
        )


class TestArrays(TestBaseAST):
    file = tests_path("file-tests", "arrays.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_variable_names(self):
        self.assertEqual(self.code[0].declaration.var_name, "arr1")
        self.assertEqual(self.code[1].declaration.var_name, "arr1b")
        self.assertEqual(self.code[2].declaration.var_name, "arr1c")
        self.assertEqual(self.code[3].declaration.var_name, "arr2")
        self.assertEqual(self.code[4].declaration.var_name, "arr2b")
        self.assertEqual(self.code[5].declaration.var_name, "arr3")
        self.assertEqual(self.code[6].declaration.var_name, "arr3b")
        self.assertEqual(self.code[7].declaration.var_name, "arr4")
        self.assertEqual(self.code[8].declaration.var_name, "arr5")
        self.assertEqual(self.code[9].declaration.var_name, "arr3d1d")
        self.assertEqual(self.code[10].declaration.var_name, "arr3d")

    def test_dimensions(self):
        self.assertEqual(self.code[0].declaration.dimensions, 1)
        self.assertEqual(self.code[1].declaration.dimensions, 1)
        self.assertEqual(self.code[2].declaration.dimensions, 1)
        self.assertEqual(self.code[3].declaration.dimensions, 2)
        self.assertEqual(self.code[4].declaration.dimensions, 2)
        self.assertEqual(self.code[5].declaration.dimensions, 2)
        self.assertEqual(self.code[6].declaration.dimensions, 2)
        self.assertEqual(self.code[7].declaration.dimensions, 2)
        self.assertEqual(self.code[8].declaration.dimensions, 1)
        self.assertEqual(self.code[9].declaration.dimensions, 3)
        self.assertEqual(self.code[10].declaration.dimensions, 3)

    def test_sizes(self):
        self.assertEqual(len(self.code[0].declaration.size), 1)
        self.assertEqual(self.code[0].declaration.size, [25])
        self.assertEqual(len(self.code[1].declaration.size), 1)
        self.assertEqual(self.code[1].declaration.size, [4])
        self.assertEqual(len(self.code[2].declaration.size), 1)
        self.assertEqual(self.code[2].declaration.size, [4])
        self.assertEqual(len(self.code[3].declaration.size), 2)
        self.assertEqual(self.code[3].declaration.size, [4, 2])
        self.assertEqual(len(self.code[4].declaration.size), 2)
        self.assertEqual(self.code[4].declaration.size, [4, 2])
        self.assertEqual(len(self.code[5].declaration.size), 2)
        self.assertEqual(self.code[5].declaration.size, [2, 3])
        self.assertEqual(len(self.code[6].declaration.size), 2)
        self.assertEqual(self.code[6].declaration.size, [3, 2])
        self.assertEqual(len(self.code[7].declaration.size), 2)
        self.assertEqual(self.code[7].declaration.size, [2, 2])
        self.assertEqual(len(self.code[8].declaration.size), 1)
        self.assertEqual(self.code[8].declaration.size, [6])
        self.assertEqual(len(self.code[9].declaration.size), 3)
        self.assertEqual(self.code[9].declaration.size, [2, 3, 2])
        self.assertEqual(len(self.code[10].declaration.size), 3)
        self.assertEqual(self.code[10].declaration.size, [2, 2, 3])

    def test_elements(self):
        self.assertEqual(self.code[0].declaration.elements, [])
        self.assertEqual(
            list(
                map(
                    lambda elem: elem.value, self.code[1].declaration.elements)
            ), [1, 5, 7, 10])
        self.assertEqual(
            list(
                map(
                    lambda elem: elem.value, self.code[2].declaration.elements)
            ), [2, 4, 6, 8])
        array_to_test = self.__build_array_for_test(
            self.code[3].declaration.elements)
        self.assertEqual(array_to_test, [[1, 2], [3, 4], [5, 6], [7, 8]])
        array_to_test = self.__build_array_for_test(
            self.code[4].declaration.elements)
        self.assertEqual(array_to_test, [[1, 2], [3, 4], [5, 6], [7, 8]])
        array_to_test = self.__build_array_for_test(
            self.code[5].declaration.elements)
        self.assertEqual(array_to_test, [[1, 2, 3], [4, 0, 0]])
        array_to_test = self.__build_array_for_test(
            self.code[6].declaration.elements)
        self.assertEqual(array_to_test, [[1, 2], [3, 4], [5, 0]])
        array_to_test = self.__build_array_for_test(
            self.code[7].declaration.elements)
        self.assertEqual(array_to_test, [[1, 2], [4, 0]])
        self.assertEqual(
            list(
                map(
                    lambda elem: elem.value, self.code[8].declaration.elements)
            ), ['h', 'e', 'l', 'l', 'o', '\0'])
        array_to_test = self.__build_array_for_test(
            self.code[9].declaration.elements)
        self.assertEqual(array_to_test, [
            [
                [1, 2],
                [3, 4],
                [5, 6]
            ],
            [
                [7, 8],
                [9, 10],
                [0, 0]
            ]
        ])
        array_to_test = self.__build_array_for_test(
            self.code[10].declaration.elements)
        self.assertEqual(array_to_test, [
            [
                [1, 2, 3],
                [4, 5, 6]
            ],
            [
                [7, 8, 9],
                [10, 11, 12]
            ]
        ])

    def __build_array_for_test(self, elements):
        array_to_test = []
        for e in elements:
            if isinstance(e, list):
                array_to_test.append(self.__build_array_for_test(e))
            else:
                array_to_test.append(e.value)
        return array_to_test


class TestArrayAccess(TestBaseAST):
    file = tests_path("file-tests", "array-access.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_var(self):
        self.assertEqual(
            self.code[0].function.sentences[0].value, "acceso_a_array")
        self.assertEqual(
            self.code[0].function.sentences[1].value, "acc_arr_2")
        self.assertEqual(
            self.code[0].function.sentences[2].value, "random")

    def test_index(self):
        self.assertEqual(
            self.code[0].function.sentences[0].indexes[0].value, 1)
        self.assertEqual(
            self.code[0].function.sentences[1].indexes[0].value, 2)
        self.assertEqual(
            self.code[0].function.sentences[1].indexes[1].value, 5)
        self.assertEqual(
            self.code[0].function.sentences[2].indexes[0].value, 1)
        self.assertEqual(
            self.code[0].function.sentences[2].indexes[1].value, 0)
        self.assertEqual(
            self.code[0].function.sentences[2].indexes[2].value, 3)


class TestConversion(TestBaseAST):
    file = tests_path("file-tests", "conversions.txt")

    def setUp(self):
        super().setUp()
        self.code = self.ast.code

    def test_type(self):
        self.assertTrue(
            isinstance(self.code[0].function.sentences[0].conv_type,
            UIntTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[0].function.sentences[1].conv_type,
            ULongTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[0].function.sentences[2].conv_type,
            ByteTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[0].function.sentences[3].conv_type,
            CharTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[0].function.sentences[4].conv_type,
            FloatTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[0].function.sentences[5].conv_type,
            IntTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[0].function.sentences[6].conv_type,
            LongTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[0].function.sentences[7].conv_type,
            WordTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[1].function.sentences[0].parameters[0].right.conv_type,
            StringTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[1].function.sentences[1].conv_type,
            ByteTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[1].function.sentences[2].conv_type,
            CharTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[1].function.sentences[3].conv_type,
            FloatTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[1].function.sentences[4].conv_type,
            IntTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[1].function.sentences[5].conv_type,
            LongTypeNode)
        )
        self.assertTrue(
            isinstance(self.code[1].function.sentences[6].conv_type,
            WordTypeNode)
        )

    def test_expr(self):
        self.assertEqual(
            self.code[0].function.sentences[0].expr.value,
            10
        )
        self.assertEqual(
            self.code[0].function.sentences[1].expr.value,
            350
        )
        self.assertEqual(
            self.code[0].function.sentences[2].expr.value,
            0
        )
        self.assertEqual(
            self.code[0].function.sentences[3].expr.value,
            55
        )
        self.assertEqual(
            self.code[0].function.sentences[4].expr.value,
            29
        )
        self.assertEqual(
            self.code[0].function.sentences[5].expr.value,
            151
        )
        self.assertEqual(
            self.code[0].function.sentences[6].expr.value,
            2487
        )
        self.assertEqual(
            self.code[0].function.sentences[7].expr.value,
            1456
        )
        self.assertEqual(
            self.code[1].function.sentences[0].parameters[0].left.value,
            "Hola"
        )
        self.assertEqual(
            self.code[1].function.sentences[1].expr.value,
            1
        )
        self.assertEqual(
            self.code[1].function.sentences[2].expr.value,
            108
        )
        self.assertEqual(
            self.code[1].function.sentences[3].expr.value,
            46468
        )
        self.assertEqual(
            self.code[1].function.sentences[4].expr.value,
            69
        )
        self.assertEqual(
            self.code[1].function.sentences[5].expr.value,
            1114
        )
        self.assertEqual(
            self.code[1].function.sentences[6].expr.value,
            6468
        )


if __name__ == '__main__':
    unittest.main()
