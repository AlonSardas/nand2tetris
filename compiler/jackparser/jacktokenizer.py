from typing import IO

from compiler.jackparser import languagerules, tokens
from compiler.errors import ParserError
from compiler.jackparser.tokens import Token


class JackTokenizer:
    def __init__(self, input_stream: IO[str]):
        self.input = input_stream
        self._current_token = None
        self._line_number = 1
        self._next_char = input_stream.read(1)
        if self._next_char == "":
            raise ValueError("The given input stream is empty")
        self.advance()

    def has_more_tokens(self) -> bool:
        return self._next_char != ""

    def get_current_token(self) -> Token:
        return self._current_token

    def get_current_line(self) -> int:
        return self._line_number

    def advance(self):
        if self._next_char == "":
            # To avoid returning the same token again
            self._current_token = None
            return

        found_token = self._try_advance()
        while not found_token and self._next_char != "":
            found_token = self._try_advance()
        self._exhaust_whitespaces()

    def _try_advance(self) -> bool:
        """
        Advances until a symbol or a comment is encountered.
        If a comment is encountered, read until the end of it.
        If a symbol is encountered, parse it and generate the relevant token

        :return: bool
        """
        self._exhaust_whitespaces()

        if self._next_char == "/":
            next_next_char = self.input.read(1)
            if next_next_char == "/":
                self._exhaust_line_comment()
                return False
            elif next_next_char == "*":
                self._exhaust_block_comment()
                return False
            else:
                self._current_token = tokens.Symbol(self._next_char)
                self._next_char = next_next_char
                return True

        if self._next_char == "":
            return False

        if self._next_char in languagerules.SYMBOLS:
            self._current_token = tokens.Symbol(self._next_char)
            self._next_char = self.input.read(1)

        elif self._next_char.isdigit():
            num = self._read_number()
            if num > languagerules.MAX_NUMBER:
                raise ParserError(
                    f"Got a number {num} that is larger then the maximum allowed number {languagerules.MAX_NUMBER}.")
            self._current_token = tokens.IntegerConstant(int(num))

        elif self._next_char == languagerules.STRING_DELIMITER:
            string = self._read_string()
            self._current_token = tokens.StringConstant(string)

        else:
            word = self._read_word()
            if word in languagerules.KEYWORDS:
                keyword = languagerules.KEYWORDS[word]
                self._current_token = tokens.KeywordConstant(keyword)
            else:
                self._current_token = tokens.Identifier(word)

        return True

    def _exhaust_whitespaces(self):
        """
        Reads until the first non-whitespace character is encountered
        """
        while self._next_char.isspace():
            if self._next_char == "\n":
                self._line_number += 1
            self._next_char = self.input.read(1)

    def _exhaust_line_comment(self):
        self._next_char = self.input.read(1)
        while self._next_char != "" and self._next_char != "\n":
            self._next_char = self.input.read(1)

    def _exhaust_block_comment(self):
        while self._next_char != "":
            self._next_char = self.input.read(1)
            if self._next_char == "\n":
                self._line_number += 1
            if self._next_char == "*":
                self._next_char = self.input.read(1)
                if self._next_char == "/":
                    break

        self._next_char = self.input.read(1)

    def _read_number(self) -> int:
        num = self._next_char
        self._next_char = self.input.read(1)
        while self._next_char.isdigit():
            num += self._next_char
            self._next_char = self.input.read(1)
            if len(num) > languagerules.MAX_NUMBER_DIGITS:
                raise ParserError("Got a number that contains more the 5 digits.")

        return int(num)

    def _read_string(self) -> str:
        string = ""
        self._next_char = self.input.read(1)
        while self._next_char != languagerules.STRING_DELIMITER:
            if self._next_char == "":
                raise ParserError("Reached end-of-file with an open string.")
            if self._next_char == "\n":
                raise ParserError("Reached the end of a line with an open string.")

            string += self._next_char
            self._next_char = self.input.read(1)
        self._next_char = self.input.read(1)

        return string

    def _read_word(self) -> str:
        word = self._next_char
        self._next_char = self.input.read(1)
        while self._next_char.isalnum() or self._next_char == '_':
            word += self._next_char
            self._next_char = self.input.read(1)

        return word
