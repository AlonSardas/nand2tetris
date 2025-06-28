import glob
import io
import os.path
from typing import IO, Optional

from vmtranslator import parser, asmgenerator
from vmtranslator.errors import TranslatorError
from vmtranslator.parser import strip_line


class VMTranslator(object):

    def __init__(self, asm_generator):
        self.asm_generator = asm_generator

    def translate(self, input_stream: IO[str], output_stream: IO[str]):
        line_number = 0
        for original_line in input_stream:
            line_number += 1
            line = strip_line(original_line)
            if line == "":
                continue
            output_stream.write(f"// {line}\n")
            try:
                command = parser.parse_line(line)
                asm_code = self.asm_generator.generate_asm(command, line_number)
                output_stream.write(asm_code)
                output_stream.write("\n")
            except TranslatorError as e:
                e.line = line
                e.lineno = line_number
                raise


class VMFolderTranslator(object):
    def __init__(self, folder_path, asm_generator: asmgenerator.AsmGenerator):
        self.folder_path = folder_path
        self.asm_generator = asm_generator

    def translate(self, output_stream: IO[str]):
        init = self.asm_generator.generate_init()
        output_stream.write(init)
        output_stream.write("\n")

        translated_files = 0
        for file_name in glob.iglob("**/*.vm", root_dir=self.folder_path, recursive=True):
            print(f"Translating {file_name}")
            translated_files += 1
            self._write_header(file_name, output_stream)
            self.asm_generator.set_source_file(file_name)

            file_path = os.path.join(self.folder_path, file_name)
            with open(file_path) as f:
                translator = VMTranslator(self.asm_generator)
                translator.translate(f, output_stream)
        if translated_files == 0:
            raise RuntimeError("There are no .vm files in the given directory")

    def _write_header(self, file_path: str, output_stream):
        header = f"// {file_path}"
        output_stream.write("/" * len(header))
        output_stream.write("\n")
        output_stream.write(header)
        output_stream.write("\n")
        output_stream.write("/" * len(header))
        output_stream.write("\n")


def translate_text(code: str, filename="code.vm") -> str:
    asm_gen = asmgenerator.AsmGenerator()
    asm_gen.set_source_file(filename)
    vm_translator = VMTranslator(asm_gen)
    with io.StringIO(code) as source:
        with io.StringIO() as output:
            vm_translator.translate(source, output)
            output.seek(0)
            return output.read()


def translate_file(input_file: str, output_file: Optional[str] = None) -> str:
    if output_file is None:
        output_file = input_file.replace(".vm", ".asm")

    asm_generator = asmgenerator.AsmGenerator()
    asm_generator.set_source_file(output_file)
    translator = VMTranslator(asm_generator)
    with open(input_file, 'r') as vm_file:
        with open(output_file, 'w') as asm_file:
            translator.translate(vm_file, asm_file)

    return output_file


def translate_folder(folder_path: str, output_file: Optional[str] = None) -> str:
    if output_file is None:
        folder_path = os.path.normpath(folder_path)
        basename = os.path.basename(folder_path) + ".asm"
        output_file = os.path.join(folder_path, basename)

    asm_generator = asmgenerator.AsmGenerator()
    folder_translator = VMFolderTranslator(folder_path, asm_generator)
    with open(output_file, 'w') as asm_file:
        folder_translator.translate(asm_file)

    return output_file
