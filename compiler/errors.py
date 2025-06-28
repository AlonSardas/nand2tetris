class CompilationError(Exception):
    pass


class ParserError(CompilationError):
    pass


class StructureError(CompilationError):
    pass


class IncompleteCommandError(StructureError):
    pass


class UndefinedVariableError(CompilationError):
    pass


class SymbolNotFoundError(CompilationError):
    pass