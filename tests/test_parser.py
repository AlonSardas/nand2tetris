import contextlib
import io

import pytest

from compiler import errors, jackgrammar
from compiler.jackparser.jackparser import JackParser
from compiler.jackparser.jacktokenizer import JackTokenizer
from compiler.jackparser.languagerules import Keyword


def test_incomplete_class():
    sanity = """class Abc{}"""
    with text_compiler(sanity) as compiler:
        compiler.compile_class()

    code = """class Abc"""
    with pytest.raises(errors.StructureError):
        with text_compiler(code) as compiler:
            compiler.compile_class()

    code = """class Abc {"""
    with pytest.raises(errors.StructureError):
        with text_compiler(code) as compiler:
            compiler.compile_class()

    code = """class Abc {
    static int bla;"""
    with pytest.raises(errors.StructureError):
        with text_compiler(code) as compiler:
            compiler.compile_class()


def test_subroutine_dec():
    code = """
    constructor Square new(int Ax, int Ay, int Asize) {
    let x = Ax;
    }"""
    with text_compiler(code) as compiler:
        subroutine_dec = compiler.compile_subroutine_dec()
    params = subroutine_dec.parameter_list
    assert len(params) == 3
    assert params[0].type_ == Keyword.int_
    assert params[0].var_name.val == "Ax"
    assert params[1].type_ == Keyword.int_
    assert params[1].var_name.val == "Ay"
    assert params[2].type_ == Keyword.int_
    assert params[2].var_name.val == "Asize"


def test_var_dec_list():
    sanity = """var int x, y, z;"""
    with text_compiler(sanity) as compiler:
        var_dec_list = compiler.compile_var_dec_list()
        assert len(var_dec_list) == 1
        var_dec = var_dec_list[0]
        assert var_dec.type_.value == "int"
        assert len(var_dec.var_names) == 3
        assert var_dec.var_names[0].val == "x"
        assert var_dec.var_names[1].val == "y"
        assert var_dec.var_names[2].val == "z"


def test_incomplete_var_dec():
    bad1 = """var int x, , z;"""
    with pytest.raises(errors.StructureError):
        with text_compiler(bad1) as compiler:
            compiler.compile_var_dec_list()

    bad2 = """var int x, boolean, z;"""
    with pytest.raises(errors.StructureError):
        with text_compiler(bad2) as compiler:
            compiler.compile_var_dec_list()

    bad3 = """var int ;"""
    with pytest.raises(errors.StructureError):
        with text_compiler(bad3) as compiler:
            compiler.compile_var_dec_list()


def test_bad_class_var_type():
    code = """class Abc {
    static not_a_type
    }"""
    with pytest.raises(errors.StructureError):
        with text_compiler(code) as compiler:
            compiler.compile_class()


def test_let_sanity():
    code = """let x=69;"""
    with text_compiler(code) as compiler:
        let_statement = compiler.compile_let()
        assert let_statement.var_name.val == "x"
        assert let_statement.at_index is None
        terms = let_statement.expression.terms_and_ops
        assert len(terms) == 1
        assert terms[0].val == 69

    code = """let xyz=My.new();"""
    with text_compiler(code) as compiler:
        let_statement = compiler.compile_let()
        assert let_statement.var_name.val == "xyz"
        assert let_statement.at_index is None
        terms = let_statement.expression.terms_and_ops
        assert len(terms) == 1
        assert terms[0].parent.val == "My"
        assert terms[0].subroutine_name.val == "new"
        assert len(terms[0].expression_list) == 0


def test_incomplete_let_command():
    code = """let x="""
    with pytest.raises(errors.IncompleteCommandError):
        with text_compiler(code) as compiler:
            compiler.compile_let()

    code = """let"""
    with pytest.raises(errors.IncompleteCommandError):
        with text_compiler(code) as compiler:
            compiler.compile_let()


def test_symbols_in_string():
    code = """do a(b, ";", ".", ",");"""
    with text_compiler(code) as compiler:
        do_statement = compiler.compile_do()
        assert len(do_statement.subroutine_call.expression_list) == 4

    code = """return ";" """
    with pytest.raises(errors.StructureError):
        with text_compiler(code) as compiler:
            compiler.compile_return()

    code = """do a(b, "c" "," ")" ";" """
    with pytest.raises(errors.StructureError):
        with text_compiler(code) as compiler:
            compiler.compile_do()

    code = """do a(b, "c" "," ")" ";" ; """
    with pytest.raises(errors.StructureError):
        with text_compiler(code) as compiler:
            compiler.compile_do()


def test_do_statement_sanity():
    code = """do a();"""
    with text_compiler(code) as compiler:
        compiler.compile_do()

    code = """do a(b);"""
    with text_compiler(code) as compiler:
        compiler.compile_do()

    code = """do a(b, c+d);"""
    with text_compiler(code) as compiler:
        compiler.compile_do()

    code = """do a(b, c+d, 5+g*2);"""
    with text_compiler(code) as compiler:
        compiler.compile_do()

    code = """do a(b[abc], c+d.bla(), 5+g[6]*2);"""
    with text_compiler(code) as compiler:
        compiler.compile_do()


def test_incomplete_do_command():
    code = """do a(b, c+d, 5+g*2,"""
    with pytest.raises(errors.IncompleteCommandError):
        with text_compiler(code) as compiler:
            compiler.compile_do()

    code = """do a(b, c+d, 5+g*2,);"""
    with pytest.raises(errors.StructureError):
        with text_compiler(code) as compiler:
            compiler.compile_do()


def test_bad_identifier_name():
    bad1 = "let 1abc=5;"
    with pytest.raises(errors.StructureError):
        with text_compiler(bad1) as compiler:
            compiler.compile_let()

    bad2 = "let 1 =5;"
    with pytest.raises(errors.StructureError):
        with text_compiler(bad2) as compiler:
            compiler.compile_let()

    bad3 = "let let =5;"
    with pytest.raises(errors.StructureError):
        with text_compiler(bad3) as compiler:
            compiler.compile_let()

    bad4 = "let while =5;"
    with pytest.raises(errors.StructureError):
        with text_compiler(bad4) as compiler:
            compiler.compile_let()


def test_no_semicolon():
    code = """let a = 5
    let b = 6"""
    with pytest.raises(errors.StructureError):
        with text_compiler(code) as compiler:
            compiler.compile_statements()


def test_if_statements():
    code = "if (a) { return; }"
    with text_compiler(code) as compiler:
        if_statement = compiler.compile_if()
    assert if_statement.else_statements is None

    code = "if (a) { return; } else {}"
    with text_compiler(code) as compiler:
        if_statement = compiler.compile_if()
    assert if_statement.else_statements == []

    code = "if (a) { return; } else {do a();}"
    with text_compiler(code) as compiler:
        if_statement = compiler.compile_if()
    assert isinstance(if_statement.else_statements[0], jackgrammar.DoStatement)


def test_statements_sanity():
    code = """
    let a = 5;
    if (a>6) {
    let x = y +c[3*2]+d.doSomething();
    }
    else {
    }
    while (a<3) {
    do m.calc();
    return;
    }
    """
    with text_compiler(code) as compiler:
        statements = compiler.compile_statements()
    assert len(statements) == 3
    assert isinstance(statements[0], jackgrammar.LetStatement)
    assert isinstance(statements[1], jackgrammar.IfStatement)
    assert isinstance(statements[2], jackgrammar.WhileStatement)
    assert isinstance(statements[2].statements[0], jackgrammar.DoStatement)
    assert isinstance(statements[2].statements[1], jackgrammar.ReturnStatement)


def test_class_sanity():
    code = """
    class Main {
    static boolean test;
    }
"""
    with text_compiler(code) as compiler:
        class_ = compiler.compile_class()
    assert class_.class_name.val == "Main"
    assert len(class_.class_var_dec_list) == 1
    assert len(class_.subroutine_dec_list) == 0


def test_void_type():
    void_in_var_dec = """
    var void b;"""
    with text_compiler(void_in_var_dec) as compiler:
        with pytest.raises(errors.StructureError):
            compiler.compile_var_dec_list()

    void_in_fund_dec = """
    function void more() {}"""
    with text_compiler(void_in_fund_dec) as compiler:
        compiler.compile_subroutine_dec()


@contextlib.contextmanager
def text_compiler(code: str):
    with io.StringIO(code) as source:
        tokenizer = JackTokenizer(source)
        yield JackParser(tokenizer)
