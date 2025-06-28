import re
from enum import Enum

from vmtranslator.errors import TranslatorError


class Segment(Enum):
    constant = "constant"
    local = "local"
    argument = "argument"
    this = "this"
    that = "that"
    static = "static"
    temp = "temp"
    pointer = "pointer"


VALID_SYMBOL_REGEX = re.compile(r"^([a-zA-Z_.][a-zA-Z_.$0-9]*)$")


class VMCommand(object):
    def _verify_args(self, args: list[str], expected_types=()):
        if len(args) != len(expected_types):
            raise TranslatorError(f"Got {len(args)} arguments but {len(expected_types)} are expected")

        for i, expected_type in enumerate(expected_types):
            if expected_type == Segment:
                segment = args[i]
                if segment not in Segment:
                    raise TranslatorError(f"Got an unknown segment {segment}")

            elif expected_type == int:
                num = args[i]
                if not num.isdigit():
                    raise TranslatorError(f"Argument {i} must be numeric, got {num}")

            elif expected_type == "Label":
                name = args[i]
                if VALID_SYMBOL_REGEX.match(name) is None:
                    raise TranslatorError(f"Got an invalid label name {name} at argument {i}")

            elif expected_type is None:
                continue  # Ignore type check

            else:
                raise TranslatorError(f"Could not handle type check for type {expected_type}")


class NoArgsCommand(VMCommand):
    def __init__(self, args: list[str]):
        self._verify_args(args, ())


class ArithmeticCommand(NoArgsCommand):
    pass


class PushPopCommand(VMCommand):
    def __init__(self, args: list[str]):
        self._verify_args(args, (Segment, int))
        segment, i = args
        self.segment = Segment[segment]
        self.i = int(i)


class Push(PushPopCommand):
    pass


class Pop(PushPopCommand):
    pass


class Add(ArithmeticCommand):
    pass


class Sub(ArithmeticCommand):
    pass


class Neg(ArithmeticCommand):
    pass


class EQ(ArithmeticCommand):
    pass


class GT(ArithmeticCommand):
    pass


class LT(ArithmeticCommand):
    pass


class And(ArithmeticCommand):
    pass


class Or(ArithmeticCommand):
    pass


class Not(ArithmeticCommand):
    pass


class Call(VMCommand):
    def __init__(self, args: list[str]):
        self._verify_args(args, ("Label", int))
        self.func_name = args[0]
        self.n_args = int(args[1])


class Function(VMCommand):
    def __init__(self, args: list[str]):
        self._verify_args(args, ("Label", int))
        self.func_name = args[0]
        self.n_vars = int(args[1])


class Return(NoArgsCommand):
    pass


class BranchingCommand(VMCommand):
    def __init__(self, args: list[str]):
        self._verify_args(args, ("Label",))
        self.label = args[0]


class Label(BranchingCommand):
    pass


class Goto(BranchingCommand):
    pass


class IfGoto(BranchingCommand):
    pass
