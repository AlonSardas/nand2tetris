import pytest

from hackassembler.assembler import Assembler
from hackassembler.errors import AssemblerError, MultipleSymbolDefinitionError, BadSymbolNameError


def test_multiple_runs():
    asm = Assembler()
    code = asm.assemble(["@a1"])
    assert code == "0000000000010000"
    code = asm.assemble(["@a1"])
    assert code == "0000000000010000"
    code = asm.assemble(["@a1"])
    assert code == "0000000000010000"


def test_resolve_variables():
    code = """
        @symbol
        @symbol
    """
    asm = Assembler()
    code = asm.assemble(code.splitlines())
    line1, line2 = code.splitlines()
    assert line1 == line2


def test_resolve_label_symbols():
    code = """
    M=D
    @END_LOOP
    0;JMP
    (END_LOOP)
    M=D
"""
    asm = Assembler()
    code = asm.assemble(code.splitlines())
    assert code.splitlines()[1] == f"{3:016b}"


def test_resolve_label_symbols_with_empty_lines_and_comments():
    code = """
    M=D
    
    @END_LOOP
    
    0;JMP
    // Some comment
    (END_LOOP)  // Another inline comment
    M=D
"""
    asm = Assembler()
    code = asm.assemble(code.splitlines())
    assert code.splitlines()[1] == f"{3:016b}"


def test_predefined_symbols():
    asm = Assembler()
    assert asm.assemble(["@R5"]) == f"{5:016b}"
    assert asm.assemble(["@KBD"]) == f"{0x6000:016b}"
    assert asm.assemble(["@THIS"]) == f"{3:016b}"


def test_multiple_symbol_definitions():
    code = """
        M=D
        (END_LOOP)
        0;JMP
        @END_LOOP
        (END_LOOP)  // Second definition
        M=D
    """
    asm = Assembler()
    with pytest.raises(MultipleSymbolDefinitionError):
        asm.assemble(code.splitlines())


def test_a_command_large_number():
    asm = Assembler()
    asm.assemble(["@32767"])  # Should pass
    with pytest.raises(AssemblerError):
        asm.assemble(["@32768"])


def test_bad_symbol_name():
    asm = Assembler()
    asm.assemble(["(abcAB2DD)"])
    asm.assemble(["@sys.init"])
    asm.assemble(["@.init"])
    asm.assemble(["@a.b$c"])
    asm.assemble(["@a.b$c"])
    with pytest.raises(BadSymbolNameError):
        asm.assemble(["@12abc"])
    with pytest.raises(BadSymbolNameError):
        asm.assemble(["@abcABC!"])
    with pytest.raises(BadSymbolNameError):
        asm.assemble(["@abcA;BC"])
    with pytest.raises(BadSymbolNameError):
        asm.assemble(["(abc;)"])
