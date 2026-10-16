import libraries.libs as libraries
import output.console as console
import compiler.ast as ast
import compiler.ast_visitor as ast_visitor


class Semantic:

    def __init__(self, library_manager):
        self.library_manager = library_manager

    def execute(self, ast):
        decl = DeclarationAnalyzer(self.library_manager)
        decl.visit_program(ast, None)
        self.errors = decl.errors
        semt = SemanticAnalyzer(self.library_manager,
                                decl.globals, decl.locals, decl.functions)
        semt.visit_program(ast, None)
        self.errors.extend(semt.errors)


class DeclarationAnalyzer(ast_visitor.ASTVisitor):

    def __init__(self, library_manager: libraries.LibraryManager):
        self.library_manager = library_manager
        self.errors = []
        self.globals = {}
        self.locals = {}
        self.functions = {}

    def visit_program(self, program: ast.ProgramNode, param):
        for inc in program.includes:
            self.visit_include(inc, param)
        for cod in program.code:
            self.visit_program_code(cod, param)
        if "setup" not in self.functions:
            self.add_error("Declaración", program, "No hay función setup")
        if "loop" not in self.functions:
            self.add_error("Declaración", program, "No hay función loop")
        return None

    def visit_include(self, program: ast.IncludeNode, param):
        library = program.file_name
        self.library_manager.add_library(library)
        return None

    def visit_function(self, function: ast.FunctionNode, param):
        if function.type is not None:
            function.type.accept(self, param)
        if len(function.args) > 0:
            for arg in function.args:
                arg.set_function(function)
                arg.accept(self, param)
        if len(function.opts_args) > 0:
            for arg in function.opt_args:
                arg.set_function(function)
                arg.accept(self, param)
        if function.sentences is not None:
            for sent in function.sentences:
                sent.set_function(function)
                sent.accept(self, param)
        if function.name not in self.functions:
            self.functions[function.name] = [function]
        else:
            is_repeated = False
            for func in self.functions[function.name]:
                if len(function.args) == len(func.args):
                    is_repeated = True
            if not is_repeated:
                self.functions[function.name].append(function)
            else:
                self.add_error("Declaración", function,
                               "La función ya ha sido declarada")
        return None

    def visit_declaration(self, declaration: ast.DeclarationNode, param):
        if declaration.type is not None:
            declaration.type.accept(self, param)
        if declaration.expr is not None:
            declaration.expr.accept(self, param)
        dec = self.__lookfor_var(declaration.var_name, declaration.function)
        if dec is not None:
            self.add_error("Declaración", declaration,
                           "La variable ya ha sido declarada")
        else:
            self.add_declaration(declaration.function,
                                 declaration.var_name, declaration)
        return None

    def visit_array_declaration(self, array_declaration: ast.ArrayDeclarationNode, param):
        if array_declaration.type is not None:
            array_declaration.type.accept(self, param)
        self.visit_array_elements(array_declaration.elements, param)
        dec = self.__lookfor_var(
            array_declaration.var_name, array_declaration.function)
        if dec is not None:
            self.add_error("Declaración", array_declaration,
                           "El array ya ha sido declarado")
        elif len(array_declaration.size) < 1:
            self.add_error("Tamaños", array_declaration,
                           "No se ha introducido el tamaño del array")
        else:
            self.add_declaration(array_declaration.function,
                                 array_declaration.var_name, array_declaration)
        return None

    def visit_define_macro(self, define_macro: ast.DefineMacroNode, param):
        if define_macro.expr is not None:
            define_macro.expr.accept(self, param)
        dec = self.__lookfor_var(
            define_macro.macro_name, define_macro.function)
        if dec is not None:
            self.add_error("Declaración", define_macro,
                           "La macro ya ha sido declarada")
        else:
            self.add_declaration(define_macro.function,
                                 define_macro.macro_name, define_macro)
        return None

    def add_error(self, e_type, element, message):
        self.errors.append(
            console.Error(e_type, element.line, element.position, message))

    def add_declaration(self, function, name, decl):
        if function is not None:
            if function.name in self.locals:
                self.locals[function.name][name] = decl
            else:
                self.locals[function.name] = {name: decl}
        else:
            self.globals[name] = decl

    def __lookfor_var(self, name, function):
        if function is not None:
            if function.name in self.locals:
                if name in self.locals[function.name]:
                    return self.locals[function.name][name]
        else:
            if name in self.globals:
                return self.globals[name]
        return None


class SemanticAnalyzer(ast_visitor.ASTVisitor):

    def __init__(self, library_manager: libraries.LibraryManager, globals, locals, functions):
        self.errors = []
        self.library_manager = library_manager
        self.globals = globals
        self.locals = locals
        self.functions = functions
        self.numerical_types = [ast.IntTypeNode, ast.FloatTypeNode,
                                ast.DoubleTypeNode, ast.ByteTypeNode,
                                ast.ShortTypeNode, ast.LongTypeNode,
                                ast.CharTypeNode, ast.BooleanTypeNode,
                                ast.Size_tTypeNode, ast.WordTypeNode,
                                ast.ULongTypeNode, ast.UIntTypeNode,
                                ast.UCharTypeNode]
        self.integer_types = [ast.IntTypeNode, ast.ByteTypeNode,
                              ast.ShortTypeNode, ast.LongTypeNode,
                              ast.CharTypeNode, ast.BooleanTypeNode,
                              ast.Size_tTypeNode, ast.WordTypeNode,
                              ast.ULongTypeNode, ast.UIntTypeNode,
                              ast.UCharTypeNode]

    def visit_program(self, program: ast.ProgramNode, param):
        self.visit_children(program.includes, param)
        self.visit_children(program.code, param)
        if "setup" in self.functions:
            setup = self.functions["setup"][0]
            if self.check_type(setup.type, ast.VoidTypeNode):
                self.add_error("Tipo de función setup", program,
                               "La función setup debe ser de tipo void")
        if "loop" in self.functions:
            setup = self.functions["loop"][0]
            if self.check_type(setup.type, ast.VoidTypeNode):
                self.add_error("Tipo de función loop", program,
                               "La función loop debe ser de tipo void")
        return None

    def visit_int(self, int_node: ast.IntNode, param):
        int_node.set_type(ast.IntTypeNode())
        int_node.set_modifiable(False)
        return None

    def visit_float(self, float_node: ast.FloatNode, param):
        float_node.set_type(ast.FloatTypeNode())
        float_node.set_modifiable(False)
        return None

    def visit_hex(self, hex_node: ast.HexNode, param):
        hex_node.set_type(ast.IntTypeNode())
        hex_node.set_modifiable(False)
        return None

    def visit_octal(self, oct_node: ast.OctalNode, param):
        oct_node.set_type(ast.IntTypeNode())
        oct_node.set_modifiable(False)
        return None

    def visit_binary(self, binary_node: ast.BinaryNode, param):
        binary_node.set_type(ast.IntTypeNode())
        binary_node.set_modifiable(False)
        return None

    def visit_char(self, char_node: ast.CharNode, param):
        char_node.set_type(ast.CharTypeNode())
        char_node.set_modifiable(False)
        return None

    def visit_string(self, string_node: ast.StringNode, param):
        string_node.set_type(ast.StringTypeNode())
        string_node.set_modifiable(False)
        return None

    def visit_boolean(self, boolean_node: ast.BooleanNode, param):
        boolean_node.set_type(ast.BooleanTypeNode())
        boolean_node.set_modifiable(False)
        return None

    def visit_id(self, id_node: ast.IDNode, param):
        definition = self.__get_declaration(id_node.value, id_node.function)
        id_node.set_definition(definition)
        if definition is not None:
            if isinstance(definition, ast.DefineMacroNode):
                definition.type = definition.expr.type
            id_node.set_type(id_node.definition.type)
        elif id_node.value in self.library_manager.library_methods:
            pass
        else:
            self.add_error("Declaración", id_node,
                           "La variable no está declarada")
            id_node.set_type(None)
        id_node.set_modifiable(True)
        return None

    def visit_function(self, function: ast.FunctionNode, param):
        has_returned = False
        if function.type is not None:
            function.type.accept(self, param)
        if len(function.args) > 0:
            for arg in function.args:
                arg.accept(self, param)
        if len(function.opts_args) > 0:
            for arg in function.opts_args:
                arg.accept(self, param)
        if function.sentences is not None:
            for sent in function.sentences:
                if has_returned:
                    self.add_error("Mal uso de identificador", sent,
                                   "La sentencia return debe de estar al final de la función")
                sent.set_function(function)
                sent.accept(self, param)
                if isinstance(sent, ast.ContinueNode):
                    self.add_error("Mal uso de identificador", sent,
                                   "Continue debe ser usado dentro de un bucle")
                if isinstance(sent, ast.BreakNode):
                    self.add_error("Mal uso de identificador", sent,
                                   "Break debe ser usado dentro de un bucle o en case switch")
                if isinstance(sent, ast.ReturnNode):
                    has_returned = True
        if function.name not in self.functions:
            self.functions[function.name] = [function]
        else:
            is_repeated = False
            for func in self.functions[function.name]:
                if len(function.args) == len(func.args):
                    is_repeated = True
            if not is_repeated:
                self.functions[function.name].append(function)
        return None

    def visit_declaration(self, declaration: ast.DeclarationNode, param):
        if declaration.type is not None:
            declaration.type.accept(self, param)
        if declaration.expr is not None:
            declaration.expr.set_function(declaration.function)
            declaration.expr.accept(self, param)
            if self.check_type(declaration.type, type(declaration.expr.type)):
                self.manage_types(declaration.type,
                                  declaration.expr.type, declaration, "El tipo de la variable")
        # Modifiability not checked, it should be always modifiable
        return None

    def visit_array_declaration(self, array_declaration: ast.ArrayDeclarationNode, param):
        if array_declaration.type is not None:
            array_declaration.type.accept(self, param)
        self.visit_array_elements(array_declaration.elements, param)
        if array_declaration.elements is not None and array_declaration.elements != []:
            if self.check_type(array_declaration.type, array_declaration.elements):
                self.manage_types(array_declaration.type,
                                  array_declaration.elements, array_declaration, "El tipo del array")
        # Modifiablity not checked, it should always be modifiable
        return None

    def visit_while(self, while_p: ast.WhileNode, param):
        if while_p.expression is not None:
            while_p.expression.set_function(while_p.function)
            while_p.expression.accept(self, param)
        if while_p.sentences is not None:
            for sent in while_p.sentences:
                sent.set_is_loop_sent(True)
                sent.set_function(while_p.function)
                sent.accept(self, param)
        if self.check_in_types(while_p.expression.type, self.integer_types):
            self.add_error(
                "Tipos", while_p, "El resultado de la condición debe ser int o boolean")
        return None

    def visit_do_while(self, do_while: ast.DoWhileNode, param):
        if do_while.expression is not None:
            do_while.expression.set_function(do_while.function)
            do_while.expression.accept(self, param)
        for sent in do_while.sentences:
            sent.set_is_loop_sent(True)
            sent.set_function(do_while.function)
            sent.accept(self, param)
        if self.check_in_types(do_while.expression.type, self.integer_types):
            self.add_error(
                "Tipos", do_while, "El resultado de la condición debe ser int o boolean")
        return None

    def visit_for(self, for_p: ast.ForNode, param):
        if for_p.assignment is not None:
            for_p.assignment.set_function(for_p.function)
            for_p.assignment.accept(self, param)
        if for_p.condition is not None:
            for_p.condition.set_function(for_p.function)
            for_p.condition.accept(self, param)
        if for_p.expression is not None:
            for_p.expression.set_function(for_p.function)
            for_p.expression.accept(self, param)
        if for_p.sentences is not None:
            for sent in for_p.sentences:
                sent.set_is_loop_sent(True)
                sent.set_function(for_p.function)
                sent.accept(self, param)
        if self.check_in_types(for_p.assignment.type, self.integer_types):
            self.add_error(
                "Tipos", for_p, "La variable del for debe ser int (en Arduino realmente no)")
        if self.check_in_types(for_p.condition.type, self.integer_types):
            self.add_error(
                "Tipos", for_p, "El resultado de la condición debe ser int o boolean")
        if self.check_in_types(for_p.expression.type, self.integer_types):
            self.add_error(
                "Tipos", for_p, "El incremento del for debe ser int")
        return None

    def visit_conditional_sentence(self, conditional_sentence: ast.ConditionalSentenceNode, param):
        if conditional_sentence.condition is not None:
            conditional_sentence.condition.set_function(
                conditional_sentence.function)
            conditional_sentence.condition.accept(self, param)
        if conditional_sentence.if_expr is not None:
            for sent in conditional_sentence.if_expr:
                sent.set_function(conditional_sentence.function)
                sent.accept(self, param)
                if isinstance(sent, ast.ContinueNode) and not conditional_sentence.is_loop_sent:
                    self.add_error("Mal uso de identificador", sent,
                                   "Continue debe usarse en bucles")
                if isinstance(sent, ast.BreakNode) and not conditional_sentence.is_loop_sent:
                    self.add_error("Mal uso de identificador", sent,
                                   "Break debe usarse en bucles o en case switch")
        if conditional_sentence.else_expr is not None:
            for sent in conditional_sentence.else_expr:
                sent.set_function(conditional_sentence.function)
                sent.accept(self, param)
                if isinstance(sent, ast.ContinueNode) and not conditional_sentence.is_loop_sent:
                    self.add_error("Mal uso de identificador", sent,
                                   "Continue debe usarse en bucles")
                if isinstance(sent, ast.BreakNode) and not conditional_sentence.is_loop_sent:
                    self.add_error("Mal uso de identificador", sent,
                                   "Break debe usarse en bucles o en case switch")
        if self.check_in_types(conditional_sentence.condition.type, self.integer_types):
            self.add_error(
                "Tipos", conditional_sentence, "El resultado de la condición debe ser int o boolean")
        return None

    def visit_switch_sentence(self, switch_sentence: ast.SwitchSentenceNode, param):
        if switch_sentence.expression is not None:
            switch_sentence.expression.set_function(switch_sentence.function)
            switch_sentence.expression.accept(self, param)
        if switch_sentence.cases is not None:
            for case_block in switch_sentence.cases:
                case_block.set_function(switch_sentence.function)
                case_block.accept(self, param)
                for sent in case_block.sentences:
                    if isinstance(sent, ast.ContinueNode) and not switch_sentence.is_loop_sent:
                        self.add_error("Mal uso de identificador", sent,
                                       "Continue debe usarse en bucles")
                if case_block.type != "default":
                    definition = self.__get_declaration(
                        switch_sentence.expression.value, switch_sentence.expression.function)
                    if self.check_type(definition.type, type(case_block.expression.type)):
                        self.add_error(
                            "Tipos", case_block,
                            "La sentencia case debe de tener una expresión del tipo marcado en switch")
        return None

    def visit_assignment(self, assignment: ast.AssignmentNode, param):
        if assignment.var is not None:
            assignment.var.set_function(assignment.function)
            assignment.var.accept(self, param)
        if assignment.expr is not None:
            assignment.expr.set_function(assignment.function)
            assignment.expr.accept(self, param)
        if self.variable_defined(assignment.var.value, assignment.function):
            if self.check_modifiable(assignment.var):
                self.add_error("No modificable", assignment,
                               "La variable no se puede modificar. Puede que sea una constante")
            elif self.check_type(assignment.var.type, type(assignment.expr.type)):
                self.manage_types(assignment.var.type,
                                  assignment.expr.type, assignment, "El tipo de la variable")
        return None

    def visit_return(self, return_p: ast.ReturnNode, param):
        if return_p.expression is not None:
            return_p.expression.set_function(return_p.function)
            return_p.expression.accept(self, param)
        if return_p.expression is not None and isinstance(return_p.function.type, ast.VoidTypeNode):
            self.add_error("Tipos", return_p,
                           "Las funciones de tipo void no deben retornar valor")
        elif return_p.expression is None and not isinstance(return_p.function.type, ast.VoidTypeNode):
            self.add_error("Tipos", return_p,
                           "Las funciones de tipo no void deben retornar valor")
        elif self.check_type(return_p.function.type, type(return_p.expression.type)):
            self.manage_types(
                return_p.function.type, return_p.expression.type, return_p, "El tipo de retorno")
        return None

    def visit_function_call(self, function_call: ast.FunctionCallNode, param):
        definition = func = None
        user_defined = found_func = False
        implemented = True

        # Find function that is being called
        if isinstance(function_call.name, ast.MemberAccessNode):
            function_call.name.element.set_function(function_call.function)
            function_call.name.accept(self, param)
            lib = function_call.name.element.value
            f_type = function_call.name.element.type
            if f_type is not None:
                if type(f_type) == ast.StringTypeNode:
                    lib = "String"
                else:
                    lib = function_call.name.element.type.type_name
            method = function_call.name.member
            func = self.library_manager.find(lib, method.value)
            found_func = func is not None
            implemented = self.__check_implemented(method.value, lib)
        else:
            method = function_call.name
            if function_call.name.value in self.functions:
                definition = self.functions[method.value]
                found_func = True
                user_defined = True
            else:
                lib = "Standard"
                func = self.library_manager.find(lib, method.value)
                if func is not None:
                    found_func = True
                    implemented = self.__check_implemented(method.value, lib)
        if not found_func:
            self.add_error("Declaración", function_call,
                           "La función no se ha declarado")

        # Create function node in case is a library function
        if not user_defined and func is not None:
            func_name = lib + '.' + method.value
            definition = [self.__create_function(function_call, func, func_name)]

        # Manage parameters
        if definition is not None and function_call.parameters is not None:
            if implemented:
                self.__check_parameters(function_call, definition, param)
        return None

    def __check_implemented(self, method, lib):
        if method is not None:
            implemented = self.library_manager.not_implemented(lib, method) == ""
        else:
            implemented = False
        return implemented

    def __check_parameters(self, function_call, definitions, param):
        n_params_correct = False
        definition = None
        for d in definitions:
            if (
                    len(function_call.parameters) == len(d.args)
                    or len(function_call.parameters) == len(d.args) + len(d.opts_args)
            ):
                n_params_correct = True
                definition = d
        if not n_params_correct:
            self.add_error("Parámetros", function_call,
                           "El número de parámetros no coincide con los de la definición")
        if definition is not None:
            for i in range(0, len(function_call.parameters)):
                function_call.parameters[i].function = function_call.function
                function_call.parameters[i].accept(self, param)
                type_to_check = None
                is_wrong_type = False
                if i < len(definition.args):
                    type_to_check = definition.args[i].type
                else:
                    type_to_check = definition.opts_args[i - len(definition.args)].type
                not_any = True
                if type(type_to_check) == ast.IDTypeNode:
                    if type_to_check.type_name == 'any':
                        is_wrong_type = False
                        not_any = False
                if not_any:
                    is_wrong_type = self.check_type(function_call.parameters[i].type, type(type_to_check))
                if is_wrong_type:
                    self.manage_types(
                        function_call.parameters[i].type, definition.args[i].type, function_call,
                        "El tipo del parámetro")

    def __create_function(self, function_call, lib_func, func_name):
        """
        Creates a FunctionNode in case the found function is one that
        is defined on the external libraries.
        Arguments:
            function_call: the function call node
            lib_func: the function found on the library
            func_name: the name of the function (including object if
            is needed to call the function)
        Returns:
            A FunctionNode with the corresponding values
        """
        func_type = lib_func[0]
        f_type = self.__parse_type(func_type)
        function_call.type = f_type
        decls = []
        opt_decls = []
        for i in range(len(lib_func[2])):
            is_optional = False
            str_arg_type = lib_func[2][i]
            if str_arg_type[0] == '(' and str_arg_type[-1] == ')':
                is_optional = True
                str_arg_type = str_arg_type[1:-1]
            arg_type = self.__parse_type(str_arg_type)
            char = chr(97 + i)
            decl = ast.DeclarationNode(arg_type, char)
            if not is_optional:
                decls.append(decl)
            else:
                opt_decls.append(decl)
        definition = ast.FunctionNode(f_type, func_name, args=decls, opts_args=opt_decls)
        return definition

    def __parse_type(self, func_type):
        """
        Parses type from text to its corresponding class type
        Arguments:
            func_type: the type (string) to parse
        Returns:
            The type class to create
        """
        if func_type == 'bool':
            return ast.BooleanTypeNode()
        elif func_type == 'byte':
            return ast.ByteTypeNode()
        elif func_type == 'char':
            return ast.CharTypeNode()
        elif func_type == 'double':
            return ast.DoubleTypeNode()
        elif func_type == 'float':
            return ast.FloatTypeNode()
        elif func_type == 'int':
            return ast.IntTypeNode()
        elif func_type == 'long':
            return ast.LongTypeNode()
        elif func_type == 'short':
            return ast.ShortTypeNode()
        elif func_type == 'size_t':
            return ast.Size_tTypeNode()
        elif func_type == 'string':
            return ast.StringTypeNode()
        elif func_type == 'uint':
            return ast.UIntTypeNode()
        elif func_type == 'uchar':
            return ast.UCharTypeNode()
        elif func_type == 'ulong':
            return ast.ULongTypeNode()
        elif func_type == 'void':
            return ast.VoidTypeNode()
        elif func_type == 'word':
            return ast.WordTypeNode()
        else:
            return ast.IDTypeNode(func_type)

    def visit_conversion(self, conversion: ast.ConversionNode, param):
        if conversion.conv_type is not None:
            conversion.conv_type.accept(self, param)
        if conversion.expr is not None:
            conversion.expr.set_function(conversion.function)
            conversion.expr.accept(self, param)
        conversion.set_type(conversion.conv_type)
        return None

    def visit_inc_dec_expression(self, inc_dec_expression: ast.IncDecExpressionNode, param):
        if inc_dec_expression.var is not None:
            inc_dec_expression.var.set_function(inc_dec_expression.function)
            inc_dec_expression.var.accept(self, param)
        inc_dec_expression.set_type(inc_dec_expression.var.type)
        if self.variable_defined(inc_dec_expression.var.value, inc_dec_expression.function):
            if self.check_in_types(inc_dec_expression.var.type, self.numerical_types):
                self.add_error("Tipos", inc_dec_expression,
                               "La expresión no es de tipo numérico")
        return None

    def visit_array_access(self, array_access: ast.ArrayAccessNode, param):
        if array_access.indexes is not None:
            for i in array_access.indexes:
                i.accept(self, param)
        definition = None
        array_access.set_modifiable(True)
        if not isinstance(array_access.value, ast.ArrayAccessNode):
            if array_access.value in self.globals:
                definition = self.globals[array_access.value]
            elif array_access.function.name in self.locals:
                if array_access.value in self.locals[array_access.function.name]:
                    definition = self.locals[array_access.function.name][array_access.value]
        if definition is not None:
            array_access.set_type(definition.type)
            definition_size = -1
            if type(definition) == ast.ArrayDeclarationNode:
                definition_size = len(definition.size)
            elif type(definition.type) == ast.StringTypeNode:
                definition_size = len(definition.expr.value)
            if definition_size == len(array_access.indexes):
                for i in range(0, definition_size):
                    if self.check_in_types(array_access.indexes[i].type, self.integer_types) and self.check_type(
                            array_access.indexes[i].type, ast.IDTypeNode):
                        self.add_error("Índice", array_access.indexes[i],
                                       "El tipo del índice debe ser int (o cualquiera que sea compatible)")
                    else:
                        index = array_access.indexes[i].value
                        if isinstance(index, str):
                            index = self.__get_declaration(index, array_access.function).expr.value
                        if index >= definition.size[i]:
                            self.add_error("Tamaños", array_access.indexes[i],
                                           "El índice sobrepasa el tamaño del array")
        else:
            self.add_error("Declaración", array_access, "El array no está declarado")
        return None

    def visit_not_expression(self, not_expression: ast.NotExpressionNode, param):
        if not_expression.expression is not None:
            not_expression.expression.set_function(not_expression.function)
            not_expression.expression.accept(self, param)
        not_expression.set_type(ast.BooleanTypeNode())
        if self.check_type(not_expression.expression.type, ast.BooleanTypeNode) or self.check_in_types(
                not_expression.expression.type, self.numerical_types):
            self.add_error("Tipos", not_expression,
                           "La expresión debe ser tipo int o boolean")
        not_expression.set_type(not_expression.expression.type)
        return None

    def visit_bit_not_expression(self, bit_not_expression: ast.BitNotExpressionNode, param):
        if bit_not_expression.expression is not None:
            bit_not_expression.expression.set_function(bit_not_expression.function)
            bit_not_expression.expression.accept(self, param)
        bit_not_expression.set_type(ast.IntTypeNode())
        if self.check_in_types(bit_not_expression.expression.type, self.integer_types):
            self.add_error("Tipos", bit_not_expression,
                           "La expresión debe ser tipo int")
        bit_not_expression.set_type(bit_not_expression.expression.type)
        return None

    def visit_arithmetic_expression(self, arithmetic_expression: ast.ArithmeticExpressionNode, param):
        if arithmetic_expression.left is not None:
            arithmetic_expression.left.set_function(arithmetic_expression.function)
            arithmetic_expression.left.accept(self, param)
        if arithmetic_expression.right is not None:
            arithmetic_expression.right.set_function(arithmetic_expression.function)
            arithmetic_expression.right.accept(self, param)
        error = False
        if self.check_in_types(arithmetic_expression.left.type, self.numerical_types) and self.check_in_types(
                arithmetic_expression.right.type, self.numerical_types):
            if arithmetic_expression.op == '+':
                if not type(arithmetic_expression.left.type) == type(
                        arithmetic_expression.right.type) == ast.StringTypeNode:
                    error = True
            else:
                error = True
        if error:
            self.add_error("Tipos", arithmetic_expression,
                           "Las operaciones artiméticas deben ser entre números (salvo +, que también puede ser entre String)")
        arithmetic_expression.set_type(arithmetic_expression.left.type)
        return None

    def visit_comparision_expression(self, comparison_expression: ast.ComparisionExpressionNode, param):
        if comparison_expression.left is not None:
            comparison_expression.left.set_function(comparison_expression.function)
            comparison_expression.left.accept(self, param)
        if comparison_expression.right is not None:
            comparison_expression.right.set_function(comparison_expression.function)
            comparison_expression.right.accept(self, param)
        if self.check_type(comparison_expression.left.type, type(comparison_expression.right.type)):
            if self.check_in_types(comparison_expression.left.type, self.numerical_types) and self.check_in_types(
                    comparison_expression.right.type, self.numerical_types):
                if not type(comparison_expression.left.type) == type(
                        comparison_expression.right.type) == ast.StringTypeNode:
                    self.add_error("Tipos", comparison_expression,
                                   "Los tipos de ambas expresiones deben coincidir o ser interoperables")
        comparison_expression.set_type(ast.BooleanTypeNode())
        return None

    def visit_boolean_expression(self, boolean_expression: ast.BooleanExpressionNode, param):
        if boolean_expression.left is not None:
            boolean_expression.left.set_function(boolean_expression.function)
            boolean_expression.left.accept(self, param)
        if boolean_expression.right is not None:
            boolean_expression.right.set_function(boolean_expression.function)
            boolean_expression.right.accept(self, param)
        if self.check_in_types(boolean_expression.left.type, self.integer_types):
            self.add_error("Tipos", boolean_expression,
                           "La expresión izquierda debe ser int o boolean")
        if self.check_in_types(boolean_expression.right.type, self.integer_types):
            self.add_error("Tipos", boolean_expression,
                           "La expresión derecha debe ser int o boolean")
        boolean_expression.set_type(ast.BooleanTypeNode())
        return None

    def visit_bitwise_expression(self, bitwise_expression: ast.BitwiseExpressionNode, param):
        if bitwise_expression.left is not None:
            bitwise_expression.left.set_function(bitwise_expression.function)
            bitwise_expression.left.accept(self, param)
        if bitwise_expression.right is not None:
            bitwise_expression.right.set_function(bitwise_expression.function)
            bitwise_expression.right.accept(self, param)
        if self.check_in_types(bitwise_expression.left.type, self.integer_types):
            self.add_error("Tipos", bitwise_expression,
                           "El tipo de la izquierda debe ser numérico")
        if self.check_in_types(bitwise_expression.right.type, self.integer_types):
            self.add_error("Tipos", bitwise_expression,
                           "El tipo de la derecha debe ser numérico")
        bitwise_expression.set_type(bitwise_expression.left.type)
        return None

    def visit_compound_assignment(self, compound_asigment: ast.CompoundAssignmentNode, param):
        if compound_asigment.left is not None:
            compound_asigment.left.set_function(compound_asigment.function)
            compound_asigment.left.accept(self, param)
        if compound_asigment.right is not None:
            compound_asigment.right.set_function(compound_asigment.function)
            compound_asigment.right.accept(self, param)
        compound_asigment.set_type(compound_asigment.left.type)
        if self.variable_defined(compound_asigment.left.value, compound_asigment.function):
            if self.check_type(compound_asigment.left.type, type(compound_asigment.right.type)):
                self.manage_types(compound_asigment.left.type, compound_asigment.right.type,
                                  compound_asigment, "El tipo de la variable")
        return None

    def manage_types(self, type_1, type_2, node, encabezado):
        if type(type_1) is ast.CharTypeNode:
            if self.check_in_types(type_2, self.integer_types):
                self.add_error(
                    "Tipos", node, encabezado + " es char, pero su valor no es char o int")
        elif type(type_1) in self.numerical_types:
            if self.check_in_types(type_2, self.numerical_types):
                self.add_error(
                    "Tipos", node, encabezado + " es numérico, pero su valor no")
        else:
            self.add_error("Tipos", node,
                           encabezado + " y del valor no coincide")

    def check_type(self, type_to_check, type_class_to_compare):
        list_types = self.__look_for_elements(type_to_check)
        if list_types is not None:
            return self.__check_elements(type_class_to_compare, list_types)
        list_types = self.__look_for_elements(type_class_to_compare)
        if list_types is not None:
            return self.__check_elements(type_to_check, list_types)
        if type(type_to_check) in self.numerical_types:
            return type_class_to_compare not in self.numerical_types
        return not type(type_to_check) is type_class_to_compare

    def check_in_types(self, var, types):
        if isinstance(var, list):
            return self.__check_elements_in_types(var, types)
        return type(var) not in types

    def check_modifiable(self, element):
        return not element.modifiable

    def add_error(self, e_type, element, message):
        self.errors.append(
            console.Error(e_type, element.line, element.position, message))

    def is_global(self, elem):
        try:
            return elem.function is not None
        except AttributeError:
            return True

    def variable_defined(self, name, function):
        if name in self.globals:
            return True
        if function is not None:
            if function.name in self.locals:
                return name in self.locals[function.name]

    def __get_declaration(self, value, function):
        definition = None
        try:
            if value in self.globals:
                definition = self.globals[value]
            elif function.name in self.locals:
                if value in self.locals[function.name]:
                    definition = self.locals[function.name][value]
        finally:
            return definition

    def __check_elements(self, type_to_compare, types):
        if len(types) > 1:
            return True
        if type(type_to_compare) in self.numerical_types:
            return types[0] not in self.numerical_types
        return not type(type_to_compare) is types[0]

    def __look_for_elements(self, types):
        if isinstance(types, list):
            list_types = self.__list_types(types)
            return list_types
        return None

    def __list_types(self, elems):
        types = []
        for elem in elems:
            if isinstance(elem, list):
                obtained_types = self.__list_types(elem)
                for obt in obtained_types:
                    if obt not in types:
                        types.append(obt)
            else:
                elem_type = type(elem.type)
                if elem_type not in types:
                    types.append(elem_type)
        return types

    def __check_elements_in_types(self, var, types):
        list_types = self.__list_types(var)
        for ty in list_types:
            if ty not in types:
                return True
        return False
