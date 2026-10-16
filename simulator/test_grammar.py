import unittest

from path_helper import tests_path

from antlr4 import *
from compiler.ArduinoLexer import ArduinoLexer
from compiler.ArduinoListenerTests import ArduinoListenerTests
from compiler.ArduinoParser import ArduinoParser


class TestBase(unittest.TestCase):

    def setUp(self):
        input = FileStream(fileName=self.file, encoding="utf-8")
        lexer = ArduinoLexer(input)
        stream = CommonTokenStream(lexer)
        parser = ArduinoParser(stream)
        listener = ArduinoListenerTests()
        walker = ParseTreeWalker()
        tree = parser.program()
        walker.walk(listener, tree)
        self.tokens = listener.tokens

    def tearDown(self):
        return super().tearDown()

    def read_results(self, file_name):
        file = open(file_name, "r")
        self.lines = []
        for line in file:
            self.lines.append(line.rstrip('\n'))
        file.close()


class TestArray(TestBase):
    file = tests_path("grammar-tests", "ejemploArrays.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputArrays.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestFor(TestBase):
    file = tests_path("grammar-tests", "ejemploFor.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputFor.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestWhile(TestBase):
    file = tests_path("grammar-tests", "ejemploWhile.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputWhile.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestDoWhile(TestBase):
    file = tests_path("grammar-tests", "ejemploDoWhile.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputDoWhile.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestIf(TestBase):
    file = tests_path("grammar-tests", "ejemploIf.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputIf.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestElse(TestBase):
    file = tests_path("grammar-tests", "ejemploElse.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputElse.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestSwitchCase(TestBase):
    file = tests_path("grammar-tests", "ejemploSwitchCase.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputSwitchCase.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestBreakContinue(TestBase):
    file = tests_path("grammar-tests", "ejemploBreakContinue.txt")

    def test_parsed(self):
        self.read_results(
            tests_path("grammar-tests", "outputs", "outputBreakContinue.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestReturn(TestBase):
    file = tests_path("grammar-tests", "ejemploReturn.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputReturn.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestAritmetico(TestBase):
    file = tests_path("grammar-tests", "ejemploAritmetico.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputAritmetico.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestComparisonBool(TestBase):
    file = tests_path("grammar-tests", "ejemploComparisonBool.txt")

    def test_parsed(self):
        self.read_results(
            tests_path("grammar-tests", "outputs", "outputComparisonBool.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestBitwise(TestBase):
    file = tests_path("grammar-tests", "ejemploBitwise.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputBitwise.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestCompound(TestBase):
    file = tests_path("grammar-tests", "ejemploCompound.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputCompound.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestVariablesAsignacion(TestBase):
    file = tests_path("grammar-tests", "testVariablesAsignacion.txt")

    def test_parsed(self):
        self.read_results(
            tests_path("grammar-tests", "outputs", "outputVariablesAsignacion.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestFurtherSyntax(TestBase):
    file = tests_path("grammar-tests", "testFurtherSyntax.txt")

    def test_parsed(self):
        self.read_results(
            tests_path("grammar-tests", "outputs", "outputFurtherSyntax.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestArrayAccess(TestBase):
    file = tests_path("grammar-tests", "testArrays.txt")

    def test_parsed(self):
        self.read_results(tests_path("grammar-tests", "outputs", "outputTestArrays.txt"))
        self.assertEqual(self.tokens, self.lines)


class TestConversion(TestBase):
    file = tests_path("grammar-tests", "testConversion.txt")

    def test_parsed(self):
        print("done")
        self.read_results(tests_path("grammar-tests", "outputs", "outputTestConversion.txt"))
        self.assertEqual(self.tokens, self.lines)


if __name__ == '__main__':
    unittest.main()
