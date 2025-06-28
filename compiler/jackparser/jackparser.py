from typing import Union, Optional

from compiler import jackgrammar
from compiler.errors import StructureError, IncompleteCommandError
from compiler.jackparser import tokens
from compiler.jackparser.jacktokenizer import JackTokenizer
from compiler.jackparser.languagerules import Keyword


class JackParser:
    def __init__(self, tokenizer: JackTokenizer):
        self.input = tokenizer

    def compile_class(self) -> jackgrammar.Class:
        self._eat(Keyword.class_)
        class_name = self._get_identifier()
        self._eat('{')
        class_var_dec_list = self._compile_class_var_dec_list()
        subroutine_dec_list = self._compile_subroutine_dec_list()
        self._eat('}')
        return jackgrammar.Class(class_name=class_name,
                                 class_var_dec_list=class_var_dec_list,
                                 subroutine_dec_list=subroutine_dec_list)

    def _compile_class_var_dec_list(self):
        class_var_dec_list = []
        while self._get_current().val in [Keyword.static, Keyword.field]:
            class_var_dec = self._compile_class_var_dec()
            class_var_dec_list.append(class_var_dec)

        return class_var_dec_list

    def _compile_class_var_dec(self) -> jackgrammar.ClassVarDec:
        dec = self._get_and_advance().val
        type_, var_names = self._compile_var_names()
        return jackgrammar.ClassVarDec(dec=dec, type_=type_, var_names=var_names)

    def _compile_var_names(self):
        type_ = self._get_type()
        var_names: list[tokens.Identifier] = [self._get_identifier()]
        while self._equals_symbol(","):
            self.input.advance()
            var_names.append(self._get_identifier())
        self._eat(";")
        return type_, var_names

    def _compile_subroutine_dec_list(self):
        subroutine_dec_list = []

        while self._get_current().val in [Keyword.constructor, Keyword.function, Keyword.method]:
            subroutine_dec = self.compile_subroutine_dec()
            subroutine_dec_list.append(subroutine_dec)
        return subroutine_dec_list

    def compile_subroutine_dec(self) -> jackgrammar.SubroutineDec:
        current = self._get_and_advance().val
        type_ = self._get_type(accept_void=True)
        subroutine_name = self._get_identifier()
        self._eat("(")
        parameter_list = self._compile_parameter_list()
        self._eat(")")
        subroutine_body = self._compile_subroutine_body()
        return jackgrammar.SubroutineDec(dec=current, ret_val=type_, subroutine_name=subroutine_name,
                                         parameter_list=parameter_list, subroutine_body=subroutine_body)

    def _compile_parameter_list(self):
        if self._equals_symbol(")"):
            return []

        parameter_list = [self._compile_parameter()]
        while self._equals_symbol(","):
            self.input.advance()
            parameter_list.append(self._compile_parameter())

        return parameter_list

    def _compile_parameter(self):
        type_ = self._get_type()
        var_name = self._get_identifier()
        param = jackgrammar.Parameter(type_=type_, var_name=var_name)
        return param

    def _compile_subroutine_body(self):
        self._eat("{")
        var_dec_list = self.compile_var_dec_list()
        statements = self.compile_statements()
        self._eat("}")
        return jackgrammar.SubroutineBody(var_dec_list=var_dec_list, statements=statements)

    def compile_var_dec_list(self) -> list[jackgrammar.VarDec]:
        var_dec_list = []
        while self.input.has_more_tokens() and self.input.get_current_token().val == Keyword.var:
            self.input.advance()
            type_, var_names = self._compile_var_names()
            var_dec_list.append(jackgrammar.VarDec(type_, var_names))
        return var_dec_list

    def _get_type(self, advance=True, accept_void=False) -> jackgrammar.TYPES:
        current = self._get_current()
        if advance:
            self.input.advance()

        if isinstance(current, tokens.KeywordConstant):
            possible_types = [Keyword.int_, Keyword.char, Keyword.boolean]
            if accept_void:
                possible_types.append(Keyword.void)

            if not current.val in possible_types:
                raise StructureError(f"Expected to get a type keyword but instead got {current.val}.")
            return current.val
        if isinstance(current, tokens.Identifier):
            return current
        raise StructureError(f"Expected to get a type, instead got {current}.")

    def _try_get_type(self) -> Optional[jackgrammar.TYPES]:
        try:
            return self._get_type(advance=False)
        except StructureError:
            return None

    def _assert_is_identifier(self):
        try:
            self._get_identifier(advance=False)
            return True
        except StructureError:
            return False

    def _get_identifier(self, advance=True) -> tokens.Identifier:
        current = self._get_current()
        if not isinstance(current, tokens.Identifier):
            raise StructureError(f"Expected an identifier but got {self.input.get_current_token().val}")
        if advance:
            self.input.advance()
        return current

    def compile_statements(self):
        statement_handlers = {
            Keyword.let: self.compile_let,
            Keyword.if_: self.compile_if,
            Keyword.while_: self.compile_while,
            Keyword.do: self.compile_do,
            Keyword.return_: self.compile_return,
        }

        statements = []
        while self.input.has_more_tokens() and self.input.get_current_token().val in statement_handlers:
            statement = statement_handlers[self.input.get_current_token().val]()
            statements.append(statement)

        return statements

    def compile_let(self) -> jackgrammar.LetStatement:
        self.input.advance()
        var_name = self._get_identifier()
        next_token = self._get_and_advance()
        if not isinstance(next_token, tokens.Symbol):
            raise StructureError("Let statement is missing '[' or '=' after identifier.")
        if next_token.val == "[":
            at_index = self.compile_expression()
            self._eat("]")
            self._eat("=")
        elif next_token.val == "=":
            at_index = None
        else:
            raise StructureError("Let statement is missing '[' or '=' after identifier.")

        expression = self.compile_expression()
        self._eat(";")
        return jackgrammar.LetStatement(var_name=var_name, at_index=at_index, expression=expression)

    def compile_if(self) -> jackgrammar.IfStatement:
        self.input.advance()
        self._eat("(")
        condition = self.compile_expression()
        self._eat(")")
        self._eat("{")
        then_statements = self.compile_statements()
        self._eat("}")
        if self.input.has_more_tokens() and self._get_current().val == Keyword.else_:
            self._eat(Keyword.else_)
            self._eat("{")
            else_statements = self.compile_statements()
            self._eat("}")
        else:
            else_statements = None

        return jackgrammar.IfStatement(condition, then_statements, else_statements)

    def compile_while(self):
        self.input.advance()
        self._eat("(")
        condition = self.compile_expression()
        self._eat(")")
        self._eat("{")
        statements = self.compile_statements()
        self._eat("}")
        return jackgrammar.WhileStatement(condition=condition, statements=statements)

    def compile_do(self) -> jackgrammar.DoStatement:
        self.input.advance()
        term = self.compile_term()
        if not isinstance(term, jackgrammar.SubroutineCall):
            raise StructureError(f"Do statement expects to have subroutine call, got {term}.")
        self._eat(";")
        return jackgrammar.DoStatement(subroutine_call=term)

    def compile_return(self):
        self.input.advance()
        if self._equals_symbol(";"):
            expression = None
        else:
            expression = self.compile_expression()

        self._eat(";")

        return jackgrammar.ReturnStatement(expression=expression)

    def compile_expression(self):
        expression = [self.compile_term()]
        while self._is_op():
            expression.append(self._get_and_advance().val)
            expression.append(self.compile_term())
        return jackgrammar.Expression(terms_and_ops=expression)

    def compile_expression_list(self):
        # Expression list is always terminated in ')'
        if self._equals_symbol(")"):
            return []

        expressions = [self.compile_expression()]
        while self._equals_symbol(","):
            self.input.advance()
            expressions.append(self.compile_expression())

        return expressions

    def compile_term(self) -> jackgrammar.TERM:
        current = self._get_and_advance()
        if isinstance(current,
                      (tokens.IntegerConstant, tokens.StringConstant)):
            return current
        if isinstance(current, tokens.KeywordConstant):
            return current.val
        if isinstance(current, tokens.Symbol):
            if current.val == "(":
                expression = self.compile_expression()
                self._eat(")")
                return expression
            elif current.val in "-~":
                unary_op = current.val
                term = self.compile_term()
                return jackgrammar.CompoundTerm(unary_op=unary_op, term=term)
            else:
                raise StructureError(f"Got invalid symbol '{current.val}' as term")

        # Then current is identifier

        next_token = self._get_current()
        if not isinstance(next_token, tokens.Symbol):
            return current

        if next_token.val == "[":
            self.input.advance()
            expression = self.compile_expression()
            self._eat("]")
            return jackgrammar.ArrayAt(var_name=current, at_index=expression)

        if next_token.val == "(":
            self.input.advance()
            parent = None
            subroutine_name = current
            expression_list = self.compile_expression_list()
            self._eat(")")
            return jackgrammar.SubroutineCall(
                parent=parent, subroutine_name=subroutine_name, expression_list=expression_list)

        if next_token.val == ".":
            self.input.advance()
            parent = current
            subroutine_name = self._get_identifier()
            self._eat("(")
            expression_list = self.compile_expression_list()
            self._eat(")")
            return jackgrammar.SubroutineCall(
                parent=parent, subroutine_name=subroutine_name, expression_list=expression_list)

        return current

    def _is_op(self):
        current = self._get_current()
        if isinstance(current, tokens.Symbol):
            return current.val in "+-*/&|<>="
        else:
            return False

    def _equals_symbol(self, expected: str):
        current = self._get_current()
        if isinstance(current, tokens.Symbol):
            return current.val == expected

    def _eat(self, expected: Union[Keyword, str]):
        current = self._get_and_advance()

        if isinstance(current, tokens.KeywordConstant):
            if isinstance(expected, Keyword):
                if current.val != expected:
                    raise StructureError(f"Expected keyword {expected} but got {current.val}.")
            else:
                raise StructureError(f"Expected symbol {expected} but got keyword {current}.")
        elif isinstance(current, tokens.Symbol):
            if isinstance(expected, str):
                if current.val != expected:
                    raise StructureError(f"Expected symbol '{expected}' but got '{current.val}'.")
            else:
                raise StructureError(f"Expected keyword {expected} but got symbol {current.val}.")
        else:
            raise StructureError(f"Expected keyword or symbol but got {current}.")

    def _get_current(self):
        current = self.input.get_current_token()
        if current is None:
            raise IncompleteCommandError(f"Reached end-of-file unexpectedly.")
        return current

    def _get_and_advance(self) -> tokens.Token:
        current = self._get_current()
        self.input.advance()
        return current
