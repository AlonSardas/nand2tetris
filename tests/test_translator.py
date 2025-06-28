import pytest

from vmtranslator import parser, vmtranslator
from vmtranslator.errors import TranslatorError
from vmtranslator.vmcommands import Push, Pop


def test_push_pop():
    push_command = parser.parse_line("push local 10")
    assert isinstance(push_command, Push)
    assert push_command.segment.name == "local"
    assert push_command.i == 10

    pop_command = parser.parse_line("pop static 15")
    assert isinstance(pop_command, Pop)
    assert pop_command.segment.name == "static"
    assert pop_command.i == 15


def test_push_pop_arguments_wrong_number():
    with pytest.raises(TranslatorError):
        parser.parse_line("push 1")

    with pytest.raises(TranslatorError):
        parser.parse_line("push static 20 43")

    with pytest.raises(TranslatorError):
        parser.parse_line("pop static abfd")


def test_call_arguments():
    with pytest.raises(TranslatorError):
        parser.parse_line("call foo bla")

    with pytest.raises(TranslatorError):
        parser.parse_line("call foo 20 43")

    with pytest.raises(TranslatorError):
        parser.parse_line("call 123 456")

    parser.parse_line("call foo 3")
    parser.parse_line("call foo5 3")
    parser.parse_line("call .$myfunc 3")


def test_translator_sanity():
    code = """
    push constant 17
    pop local 2
    push pointer 1
    pop local 0
    """
    vmtranslator.translate_text(code)


def test_line_counter():
    code = """
    push constant 17
    
    
    // Some comment
    pop local 2
    // another
    
    no_such_command
    
    push constant 17    
    """
    with pytest.raises(TranslatorError) as e:
        vmtranslator.translate_text(code)
    assert e.value.lineno == 9


def test_static_segment():
    code = """
    push local 2
    add
    pop static 3
    """
    output = vmtranslator.translate_text(code, "path/to/file/some_file.vm")
    assert "\n@some_file.3\n" in output

    code = """
    push local 2
    push static 3
    add
    """
    output = vmtranslator.translate_text(code, "path/to/file/some_file.vm")
    assert "\n@some_file.3\n" in output


def test_push_pointers():
    code = """
    push constant 4000
	pop pointer 0
	push constant 5000
	pop pointer 1
	"""
    output = vmtranslator.translate_text(code, "path/to/file/some_file.vm")


def test_temp_out_of_range():
    code = """
    pop temp 2
    pop temp 0
    pop temp 7"""
    vmtranslator.translate_text(code)

    with pytest.raises(TranslatorError):
        vmtranslator.translate_text("pop temp -1")
    with pytest.raises(TranslatorError):
        vmtranslator.translate_text("pop temp 8")
    with pytest.raises(TranslatorError):
        vmtranslator.translate_text("pop temp 25")


def test_functions_sanity():
    code = """
    function Foo.main 4
    push constant 5

    call Bar.mult 2

    function Bar.mult 3
    push local 1
    return

    """
    vmtranslator.translate_text(code)


def test_branching_sanity():
    code = """
    push local 1
    if-goto LABEL1
    add
    label LABEL2
    sub
    label LABEL1
    goto LABEL2

    """
    vmtranslator.translate_text(code)
