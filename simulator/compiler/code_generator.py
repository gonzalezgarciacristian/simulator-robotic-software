"""
'Translates' Arduino code into Python code that is readable
from the simulator's point of view. This makes the compiler
into a transpiler
"""

import compiler.ast as ast
import compiler.ast_visitor as ast_visitor
import libraries.libs as libraries
import os


class CodeGenerator(ast_visitor.ASTVisitor):
    VARIABLE = 1
    FUNCTION_CALL = 2

    continue_line = False

    def __init__(self, library_manager):
        """
        Constructor for code generator.
        Uses the ASTVisitor implementation. The pattern used
        is visitor.
        """
        self.script_tabs = 0
        self.library_manager: libraries.LibraryManager = library_manager
        self.globals = []
        self.functions = {}
        self.function_visitor = FunctionDefiner()
        try:
            os.mkdir('temp')
        except FileExistsError:
            pass
        open('temp/__init__.py', 'a').close()

    def visit_program(self, program: ast.ProgramNode, param):
        self.function_visitor.visit_program(program, param)
        self.functions = self.function_visitor.functions
        self.script = open("temp/script_arduino.py", 'w', encoding='utf-8')
        self.write_to_script("import libraries.standard as standard")
        self.write_endl()
        self.write_to_script("import libraries.serial as Serial")
        self.write_endl()
        self.write_to_script("import libraries.string as String")
        self.write_endl()
        self.write_to_script(
            "import graphics.screen_updater as screen_updater")
        self.write_endl()
        for include in program.includes:
            include.accept(self, param)
            self.write_endl()
            self.write_endl()
            self.write_endl()
        for c in program.code:
            c.accept(self, param)
        self.script.close()
        return None

    def visit_include(self, program: ast.IncludeNode, param):
        imported = str(program.file_name[:-2])
        library = "libraries.{}".format(str(imported).lower())
        self.library_manager.add_library(library)
        self.write_to_script("import {} as {}".format(library, imported))

    def visit_program_code(self, program_code: ast.ProgramCodeNode, param):
        if program_code.declaration is not None:
            program_code.declaration.accept(self, param)
            self.write_endl()
        if program_code.function is not None:
            self.write_endl()
            program_code.function.accept(self, param)
        if program_code.macro is not None:
            program_code.macro.accept(self, param)
            self.write_endl()
        return None

    def visit_declaration(self, declaration: ast.DeclarationNode, param):
        self.write_to_script(declaration.var_name)
        if declaration.function is None:
            self.globals.append(declaration.var_name)
        if declaration.expr is not None:
            self.write_to_script(" = ")
            declaration.expr.accept(self, param)
        elif declaration.type is not None:
            declaration.type.accept(self, param)
        return None

    def visit_array_declaration(self, array_declaration: ast.ArrayDeclarationNode, param):
        self.write_to_script(array_declaration.var_name)
        self.write_to_script(" = [")
        if len(array_declaration.elements) > 0:
            self.visit_array_elements(array_declaration.elements, param)
        self.write_to_script("]")
        self.write_endl()
        if array_declaration.function is None:
            self.globals.append(array_declaration.var_name)
        return None

    def visit_define_macro(self, define_macro: ast.DefineMacroNode, param):
        self.write_to_script("{} = ".format(define_macro.macro_name))
        if define_macro.expr is not None:
            define_macro.expr.accept(self, param)
        if len(define_macro.elements) > 0:
            self.visit_array_elements(define_macro.elements, param)
        if define_macro.function is None:
            self.globals.append(define_macro.macro_name)
        return None

    def visit_boolean_type(self, boolean_type: ast.BooleanTypeNode, param):
        self.write_to_script(" = False")
        return None

    def visit_byte_type(self, byte_type: ast.ByteTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_char_type(self, char_type: ast.CharTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_double_type(self, double_type: ast.DoubleTypeNode, param):
        self.write_to_script(" = 0.0")
        return None

    def visit_float_type(self, float_type: ast.FloatTypeNode, param):
        self.write_to_script(" = 0.0")
        return None

    def visit_int_type(self, int_type: ast.IntTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_long_type(self, long_type: ast.LongTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_short_type(self, short_type: ast.ShortTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_size_t_type(self, size_t_type: ast.Size_tTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_string_type(self, string: ast.StringTypeNode, param):
        self.write_to_script("")
        return None

    def visit_u_int_type(self, u_int_type: ast.UIntTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_u_char_type(self, u_char_type: ast.UCharTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_u_long_type(self, u_long_type: ast.ULongTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_word_type(self, word_type: ast.WordTypeNode, param):
        self.write_to_script(" = 0")
        return None

    def visit_id_type(self, id_type: ast.IDTypeNode, param):
        lib = str(id_type.type_name)
        used_class = id_type.type_name
        self.write_to_script(
            " = {}.{}(standard.board)".format(lib, used_class))
        return None

    def visit_function(self, function: ast.FunctionNode, param):
        for func in self.functions[function.name]:
            nparams = func['nparams']
            if nparams == len(function.args) + len(function.opts_args):
                self.write_to_script("def {}".format(func['name']))
                break

        self.write_to_script("(")
        for arg in function.args:
            arg.set_function(function)
            arg.accept(self, param)
        self.write_to_script("):")
        self.write_endl()

        self.increase_tab()
        for variable in self.globals:
            self.write_to_script("global {}".format(variable))
            self.write_endl()

        if len(function.sentences) > 0:
            for sent in function.sentences:
                sent.accept(self, param)
                self.write_endl()
        else:
            self.write_no_sentence()
        self.decrease_tab()

        return None

    def visit_while(self, while_p: ast.WhileNode, param):
        self.write_to_script("while ")
        if while_p.expression is not None:
            while_p.expression.accept(self, param)
        self.write_to_script(":")
        self.write_endl()

        self.increase_tab()
        n_sents = len(while_p.sentences)
        if n_sents > 0:
            for i in range(0, n_sents):
                sent = while_p.sentences[i]
                sent.accept(self, param)
                if i + 1 < n_sents:
                    self.write_endl()
        else:
            self.write_no_sentence()
        self.write_endl()
        self.write_to_script("screen_updater.refresh()")
        self.write_endl()
        self.decrease_tab()

        return None

    def visit_do_while(self, do_while: ast.DoWhileNode, param):
        self.write_to_script("while True:")
        self.write_endl()
        self.increase_tab()
        n_sents = len(do_while.sentences)
        if n_sents > 0:
            for i in range(0, n_sents):
                sent = do_while.sentences[i]
                sent.accept(self, param)
                if i + 1 < n_sents:
                    self.write_endl()
        else:
            self.write_no_sentence()

        self.write_endl()
        self.write_to_script("screen_updater.update()")
        self.write_endl()

        self.write_to_script("if ")
        if do_while.expression is not None:
            do_while.expression.accept(self, param)
        self.write_to_script(":")
        self.write_endl()

        self.increase_tab()
        self.write_to_script("break")
        self.write_endl()
        self.decrease_tab()

        self.decrease_tab()

        return None

    def visit_for(self, for_p: ast.ForNode, param):
        self.write_to_script(f"for {for_p.assignment.var_name} in range(")
        if for_p.assignment is not None:
            self.write_to_script(for_p.assignment.expr.value)
        self.write_to_script(", ")
        if for_p.condition is not None:
            for_p.condition.accept(self, param)
        self.write_to_script(", ")
        if for_p.expression is not None:
            if isinstance(for_p.expression, ast.IncDecExpressionNode):
                if for_p.expression.op == '++':
                    self.write_to_script(1)
                else:
                    self.write_to_script(-1)
            else:
                self.write_to_script(for_p.expression.right)
        self.write_to_script("):")
        self.write_endl()

        self.increase_tab()
        n_sents = len(for_p.sentences)
        if n_sents > 0:
            for i in range(0, n_sents):
                sent = for_p.sentences[i]
                sent.accept(self, param)
                if i + 1 < n_sents:
                    self.write_endl()
        else:
            self.write_no_sentence()
        self.write_endl()
        self.write_to_script("screen_updater.update()")
        self.write_endl()
        self.decrease_tab()

        return None

    def visit_conditional_sentence(self, conditional_sentence: ast.ConditionalSentenceNode, param):
        self.write_to_script("if ")
        if conditional_sentence.condition is not None:
            conditional_sentence.condition.accept(self, param)
        self.write_to_script(":")
        self.write_endl()

        self.increase_tab()
        increases = True
        n_ifs = len(conditional_sentence.if_expr)
        if n_ifs > 0:
            for i in range(0, n_ifs):
                if_sent = conditional_sentence.if_expr[i]
                if_sent.accept(self, param)
                if i + 1 < n_ifs:
                    self.write_endl()
        else:
            self.write_no_sentence()
        if increases:
            self.decrease_tab()

        increases = True
        n_elses = len(conditional_sentence.else_expr)
        if n_elses > 0:
            else_written = False
            self.write_endl()
            for i in range(0, n_elses):
                else_sent = conditional_sentence.else_expr[i]
                if isinstance(else_sent, ast.ConditionalSentenceNode):
                    self.write_to_script("el")
                    increases = False
                elif not else_written:
                    self.write_to_script("else:")
                    self.write_endl()
                    self.increase_tab()
                    else_written = True
                else_sent.accept(self, param)
                if i + 1 < n_elses:
                    self.write_endl()
            if increases:
                self.decrease_tab()

        return None

    def visit_switch_sentence(self, switch_sentence: ast.SwitchSentenceNode, param):
        self.write_to_script("match ")
        if switch_sentence.expression is not None:
            switch_sentence.expression.accept(self, param)
        self.write_to_script(":")
        self.write_endl()

        self.increase_tab()
        if len(switch_sentence.cases) > 0:
            for case in switch_sentence.cases:
                case.accept(self, param)
        else:
            self.write_no_sentence()
        self.decrease_tab()

        return None

    def visit_case(self, case: ast.CaseNode, param):
        self.write_to_script("case ")
        if case.expression is not None:
            case.expression.accept(self, param)
        self.write_to_script(":")
        self.write_endl()

        self.increase_tab()
        if len(case.sentences) > 0:
            for sent in case.sentences:
                if not isinstance(sent, ast.BreakNode):
                    sent.accept(self, param)
                    self.write_endl()
        else:
            self.write_no_sentence()
        self.decrease_tab()

        return None

    def visit_assignment(self, assignment: ast.AssignmentNode, param):
        if assignment.var is not None:
            assignment.var.accept(self, param)
        self.write_to_script(" = ")
        if assignment.expr is not None:
            assignment.expr.accept(self, param)
        return None

    def visit_array_access(self, array_access: ast.ArrayAccessNode, param):
        self.write_to_script(array_access.value)
        for index in array_access.indexes:
            self.write_to_script("[{}]".format(index.value))
        return None

    def visit_arithmetic_expression(self, arithmetic_expression: ast.ArithmeticExpressionNode, param):
        self.write_to_script("(")
        if arithmetic_expression.left is not None:
            arithmetic_expression.left.accept(self, param)
        self.write_to_script(" {} ".format(arithmetic_expression.op))
        if arithmetic_expression.right is not None:
            arithmetic_expression.right.accept(self, param)
        self.write_to_script(")")
        return None

    def visit_comparision_expression(self, comparison_expression: ast.ComparisionExpressionNode, param):
        self.write_to_script("(")
        if comparison_expression.left is not None:
            comparison_expression.left.accept(self, param)
        self.write_to_script(" {} ".format(comparison_expression.op))
        if comparison_expression.right is not None:
            comparison_expression.right.accept(self, param)
        self.write_to_script(")")
        return None

    def visit_boolean_expression(self, boolean_expression: ast.BooleanExpressionNode, param):
        self.write_to_script("(")
        if boolean_expression.left is not None:
            boolean_expression.left.accept(self, param)
        if boolean_expression.op == "&&":
            self.write_to_script(" and ")
        if boolean_expression.op == "||":
            self.write_to_script(" or ")
        if boolean_expression.right is not None:
            boolean_expression.right.accept(self, param)
        self.write_to_script(")")
        return None

    def visit_bitwise_expression(self, bitwise_expression: ast.BitwiseExpressionNode, param):
        self.write_to_script("(")
        if bitwise_expression.left is not None:
            bitwise_expression.left.accept(self, param)
        self.write_to_script(" {} ".format(bitwise_expression.op))
        if bitwise_expression.right is not None:
            bitwise_expression.right.accept(self, param)
        self.write_to_script(")")
        return None

    def visit_compound_assignment(self, compound_asigment: ast.CompoundAssignmentNode, param):
        if compound_asigment.left is not None:
            compound_asigment.left.accept(self, param)
        self.write_to_script(" {} ".format(compound_asigment.op))
        if compound_asigment.right is not None:
            compound_asigment.right.accept(self, param)
        return None

    def visit_inc_dec_expression(self, inc_dec_expression: ast.IncDecExpressionNode, param):
        if inc_dec_expression.var is not None:
            inc_dec_expression.var.accept(self, param)
        if inc_dec_expression.op == "++":
            self.write_to_script(" += 1")
        if inc_dec_expression.op == "--":
            self.write_to_script(" -= 1")
        return None

    def visit_not_expression(self, not_expression: ast.NotExpressionNode, param):
        self.write_to_script("not ")
        if not_expression.expression is not None:
            not_expression.expression.accept(self, param)
        return None

    def visit_bit_not_expression(self, bit_not_expression: ast.BitNotExpressionNode, param):
        self.write_to_script("~ ")
        if bit_not_expression.expression is not None:
            bit_not_expression.expression.accept(self, param)
        return None

    def visit_int(self, int_node: ast.IntNode, param):
        self.write_to_script(int_node.value)
        return None

    def visit_float(self, float_node: ast.FloatNode, param):
        self.write_to_script(float_node.value)
        return None

    def visit_hex(self, hex_node: ast.HexNode, param):
        self.write_to_script(hex_node.value)
        return None

    def visit_octal(self, oct_node: ast.OctalNode, param):
        self.write_to_script(oct_node.value)
        return None

    def visit_binary(self, binary_node: ast.BinaryNode, param):
        self.write_to_script(binary_node.value)
        return None

    def visit_char(self, char_node: ast.CharNode, param):
        self.write_to_script("'{}'".format(char_node.value))
        return None

    def visit_string(self, string_node: ast.StringNode, param):
        self.write_to_script("String.String(\"{}\")".format(string_node.value))
        return None

    def visit_boolean(self, boolean_node: ast.BooleanNode, param):
        self.write_to_script(boolean_node.value)
        return None

    def visit_id(self, id_node: ast.IDNode, param):
        if param is None:
            self.write_to_script(id_node.value)
        else:
            if param == self.FUNCTION_CALL:
                method = None
                lib = None
                for key in self.library_manager.library_methods:
                    lib = key
                    method = self.library_manager.find(key, id_node.value)
                    if method is not None:
                        method = method[1]
                        break
                if method is not None:
                    self.write_to_script(
                        "{}.{}".format(str(lib).lower(), method))
                else:
                    return id_node.value
        return None

    def visit_function_call(self, function_call: ast.FunctionCallNode, param):
        if function_call.name is not None:
            function_call.name.set_function_call(function_call)
            name = function_call.name.accept(self, self.FUNCTION_CALL)
            if name is not None:
                if name in self.functions:
                    for f in self.functions[name]:
                        if len(function_call.parameters) == f['nparams']:
                            self.write_to_script(f['name'])
                else:
                    self.write_to_script(name)
        self.write_to_script("(")
        is_special = False
        if isinstance(function_call.name, ast.IDNode):
            if function_call.name.value == "random":
                is_special = True
                for i in range(len(function_call.parameters) - 1, -1, -1):
                    function_call.parameters[i].accept(self, param)
                    if i > 0:
                        self.write_to_script(", ")
                self.write_to_script(")")
        if not is_special:
            for i in range(0, len(function_call.parameters)):
                if i > 0:
                    self.write_to_script(", ")
                function_call.parameters[i].accept(self, param)
            self.write_to_script(")")
        return None

    def visit_member_access(self, member_access: ast.MemberAccessNode, param):
        if member_access.element is not None:
            elem = member_access.element.value
        if member_access.member is not None:
            method = member_access.member.value
            for key in self.library_manager.library_methods:
                found_method = self.library_manager.find(key, method)
                if found_method is not None:
                    if found_method[3] != -1:
                        var = member_access.function_call.parameters[found_method[3]].value
                        self.write_to_script("{} = {}.{}".format(
                            var, elem, found_method[1]))
                    else:
                        self.write_to_script(
                            "{}.{}".format(elem, found_method[1]))
                    break
        return None

    def visit_return(self, return_p: ast.ReturnNode, param):
        self.write_to_script("return ")
        if return_p.expression is not None:
            return_p.expression.accept(self, param)

    def visit_break(self, break_p: ast.BreakNode, param):
        self.write_to_script("break")
        return None

    def visit_continue(self, continue_p: ast.ContinueNode, param):
        self.write_to_script("continue")
        return None

    def visit_array_elements(self, elements, param):
        if elements is not None:
            for i in range(0, len(elements)):
                if isinstance(elements[i], list):
                    if i > 0:
                        self.write_to_script(", ")
                    self.write_to_script("[")
                    self.visit_array_elements(elements[i], param)
                    self.write_to_script("]")
                else:
                    if i > 0:
                        self.write_to_script(", ")
                    elements[i].accept(self, param)
        return None

    def write_to_script(self, sentence):
        """
        Writes a sentence into a python script, which will be
        the transpiled Arduino code.
        Arguments:
            sentence: the sentence to write
            endl: True if the line ends, False if not
        """
        i = 0
        tabs = ""

        if not self.continue_line:
            while i < self.script_tabs:
                tabs += "\t"
                i += 1
        self.script.write("{}{}".format(tabs, sentence).rstrip('\n'))
        self.continue_line = True

    def write_endl(self):
        """
        Writes an end line to the current line
        """
        self.script.write("\n")
        self.continue_line = False

    def write_no_sentence(self):
        self.write_to_script("pass")
        self.write_endl()

    def increase_tab(self):
        """
        Increases the indentation
        """
        self.script_tabs += 1

    def decrease_tab(self):
        """
        Decreases the intentation
        """
        self.script_tabs -= 1


class FunctionDefiner(ast_visitor.ASTVisitor):

    def __init__(self) -> None:
        self.functions = {}

    def visit_function(self, function: ast.FunctionNode, param):
        if function.name not in self.functions:
            self.functions[function.name] = [
                {
                    'name': function.name,
                    'nparams': len(function.args) + len(function.opts_args)
                }
            ]
        else:
            self.functions[function.name].append(
                {
                    'name': str(function.name) + str(len(self.functions[function.name])),
                    'nparams': len(function.args) + len(function.opts_args)
                }
            )
        return None
