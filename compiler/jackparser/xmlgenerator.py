import xml.etree.ElementTree as ET
from typing import IO
from xml.sax.saxutils import escape

from compiler import jackgrammar
from compiler.jackparser import tokens
from compiler.jackparser.languagerules import Keyword

CLASS_VAR_DEC_TAG = "classVarDec"
SUBROUTINE_DEC_TAG = "subroutineDec"
PARAMETER_LIST_TAG = "parameterList"
SUBROUTINE_BODY_TAG = "subroutineBody"
SUBROUTINE_CALL_TAG = "subroutineCall"
STATEMENTS_TAG = "statements"
LET_STATEMENT_TAG = "letStatement"
IF_STATEMENT_TAG = "ifStatement"
WHILE_STATEMENT_TAG = "whileStatement"
DO_STATEMENT_TAG = "doStatement"
RETURN_STATEMENT_TAG = "returnStatement"
EXPRESSION_LIST_TAG = "expressionList"
EXPRESSION_TAG = "expression"
VAR_DEC_TAG = "varDec"
KEYWORD_TAG = "keyword"
IDENTIFIER_TAG = "identifier"
SYMBOL_TAG = "symbol"
INTEGER_CONSTANT_TAG = "integerConstant"
STRING_CONSTANT_TAG = "stringConstant"
TERM_TAG = "term"


def write_xml(element, indent="  ", level=0):
    lines = []
    space = indent * level
    tag = element.tag

    opening_tag = f"{space}<{tag}>"
    if element.text:
        text = escape(element.text)
        lines.append(f"{opening_tag} {text} </{tag}>")
        assert not len(element)
    else:
        lines.append(opening_tag)
        for child in element:
            lines.extend(write_xml(child, indent, level + 1))
        closing_tag = f"{space}</{tag}>"
        lines.append(closing_tag)

    return lines


class XmlGenerator:
    def __init__(self):
        pass

    def write_class(self, class_: jackgrammar.Class, output_stream: IO[str], *, line_ending="\n"):
        class_elm = self.generate_class(class_)

        xml_content = line_ending.join(write_xml(class_elm))
        output_stream.write(xml_content)
        output_stream.write(line_ending)

    def generate_class(self, class_: jackgrammar.Class):
        class_elm = ET.Element(Keyword.class_.value)
        class_elm.append(self._keyword(Keyword.class_))
        class_elm.append(self._identifier(class_.class_name))
        class_elm.append(self._symbol("{"))
        class_elm.extend(self._generate_class_var_dec_list(class_.class_var_dec_list))
        class_elm.extend(self._generate_subroutine_dec_list(class_.subroutine_dec_list))
        class_elm.append(self._symbol("}"))
        return class_elm

    def _generate_class_var_dec_list(self, class_var_dec_list: list[jackgrammar.ClassVarDec]):
        elements = []
        for class_var_dec in class_var_dec_list:
            elm = ET.Element(CLASS_VAR_DEC_TAG)
            elm.append(self._keyword(class_var_dec.dec))
            elm.append(self._type(class_var_dec.type_))
            elm.extend(self._generate_var_names(class_var_dec.var_names))
            elm.append(self._symbol(";"))
            elements.append(elm)

        return elements

    def _generate_subroutine_dec_list(self, subroutine_dec_list: list[jackgrammar.SubroutineDec]):
        elements = []
        for subroutine_dec in subroutine_dec_list:
            elm = ET.Element(SUBROUTINE_DEC_TAG)
            elm.append(self._keyword(subroutine_dec.dec))
            elm.append(self._type(subroutine_dec.ret_val))
            elm.append(self._identifier(subroutine_dec.subroutine_name))
            elm.append(self._symbol("("))
            elm.append(self._generate_parameter_list(subroutine_dec.parameter_list))
            elm.append(self._symbol(")"))
            elm.append(self._generate_subroutine_body(subroutine_dec.subroutine_body))

            elements.append(elm)

        return elements

    def _generate_parameter_list(self, parameter_list: list[jackgrammar.Parameter]):
        elm = ET.Element(PARAMETER_LIST_TAG)

        elements = []
        for parameter in parameter_list:
            elements.append(self._type(parameter.type_))
            elements.append(self._identifier(parameter.var_name))
            elements.append(self._symbol(","))

        elm.extend(elements[:-1])
        return elm

    def _generate_subroutine_body(self, subroutine_body: jackgrammar.SubroutineBody):
        elm = ET.Element(SUBROUTINE_BODY_TAG)
        elm.append(self._symbol("{"))
        elm.extend(self._generate_var_dec_list(subroutine_body.var_dec_list))
        elm.append(self.generate_statements(subroutine_body.statements))
        elm.append(self._symbol("}"))

        return elm

    def _generate_var_dec_list(self, var_dec_list: list[jackgrammar.VarDec]):
        statements = ET.Element(STATEMENTS_TAG)
        for var_dec in var_dec_list:
            elm = ET.Element(VAR_DEC_TAG)
            elm.append(self._keyword(Keyword.var))
            elm.append(self._type(var_dec.type_))
            elm.extend(self._generate_var_names(var_dec.var_names))
            elm.append(self._symbol(";"))
            statements.append(elm)

        return statements

    def generate_statements(self, statements: list[jackgrammar.Statement]):
        statement_handler = {
            jackgrammar.LetStatement: self.generate_let_statement,
            jackgrammar.IfStatement: self.generate_if_statement,
            jackgrammar.WhileStatement: self.generate_while_statement,
            jackgrammar.DoStatement: self.generate_do_statement,
            jackgrammar.ReturnStatement: self.generate_return_statement,
        }

        elm = ET.Element(STATEMENTS_TAG)
        for statement in statements:
            statement_elm = statement_handler[type(statement)](statement)
            elm.append(statement_elm)

        return elm

    def generate_let_statement(self, statement: jackgrammar.LetStatement):
        elm = ET.Element(LET_STATEMENT_TAG)
        elm.append(self._keyword(Keyword.let))
        elm.append(self._identifier(statement.var_name))

        if statement.at_index is not None:
            elm.append(self._symbol("["))
            elm.append(self.generate_expression(statement.at_index))
            elm.append(self._symbol("]"))

        elm.append(self._symbol("="))
        elm.append(self.generate_expression(statement.expression))
        elm.append(self._symbol(";"))

        return elm

    def generate_if_statement(self, statement: jackgrammar.IfStatement):
        elm = ET.Element(IF_STATEMENT_TAG)
        elm.append(self._keyword(Keyword.if_))
        elm.append(self._symbol("("))
        elm.append(self.generate_expression(statement.condition))
        elm.append(self._symbol(")"))
        elm.append(self._symbol("{"))
        elm.append(self.generate_statements(statement.then_statements))
        elm.append(self._symbol("}"))
        if statement.else_statements is not None:
            elm.append(self._keyword(Keyword.else_))
            elm.append(self._symbol("{"))
            elm.append(self.generate_statements(statement.else_statements))
            elm.append(self._symbol("}"))

        return elm

    def generate_while_statement(self, statement: jackgrammar.WhileStatement):
        elm = ET.Element(WHILE_STATEMENT_TAG)
        elm.append(self._keyword(Keyword.while_))
        elm.append(self._symbol("("))
        elm.append(self.generate_expression(statement.condition))
        elm.append(self._symbol(")"))
        elm.append(self._symbol("{"))
        elm.append(self.generate_statements(statement.statements))
        elm.append(self._symbol("}"))

        return elm

    def generate_do_statement(self, statement: jackgrammar.DoStatement):
        elm = ET.Element(DO_STATEMENT_TAG)
        elm.append(self._keyword(Keyword.do))
        elm.extend(self._generate_subroutine_call(statement.subroutine_call))
        elm.append(self._symbol(";"))

        return elm

    def generate_return_statement(self, statement: jackgrammar.ReturnStatement):
        elm = ET.Element(RETURN_STATEMENT_TAG)
        elm.append(self._keyword(Keyword.return_))
        if statement.expression:
            elm.append(self.generate_expression(statement.expression))
        elm.append(self._symbol(";"))

        return elm

    def generate_expression(self, expr: jackgrammar.Expression):
        elm = ET.Element(EXPRESSION_TAG)
        for term_or_op in expr.terms_and_ops:
            if isinstance(term_or_op, str):
                elm.append(self._symbol(term_or_op))
            else:
                elm.append(self._generate_term(term_or_op))

        return elm

    def _generate_term(self, term: jackgrammar.TERM):
        elm = ET.Element(TERM_TAG)
        if isinstance(term, tokens.Identifier):
            elm.append(self._identifier(term))

        if isinstance(term, tokens.IntegerConstant):
            inner = ET.Element(INTEGER_CONSTANT_TAG)
            inner.text = str(term.val)
            elm.append(inner)

        if isinstance(term, tokens.StringConstant):
            inner = ET.Element(STRING_CONSTANT_TAG)
            inner.text = term.val
            elm.append(inner)

        if isinstance(term, tokens.Keyword):
            elm.append(self._keyword(term))

        if isinstance(term, jackgrammar.ArrayAt):
            elm.append(self._identifier(term.var_name))
            elm.append(self._symbol("["))
            elm.append(self.generate_expression(term.at_index))
            elm.append(self._symbol("]"))

        if isinstance(term, jackgrammar.SubroutineCall):
            elm.extend(self._generate_subroutine_call(term))

        if isinstance(term, jackgrammar.Expression):
            elm.append(self._symbol("("))
            elm.append(self.generate_expression(term))
            elm.append(self._symbol(")"))

        if isinstance(term, jackgrammar.CompoundTerm):
            elm.append(self._symbol(term.unary_op))
            elm.append(self._generate_term(term.term))

        return elm

    def _generate_subroutine_call(self, subroutine_call: jackgrammar.SubroutineCall):
        # elm = ET.Element(SUBROUTINE_CALL_TAG)
        elements = []

        if subroutine_call.parent is not None:
            elements.append(self._identifier(subroutine_call.parent))
            elements.append(self._symbol("."))

        elements.append(self._identifier(subroutine_call.subroutine_name))
        elements.append(self._symbol("("))
        elements.append(self._generate_expression_list(subroutine_call.expression_list))
        elements.append(self._symbol(")"))

        return elements

    def _generate_expression_list(self, expression_list: list[jackgrammar.Expression]):
        elm = ET.Element(EXPRESSION_LIST_TAG)

        if not expression_list:
            return elm

        elm.append(self.generate_expression(expression_list[0]))
        for expr in expression_list[1:]:
            elm.append(self._symbol(","))
            elm.append(self.generate_expression(expr))

        return elm

    def _generate_var_names(self, var_names: list[tokens.Identifier]):
        if not var_names:
            return []

        elements = [self._identifier(var_names[0])]

        for var_name in var_names[1:]:
            elements.append(self._symbol(","))
            elements.append(self._identifier(var_name))
        return elements

    def _keyword(self, keyword: Keyword):
        keyword_elm = ET.Element(KEYWORD_TAG)
        keyword_elm.text = keyword.value
        return keyword_elm

    def _identifier(self, name: tokens.Identifier):
        identifier_elm = ET.Element(IDENTIFIER_TAG)
        identifier_elm.text = name.val
        return identifier_elm

    def _symbol(self, symbol: str):
        symbol_elm = ET.Element(SYMBOL_TAG)
        symbol_elm.text = symbol
        return symbol_elm

    def _type(self, type_: jackgrammar.TYPES):
        if isinstance(type_, tokens.Identifier):
            return self._identifier(type_)
        elif isinstance(type_, Keyword):
            return self._keyword(type_)
        else:
            raise RuntimeError("Type is neither an identifier nor a keyword")
