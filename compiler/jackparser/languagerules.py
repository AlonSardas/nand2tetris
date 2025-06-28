import re
from enum import Enum

VALID_IDENTIFIER_REGEX = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)$")
VALID_CLASS_REGEX = re.compile(r"^([A-Z][a-zA-Z0-9_]*)$")
MAX_NUMBER = 32767
MAX_NUMBER_DIGITS = 5
MAX_STRING_CHARS = 2 ** 10
LINE_COMMENT = "//"
BLOCK_COMMENT_START = "/*"
BLOCK_COMMENT_END = "*/"
STRING_DELIMITER = '"'


class Keyword(Enum):
    class_ = "class"
    constructor = "constructor"
    function = "function"
    method = "method"
    field = "field"
    static = "static"
    var = "var"
    int_ = "int"
    char = "char"
    boolean = "boolean"
    void = "void"
    true = "true"
    false = "false"
    null = "null"
    this = "this"
    let = "let"
    do = "do"
    if_ = "if"
    else_ = "else"
    while_ = "while"
    return_ = "return"


PRIMITIVES = [Keyword.int_, Keyword.char, Keyword.boolean]

KEYWORDS = dict((k.value, k) for k in Keyword)

SYMBOLS = "{}()[].,;+-*/&|<>=~"
