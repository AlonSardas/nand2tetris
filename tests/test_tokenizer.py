import io

import pytest

from compiler import errors
from compiler.jackparser import tokens
from compiler.jackparser.jacktokenizer import JackTokenizer
from compiler.jackparser.languagerules import Keyword


def test_sanity():
    code = """
    // comment
    
    if (x<25) {
    /* some block comment
    text 
    inside comment
    */
    
        let sign="negative";
    }
    """
    expected = [tokens.KeywordConstant(Keyword.if_),
                tokens.Symbol('('),
                tokens.Identifier('x'),
                tokens.Symbol('<'),
                tokens.IntegerConstant(25),
                tokens.Symbol(')'),
                tokens.Symbol('{'),
                tokens.KeywordConstant(Keyword.let),
                tokens.Identifier('sign'),
                tokens.Symbol('='),
                tokens.StringConstant("negative"),
                tokens.Symbol(';'),
                tokens.Symbol('}')
                ]

    output = extract_tokens_from_text(code)
    assert output == expected


def test_number_too_large():
    code = " let x=32767;"
    extract_tokens_from_text(code)

    code = " let x=32768;"
    with pytest.raises(errors.ParserError):
        extract_tokens_from_text(code)

    code = " let x=123456;"
    with pytest.raises(errors.ParserError):
        extract_tokens_from_text(code)


def test_command_with_new_line():
    code = """ let s=2;
    """
    output = extract_tokens_from_text(code)
    expected = [tokens.KeywordConstant(Keyword.let),
                tokens.Identifier('s'),
                tokens.Symbol('='),
                tokens.IntegerConstant(2),
                tokens.Symbol(';'),
                ]
    assert output == expected
    assert count_lines(code) == 2


def test_block_comment():
    code = """let my_/* some block 
    comment
    over some lines
    */=2;"""
    output = extract_tokens_from_text(code)
    expected = [tokens.KeywordConstant(Keyword.let),
                tokens.Identifier('my_'),
                tokens.Symbol('='),
                tokens.IntegerConstant(2),
                tokens.Symbol(";"),
                ]
    assert output == expected


def test_comments():
    code = """let my_ // some comment 
    // another comment
    /* block */
    /**/
    // and empty block

    = 2 ;
    """
    output = extract_tokens_from_text(code)
    expected = [tokens.KeywordConstant(Keyword.let),
                tokens.Identifier('my_'),
                tokens.Symbol('='),
                tokens.IntegerConstant(2),
                tokens.Symbol(';'),
                ]
    assert expected == output

    total_lines = count_lines(code)
    assert total_lines == 8


def test_simple_string():
    code = """ let s="my string with 123 and %^&*() #@! ;; s";"""
    output = extract_tokens_from_text(code)
    expected = [tokens.KeywordConstant(Keyword.let),
                tokens.Identifier('s'),
                tokens.Symbol('='),
                tokens.StringConstant("""my string with 123 and %^&*() #@! ;; s"""),
                tokens.Symbol(';'),
                ]

    compare_tokens(expected, output)


def test_empty_string():
    code = """ let s="";"""
    output = extract_tokens_from_text(code)
    expected = [tokens.KeywordConstant(Keyword.let),
                tokens.Identifier('s'),
                tokens.Symbol('='),
                tokens.StringConstant(""),
                tokens.Symbol(';'),
                ]

    assert output == expected


def test_bad_terminating_strings():
    bad1 = """let my_s="string that doesn't end """
    with pytest.raises(errors.ParserError):
        extract_tokens_from_text(bad1)

    bad2 = """let my_s="string 
    that ends on the next line" """
    with pytest.raises(errors.ParserError):
        extract_tokens_from_text(bad2)


def test_when_exhausted():
    code = "let a while "
    with io.StringIO(code) as source:
        tokenizer = JackTokenizer(source)
        assert tokenizer.get_current_token().val == Keyword.let
        tokenizer.advance()
        assert tokenizer.get_current_token().val == "a"
        tokenizer.advance()
        assert tokenizer.get_current_token().val == Keyword.while_
        tokenizer.advance()
        assert tokenizer.get_current_token() is None
        tokenizer.advance()
        assert tokenizer.get_current_token() is None


def extract_tokens_from_text(code: str) -> list[tokens.Token]:
    tokens_list = []
    with io.StringIO(code) as source:
        tokenizer = JackTokenizer(source)
        tokens_list.append(tokenizer.get_current_token())
        while tokenizer.has_more_tokens():
            tokenizer.advance()
            tokens_list.append(tokenizer.get_current_token())
    return tokens_list


def count_lines(code: str) -> int:
    with io.StringIO(code) as source:
        tokenizer = JackTokenizer(source)
        while tokenizer.has_more_tokens():
            tokenizer.advance()
    return tokenizer.get_current_line()


def compare_tokens(expected, output):
    assert len(expected) == len(output)
    for tok1, tok2 in zip(expected, output):
        assert type(tok1) == type(tok2)
        assert tok1.val == tok2.val
