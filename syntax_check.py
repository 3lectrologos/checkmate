import ast


class NoImportsAllowedError(Exception):
    def __init__(self, lineno, msg):
        super().__init__(msg)
        self.lineno = lineno


class FunctionDefNotFoundError(Exception):
    def __init__(self, lineno, msg):
        super().__init__(msg)
        self.lineno = lineno


class WrongNumberOfArgumentsError(Exception):
    def __init__(self, lineno, msg):
        super().__init__(msg)
        self.lineno = lineno


class SpecificationCheckVisitor(ast.NodeVisitor):
    def __init__(self, input_args, function_name=None, is_level5=False):
        self.input_args = input_args
        self.function_name = function_name
        if is_level5:
            self.function_name = 'when_run'
        self.arg_names = None
        self.is_level_5 = is_level5
        self.function_def_found = False
        super().__init__()

    def visit_Import(self, node):
        if self.is_level_5:
            raise NoImportsAllowedError(node.lineno, '\'import\' statement not allowed')

    def visit_FunctionDef(self, node):
        if self.function_name is None:
            self.function_name = node.name
        if node.name != self.function_name:
            return
        self.function_def_found = True
        self.arg_names = [arg.arg for arg in node.args.args]
        num_args = len(node.args.args)
        expected_num_args = len(self.input_args)
        if num_args != expected_num_args:
            arg_str = 'argument' if expected_num_args == 1 else 'arguments'
            raise WrongNumberOfArgumentsError(
                node.lineno,
                f'Function \'{self.function_name}\' must accept {expected_num_args} {arg_str}, but accepts {num_args}'
            )


def check_specification(source, input_args, function_name=None, is_level5=False):
    tree = ast.parse(source)
    visitor = SpecificationCheckVisitor(input_args, function_name, is_level5)
    visitor.visit(tree)
    if not visitor.function_def_found:
        if function_name is None:
            raise FunctionDefNotFoundError(0, 'No function found in source')
        else:
            raise FunctionDefNotFoundError(0, f'Function \'{function_name}\' not found')
    return visitor.function_name, visitor.arg_names
