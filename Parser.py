import constants

class Parser:
    def __init__(self, in_filepath):
        self.filepath = in_filepath
        self.commands = []


    def parse(self):
        with open(self.filepath, 'r') as vm_file:
            line = vm_file.readline()
            while line:
                line = (line.split('/', 1)[0]).strip()
                if line and line[0] != '/':
                    command_lex = line.split()
                    cmd_len = len(command_lex)
                    if cmd_len == 1 and command_lex[0] != constants.C_RETURN:
                        self.commands.append(Command(constants.C_ARITHMETIC, command_lex[0], None))
                    elif cmd_len == 1:
                        self.commands.append(Command(command_lex[0], None, None))
                    elif cmd_len == 3:
                        self.commands.append(Command(command_lex[0], command_lex[1], command_lex[2]))
                    elif cmd_len == 2:
                        self.commands.append(Command(command_lex[0], command_lex[1], None))
                line = vm_file.readline()
        return self.commands


class Command:
    def __init__(self, in_command_type, in_arg1, in_arg2):
        self.command_type = in_command_type
        self.arg1 = in_arg1
        self.arg2 = in_arg2