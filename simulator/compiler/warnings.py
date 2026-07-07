import compiler.ast as ast
import compiler.ast_visitor as ast_visitor
import output.console as console
import libraries.libs as libs
import compiler.ast as ast


class WarningAnalyzer(ast_visitor.ASTVisitor):

    def __init__(self) -> None:
        self.warnings = []
        self.locals = {}
        self.globals = {}
        self.lib_manager = libs.LibraryManager()

    def visit_declaration(self, declaration: ast.DeclarationNode, param):
        if declaration.type is not None:
            declaration.type.accept(self, param)
        if declaration.expr is not None:
            declaration.expr.accept(self, param)
        self.add_declaration(declaration.function,
                             declaration.var_name, declaration)
        return None

    def visit_array_declaration(self, array_declaration: ast.ArrayDeclarationNode, param):
        if array_declaration.type is not None:
            array_declaration.type.accept(self, param)
        self.visit_array_elements(array_declaration.elements, param)
        self.add_declaration(array_declaration.function,
                             array_declaration.var_name, array_declaration)
        return None

    def visit_define_macro(self, define_macro: ast.DefineMacroNode, param):
        if define_macro.expr is not None:
            define_macro.expr.accept(self, param)
        self.visit_array_elements(define_macro.elements, param)
        self.add_declaration(define_macro.function,
                             define_macro.macro_name, define_macro)
        return None

    def visit_function(self, function: ast.FunctionNode, param):
        if function.type is not None:
            function.type.accept(self, param)
        self.visit_children(function.args, param)
        if function.sentences is not None:
            for sent in function.sentences:
                sent.set_function(function)
                sent.accept(self, param)
        return None

    def visit_while(self, while_p: ast.WhileNode, param):
        self.warnings.append(console.Warning("Uso", while_p.line, while_p.position,
                                             "No es recomendable el uso de bucles (while), aunque sea correcto"))
        if while_p.expression is not None:
            while_p.expression.accept(self, param)
        self.visit_children(while_p.sentences, param)
        return None

    def visit_do_while(self, do_while: ast.DoWhileNode, param):
        self.warnings.append(console.Warning("Uso", do_while.line, do_while.position,
                                             "No es recomendable el uso de bucles (do while), aunque sea correcto"))
        if do_while.expression is not None:
            do_while.expression.accept(self, param)
        self.visit_children(do_while.sentences, param)
        return None

    def visit_for(self, for_p: ast.ForNode, param):
        self.warnings.append(console.Warning("Uso", for_p.line, for_p.position,
                                             "No es recomendable el uso de bucles (for), aunque sea correcto"))
        if for_p.assignment is not None:
            for_p.assignment.accept(self, param)
        if for_p.condition is not None:
            for_p.condition.accept(self, param)
        if for_p.expression is not None:
            for_p.expression.accept(self, param)
        self.visit_children(for_p.sentences, param)
        return None

    def visit_function_call(self, function_call: ast.FunctionCallNode, param):
        if function_call.name is not None:
            function_call.name.accept(self, param)
        self.visit_children(function_call.parameters, param)
        f_name = ""
        lib_name = ""
        if isinstance(function_call.name, ast.MemberAccessNode):
            f_name = function_call.name.member.value
            lib_name = function_call.name.element.value
            if lib_name != 'Serial':
                name = function_call.name.element.type
                if isinstance(name, ast.StringTypeNode):
                    lib_name = 'String'
                elif name is not None:
                    lib_name = name.type_name
                # else: lib_name ya es el identificador (p. ej. "Braccio")
        elif function_call.name is not None:
            f_name = getattr(function_call.name, 'value', '')
            lib_name = "Standard"
        if not lib_name or not f_name:
            return None
        lib_name = lib_name[0].upper() + lib_name[1:]
        message = self.lib_manager.not_implemented(lib_name, f_name)
        if message != "":
            self.warnings.append(
                console.Warning("No implementado", function_call.line, function_call.position, message))
        return None

    def add_declaration(self, function, name, decl):
        if function is not None:
            if function.name in self.locals:
                self.locals[function.name][name] = decl
            else:
                self.locals[function.name] = {name: decl}
        else:
            self.globals[name] = decl
