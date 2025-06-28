import glob
import os.path
from functools import singledispatchmethod

from vmtranslator import vmcommands
from vmtranslator.errors import TranslatorError
from vmtranslator.vmcommands import VMCommand, Segment

TEMPLATES_PATH = os.path.abspath(os.path.join(__file__, "..", "asm_templates"))

SEGMENTS_BASE_ADDRESS = {Segment.local: "LCL",
                         Segment.argument: "ARG",
                         Segment.this: "THIS",
                         Segment.that: "THAT"}

TEMP_MEMORY_BASE_ADDR = 5

templates: dict[str, str] = {}


def load_templates():
    if templates:
        return

    for filename in glob.iglob("**/*.asm", root_dir=TEMPLATES_PATH, recursive=True):
        basename, _ = os.path.splitext(os.path.basename(filename))
        file_path = os.path.join(TEMPLATES_PATH, filename)
        with open(file_path) as f:
            content = f.read()

        # Just to ensure convention
        assert content.endswith("\n"), f"Template file {basename} doesn't end with new line"
        templates[basename] = content


class AsmGenerator(object):
    def __init__(self):
        load_templates()
        self.source_file_name = None

    def set_source_file(self, source_file: str):
        source_file_name = os.path.basename(source_file)
        self.source_file_name, _ = os.path.splitext(source_file_name)

    def generate_init(self) -> str:
        return templates["INIT"]

    def generate_asm(self, command: VMCommand, line_number: int) -> str:
        return self.handle_command(command, line_number)

    @singledispatchmethod
    def handle_command(self, command, line_number) -> str:
        raise TranslatorError(f"Bad command handling for command {command}")

    @handle_command.register
    def handle_push_pop(self, command: vmcommands.PushPopCommand, _: int) -> str:
        if command.segment == Segment.constant:
            if isinstance(command, vmcommands.Pop):
                raise TranslatorError("Cannot pop a constant")
            return templates["PUSH_CONSTANT"].format(i=command.i)

        if isinstance(command, vmcommands.Push):
            command_type = "PUSH"
        elif isinstance(command, vmcommands.Pop):
            command_type = "POP_TO"
        else:
            raise TranslatorError("Got unexpected command type")

        if command.segment in SEGMENTS_BASE_ADDRESS:
            base_addr = SEGMENTS_BASE_ADDRESS[command.segment]
            if command.i == 0:
                template_name = command_type + "_BASE_ADDR0"
                return templates[template_name].format(segment_pointer=base_addr)
            else:
                template_name = command_type + "_BASE_ADDR"
                return templates[template_name].format(i=command.i, segment_pointer=base_addr)

        template_name = command_type + "_MEMORY"
        template = templates[template_name]
        memory = self._extract_memory(command)
        return template.format(memory=memory)

    def _extract_memory(self, command: vmcommands.PushPopCommand):
        if command.segment == Segment.static:
            basename = self.source_file_name
            return f"{basename}.{command.i}"

        if command.segment == Segment.temp:
            if command.i < 0 or command.i >= 8:
                raise TranslatorError(f"Argument i={command.i} must be between 0 to 7")

            return TEMP_MEMORY_BASE_ADDR + command.i

        if command.segment == Segment.pointer:
            if command.i < 0 or command.i >= 2:
                raise TranslatorError(f"Argument i={command.i} must be between 0 to 1")
            return "THIS" if command.i == 0 else "THAT"

        raise TranslatorError(f"Got an unexpected command {command}")

    @handle_command.register
    def handle_arithmetic(self, command: vmcommands.ArithmeticCommand, line_number: int) -> str:
        name = type(command).__name__.upper()
        return templates[name].format(line_number=f"{self.source_file_name}_{line_number}")

    @handle_command.register
    def handle_call(self, command: vmcommands.Call, line_number: int) -> str:
        return_label = f"RETURN_FROM_{self.source_file_name}${command.func_name}$line_{line_number}"
        template = templates["CALL"]
        return template.format(func_name=command.func_name, return_label=return_label, n_args=command.n_args)

    @handle_command.register
    def handle_function(self, command: vmcommands.Function, _: int) -> str:
        template = templates["FUNCTION"]
        code = template.format(function_name=command.func_name, n_vars=command.n_vars)
        if command.n_vars >= 1:
            push_local_header = templates["PUSH_LOCAL_HEADER"]
            push_local = templates["PUSH_LOCAL"]
            code = code + push_local_header + push_local * command.n_vars
        return code

    @handle_command.register
    def handle_return(self, command: vmcommands.Return, _: int) -> str:
        return templates["RETURN"]

    @handle_command.register
    def handle_branching(self, command: vmcommands.BranchingCommand, _: int) -> str:
        template_to_name = {vmcommands.Goto: "GOTO",
                            vmcommands.IfGoto: "IF_GOTO",
                            vmcommands.Label: "LABEL", }
        template_name = template_to_name[type(command)]
        template = templates[template_name]
        return template.format(label=command.label)
