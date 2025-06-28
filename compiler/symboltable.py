from enum import Enum

from pydantic.dataclasses import dataclass

from compiler import jackgrammar, errors


class SymbolKind(Enum):
    field = "this"
    static = "static"
    argument = "argument"
    local = "local"


@dataclass
class SymbolEntry:
    name: str
    type_: jackgrammar.TYPES
    kind: SymbolKind
    index: int


class SymbolTable:
    def __init__(self):
        self._counters = {
            SymbolKind.field: 0,
            SymbolKind.static: 0,
            SymbolKind.argument: 0,
            SymbolKind.local: 0,
        }
        self.class_symbols: dict[str, SymbolEntry] = {}
        self.subroutine_symbols: dict[str, SymbolEntry] = {}
        self._n_fields = 0

    def start_subroutine(self):
        self.subroutine_symbols = {}
        self._counters[SymbolKind.argument] = 0
        self._counters[SymbolKind.local] = 0

    def define(self, name: str, type_: jackgrammar.TYPES, kind: SymbolKind):
        index = self._counters[kind]
        symbol = SymbolEntry(name, type_, kind, index)
        self._counters[kind] += 1
        if kind in [SymbolKind.field, SymbolKind.static]:
            self.class_symbols[name] = symbol
            if kind == SymbolKind.field:
                self._n_fields += 1
        elif kind in [SymbolKind.argument, SymbolKind.local]:
            self.subroutine_symbols[name] = symbol
        else:
            raise RuntimeError(f"Unknown symbol kind {kind}.")

    def kind_of(self, name: str):
        entry = self._get_by_name(name)
        return entry.kind

    def index_of(self, name: str):
        entry = self._get_by_name(name)
        return entry.index

    def type_of(self, name: str):
        entry = self._get_by_name(name)
        return entry.type_

    def get_kind_and_index(self, name: str):
        entry = self._get_by_name(name)
        return entry.kind, entry.index

    def get_entry(self, name:str):
        return self._get_by_name(name)

    def get_num_of_fields(self):
        return self._n_fields

    def _get_by_name(self, name: str):
        entry = self.subroutine_symbols.get(name)
        if entry is None:
            entry = self.class_symbols.get(name)
        if entry is None:
            raise errors.SymbolNotFoundError(f"Could not find the requested symbol: {name}")
        return entry
