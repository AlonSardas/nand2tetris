from typing import IO

from vmtranslator import vmcommands
from vmtranslator.vmcommands import ArithmeticCommand

ARITHMETIC_TO_COMMAND_STR = {
    vmcommands.Add: "add",
    vmcommands.Sub: "sub",
    vmcommands.Neg: "neg",
    vmcommands.EQ: "eq",
    vmcommands.GT: "gt",
    vmcommands.LT: "lt",
    vmcommands.And: "and",
    vmcommands.Or: "or",
    vmcommands.Not: "not",
}


class VMWriter:
    def __init__(self, output_stream: IO[str]):
        self.output = output_stream

    def write_push(self, segment: vmcommands.Segment, index: int):
        self.output.write(f"push {segment.value} {index}\n")

    def write_pop(self, segment: vmcommands.Segment, index: int):
        self.output.write(f"pop {segment.value} {index}\n")

    def write_arithmetic(self, command):
        command_str = ARITHMETIC_TO_COMMAND_STR[command]
        self.output.write(command_str)
        self.output.write("\n")

    def write_label(self, label: str):
        self.output.write(f"label {label}\n")

    def write_goto(self, label: str):
        self.output.write(f"goto {label}\n")

    def write_if_goto(self, label: str):
        self.output.write(f"if-goto {label}\n")

    def write_call(self, name: str, n_args: int):
        self.output.write(f"call {name} {n_args}\n")

    def write_function(self, name: str, n_locals: int):
        self.output.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.output.write(f"return\n")
