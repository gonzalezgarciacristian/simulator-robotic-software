# coding: utf-8


# from ast import operator
# from cmath import exp
from functools import reduce
from operator import le
from typing import List
from antlr4 import *
from .ArduinoVisitor import ArduinoVisitor

from .ast import *

if __name__ is not None and "." in __name__:
    from .ArduinoParser import ArduinoParser
else:
    from ArduinoParser import ArduinoParser


# This class defines a complete generic visitor for a parse tree produced by ArduinoParser.

class ASTBuilderVisitor(ArduinoVisitor):

    def visit(self, tree):
        """Compatibilidad con parsers generados sin métodos `accept()` específicos.

        Parte del código heredado invoca `visitor.visit(tree)` sobre contextos del
        parser. En este repositorio, el parser generado no expone los `accept()`
        especializados por regla y, si delegamos en el comportamiento genérico de
        ANTLR, la visita acaba en `visitChildren()` y el AST raíz puede quedar en
        `None`.

        Para mantener el contrato esperado por los tests heredados y por el resto
        del compilador, despachamos explícitamente al método `visit<Rule>` cuando
        exista para el contexto recibido.
        """
        if tree is None:
            return None
        ctx_name = type(tree).__name__
        if ctx_name.endswith("Context"):
            method_name = "visit" + ctx_name[:-7]
            visitor = getattr(self, method_name, None)
            if callable(visitor):
                return visitor(tree)
        return super().visit(tree)

    # Visit a parse tree produced by ArduinoParser#start.
    def visitStart(self, ctx: ArduinoParser.StartContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by ArduinoParser#program.
    def visitProgram(self, ctx: ArduinoParser.ProgramContext):
        decs = []
        if ctx.include_directives is not None:
            for include_s in ctx.include_directives:
                decs.append(self.visitInclude(include_s))
        code = []
        if ctx.code is not None:
            for sent in ctx.code:
                code.append(self.visitProgram_code(sent))
        node = ProgramNode(decs, code)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#include.
    def visitInclude(self, ctx: ArduinoParser.IncludeContext):
        file = None
        if ctx.ID(0) is not None and ctx.ID(1) is not None:
            file = ctx.ID(0).getText() + "." + ctx.ID(1).getText()
        if ctx.STRING_CONST() is not None:
            file = ctx.STRING_CONST().getText()
            file = file.replace('"', '')
        node = IncludeNode(file)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#program_code.
    def visitProgram_code(self, ctx: ArduinoParser.Program_codeContext):
        declaration = function = macro = None
        if ctx.var_dec is not None:
            declaration = self.visitDeclaration(ctx.var_dec)
        if ctx.func_def is not None:
            function = self.visitFunction(ctx.func_def)
        if ctx.def_mac is not None:
            macro = self.visitDefine_macro(ctx.def_mac)
        node = ProgramCodeNode(declaration, function, macro)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#declaration.
    def visitDeclaration(self, ctx: ArduinoParser.DeclarationContext):
        node = None
        if ctx.declaration() is not None:
            node = self.visitDeclaration(ctx.declaration())
        if ctx.s_def is not None:
            node = self.visitSimple_declaration(ctx.s_def)
        if ctx.a_def is not None:
            node = self.visitArray_declaration(ctx.a_def)
        if ctx.qual is not None:
            if node is not None and ctx.qual.text == "const":
                node.is_const = True
            if node is not None and ctx.qual.text == "static":
                node.is_static = True
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#simple_declaration.
    def visitSimple_declaration(self, ctx: ArduinoParser.Simple_declarationContext):
        v_type = var_name = expr = None
        if ctx.ptr_type is not None:
            v_type = StringTypeNode()
        elif ctx.v_type is not None:
            v_type = self.visitVar_type(ctx.v_type)
        if ctx.var_name is not None:
            var_name = ctx.var_name.text
        if ctx.val is not None:
            expr = self.visitExpression(ctx.val)
        node = DeclarationNode(type=v_type, var_name=var_name, expr=expr)
        if ctx.ptr_type is not None:
            node.is_reference = True
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#array_declaration.
    def visitArray_declaration(self, ctx: ArduinoParser.Array_declarationContext):
        elements = sizes = []
        v_type = var_name = dimensions = None
        is_constant = False
        if ctx.v_type is not None:
            v_type = self.visitVar_type(ctx.v_type)
        if ctx.var_name is not None:
            var_name = ctx.var_name.text
        if ctx.elems is not None:
            elements = self.visitArray_elements(ctx.elems)
        if ctx.a_index is not None:
            arr_tuple = self.visitArray_index(ctx.a_index)
            sizes = arr_tuple[0]
            dimensions = arr_tuple[1]
        if ctx.expr is not None:
            expr = ctx.expr.getText().replace('"', '')
            for character in expr:
                elements.append(CharNode(character))
        if ctx.expr is None and ctx.elems is None:
            elements = None
        node = ArrayDeclarationNode(
            v_type, var_name, dimensions, sizes, elements, is_constant)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#define_declaration.
    def visitDefine_macro(self, ctx: ArduinoParser.Define_macroContext):
        name = value = None
        elems = []
        if ctx.ID() is not None:
            name = ctx.ID().getText()
        if ctx.val is not None:
            value = self.visitExpression(ctx.val)
        if ctx.elems is not None:
            elems = self.visitArray_elements(ctx.elems)
        node = DefineMacroNode(name, value, elems)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#array_index.
    def visitArray_index(self, ctx: ArduinoParser.Array_indexContext):
        sizes = []
        dimension = 1
        if ctx.sizes is not None:
            for size in ctx.sizes:
                sizes.append(int(size.text))
        if ctx.dimensions is not None:
            dimension = len(ctx.dimensions)
        return sizes, dimension

    # Visit a parse tree produced by ArduinoParser#array_elements.
    def visitArray_elements(self, ctx: ArduinoParser.Array_elementsContext):
        elements = []
        if ctx.array_elements() is not None:
            for elem in ctx.array_elements():
                elements.append(self.visitArray_elements(elem))
        if ctx.elements is not None:
            for elem in ctx.elements:
                elements.append(self.visitExpression(elem))
        return elements

    # Visit a parse tree produced by ArduinoParser#var_type.
    def visitVar_type(self, ctx: ArduinoParser.Var_typeContext):
        node = None
        if ctx.ID() is not None:
            node = IDTypeNode(ctx.ID().getText())
        if ctx.getText() == "bool" or ctx.getText() == "boolean":
            node = BooleanTypeNode()
        if ctx.getText() == "byte":
            node = ByteTypeNode()
        if ctx.getText() == "char":
            node = CharTypeNode()
        if ctx.getText() == "double":
            node = DoubleTypeNode()
        if ctx.getText() == "float":
            node = FloatTypeNode()
        if ctx.getText() == "int":
            node = IntTypeNode()
        if ctx.getText() == "long":
            node = LongTypeNode()
        if ctx.getText() == "short":
            node = ShortTypeNode()
        if ctx.getText() == "size_t":
            node = Size_tTypeNode()
        if ctx.getText() == "String":
            node = StringTypeNode()
        if ctx.getText() == "unsigned int":
            node = UIntTypeNode()
        if ctx.getText() == "unsigned char":
            node = UCharTypeNode()
        if ctx.getText() == "unsigned long":
            node = ULongTypeNode()
        if ctx.getText() == "void":
            node = VoidTypeNode()
        if ctx.getText() == "word":
            node = WordTypeNode()
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#function.
    def visitFunction(self, ctx: ArduinoParser.FunctionContext):
        v_type = f_name = None
        args = []
        sentences = []
        if ctx.ptr_type is not None:
            v_type = StringTypeNode()
        elif ctx.v_type is not None:
            v_type = self.visitVar_type(ctx.v_type)
        if ctx.f_name is not None:
            f_name = ctx.f_name.text
        if ctx.f_args is not None:
            args = self.visitFunction_args(ctx.f_args)
        if ctx.sentences is not None:
            for sent in ctx.sentences:
                sentences.append(self.visitSentence(sent))
        node = FunctionNode(v_type, f_name, args=args, sentences=sentences)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#function_args.
    def visitFunction_args(self, ctx: ArduinoParser.Function_argsContext):
        args = []
        if ctx.f_args is not None:
            for arg in ctx.f_args:
                args.append(self.visitFunction_arg(arg))
        return args

    def visitFunction_arg(self, ctx: ArduinoParser.Function_argContext):
        v_type = var_name = expr = None
        if ctx.ptr_type is not None:
            v_type = StringTypeNode()
        elif ctx.v_type is not None:
            v_type = self.visitVar_type(ctx.v_type)
        if ctx.var_name is not None:
            var_name = ctx.var_name.text
        if ctx.val is not None:
            expr = self.visitExpression(ctx.val)
        node = DeclarationNode(type=v_type, var_name=var_name, expr=expr)
        if ctx.reference_ref() is not None and not getattr(node, "is_const", False):
            node.is_reference = True
        if ctx.qual is not None:
            if ctx.qual.text == "const":
                node.is_const = True
            if ctx.qual.text == "static":
                node.is_static = True
            if ctx.qual.text == "const":
                node.is_reference = False
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#iteration_sentence.
    def visitIteration_sentence(self, ctx: ArduinoParser.Iteration_sentenceContext):
        node = expr = a_def = cond = None
        it_type = ctx.it_type.text
        sents = []
        if ctx.code is not None:
            sents = self.visitCode_block(ctx.code)
        if ctx.expr is not None:
            expr = self.visitExpression(ctx.expr)
        if it_type == "while":
            node = WhileNode(expr, sents)
        if it_type == "do":
            node = DoWhileNode(expr, sents)
        if it_type == "for":
            if ctx.assign_def is not None:
                a_def = self.visitSimple_declaration(ctx.assign_def)
            if ctx.condition is not None:
                cond = self.visitExpression(ctx.condition)
            node = ForNode(a_def, cond, expr, sents)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#conditional_sentence.
    def visitConditional_sentence(self, ctx: ArduinoParser.Conditional_sentenceContext):
        node = cond = None
        if ctx.expr is not None:
            cond = self.visitExpression(ctx.expr)
        if ctx.cond_type.text == "if":
            if_sents = []
            else_sents = []
            if ctx.if_code is not None:
                if_sents = self.visitCode_block(ctx.if_code)
            if ctx.else_code is not None:
                else_sents = self.visitCode_block(ctx.else_code)
            node = ConditionalSentenceNode(condition=cond, if_expr=if_sents, else_expr=else_sents)
        if ctx.cond_type.text == "switch":
            cases = []
            if ctx.sentences is not None:
                for sent in ctx.sentences:
                    cases.append(self.visitCase_sentence(sent))
            node = SwitchSentenceNode(cond, cases)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#case_sentence.
    def visitCase_sentence(self, ctx: ArduinoParser.Case_sentenceContext):
        expr = s_type = None
        sents = []
        if ctx.sent_type is not None:
            s_type = ctx.sent_type.text
        if ctx.expr is not None:
            expr = self.visitExpression(ctx.expr)
        if ctx.sentences is not None:
            for sent in ctx.sentences:
                sents.append(self.visitSentence(sent))
        node = CaseNode(s_type, expr, sents)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#code_block.
    def visitCode_block(self, ctx: ArduinoParser.Code_blockContext):
        sents = []
        if ctx.sentences is not None:
            for sent in ctx.sentences:
                sents.append(self.visitSentence(sent))
        return sents

    # Visit a parse tree produced by ArduinoParser#sentence.
    def visitSentence(self, ctx: ArduinoParser.SentenceContext):
        node = None
        if ctx.dec is not None:
            node = self.visitDeclaration(ctx.dec)
        if ctx.it_sent is not None:
            node = self.visitIteration_sentence(ctx.it_sent)
        if ctx.cond_sent is not None:
            node = self.visitConditional_sentence(ctx.cond_sent)
        if ctx.scope_block is not None:
            node = self.visitScoped_block(ctx.scope_block)
        if ctx.assign is not None:
            node = self.visitAssignment(ctx.assign)
        if ctx.expr is not None:
            node = self.visitExpression(ctx.expr)
        if ctx.def_mac is not None:
            node = self.visitDefine_macro(ctx.def_mac)
        if ctx.s_type is not None:
            if ctx.s_type.text == "return":
                expr = None
                if ctx.expr is not None:
                    expr = self.visitExpression(ctx.expr)
                node = ReturnNode(expr)
            if ctx.s_type.text == "break":
                node = BreakNode()
            if ctx.s_type.text == "continue":
                node = ContinueNode()
        self.__add_line_info(node, ctx)
        return node

    def visitScoped_block(self, ctx: ArduinoParser.Scoped_blockContext):
        sents = []
        if ctx.sentences is not None:
            for sent in ctx.sentences:
                sents.append(self.visitSentence(sent))
        node = BlockNode(sents)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#assignment.
    def visitAssignment(self, ctx: ArduinoParser.AssignmentContext):
        assign = value = None
        if ctx.assign is not None:
            assign = self.visitExpression(ctx.assign)
        if ctx.value is not None:
            value = self.visitExpression(ctx.value)
        node = AssignmentNode(assign, value)
        self.__add_line_info(node, ctx)
        return node


    # Visit a parse tree produced by ArduinoParser#expression.
    def visitExpression(self, ctx: ArduinoParser.ExpressionContext):
        node = None
        arit_ops = {'*', '/', '%', '+', '-'}
        bitwise_ops = {'<<', '>>', '&', '^', '|'}
        bool_ops = {'&&', '||'}
        comp_ops = {'==', '!=', '>', '>=', '<', '<='}
        comp_assign_ops = {'%=', '&=', '*=', '+=', '-=', '/=', '^=', '|='}
        if ctx.r_expr is not None:
            node = self.visitExpression(ctx.r_expr)
        if ctx.member_acc is not None:
            element = self.visitExpression(ctx.member_acc)
            member = IDNode(ctx.id_acc.text)
            node = MemberAccessNode(element, member)
        if ctx.array_name is not None:
            name = ctx.array_name.text
            indexes = []
            if ctx.indexes is not None:
                for i in ctx.indexes:
                    indexes.append(self.visitExpression(i))
            node = ArrayAccessNode(name, indexes)
        if ctx.f_call is not None:
            args = []
            name = self.visitExpression(ctx.f_call)
            if ctx.args is not None:
                args = self.visitParameter(ctx.args)
            node = FunctionCallNode(name, args)
        if ctx.conv is not None:
            node = self.visitConversion(ctx.conv)
        if ctx.cond is not None:
            condition = self.visitExpression(ctx.cond)
            true_expr = self.visitExpression(ctx.true_expr)
            false_expr = self.visitExpression(ctx.false_expr)
            node = ConditionalExpressionNode(condition, true_expr, false_expr)
        if ctx.operator is not None:
            left = right = expr = None
            op = ctx.operator
            if ctx.left is not None:
                left = self.visitExpression(ctx.left)
            if ctx.right is not None:
                right = self.visitExpression(ctx.right)
            if ctx.expr is not None:
                expr = self.visitExpression(ctx.expr)
            if op is not None:
                operator = op.text
                if operator == '++' or operator == '--':
                    node = IncDecExpressionNode(expr, operator)
                if operator in arit_ops:
                    if left is None:
                        if operator == '+':
                            node = expr
                        else:
                            node = ArithmeticExpressionNode(IntNode(0), operator, expr)
                    else:
                        node = ArithmeticExpressionNode(left, operator, right)
                if operator in bitwise_ops:
                    node = BitwiseExpressionNode(left, operator, right)
                if operator in bool_ops:
                    node = BooleanExpressionNode(left, operator, right)
                if operator in comp_ops:
                    node = ComparisionExpressionNode(left, operator, right)
                if operator in comp_assign_ops:
                    node = CompoundAssignmentNode(left, operator, right)
                if operator == '!':
                    node = NotExpressionNode(expr)
                if operator == '~':
                    node = BitNotExpressionNode(expr)
                if operator == '*' and left is None:
                    node = expr
                if operator == '&' and left is None:
                    node = expr
        if ctx.getText() == "true":
            node = BooleanNode(True)
        elif ctx.getText() == "false":
            node = BooleanNode(False)
        if ctx.LOW() is not None:
            node = IntNode(0)
        if ctx.HIGH() is not None:
            node = IntNode(1)
        if ctx.ANALOG_PIN() is not None:
            node = IntNode(14 + int(ctx.ANALOG_PIN().getText()[-1]))
        if ctx.INPUT() is not None:
            node = HexNode(int('0x0', 16))
        if ctx.OUTPUT() is not None:
            node = HexNode(int('0x1', 16))
        if ctx.INPUT_PULLUP() is not None:
            node = HexNode(int('0x2', 16))
        if ctx.HEX_CONST() is not None:
            node = HexNode(int(ctx.HEX_CONST().getText(), 16))
        if ctx.OCTAL_CONST() is not None:
            node = OctalNode(int(ctx.OCTAL_CONST().getText(), 8))
        if ctx.BINARY_CONST() is not None:
            node = BinaryNode(int(ctx.BINARY_CONST().getText(), 2))
        if ctx.INT_CONST() is not None:
            node = IntNode(int(ctx.INT_CONST().getText()))
        if ctx.FLOAT_CONST() is not None:
            node = FloatNode(float(ctx.FLOAT_CONST().getText()))
        if ctx.CHAR_CONST() is not None:
            char_const = ctx.CHAR_CONST().getText()
            char_const = char_const.replace('\'', '')
            node = CharNode(char_const)
        if ctx.STRING_CONST() is not None:
            string_const = ctx.STRING_CONST().getText()
            string_const = string_const.replace('"', '')
            node = StringNode(string_const)
        if ctx.getText() == "nullptr":
            node = NullPtrNode(None)
        if ctx.ID() is not None and ctx.array_name is None and ctx.id_acc is None:
            node = IDNode(ctx.ID().getText())
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#conversion.
    def visitConversion(self, ctx:ArduinoParser.ConversionContext):
        conv_type = expr = None
        if ctx.uc_type is not None:
            if ctx.uc_type.text == "(unsigned int)":
                conv_type = UIntTypeNode()
            elif ctx.uc_type.text == "(unsigned long)":
                conv_type = ULongTypeNode()
            elif ctx.uc_type.text == 'String':
                conv_type = StringTypeNode()
        if ctx.c_type is not None:
            conv_type = self.visitType_convert(ctx.c_type)
        if ctx.expr is not None:
            expr = self.visitExpression(ctx.expr)
        node = ConversionNode(conv_type, expr)
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#type_convert.
    def visitType_convert(self, ctx:ArduinoParser.Type_convertContext):
        node = None
        if ctx.getText() == 'byte':
            node = ByteTypeNode()
        elif ctx.getText() == 'char':
            node = CharTypeNode()
        elif ctx.getText() == 'float':
            node = FloatTypeNode()
        elif ctx.getText() == 'int':
            node = IntTypeNode()
        elif ctx.getText() == 'long':
            node = LongTypeNode()
        elif ctx.getText() == 'word':
            node = WordTypeNode()
        self.__add_line_info(node, ctx)
        return node

    # Visit a parse tree produced by ArduinoParser#parameter.
    def visitParameter(self, ctx: ArduinoParser.ParameterContext):
        params = []
        if ctx.parameters is not None:
            for param in ctx.parameters:
                params.append(self.visitExpression(param))
        return params

    def __add_line_info(self, node, ctx):
        node.set_line(ctx.start.line)
        node.set_position(ctx.start.column)


del ArduinoParser
