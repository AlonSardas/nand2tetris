from dataclasses import dataclass

from compiler.jackparser.languagerules import Keyword


class Token:
    val = None


@dataclass
class IntegerConstant(Token):
    val: int


@dataclass
class StringConstant(Token):
    val: str


@dataclass
class KeywordConstant(Token):
    val: Keyword


@dataclass
class Identifier(Token):
    val: str


@dataclass
class Symbol(Token):
    val: str
