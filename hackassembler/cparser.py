import re

from hackassembler.errors import AssemblerError

COMP_TABLE_A0 = {
    "0": 0b101010,
    "1": 0b111111,
    "-1": 0b111010,
    "D": 0b001100,
    "A": 0b110000,
    "!D": 0b001101,
    "!A": 0b110001,
    "-D": 0b001111,
    "-A": 0b110011,
    "D+1": 0b011111,
    "A+1": 0b110111,
    "D-1": 0b001110,
    "A-1": 0b110010,
    "D+A": 0b000010,
    "D-A": 0b010011,
    "A-D": 0b000111,
    "D&A": 0b000000,
    "D|A": 0b010101
}
COMP_TABLE_A1 = {
    "M": 0b110000,
    "!M": 0b110001,
    "-M": 0b110011,
    "M+1": 0b110111,
    "M-1": 0b110010,
    "D+M": 0b000010,
    "D-M": 0b010011,
    "M-D": 0b000111,
    "D&M": 0b000000,
    "D|M": 0b010101
}
DEST_TABLE = {
    None: 0b000,
    "M": 0b001,
    "D": 0b010,
    "MD": 0b011,
    "A": 0b100,
    "AM": 0b101,
    "AD": 0b110,
    "AMD": 0b111
}
JUMP_TABLE = {
    None: 0b000,
    "JGT": 0b001,
    "JEQ": 0b010,
    "JGE": 0b011,
    "JLT": 0b100,
    "JNE": 0b101,
    "JLE": 0b110,
    "JMP": 0b111
}

# self.c_regex = re.compile(r"^(([AMD]+)=)?([AMD01\-\+!\&\|]+)(;([A-Z][A-Z][A-Z]))?$")
# It is better to make the regex more general, so that parsing errors may be clearer
c_regex = re.compile(r"^(([A-Z]+)=)?([A-Z01\-+!&|]+)(;([A-Z]+))?$")


def parse_c_instruction(line: str) -> int:
    dest, comp, jump = extract_fields(line)

    a_bit = 1 if "M" in comp else 0
    if a_bit:
        comp_num = COMP_TABLE_A1.get(comp)
        if comp_num is None:
            raise AssemblerError(f"Could not find comp '{comp}' in table for a=1. "
                                 f"Available comp commands are {COMP_TABLE_A1.keys()}\n"
                                 f"raised when parsing")
    else:
        comp_num = COMP_TABLE_A0.get(comp)
        if comp_num is None:
            raise AssemblerError(f"Could not find comp '{comp}' in table for a=0. "
                                 f"Available comp commands are {COMP_TABLE_A0.keys()}\n"
                                 f"raised when parsing")

    dest_num = DEST_TABLE.get(dest)
    if dest_num is None:
        raise AssemblerError(f"Could not find dest '{dest}' in table. "
                             f"Available dest are {DEST_TABLE.keys()}\n"
                             f"raised when parsing")

    jump_num = JUMP_TABLE.get(jump)
    if jump_num is None:
        raise AssemblerError(f"Could not find jump '{jump}' in table. "
                             f"Available jump are {JUMP_TABLE.keys()}\n"
                             f"raised when parsing")

    output = jump_num
    output = output ^ (dest_num << 3)
    output = output ^ (comp_num << 6)
    output = output ^ (a_bit << 12)
    output = output ^ (0b111 << 13)
    assert output < 2 ** 16
    return output


def extract_fields(line):
    match = c_regex.match(line)
    if not match:
        raise AssemblerError(f"Could not parse the C-instruction")
    _, dest, comp, _, jump = match.groups()
    return dest, comp, jump
