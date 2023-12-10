import ast


class SpecificationError(Exception):
    def __init__(self, lineno, msg):
        super().__init__(msg)
        self.lineno = lineno


class NoImportsAllowedError(SpecificationError):
    pass


class FunctionDefNotFoundError(SpecificationError):
    pass


class WrongNumberOfArgumentsError(SpecificationError):
    pass


class SpecificationCheckVisitor(ast.NodeVisitor):
    def __init__(self, input_args, function_name=None, is_level5=False):
        self.input_args = input_args
        self.function_name = function_name
        self.arg_names = None
        self.is_level_5 = is_level5
        self.function_def_found = False
        self.parents = []
        super().__init__()

    def generic_visit(self, node):
        self.parents.append(node)
        super().generic_visit(node)
        self.parents.pop()

    def is_top_level(self):
        return isinstance(self.parents[-1], ast.Module)

    def visit_Import(self, node):
        if self.is_level_5:
            raise NoImportsAllowedError(node.lineno, "'import' statement not allowed")

    def visit_FunctionDef(self, node):
        if not self.is_top_level():
            self.generic_visit(node)
            return
        if self.function_name is None:
            self.function_name = node.name
        if node.name != self.function_name:
            return
        self.function_def_found = True
        self.arg_names = [arg.arg for arg in node.args.args]
        num_args = len(node.args.args)
        expected_num_args = len(self.input_args)
        if num_args != expected_num_args:
            arg_str = "argument" if expected_num_args == 1 else "arguments"
            raise WrongNumberOfArgumentsError(
                node.lineno,
                f"Function '{self.function_name}' accepts {expected_num_args} {arg_str}, but was given {num_args}",
            )
        self.generic_visit(node)


def check_specification(source, input_args, function_name=None, is_level5=False):
    if is_level5:
        function_name = "when_run"
    tree = ast.parse(source)
    visitor = SpecificationCheckVisitor(input_args, function_name, is_level5)
    visitor.visit(tree)
    if not visitor.function_def_found:
        if function_name is None:
            raise FunctionDefNotFoundError(0, "No function found in source")
        else:
            raise FunctionDefNotFoundError(0, f"Function '{function_name}' not found")
    return visitor.function_name, visitor.arg_names
