from typing import Literal, Optional, Union

# from dataclasses import dataclass
from pydantic.dataclasses import dataclass

from compiler.jackparser import tokens
from compiler.jackparser.languagerules import Keyword

TYPES = tokens.Identifier | Literal[Keyword.int_, Keyword.char, Keyword.boolean]
OPS = Literal['+', '-', '*', '/', '&', '|', '<', '>', '=']
UNARY_OPS = Literal["-", "~"]
KEYWORD_CONSTANT = Literal[Keyword.true, Keyword.false, Keyword.null, Keyword.this]

#############
# expressions
#############
TERM = Union[
    tokens.IntegerConstant, tokens.StringConstant, KEYWORD_CONSTANT, tokens.Identifier,
    "ArrayAt",
    "SubroutineCall",
    "Expression",
    "CompoundTerm"
]


@dataclass
class CompoundTerm:
    unary_op: UNARY_OPS
    term: TERM


@dataclass
class Expression:
    terms_and_ops: list[TERM | OPS]


@dataclass
class ArrayAt:
    var_name: tokens.Identifier
    at_index: Expression


@dataclass
class SubroutineCall:
    parent: Optional[tokens.Identifier]
    subroutine_name: tokens.Identifier
    expression_list: list[Expression]


############
# statements
############

@dataclass
class Statement:
    pass


@dataclass
class LetStatement(Statement):
    var_name: tokens.Identifier
    at_index: Optional[Expression]
    expression: Expression


@dataclass
class IfStatement(Statement):
    condition: Expression
    then_statements: list[Statement]
    else_statements: Optional[list[Statement]]


@dataclass
class WhileStatement(Statement):
    condition: Expression
    statements: list[Statement]


@dataclass
class DoStatement(Statement):
    subroutine_call: SubroutineCall


@dataclass
class ReturnStatement(Statement):
    expression: Optional[Expression]


###################
# program structure
###################

@dataclass
class VarDec:
    type_: TYPES
    var_names: list[tokens.Identifier]


@dataclass
class SubroutineBody:
    var_dec_list: list[VarDec]
    statements: list[Statement]


@dataclass
class Parameter:
    type_: TYPES
    var_name: tokens.Identifier


@dataclass
class SubroutineDec:
    dec: Literal[Keyword.constructor, Keyword.function, Keyword.method]
    ret_val: TYPES | Literal[Keyword.void]
    subroutine_name: tokens.Identifier
    parameter_list: list[Parameter]
    subroutine_body: SubroutineBody


@dataclass
class ClassVarDec:
    dec: Literal[Keyword.static, Keyword.field]
    type_: TYPES
    var_names: list[tokens.Identifier]


@dataclass
class Class:
    class_name: tokens.Identifier
    class_var_dec_list: list[ClassVarDec]
    subroutine_dec_list: list[SubroutineDec]
