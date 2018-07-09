import sys
import Parser
import CodeWriter
from os import listdir
from os.path import isfile, isdir, join, split


def generate_code(in_file, output_file):
    parser = Parser.Parser(in_file)
    (CodeWriter.Code_Writer(parser.parse(), in_file)).generate_asm_code(output_file)


if __name__ == "__main__":
    in_path = sys.argv[1]
    if isfile(in_path):
        out_file = in_path.replace('vm', 'asm')
        with open(out_file, 'w') as asm_file:
            generate_code(in_path, asm_file)
    elif isdir(in_path):
        folder_name = str(split(in_path)[1].split('.')[0])
        out_file = join(in_path,  folder_name + '.asm')
        with open(out_file, 'w') as asm_file:
            CodeWriter.Code_Writer(None, 'Sys.vm').write_bootstrap(asm_file)
            vm_files = [f for f in listdir(in_path) if isfile(join(in_path, f)) and '.vm' in f]
            for vm_file in vm_files:
                generate_code(join(in_path, vm_file), asm_file)








