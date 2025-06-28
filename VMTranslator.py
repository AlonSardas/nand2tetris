import argparse
import os
import sys
import traceback

from vmtranslator import vmtranslator
from vmtranslator.errors import TranslatorError


def main():
    parser = argparse.ArgumentParser(
        description="VMTranslator - Convert .vm file(s) to .asm assembly output.")
    parser.add_argument("input", help="Input .vm file or a directory containing .vm files")
    args = parser.parse_args()

    input_path = args.input

    if not os.path.exists(input_path):
        print(f"Error: '{input_path}' does not exist.")
        sys.exit(2)

    try:
        if os.path.isdir(input_path):
            output_file = vmtranslator.translate_folder(input_path)
        elif input_path.endswith(".vm") and os.path.isfile(input_path):
            output_file = vmtranslator.translate_file(input_path)
        else:
            print("Error: Input must be a .vm file or a directory containing .vm files.")
            sys.exit(3)
    except TranslatorError:
        traceback.print_exc()
        sys.exit(1)

    print(f"Successfully translated file: {output_file}")


if __name__ == "__main__":
    main()
