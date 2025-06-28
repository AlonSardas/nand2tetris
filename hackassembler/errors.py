class AssemblerError(Exception):
    def __init__(self, msg: str, line: str = "", lineno: int = -1):
        super().__init__(msg)
        self.msg = msg
        self.line = line
        self.lineno = lineno

    def __str__(self):
        return f"{self.msg}. Raised from command\n{self.line}\nat line {self.lineno}"


class MultipleSymbolDefinitionError(AssemblerError):
    pass


class BadSymbolNameError(AssemblerError):
    pass
