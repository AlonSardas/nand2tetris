from hackassembler import cparser
from hackassembler.errors import AssemblerError
from hackassembler.symbolmanager import SymbolManager

INLINE_COMMENT_SEP = "//"


class Assembler(object):

    def __init__(self):
        self.cur_command = -1
        self.symbol_manager = None

    def _reset(self):
        self.cur_command = 0
        self.symbol_manager = SymbolManager()

    def assemble(self, input_stream):
        self._reset()

        cur_line = 0
        commands = []

        for original_line in input_stream:
            cur_line += 1
            line = self.strip_line(original_line)
            if line == "":
                continue

            try:
                if line.startswith("@"):
                    command = self.parse_a_instruction(line)
                    commands.append(command)
                    self.cur_command += 1
                elif line.startswith("("):
                    self.parse_label_symbol(line)
                else:
                    command = cparser.parse_c_instruction(line)
                    commands.append(command)
                    self.cur_command += 1
            except AssemblerError as e:
                e.line = original_line
                e.lineno = cur_line
                raise

        self.symbol_manager.resolve_all_symbols(commands)

        return "\n".join(f"{command:016b}" for command in commands)

    @staticmethod
    def strip_line(line: str) -> str:
        line = line.split(INLINE_COMMENT_SEP, 1)[0]
        line = line.strip()
        return line

    def parse_a_instruction(self, line) -> int:
        line = line[1:]
        if line.isnumeric():
            val = int(line)
            if val >= 2 ** 15:
                raise AssemblerError(f"Got an A-instruction with number larger then 2^15")
            return val
        else:
            return self.symbol_manager.try_resolve_symbol(line, self.cur_command)

    def parse_label_symbol(self, line):
        if not line.endswith(")"):
            raise AssemblerError("No ending ')'")

        line = line[1:-1]
        self.symbol_manager.create_new_label_symbol(line, self.cur_command)
