# Generated from Arduino.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .ArduinoParser import ArduinoParser
else:
    from ArduinoParser import ArduinoParser

# This class defines a complete generic visitor for a parse tree produced by ArduinoParser.

class ArduinoVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by ArduinoParser#start.
    def visitStart(self, ctx:ArduinoParser.StartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#program.
    def visitProgram(self, ctx:ArduinoParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#include.
    def visitInclude(self, ctx:ArduinoParser.IncludeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#program_code.
    def visitProgram_code(self, ctx:ArduinoParser.Program_codeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#declaration.
    def visitDeclaration(self, ctx:ArduinoParser.DeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#simple_declaration.
    def visitSimple_declaration(self, ctx:ArduinoParser.Simple_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#array_declaration.
    def visitArray_declaration(self, ctx:ArduinoParser.Array_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#pointer_ref.
    def visitPointer_ref(self, ctx:ArduinoParser.Pointer_refContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#reference_ref.
    def visitReference_ref(self, ctx:ArduinoParser.Reference_refContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#define_macro.
    def visitDefine_macro(self, ctx:ArduinoParser.Define_macroContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#array_index.
    def visitArray_index(self, ctx:ArduinoParser.Array_indexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#array_elements.
    def visitArray_elements(self, ctx:ArduinoParser.Array_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#var_type.
    def visitVar_type(self, ctx:ArduinoParser.Var_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#function.
    def visitFunction(self, ctx:ArduinoParser.FunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#function_args.
    def visitFunction_args(self, ctx:ArduinoParser.Function_argsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#function_arg.
    def visitFunction_arg(self, ctx:ArduinoParser.Function_argContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#iteration_sentence.
    def visitIteration_sentence(self, ctx:ArduinoParser.Iteration_sentenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#conditional_sentence.
    def visitConditional_sentence(self, ctx:ArduinoParser.Conditional_sentenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#case_sentence.
    def visitCase_sentence(self, ctx:ArduinoParser.Case_sentenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#code_block.
    def visitCode_block(self, ctx:ArduinoParser.Code_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#sentence.
    def visitSentence(self, ctx:ArduinoParser.SentenceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#scoped_block.
    def visitScoped_block(self, ctx:ArduinoParser.Scoped_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#assignment.
    def visitAssignment(self, ctx:ArduinoParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#expression.
    def visitExpression(self, ctx:ArduinoParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#conversion.
    def visitConversion(self, ctx:ArduinoParser.ConversionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#type_convert.
    def visitType_convert(self, ctx:ArduinoParser.Type_convertContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ArduinoParser#parameter.
    def visitParameter(self, ctx:ArduinoParser.ParameterContext):
        return self.visitChildren(ctx)



del ArduinoParser