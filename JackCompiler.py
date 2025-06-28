import argparse
import glob
import os
import sys
import traceback

from compiler import errors, jackcompiler


def main():
    parser = argparse.ArgumentParser(
        description="JackCompiler - Convert .jack file(s) to .vm output.")
    parser.add_argument("input", help="Input .jack file or a directory containing .jack files")
    args = parser.parse_args()

    input_path = args.input

    if not os.path.exists(input_path):
        print(f"Error: '{input_path}' does not exist.")
        sys.exit(2)

    try:
        if os.path.isdir(input_path):
            analyze_folder(input_path)
        elif input_path.endswith(".jack") and os.path.isfile(input_path):
            analyze_file(input_path)
        else:
            print("Error: Input must be a .jack file or a directory containing .jack files.")
            sys.exit(3)
    except errors.CompilationError:
        traceback.print_exc()
        sys.exit(1)

    print(f"Compilation ended successfully.")


def analyze_folder(folder_path):
    translated_files = 0
    for file_name in glob.iglob("**/*.jack", root_dir=folder_path, recursive=True):
        translated_files += 1
        file_path = os.path.join(folder_path, file_name)
        analyze_file(file_path)

    if translated_files == 0:
        print("Error: Could not find any .jack files in the folder.")
        exit(4)


def analyze_file(file_path):
    print(f"Compiling {file_path}")
    output_file = file_path.replace(".jack", ".vm")

    with open(file_path, 'r') as jack_file:
        with open(output_file, 'w') as vm_file:
            compiler = jackcompiler.JackCompiler(jack_file, vm_file)
            compiler.compile()


if __name__ == "__main__":
    main()
