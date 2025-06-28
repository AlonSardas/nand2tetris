import re

from hackassembler.errors import MultipleSymbolDefinitionError, BadSymbolNameError

PREDEFINED_SYMBOLS = {
    "SCREEN": 0X4000,
    "KBD": 0X6000,
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4
}
PREDEFINED_SYMBOLS.update((f"R{i}", i) for i in range(16))
BASE_VARIABLE_SYMBOL_POSITION = 16


class SymbolManager(object):
    def __init__(self):
        self.label_symbol_regex = re.compile(r"^([a-zA-Z_.][a-zA-Z_.$0-9]*)$")
        self.symbol_table = PREDEFINED_SYMBOLS.copy()
        self.symbols_to_resolve = []
        self.variable_symbol_position = BASE_VARIABLE_SYMBOL_POSITION

    def try_resolve_symbol(self, line: str, cur_command: int) -> int:
        symbol = self._verify_symbol(line)

        resolved_symbol = self.symbol_table.get(symbol)
        if resolved_symbol is not None:
            return resolved_symbol
        else:
            self.symbols_to_resolve.append((symbol, cur_command))
            return 0

    def create_new_label_symbol(self, line: str, cur_command: int):
        symbol = self._verify_symbol(line)

        old_definition = self.symbol_table.get(symbol)
        if old_definition is not None:
            raise MultipleSymbolDefinitionError(f"Symbol was already defined at command {old_definition}")

        self.symbol_table[symbol] = cur_command

    def resolve_all_symbols(self, commands):
        for symbol, index in self.symbols_to_resolve:
            resolved_symbol = self.symbol_table.get(symbol)
            if resolved_symbol is None:
                resolved_symbol = self.variable_symbol_position
                self.variable_symbol_position += 1
            assert resolved_symbol < 2 ** 15
            self.symbol_table[symbol] = resolved_symbol
            commands[index] = resolved_symbol

    def _verify_symbol(self, line) -> str:
        match = self.label_symbol_regex.match(line)
        if not match:
            raise BadSymbolNameError("Could not parse the label symbol")

        return match.group(1)
