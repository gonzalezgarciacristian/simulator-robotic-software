# coding: utf-8


# This class has all the classes needed in the roots of AST
# Setters are generated automatically from the attributes that the class has
from dataclasses import dataclass, field
from typing import List
from functools import reduce
import re


# This decorator adds setters

def generate_setter(name):
    return lambda self, value: setattr(self, name, value)


class BaseType(type):
    '''
    This base adds setters to all the classes
    '''
    def __new__(cls, clsname, bases, clsdict):
        new_dict = dict()
        for name, val in clsdict.items():
            if not callable(val) and '__' not in name:
                new_dict[f'set_{name}'] = generate_setter(name)
        clsdict.update(new_dict)
        return super().__new__(cls, clsname, bases, clsdict)


@dataclass
class ASTNode(metaclass=BaseType):

    position: int = field(init=False, default_factory=int)
    line: int = field(init=False, default_factory=int)

    def accept(self, visitor, param):
        '''
        This method take the name of the class which must be NameNode and then
        apply the method named visitor.visit_name(param)
        '''
        NAME = re.compile(r'([A-Z][a-z]+)')
        name = '_'.join([i.lower() for i in NAME.findall(str(type(self)))
                         if not i == "Node"])
        if name:
            return getattr(visitor, f'visit_{name}')(self, param)
        else:
            raise Exception("Warning!")

    def set_position(self, position):
        self.position = position

    def set_line(self, line):
        self.line = line


@dataclass
class TypeNode(ASTNode):

    def default_array_value(self):
        pass


@dataclass
class Sentence(ASTNode):

    function: int = field(init=False, default_factory=lambda: None)
    is_loop_sent: bool = field(init=False, default_factory=lambda: False)


@dataclass
class Expression(Sentence):
    type: int = field(init=False, default_factory=lambda: None)
    modifiable: bool = field(init=False, default_factory=lambda: False)


@dataclass
class ProgramNode(ASTNode):
    includes: int = field(default_factory=lambda: None)
    code: int = None


@dataclass
class IncludeNode(ASTNode):
    file_name: str


@dataclass
class ProgramCodeNode(ASTNode):
    declaration: str
    function: str
    macro: str


@dataclass
class DeclarationNode(Sentence):
    type: str 
    var_name: str = field(default_factory=lambda: None)
    expr: str = field(default_factory=lambda: None)
    is_const: bool = field(default_factory=lambda: False)
    is_static: bool = field(default_factory=lambda: False)
    is_reference: bool = field(default_factory=lambda: False)


@dataclass
class ArrayDeclarationNode(Sentence):
    type: str
    var_name: str
    dimensions: int
    size: List = field(default_factory=list)
    elements: List = field(default_factory=list)
    is_const: bool = False
    is_static: bool = False

    def __post_init__(self):
        # I suppose that self.size is a list
        if self.size or self.elements not in (None, []):
            self.__fix_array()
        if self.elements is None:
            self.elements = list()

    def __fix_array(self):
        if len(self.size) < self.dimensions:
            self.__fix_size()
        if self.elements is not None:
            self.elements = self.__organize_array_elements(self.elements)

    def __fix_size(self):
        n = len(self.elements)
        if len(self.size) > 0:
            n = self.size[0]
            if self.size[1:]:
                n *= reduce(lambda x, y: x*y, self.size[1:])
        # Here I suppose that self.elements is a list
        if self.elements:
            n_elements = self.__total_elements(self.elements)
        size_of_rows = n
        if n < n_elements:
            size_of_rows = int(n_elements / n)
            if n_elements % n != 0:
                size_of_rows += 1
        self.size.insert(0, size_of_rows)

    def __total_elements(self, elements):
        count = 0
        for elem in elements:
            if isinstance(elem, list):
                count += self.__total_elements(elem)
            else:
                count += 1
        return count

    def __organize_array_elements(self, current_elems, array_level=0):
        elems = []
        for i in range(0, self.size[array_level]):
            if (array_level < self.dimensions - 1):
                sub_elems = current_elems[i]
                # implies its 2d but declared as 1d
                if not isinstance(current_elems[i], list):
                    total = reduce(lambda n, e: n * e,
                                   self.size[array_level + 1:])
                    sub_elems = current_elems[i * total:(i + 1) * total]
                elems.append(self.__organize_array_elements(
                    sub_elems, array_level + 1))
            else:
                if i < len(current_elems):
                    elems.append(current_elems[i])
                else:
                    elems.append(self.type.default_array_value())
        return elems


@dataclass
class DefineMacroNode(Sentence):
    macro_name: str = field(default_factory=str)
    expr: Expression = field(default_factory=lambda: None)
    elements: List = field(default_factory=list)

    def __post_init__(self):
        self.type = None


@dataclass
class AssignmentNode(Sentence):
    var: str = field(default_factory=str)
    expr: Expression = field(default_factory=lambda: None)
    index: str = field(default_factory=lambda: None)


@dataclass
class BooleanTypeNode(TypeNode):
    def default_array_value(self):
        return BooleanNode(False)


@dataclass
class ByteTypeNode(TypeNode):
    def default_array_value(self):
        return IntNode(0)


@dataclass
class CharTypeNode(TypeNode):
    def default_array_value(self):
        return CharNode('\0')


@dataclass
class DoubleTypeNode(TypeNode):
    def default_array_value(self):
        return FloatNode(0.0)


@dataclass
class FloatTypeNode(TypeNode):
    def default_array_value(self):
        return FloatNode(0.0)


@dataclass
class IntTypeNode(TypeNode):
    def default_array_value(self):
        return IntNode(0)


@dataclass
class LongTypeNode(TypeNode):
    def default_array_value(self):
        return IntNode(0)


@dataclass
class ShortTypeNode(TypeNode):
    def default_array_value(self):
        return IntNode(0)


@dataclass
class Size_tTypeNode(TypeNode):
    def default_array_value(self):
        return IntNode(0)


@dataclass
class StringTypeNode(TypeNode):

    def default_array_value(self):
        return StringNode("")


@dataclass
class UIntTypeNode(TypeNode):

    def default_array_value(self):
        return IntNode(0)

@dataclass
class UCharTypeNode(TypeNode):

    def default_array_value(self):
        return CharNode('\0')


@dataclass
class ULongTypeNode(TypeNode):

    def default_array_value(self):
        return IntNode(0)

@dataclass
class VoidTypeNode(TypeNode):

    def default_array_value(self):
        return None

@dataclass
class WordTypeNode(TypeNode):

    def default_array_value(self):
        return IntNode(0)


@dataclass
class IDTypeNode(TypeNode):

    type_name: str
    def default_array_value(self):
        return None

    def accept(self, visitor, param):
        return visitor.visit_id_type(self, param)

@dataclass
class FunctionNode(ASTNode):
    type: str = ''
    name: str = ''
    args: List = field(default_factory=list)
    opts_args: List = field(default_factory=list)
    sentences: List = None


@dataclass
class WhileNode(Sentence):
    expression: str = ''
    sentences: str = None


@dataclass
class DoWhileNode(Sentence):
    expression: str = ''
    sentences: str = None


@dataclass
class ForNode(Sentence):
    assignment: str = ''
    condition: BooleanTypeNode = None
    expression: Expression = None
    sentences: str = None

@dataclass
class ConditionalSentenceNode(Sentence):
    condition: TypeNode = None
    if_expr: Expression = None
    else_expr: Expression = None


@dataclass
class SwitchSentenceNode(Sentence):
    expression: Expression = None
    cases: List = None

@dataclass
class CaseNode(Sentence):
    type: str = "case"
    expression: Expression = None
    sentences: List = None


@dataclass
class BlockNode(Sentence):
    sentences: List = None


@dataclass
class ArrayAccessNode(Expression):
    value: IntTypeNode = None
    indexes: List = None

@dataclass
class BinaryOperation(Expression):
    left: Expression = None
    op: str = None
    right: Expression = None


@dataclass
class ArithmeticExpressionNode(BinaryOperation):
    pass


@dataclass
class ComparisionExpressionNode(BinaryOperation):
    pass


@dataclass
class BooleanExpressionNode(BinaryOperation):
    pass


@dataclass
class BitwiseExpressionNode(BinaryOperation):
    pass


@dataclass
class CompoundAssignmentNode(BinaryOperation):
    pass


@dataclass
class ConditionalExpressionNode(Expression):
    condition: Expression = None
    true_expr: Expression = None
    false_expr: Expression = None


@dataclass
class IncDecExpressionNode(Expression):
    var: int = 0
    op: str = ''


@dataclass
class UnaryOperation(Expression):
    expression: Expression = None


@dataclass
class NotExpressionNode(UnaryOperation):
    pass


@dataclass
class BitNotExpressionNode(UnaryOperation):
    pass


@dataclass
class SingleValue(Expression):
    value: int = 0


@dataclass
class IntNode(SingleValue):
    pass


@dataclass
class FloatNode(SingleValue):
    pass


@dataclass
class HexNode(SingleValue):
    pass


@dataclass
class OctalNode(SingleValue):
    pass


@dataclass
class BinaryNode(SingleValue):
    pass


@dataclass
class CharNode(SingleValue):
    pass


@dataclass
class StringNode(SingleValue):
    pass


@dataclass
class BooleanNode(SingleValue):
    pass


@dataclass
class NullPtrNode(SingleValue):
    pass


@dataclass
class IDNode(Expression):
    value: int = 0
    function_call: Expression = field(init=False, default_factory=lambda: None)
    definition: Expression = field(init=False, default_factory=lambda: None)

    def accept(self, visitor, param):
        return visitor.visit_id(self, param)

@dataclass
class MemberAccessNode(Expression):
    element: int = 0
    member: int = None
    function_call: Expression = field(init=False, default_factory=lambda:None)


@dataclass
class FunctionCallNode(Expression):
    name: str=''
    parameters: List = None


@dataclass
class ConversionNode(Expression):
    conv_type: List = None
    expr: Expression = None


@dataclass
class ReturnNode(Sentence):
    expression: Expression = None


@dataclass
class BreakNode(Sentence):
    pass

@dataclass
class ContinueNode(Sentence):
    pass
