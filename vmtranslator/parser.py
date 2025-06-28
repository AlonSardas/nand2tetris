from vmtranslator import vmcommands
from vmtranslator.errors import TranslatorError
from vmtranslator.vmcommands import VMCommand

INLINE_COMMENT_SEP = "//"

NAME_TO_COMMAND = {
    "push": vmcommands.Push,
    "pop": vmcommands.Pop,
    "add": vmcommands.Add,
    "sub": vmcommands.Sub,
    "neg": vmcommands.Neg,
    "eq": vmcommands.EQ,
    "gt": vmcommands.GT,
    "lt": vmcommands.LT,
    "and": vmcommands.And,
    "or": vmcommands.Or,
    "not": vmcommands.Not,

    "call": vmcommands.Call,
    "function": vmcommands.Function,
    "return": vmcommands.Return,

    "goto": vmcommands.Goto,
    "if-goto": vmcommands.IfGoto,
    "label": vmcommands.Label,
}


def parse_line(line: str) -> VMCommand:
    parts = line.split()
    command_name = parts[0]
    if command_name not in NAME_TO_COMMAND:
        raise TranslatorError("Unknown command")
    command_class = NAME_TO_COMMAND[command_name]
    return command_class(parts[1:])


def strip_line(line: str) -> str:
    line = line.split(INLINE_COMMENT_SEP, 1)[0]
    line = line.strip()
    return line
