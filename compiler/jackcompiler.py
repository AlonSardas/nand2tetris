from typing import IO

from compiler import vmwriter, symboltable, jackgrammar, errors
from compiler.jackparser import jacktokenizer, jackparser, tokens, languagerules
from compiler.jackparser.languagerules import Keyword
from compiler.symboltable import SymbolKind
from vmtranslator import vmcommands

THIS_ARG = "this"

OP_TO_VM_COMMAND = {
    '+': vmcommands.Add,
    '-': vmcommands.Sub,
    '&': vmcommands.And,
    '|': vmcommands.Or,
    '<': vmcommands.LT,
    '>': vmcommands.GT,
    '=': vmcommands.EQ,
}

OS_MULTIPLY = "Math.multiply"
OS_DIVIDE = "Math.divide"
OS_STRING_CONSTRUCTOR = "String.new"
OS_STRING_APPEND_CHAR = "String.appendChar"
OS_ALLOC = "Memory.alloc"


class JackCompiler:
    def __init__(self, input_stream: IO[str], output_stream: IO[str]):
        tokenizer = jacktokenizer.JackTokenizer(input_stream)
        parser = jackparser.JackParser(tokenizer)

        try:
            self.class_ = parser.compile_class()
        except errors.CompilationError:
            print(f"Error while parsing line {tokenizer.get_current_line()}.")
            print()
            raise

        self.class_name = self.class_.class_name
        self._func_name = ""
        self.symbol_table = symboltable.SymbolTable()
        self.vmwriter = vmwriter.VMWriter(output_stream)
        self._label_index = 0

    def compile(self):
        self.compile_class(self.class_)

    def compile_class(self, class_: jackgrammar.Class):
        self._define_class_var_dec(class_.class_var_dec_list)
        for subroutine_dec in class_.subroutine_dec_list:
            self._func_name = subroutine_dec.subroutine_name.val
            self.compile_subroutine_dec(subroutine_dec)

    def _define_class_var_dec(self, class_var_dec_list):
        for class_var_dec in class_var_dec_list:
            if class_var_dec.dec == Keyword.static:
                kind = SymbolKind.static
            elif class_var_dec.dec == Keyword.field:
                kind = SymbolKind.field
            else:
                raise RuntimeError(f"Unknown class var dec {class_var_dec.dec}")

            type_ = class_var_dec.type_
            for var_name in class_var_dec.var_names:
                self.symbol_table.define(var_name.val, type_, kind)

    def compile_subroutine_dec(self, subroutine_dec: jackgrammar.SubroutineDec):
        self.symbol_table.start_subroutine()

        n_locals = self._define_local_var_list(subroutine_dec.subroutine_body.var_dec_list)
        name = f"{self.class_name.val}.{subroutine_dec.subroutine_name.val}"
        self.vmwriter.write_function(name, n_locals)

        if subroutine_dec.dec == Keyword.constructor:
            # Allocate the memory
            n_fields = self.symbol_table.get_num_of_fields()
            if n_fields > 0:
                self.vmwriter.write_push(vmcommands.Segment.constant, n_fields)
                self.vmwriter.write_call(OS_ALLOC, 1)
                self.vmwriter.write_pop(vmcommands.Segment.pointer, 0)

        if subroutine_dec.dec == Keyword.method:
            # Set this to first argument
            self.vmwriter.write_push(vmcommands.Segment.argument, 0)
            self.vmwriter.write_pop(vmcommands.Segment.pointer, 0)

            # Define this as an argument
            self.symbol_table.define(THIS_ARG, self.class_name, SymbolKind.argument)
        self._define_parameter_list(subroutine_dec.parameter_list)

        self.compile_statements(subroutine_dec.subroutine_body.statements)

    def _define_parameter_list(self, parameter_list: list[jackgrammar.Parameter]):
        for param in parameter_list:
            self.symbol_table.define(param.var_name.val, param.type_, SymbolKind.argument)

    def _define_local_var_list(self, var_dec_list: list[jackgrammar.VarDec]):
        n_locals = 0
        for var_dec in var_dec_list:
            for var_name in var_dec.var_names:
                self.symbol_table.define(var_name.val, var_dec.type_, SymbolKind.local)
                n_locals += 1
        return n_locals

    def compile_statements(self, statements: list[jackgrammar.Statement]):
        def bad(_):
            raise RuntimeError("Got an instance of jackgrammer.Statement.")

        statement_handlers = {
            jackgrammar.LetStatement: self.compile_let,
            jackgrammar.IfStatement: self.compile_if,
            jackgrammar.WhileStatement: self.compile_while,
            jackgrammar.DoStatement: self.compile_do,
            jackgrammar.ReturnStatement: self.compile_return,
            jackgrammar.Statement: bad
        }

        for statement in statements:
            statement_handlers[type(statement)](statement)

    def compile_let(self, statement: jackgrammar.LetStatement):
        if statement.at_index:
            self._compile_let_with_array(statement)
            return

        kind, index = self.symbol_table.get_kind_and_index(statement.var_name.val)
        segment = vmcommands.Segment[kind.value]

        self.compile_expression(statement.expression)
        self.vmwriter.write_pop(segment, index)

    def _compile_let_with_array(self, statement):
        self._compile_term(statement.var_name)
        self.compile_expression(statement.at_index)
        self.vmwriter.write_arithmetic(vmcommands.Add)
        self.compile_expression(statement.expression)

        self.vmwriter.write_pop(vmcommands.Segment.temp, 0)  # temp 0=RHS
        self.vmwriter.write_pop(vmcommands.Segment.pointer, 1)  # THAT=addr of LHS
        self.vmwriter.write_push(vmcommands.Segment.temp, 0)  # RHS on top of the stack
        self.vmwriter.write_pop(vmcommands.Segment.that, 0)  # LHS=RHS

    def compile_if(self, statement: jackgrammar.IfStatement):
        else_label = self.get_label("if_else")
        end_label = self.get_label("end_if")

        self.compile_expression(statement.condition)
        self.vmwriter.write_arithmetic(vmcommands.Not)

        self.vmwriter.write_if_goto(else_label)

        self.compile_statements(statement.then_statements)
        self.vmwriter.write_goto(end_label)

        self.vmwriter.write_label(else_label)
        if statement.else_statements is not None:
            self.compile_statements(statement.else_statements)

        self.vmwriter.write_label(end_label)

    def compile_while(self, statement: jackgrammar.WhileStatement):
        while_label = self.get_label("while")
        end_label = self.get_label("end_while")
        self.vmwriter.write_label(while_label)
        self.compile_expression(statement.condition)
        self.vmwriter.write_arithmetic(vmcommands.Not)
        self.vmwriter.write_if_goto(end_label)
        self.compile_statements(statement.statements)
        self.vmwriter.write_goto(while_label)
        self.vmwriter.write_label(end_label)

    def compile_do(self, statement: jackgrammar.DoStatement):
        self._compile_subroutine_call(statement.subroutine_call)
        # Pop the unused return value
        self.vmwriter.write_pop(vmcommands.Segment.temp, 0)

    def _compile_subroutine_call(self, subroutine_call):
        with_this_argument = 0
        if subroutine_call.parent:
            parent_name = subroutine_call.parent.val
            try:
                entry = self.symbol_table.get_entry(parent_name)
                type_ = entry.type_
                if not isinstance(type_, tokens.Identifier):
                    raise errors.CompilationError(f"Called a method of a primitive type {type_}.")
                scope = type_.val

                # This is a method call, so add this as first argument
                self.vmwriter.write_push(entry.kind, entry.index)
                with_this_argument = 1

            except errors.SymbolNotFoundError:
                # Then it is a name of another class
                scope = parent_name
        else:
            scope = self.class_name.val
            # And this is a method call, so add this as argument
            self.vmwriter.write_push(vmcommands.Segment.pointer, 0)
            with_this_argument = 1

        args = subroutine_call.expression_list
        for expr in args:
            self.compile_expression(expr)
        func_name = f"{scope}.{subroutine_call.subroutine_name.val}"
        self.vmwriter.write_call(func_name, len(args) + with_this_argument)

    def compile_return(self, statement: jackgrammar.ReturnStatement):
        if statement.expression:
            self.compile_expression(statement.expression)
        else:
            self._compile_term(tokens.IntegerConstant(0))
        self.vmwriter.write_return()

    def compile_expression(self, expression: jackgrammar.Expression):
        terms_and_ops = expression.terms_and_ops
        self._compile_term(terms_and_ops[0])
        index = 1
        while index < len(terms_and_ops):
            self._compile_term(terms_and_ops[index + 1])
            self._compile_op(terms_and_ops[index])
            index += 2

    def _compile_term(self, term: jackgrammar.TERM):
        if isinstance(term, tokens.Identifier):
            name = term.val
            kind, index = self.symbol_table.get_kind_and_index(name)
            segment = vmcommands.Segment[kind.value]
            self.vmwriter.write_push(segment, index)
        elif isinstance(term, tokens.IntegerConstant):
            self.vmwriter.write_push(vmcommands.Segment.constant, term.val)
        elif isinstance(term, tokens.StringConstant):
            self._compile_string_constant(term)
        elif isinstance(term, jackgrammar.Expression):
            self.compile_expression(term)
        elif isinstance(term, jackgrammar.ArrayAt):
            self._compile_array_at(term)
        elif isinstance(term, jackgrammar.CompoundTerm):
            self._compile_term(term.term)
            if term.unary_op == "-":
                self.vmwriter.write_arithmetic(vmcommands.Neg)
            elif term.unary_op == "~":
                self.vmwriter.write_arithmetic(vmcommands.Not)
            else:
                raise RuntimeError(f"Got an unknown unary op {term.unary_op}.")
        elif isinstance(term, jackgrammar.SubroutineCall):
            self._compile_subroutine_call(term)
        elif isinstance(term, languagerules.Keyword):
            self._compile_keyword_constant(term)
        else:
            raise RuntimeError(f"Got an unknown term type {type(term)}.")

    def _compile_op(self, op: jackgrammar.OPS):
        command = OP_TO_VM_COMMAND.get(op)
        if command is not None:
            self.vmwriter.write_arithmetic(command)
        else:
            if op == "*":
                self.vmwriter.write_call(OS_MULTIPLY, 2)
            elif op == "/":
                self.vmwriter.write_call(OS_DIVIDE, 2)
            else:
                raise RuntimeError(f"Got an unknown op {op}.")

    def _compile_keyword_constant(self, keyword: Keyword):
        if keyword == Keyword.true:
            self.vmwriter.write_push(vmcommands.Segment.constant, 1)
            self.vmwriter.write_arithmetic(vmcommands.Neg)
        elif keyword == Keyword.false or keyword == Keyword.null:
            self.vmwriter.write_push(vmcommands.Segment.constant, 0)
        elif keyword == Keyword.this:
            self.vmwriter.write_push(vmcommands.Segment.pointer, 0)
        else:
            raise RuntimeError(f"Got an unknown keyword constant {keyword}")

    def _compile_string_constant(self, string: tokens.StringConstant):
        value = string.val
        string_len = len(value)
        self.vmwriter.write_push(vmcommands.Segment.constant, string_len)
        self.vmwriter.write_call(OS_STRING_CONSTRUCTOR, 1)
        # The return value remains at the top of the stack, and become the parameter for
        # appendChar
        for c in value:
            self.vmwriter.write_push(vmcommands.Segment.constant, ord(c))
            self.vmwriter.write_call(OS_STRING_APPEND_CHAR, 2)
            # The return value is the same string. It will become the first argument of the next call

        # The string is at the top of the stack by the return value

    def _compile_array_at(self, array_at: jackgrammar.ArrayAt):
        self._compile_term(array_at.var_name)
        self.compile_expression(array_at.at_index)
        self.vmwriter.write_arithmetic(vmcommands.Add)
        self.vmwriter.write_pop(vmcommands.Segment.pointer, 1)  # THAT=addr of b[j]
        self.vmwriter.write_push(vmcommands.Segment.that, 0)  # b[j] at top of the stack

    def get_label(self, name):
        assert self._func_name != ""
        label = f"{self.class_name.val}.{self._func_name}${name}_{self._label_index}"
        self._label_index += 1
        return label
