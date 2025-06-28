import argparse
import glob
import os
import sys
import traceback

from compiler.jackparser import jackparser, jacktokenizer, xmlgenerator
from compiler.errors import CompilationError


def main():
    parser = argparse.ArgumentParser(
        description="JackAnalyzer - Convert .jack file(s) to .xml output.")
    parser.add_argument("input", help="Input .jack file or a directory containing .jack files")
    parser.add_argument(
        "--crlf",
        action="store_true",
        help="Use CRLF (Windows-style) line endings in output XML files"
    )
    args = parser.parse_args()

    input_path = args.input
    line_ending = "\r\n" if args.crlf else "\n"

    if not os.path.exists(input_path):
        print(f"Error: '{input_path}' does not exist.")
        sys.exit(2)

    try:
        if os.path.isdir(input_path):
            analyze_folder(input_path, line_ending)
        elif input_path.endswith(".jack") and os.path.isfile(input_path):
            analyze_file(input_path, line_ending)
        else:
            print("Error: Input must be a .jack file or a directory containing .jack files.")
            sys.exit(3)
    except CompilationError:
        traceback.print_exc()
        sys.exit(1)

    print(f"Analyzer ended successfully.")


def analyze_folder(folder_path, line_ending):
    translated_files = 0
    for file_name in glob.iglob("**/*.jack", root_dir=folder_path, recursive=True):
        translated_files += 1
        file_path = os.path.join(folder_path, file_name)
        analyze_file(file_path, line_ending)

    if translated_files == 0:
        print("Error: Could not find any .jack files in the folder.")
        exit(4)


def analyze_file(file_path, line_ending):
    print(f"Analyzing {file_path}")
    output_file = file_path.replace(".jack", ".xml")

    with open(file_path, 'r') as jack_file:
        try:
            tokenizer = jacktokenizer.JackTokenizer(jack_file)
            compiler = compilationengine.JackParser(tokenizer)
            content = compiler.compile_class()
        except Exception:
            print(f"ERROR: Error occurred while parsing line: {tokenizer.get_current_line()}")
            print()
            raise

    with open(output_file, 'w') as xml_file:
        xml_gen = xmlgenerator.XmlGenerator()
        xml_gen.write_class(content, xml_file, line_ending=line_ending)


if __name__ == "__main__":
    main()
