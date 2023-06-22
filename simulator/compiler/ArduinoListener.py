# Generated from Arduino.g4 by ANTLR 4.11.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .ArduinoParser import ArduinoParser
else:
    from ArduinoParser import ArduinoParser

# This class defines a complete listener for a parse tree produced by ArduinoParser.
class ArduinoListener(ParseTreeListener):

    # Enter a parse tree produced by ArduinoParser#start.
    def enterStart(self, ctx:ArduinoParser.StartContext):
        pass

    # Exit a parse tree produced by ArduinoParser#start.
    def exitStart(self, ctx:ArduinoParser.StartContext):
        pass


    # Enter a parse tree produced by ArduinoParser#program.
    def enterProgram(self, ctx:ArduinoParser.ProgramContext):
        pass

    # Exit a parse tree produced by ArduinoParser#program.
    def exitProgram(self, ctx:ArduinoParser.ProgramContext):
        pass


    # Enter a parse tree produced by ArduinoParser#include.
    def enterInclude(self, ctx:ArduinoParser.IncludeContext):
        pass

    # Exit a parse tree produced by ArduinoParser#include.
    def exitInclude(self, ctx:ArduinoParser.IncludeContext):
        pass


    # Enter a parse tree produced by ArduinoParser#program_code.
    def enterProgram_code(self, ctx:ArduinoParser.Program_codeContext):
        pass

    # Exit a parse tree produced by ArduinoParser#program_code.
    def exitProgram_code(self, ctx:ArduinoParser.Program_codeContext):
        pass


    # Enter a parse tree produced by ArduinoParser#declaration.
    def enterDeclaration(self, ctx:ArduinoParser.DeclarationContext):
        pass

    # Exit a parse tree produced by ArduinoParser#declaration.
    def exitDeclaration(self, ctx:ArduinoParser.DeclarationContext):
        pass


    # Enter a parse tree produced by ArduinoParser#simple_declaration.
    def enterSimple_declaration(self, ctx:ArduinoParser.Simple_declarationContext):
        pass

    # Exit a parse tree produced by ArduinoParser#simple_declaration.
    def exitSimple_declaration(self, ctx:ArduinoParser.Simple_declarationContext):
        pass


    # Enter a parse tree produced by ArduinoParser#array_declaration.
    def enterArray_declaration(self, ctx:ArduinoParser.Array_declarationContext):
        pass

    # Exit a parse tree produced by ArduinoParser#array_declaration.
    def exitArray_declaration(self, ctx:ArduinoParser.Array_declarationContext):
        pass


    # Enter a parse tree produced by ArduinoParser#define_macro.
    def enterDefine_macro(self, ctx:ArduinoParser.Define_macroContext):
        pass

    # Exit a parse tree produced by ArduinoParser#define_macro.
    def exitDefine_macro(self, ctx:ArduinoParser.Define_macroContext):
        pass


    # Enter a parse tree produced by ArduinoParser#array_index.
    def enterArray_index(self, ctx:ArduinoParser.Array_indexContext):
        pass

    # Exit a parse tree produced by ArduinoParser#array_index.
    def exitArray_index(self, ctx:ArduinoParser.Array_indexContext):
        pass


    # Enter a parse tree produced by ArduinoParser#array_elements.
    def enterArray_elements(self, ctx:ArduinoParser.Array_elementsContext):
        pass

    # Exit a parse tree produced by ArduinoParser#array_elements.
    def exitArray_elements(self, ctx:ArduinoParser.Array_elementsContext):
        pass


    # Enter a parse tree produced by ArduinoParser#var_type.
    def enterVar_type(self, ctx:ArduinoParser.Var_typeContext):
        pass

    # Exit a parse tree produced by ArduinoParser#var_type.
    def exitVar_type(self, ctx:ArduinoParser.Var_typeContext):
        pass


    # Enter a parse tree produced by ArduinoParser#function.
    def enterFunction(self, ctx:ArduinoParser.FunctionContext):
        pass

    # Exit a parse tree produced by ArduinoParser#function.
    def exitFunction(self, ctx:ArduinoParser.FunctionContext):
        pass


    # Enter a parse tree produced by ArduinoParser#function_args.
    def enterFunction_args(self, ctx:ArduinoParser.Function_argsContext):
        pass

    # Exit a parse tree produced by ArduinoParser#function_args.
    def exitFunction_args(self, ctx:ArduinoParser.Function_argsContext):
        pass


    # Enter a parse tree produced by ArduinoParser#iteration_sentence.
    def enterIteration_sentence(self, ctx:ArduinoParser.Iteration_sentenceContext):
        pass

    # Exit a parse tree produced by ArduinoParser#iteration_sentence.
    def exitIteration_sentence(self, ctx:ArduinoParser.Iteration_sentenceContext):
        pass


    # Enter a parse tree produced by ArduinoParser#conditional_sentence.
    def enterConditional_sentence(self, ctx:ArduinoParser.Conditional_sentenceContext):
        pass

    # Exit a parse tree produced by ArduinoParser#conditional_sentence.
    def exitConditional_sentence(self, ctx:ArduinoParser.Conditional_sentenceContext):
        pass


    # Enter a parse tree produced by ArduinoParser#case_sentence.
    def enterCase_sentence(self, ctx:ArduinoParser.Case_sentenceContext):
        pass

    # Exit a parse tree produced by ArduinoParser#case_sentence.
    def exitCase_sentence(self, ctx:ArduinoParser.Case_sentenceContext):
        pass


    # Enter a parse tree produced by ArduinoParser#code_block.
    def enterCode_block(self, ctx:ArduinoParser.Code_blockContext):
        pass

    # Exit a parse tree produced by ArduinoParser#code_block.
    def exitCode_block(self, ctx:ArduinoParser.Code_blockContext):
        pass


    # Enter a parse tree produced by ArduinoParser#sentence.
    def enterSentence(self, ctx:ArduinoParser.SentenceContext):
        pass

    # Exit a parse tree produced by ArduinoParser#sentence.
    def exitSentence(self, ctx:ArduinoParser.SentenceContext):
        pass


    # Enter a parse tree produced by ArduinoParser#assignment.
    def enterAssignment(self, ctx:ArduinoParser.AssignmentContext):
        pass

    # Exit a parse tree produced by ArduinoParser#assignment.
    def exitAssignment(self, ctx:ArduinoParser.AssignmentContext):
        pass


    # Enter a parse tree produced by ArduinoParser#expression.
    def enterExpression(self, ctx:ArduinoParser.ExpressionContext):
        pass

    # Exit a parse tree produced by ArduinoParser#expression.
    def exitExpression(self, ctx:ArduinoParser.ExpressionContext):
        pass


    # Enter a parse tree produced by ArduinoParser#conversion.
    def enterConversion(self, ctx:ArduinoParser.ConversionContext):
        pass

    # Exit a parse tree produced by ArduinoParser#conversion.
    def exitConversion(self, ctx:ArduinoParser.ConversionContext):
        pass


    # Enter a parse tree produced by ArduinoParser#type_convert.
    def enterType_convert(self, ctx:ArduinoParser.Type_convertContext):
        pass

    # Exit a parse tree produced by ArduinoParser#type_convert.
    def exitType_convert(self, ctx:ArduinoParser.Type_convertContext):
        pass


    # Enter a parse tree produced by ArduinoParser#parameter.
    def enterParameter(self, ctx:ArduinoParser.ParameterContext):
        pass

    # Exit a parse tree produced by ArduinoParser#parameter.
    def exitParameter(self, ctx:ArduinoParser.ParameterContext):
        pass



del ArduinoParser