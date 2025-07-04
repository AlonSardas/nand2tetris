from typing import IO


class LineCounter:
    def __init__(self, input_stream: IO[str]):
        self.input = input_stream
        self._line_number = 1

    def read_char(self):
        char = self.input.read(1)
        if char == "\n":
            self._line_number += 1
        return char

    def get_current_line(self):
        return self._line_number
