import argparse
import os
import sys
import traceback

from hackassembler.assembler import Assembler
from hackassembler.errors import AssemblerError


def assemble(input_file: str, output_file: str):
    asm = Assembler()
    with open(input_file, 'r') as asm_file:
        lines = asm_file.readlines()

    try:
        output = asm.assemble(lines)
    except AssemblerError:
        traceback.print_exc()
        sys.exit(1)

    with open(output_file, 'w') as hack_file:
        hack_file.writelines(output)

    print(f"Successfully assembled: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="HackAssembler - Convert .asm to .hack binary.")
    parser.add_argument("input", help="Input .asm file (Hack assembly code)")
    args = parser.parse_args()

    input_path = args.input

    if not input_path.endswith(".asm"):
        print("Error: Input file must have a .asm extension.")
        sys.exit(3)

    if not os.path.isfile(input_path):
        print(f"Error: File '{input_path}' does not exist.")
        sys.exit(2)

    # Derive output file name by replacing .asm with .hack
    output_path = input_path.replace(".asm", ".hack")

    assemble(input_path, output_path)


if __name__ == "__main__":
    main()
