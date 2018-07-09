import constants
from Parser import Command
from os.path import split


class Code_Writer:

    def __init__(self, in_parsed_lines, in_filepath):
        self.filepath = in_filepath
        self.parsed_lines = in_parsed_lines
        self.segments = {}
        self.codes = {}
        self.base_addresses = {}
        self.init_segment_table()
        self.init_code_table()
        self.file_name = str(split(in_filepath)[1].split('.')[0])
        self.count_ends = 0
        self.curr_func = ''
        self.ret_index = 0

    def init_segment_table(self):
        self.segments['local'] = 'LCL'
        self.segments['argument'] = 'ARG'
        self.segments['this'] = 'THIS'
        self.segments['that'] = 'THAT'

    def init_code_table(self):
        self.codes['push_const'] = '@{}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n'
        self.codes['push_direct'] = '@{}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n'
        self.codes['push_seg'] = '@{}\nD=A\n@{}\nA=D+M\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n'
        self.codes['pop_seg'] = '@{}\nD=A\n@{}\nD=D+M\n@R13\nM=D\n@SP\nM=M-1\nA=M\nD=M\n@R13\nA=M\nM=D\n'
        self.codes['pop_direct'] = '@SP\nM=M-1\nA=M\nD=M\n@{}\nM=D\n'

    def generate_asm_code(self, asm_file):
        for line in self.parsed_lines:
            if line.command_type == constants.C_PUSH:
                asm_file.write(self.handle_push(line))
            elif line.command_type == constants.C_POP:
                asm_file.write(self.handle_pop(line))
            elif line.command_type == constants.C_ARITHMETIC:
                asm_file.write(self.handle_arith(line))
            elif line.command_type == constants.C_IF or line.command_type == constants.C_GOTO \
                    or line.command_type == constants.C_LABEL:
                label_name = self.file_name + '.' + self.curr_func + '$' + line.arg1
                asm_file.write({constants.C_IF: '@SP\nM=M-1\nA=M\nD=M\n@{}\nD;JNE\n'.format(label_name),
                                constants.C_GOTO: '@{}\n0;JMP\n'.format(label_name),
                                constants.C_LABEL: '({})\n'.format(label_name)}[line.command_type])
            elif line.command_type == constants.C_FUNCTION:
                asm_file.write(self.handle_function(line))
            elif line.command_type == constants.C_RETURN:
                asm_file.write(self.handle_return())
            elif line.command_type == constants.C_CALL:
                asm_file.write(self.handle_call(line))
        #asm_file.write('(LOOPEND)\n@LOOPEND\n0;JMP\n')

    def handle_return(self):
        code = '@LCL\nD=M\n@R13\nM=D\n'
        code += '@R13\nD=M\n@5\nA=D-A\nD=M\n@R14\nM=D\n'
        code += '@SP\nM=M-1\nA=M\nD=M\n@ARG\nA=M\nM=D\n'
        code += '@ARG\nD=M\n@SP\nM=D+1\n'
        pop_state = '@R13\nD=M\n@{}\nA=D-A\nD=M\n@{}\nM=D\n'
        code += pop_state.format('1', 'THAT')
        code += pop_state.format('2', 'THIS')
        code += pop_state.format('3', 'ARG')
        code += pop_state.format('4', 'LCL')
        code += '@R14\nA=M\n0;JMP\n'
        return code

    def handle_function(self, cmd):
        self.curr_func = cmd.arg1
        self.ret_index = 0
        code = '({})\n'.format(cmd.arg1)
        for i in range(int(cmd.arg2)):
            code += self.codes['push_const'].format(0)
        return code

    def handle_call(self, cmd):
        ret_addr = self.curr_func + '$' + 'ret' + '.' + str(self.ret_index)
        self.ret_index += 1
        code = self.codes['push_const'].format(ret_addr)
        code += self.codes['push_direct'].format('LCL')
        code += self.codes['push_direct'].format('ARG')
        code += self.codes['push_direct'].format('THIS')
        code += self.codes['push_direct'].format('THAT')
        code += '@SP\nD=M\n@5\nD=D-A\n@{}\nD=D-A\n@ARG\nM=D\n'.format(cmd.arg2)  # ARG = sp -5 -nArgs
        code += '@SP\nD=M\n@LCL\nM=D\n'                                             # LCL = SP
        code += '@{}\n0;JMP\n'.format(cmd.arg1)
        code += '({})\n'.format(ret_addr)
        return code

    def handle_arith(self, cmd):
         pop_into_D = '@SP\nM=M-1\nA=M\nD=M\n'
         res = pop_into_D
         push_from_D = '@SP\nA=M\nM=D\n@SP\nM=M+1\n'
         if cmd.arg1 != 'neg' and cmd.arg1 != 'not':
            res += '@R13\nM=D\n'
            res += (pop_into_D + '@R13\n')
            if cmd.arg1 == 'add':
                res += 'D=M+D\n'
            elif cmd.arg1 == 'sub':
                res += 'D=D-M\n'
            elif cmd.arg1 == 'and':
                res += 'D=M&D\n'
            elif cmd.arg1 == 'or':
                res += 'D=D|M\n'
            elif cmd.arg1 == 'eq':
                res += 'D=D-M\n@ZERO{0}\nD;JEQ\nD=0\n@END{0}\n0;JMP\n(ZERO{0})\nD=-1\n(END{0})\n'\
                    .format(self.count_ends)
                self.count_ends += 1
            elif cmd.arg1 == 'lt':
                res += 'D=D-M\n@LESS{0}\nD;JLT\nD=0\n@END{0}\n0;JMP\n(LESS{0})\nD=-1\n(END{0})\n'\
                    .format(self.count_ends)
                self.count_ends += 1
            elif cmd.arg1 == 'gt':
                res += 'D=D-M\n@GREATER{0}\nD;JGT\nD=0\n@END{0}\n0;JMP\n(GREATER{0})\nD=-1\n(END{0})\n'\
                    .format(self.count_ends)
                self.count_ends += 1
         elif cmd.arg1 == 'neg':
            res += 'D=-D\n'
         elif cmd.arg1 == 'not':
            res += 'D=!D\n'
         res += push_from_D
         return res

    def handle_push(self, cmd):
        if cmd.arg1 == 'constant':
            return self.codes['push_const'].format(cmd.arg2)
        elif cmd.arg1 == 'temp':
            return self.codes['push_direct'].format(5 + int(cmd.arg2))
        elif cmd.arg1 == 'local' or cmd.arg1 == 'argument' or cmd.arg1 == 'this' or cmd.arg1 == 'that':
            return self.codes['push_seg'].format(cmd.arg2, self.segments[cmd.arg1])
        elif cmd.arg1 == 'static':
            return self.codes['push_direct'].format(self.file_name + '.' + cmd.arg2)
        elif cmd.arg1 == 'pointer':
            if cmd.arg2 == '0':
                return self.codes['push_direct'].format(self.segments['this'])
            else:
                return self.codes['push_direct'].format(self.segments['that'])

    def handle_pop(self, cmd):
        res = ''
        if cmd.arg1 == 'temp':
            res = self.codes['pop_direct'].format(5 + int(cmd.arg2))
        elif cmd.arg1 == 'local' or cmd.arg1 == 'argument' or cmd.arg1 == 'this' or cmd.arg1 == 'that':
            res = self.codes['pop_seg'].format(cmd.arg2, self.segments[cmd.arg1])
        elif cmd.arg1 == 'static':
            res = self.codes['pop_direct'].format(self.file_name + '.' + cmd.arg2)
        elif cmd.arg1 == 'pointer':
            if cmd.arg2 == '0':
                res = self.codes['pop_direct'].format(self.segments['this'])
            else:
                res = self.codes['pop_direct'].format(self.segments['that'])
        return res

    def write_bootstrap(self, asm_file):
        code = '@256\nD=A\n@SP\nM=D\n'
        code += self.handle_call(Command(constants.C_CALL, 'Sys.init', 0))
        asm_file.write(code)
