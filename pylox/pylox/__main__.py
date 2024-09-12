from __future__ import annotations
import sys
import typing
from pathlib import Path
import pylox.tokens as tokens
import pylox.error_handling as errors
import enum
import pylox.lox_scanner as scan
import logging.config
import os
import pylox.Expr as Expr
import pylox.Stmnt as stmnt
import pylox.code_gen
import pylox.lox_parser as parser_mod
import click
import time


if typing.TYPE_CHECKING:
    from pathlib import Path


LOG_LEVEL: typing.Final[str | int] = os.environ.get("LOG_LEVEL") or logging.WARNING

logging.config.dictConfig({
    "version": 1,
    "formatters": {"default": {"format": "[%(levelname)s][%(funcName)s] %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "loggers": {
        "pylox.scanner": {"level": LOG_LEVEL},
        "pylox.lox_parser": {"level": LOG_LEVEL},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
})

LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)


class Environment:
    """
    Holds variable declarations
    """

    values: dict[str, object]
    enclosing: Environment | None

    def __init__(self, enclosing: Environment | None = None):
        self.enclosing = enclosing
        self.values = {}

    def define(self, name: str, value: object):
        LOGGER.debug(f"defined {name} = {value}")
        self.values[name] = value
        LOGGER.debug(f"env after assignment: {self.values}")

    def get_variable(self, name: tokens.Token):
        LOGGER.debug(f"attempting to read '{name.lexeme}' from env:")
        LOGGER.debug(f"env: {self.values}")

        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing is not None:
            return self.enclosing.get_variable(name)

        raise errors.LoxRuntimeError(name, msg=f"Undefined variable '{name.lexeme}'")

    def assign(self, name: tokens.Token, value: object):
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return

        raise errors.LoxRuntimeError(name, f"Undefined variable {name.lexeme}.")

    def get_at(self, distance: int, name: str):
        return self.ancestor(distance).values.get(name)

    def ancestor(self, distance: int):
        environment = self
        for _ in range(distance):
            environment = environment.enclosing

        return environment

    def assign_at(self, distance: int, name: tokens.Token, value: object):
        self.ancestor(distance).values[name.lexeme] = value


@typing.runtime_checkable
class LoxCallable(typing.Protocol):
    # I guess you have to take self?
    def call(
        self, interpreter: Interpreter, arguments: list[object]
    ) -> None | object: ...
    def arity(self) -> int: ...


class LoxFunction(LoxCallable):
    declaration: stmnt.Function
    closure: Environment | None

    def __init__(self, declaration: stmnt.Function, closure: Environment):
        self.declaration = declaration
        self.closure = closure

    def call(self, interpreter: Interpreter, arguments: list[object]) -> None | object:
        environment = Environment(self.closure)
        for ind in range(len(self.declaration.params)):
            environment.define(self.declaration.params[ind].lexeme, arguments[ind])

        try:
            interpreter.execute_block(self.declaration.body, environment)
        except errors.ReturnException as return_value:
            return return_value.value

    def arity(self) -> int:
        return len(self.declaration.params)

    def __repr__(self) -> str:
        return f"<fn {self.declaration.name.lexeme} >"


class FunctionType(enum.Enum):
    NONE = 1
    FUNCTION = 2


class Resolver(Expr.Visitor[None], stmnt.Visitor[None]):
    interpreter: Interpreter
    scopes: list[dict[str, bool]]
    current_function: FunctionType

    def __init__(self, interpreter: Interpreter):
        self.interpreter = interpreter
        self.scopes = []
        self.current_function = FunctionType.NONE

    def visit_ExpressionStmnt(self, stmnt: stmnt.Expression) -> None:
        self.resolve_expr(stmnt.expression)

    def visit_IfStmnt(self, stmnt: stmnt.If) -> None:
        self.resolve_expr(stmnt.condition)
        self.resolve_stmnt(stmnt.then_branch)
        if stmnt.else_branch is not None:
            self.resolve_stmnt(stmnt.else_branch)

    def visit_PrintStmnt(self, stmnt: stmnt.Print) -> None:
        self.resolve_expr(stmnt.expression)

    def visit_ReturnStmnt(self, stmnt: stmnt.Return) -> None:
        if self.current_function == FunctionType.NONE:
            errors.error_from_token(stmnt.keyword, "Can't return from top-level code.")

        if stmnt.value is not None:
            self.resolve_expr(stmnt.value)

    def visit_WhileStmnt(self, stmnt: stmnt.While) -> None:
        self.resolve_expr(stmnt.condition)
        self.resolve_stmnt(stmnt.body)

    def visit_BinaryExpr(self, expr: Expr.Binary) -> None:
        self.resolve_expr(expr.left)
        self.resolve_expr(expr.right)

    def visit_CallExpr(self, expr: Expr.Call) -> None:
        self.resolve_expr(expr.callee)

        for argument in expr.arguments:
            self.resolve_expr(argument)

    def visit_GroupingExpr(self, expr: Expr.Grouping) -> None:
        self.resolve_expr(expr.expression)

    def visit_LiteralExpr(self, expr: Expr.Literal) -> None:
        return None

    def visit_LogicalExpr(self, expr: Expr.Logical) -> None:
        self.resolve_expr(expr.left)
        self.resolve_expr(expr.right)

    def visit_UnaryExpr(self, expr: Expr.Unary) -> None:
        self.resolve_expr(expr.right)

    def visit_VariableExpr(self, expr: Expr.Variable) -> None:
        if not len(self.scopes) == 0 and self.scopes[-1].get(expr.name.lexeme) == False:
            errors.error_from_token(
                expr.name, "Can't read local variable in its own initializer."
            )

        self.resolve_local(expr, expr.name)

    def visit_FunctionStmnt(self, stmnt: stmnt.Function) -> None:
        self.declare(stmnt.name)
        self.define(stmnt.name)

        self.resolve_function(stmnt, FunctionType.FUNCTION)
        return None

    def resolve_function(self, function: stmnt.Function, function_type: FunctionType):
        enclosing_function = self.current_function
        self.current_function = function_type
        self.begin_scope()
        for param in function.params:
            self.declare(param)
            self.define(param)

        self.resolve(function.body)

        self.end_scope()
        self.current_function = enclosing_function

    def visit_AssignExpr(self, expr: Expr.Assign) -> None:
        self.resolve_expr(expr.value)
        self.resolve_local(expr, expr.name)

    def resolve_local(self, expr: Expr.Expr, name: tokens.Token):
        for i in range(len(self.scopes) - 1, -1, -1):
            if name.lexeme in self.scopes[i]:
                num_scopes = len(self.scopes)
                cur_scope = i
                num_scopes - 1 - cur_scope
                self.interpreter.resolve(expr, len(self.scopes) - 1 - i)
                return

    def declare(self, name: tokens.Token):
        if len(self.scopes) == 0:
            return

        scope = self.scopes[-1]
        if name.lexeme in scope:
            errors.error_from_token(
                name, "Already a variable with this name in this scope."
            )
        scope[name.lexeme] = False

    def define(self, name: tokens.Token):
        if len(self.scopes) == 0:
            return

        self.scopes[-1][name.lexeme] = True

    def visit_VarStmnt(self, stmnt: stmnt.Var) -> None:
        self.declare(stmnt.name)
        if stmnt.initializer is not None:
            self.resolve_expr(stmnt.initializer)

        self.define(stmnt.name)
        return None

    def visit_BlockStmnt(self, stmnt: stmnt.Block) -> None:
        self.begin_scope()
        self.resolve(stmnt.statements)
        self.end_scope()
        return None

    def resolve(self, statements: list[stmnt.Stmnt]):
        for statement in statements:
            self.resolve_stmnt(statement)

    def resolve_stmnt(self, statement: stmnt.Stmnt):
        statement.accept(self)

    def resolve_expr(self, expr: Expr.Expr):
        expr.accept(self)

    def begin_scope(self):
        self.scopes.append({})

    def end_scope(self):
        self.scopes.pop()


class Interpreter(Expr.Visitor[object], stmnt.Visitor[None]):
    lox_globals: Environment
    environment: Environment
    lox_locals: dict[Expr.Expr, int]

    def __init__(self):
        class Anon(LoxCallable):
            def arity(self):
                return 0

            def call(self, interpreter: Interpreter, arguments: list[object]):
                return float(time.time())

            def __repr__(self):
                return "<native fn>"

        self.lox_globals = Environment()
        self.environment = self.lox_globals
        self.lox_globals.define(
            "clock",
            Anon(),
        )
        self.lox_locals = {}

    # Statements

    def visit_ReturnStmnt(self, stmnt: stmnt.Return) -> None:
        value = None
        if stmnt.value is not None:
            value = self.evaluate(stmnt.value)

        raise errors.ReturnException(value)

    def visit_FunctionStmnt(self, stmnt: stmnt.Function) -> None:
        function = LoxFunction(stmnt, self.environment)
        self.environment.define(stmnt.name.lexeme, function)
        return None

    def visit_WhileStmnt(self, stmnt: stmnt.While) -> None:
        while self.is_truthy(self.evaluate(stmnt.condition)):
            self.execute(stmnt.body)

        return None

    def visit_BlockStmnt(self, stmnt: stmnt.Block) -> None:
        self.execute_block(stmnt.statements, Environment(self.environment))

    def execute_block(self, statements: list[stmnt.Stmnt], environment: Environment):
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def visit_VarStmnt(self, stmnt: stmnt.Var) -> None:
        value: object | None = None
        if stmnt.initializer != None:
            value = self.evaluate(stmnt.initializer)

        self.environment.define(stmnt.name.lexeme, value)

    def visit_ExpressionStmnt(self, stmnt: stmnt.Expression) -> None:
        self.evaluate(stmnt.expression)

    def visit_PrintStmnt(self, stmnt: stmnt.Print) -> None:
        value = self.evaluate(stmnt.expression)
        print(self.stringify(value))

    def visit_IfStmnt(self, stmnt: stmnt.If) -> None:
        if self.is_truthy(self.evaluate(stmnt.condition)):
            self.execute(stmnt.then_branch)
        elif stmnt.else_branch is not None:
            self.execute(stmnt.else_branch)
        return None

    # Expressions

    def visit_CallExpr(self, expr: Expr.Call) -> object:
        callee = self.evaluate(expr.callee)

        arguments = []
        for arg in expr.arguments:
            arguments.append(self.evaluate(arg))

        function = callee

        # TODO: I think this might break when running. Make sure it works.
        if not isinstance(function, LoxCallable):
            raise errors.LoxRuntimeError(
                expr.paren, "can only call functions and classes."
            )

        if len(arguments) != function.arity():
            raise errors.LoxRuntimeError(
                expr.paren,
                f"Expected {function.arity()} arguments but got {len(arguments)}.",
            )

        return function.call(self, arguments)

    def visit_LogicalExpr(self, expr: Expr.Logical) -> object:
        left = self.evaluate(expr.left)

        if expr.operator.token_type == tokens.TokenType.OR:
            if self.is_truthy(expr.left):
                return left
        else:
            if not self.is_truthy(expr.left):
                return left

        return self.evaluate(expr.right)

    def visit_VariableExpr(self, expr: Expr.Variable) -> object:
        # old implementation
        # return self.environment.get_variable(expr.name)
        return self.lookup_variable(expr.name, expr)

    def lookup_variable(self, name: tokens.Token, expr: Expr.Expr):
        distance = self.lox_locals.get(expr, None)
        if distance is not None:
            return self.environment.get_at(distance, name.lexeme)
        else:
            return self.lox_globals.get_variable(name)

    def visit_AssignExpr(self, expr: Expr.Assign) -> object:
        value = self.evaluate(expr.value)
        distance = self.lox_locals.get(expr, None)
        if distance is not None:
            self.environment.assign_at(distance, expr.name, value)
        else:
            self.lox_globals.assign(expr.name, value)
        return value

    def visit_LiteralExpr(self, expr: Expr.Literal) -> object:
        LOGGER.info(f"Interpreting literal: {expr}")
        return expr.value

    def visit_GroupingExpr(self, expr: Expr.Grouping) -> object:
        return self.evaluate(expr.expression)

    def visit_UnaryExpr(self, expr: Expr.Unary) -> object:
        right = self.evaluate(expr.right)

        match expr.operator.token_type:
            case scan.TokenType.MINUS:
                self.check_number_operand(expr.operator, right)
                return -float(right)
            case scan.TokenType.BANG:
                return self.is_truthy(right)
            case _:
                return None  # unreachable?

    def visit_BinaryExpr(self, expr: Expr.Binary) -> object:
        LOGGER.info("evaluating BinaryExpression")
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        match expr.operator.token_type:
            case scan.TokenType.MINUS:
                self.check_number_operands(expr.operator, left, right)
                return float(left) - float(right)
            case scan.TokenType.SLASH:
                self.check_number_operands(expr.operator, left, right)
                return float(left) / float(right)
            case scan.TokenType.STAR:
                self.check_number_operands(expr.operator, left, right)
                return float(left) * float(right)
            case scan.TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return float(left) + float(right)
                if isinstance(left, str) and isinstance(right, str):
                    return (
                        str(left) + str(right)
                    )  # I don't need to technically do this they are already the correct type\
                raise errors.LoxRuntimeError(
                    expr.operator, "Operatnds must be two numbers or two strings"
                )
            case scan.TokenType.GREATER:
                self.check_number_operands(expr.operator, left, right)
                return float(left) > float(right)
            case scan.TokenType.GREATER_EQUAL:
                self.check_number_operands(expr.operator, left, right)
                return float(left) >= float(right)
            case scan.TokenType.LESS:
                self.check_number_operands(expr.operator, left, right)
                return float(left) < float(right)
            case scan.TokenType.LESS_EQUAL:
                self.check_number_operands(expr.operator, left, right)
                return float(left) <= float(right)
            case scan.TokenType.BANG_EQUAL:
                return not self.is_equal(left, right)
            case scan.TokenType.EQUAL_EQUAL:
                return self.is_equal(left, right)
            case _:
                return None  # should never happen

    def execute(self, statement: stmnt.Stmnt):
        """
        Executes an Stmnt for side effects
        """
        statement.accept(self)

    def evaluate(self, expr: Expr.Expr):
        """
        Evaluates an Expr and returns it's value
        """
        return expr.accept(self)

    def is_truthy(self, obj: object):
        if obj == None:
            return False
        if isinstance(obj, bool):
            return bool(obj)
        return True

    def is_equal(a: object, b: object) -> bool:
        if a == None and b == None:
            return True
        if a == None:
            return False

        return a == b

    def stringify(self, obj: object):
        if obj == None:
            return "nil"

        if isinstance(obj, float):
            text = str(obj)

            if text.endswith(".0"):
                text = int(float(text))
            return text

        return str(obj)

    def check_number_operand(self, operator: scan.Token, operand: object):
        if isinstance(operand, float):
            return
        raise errors.LoxRuntimeError(operator, "Operand must be a number.")

    def check_number_operands(self, operator: scan.Token, left: object, right: object):
        if isinstance(left, float) and isinstance(right, float):
            return

        raise errors.LoxRuntimeError(operator, "Operands must be numbers.")

    def interpret(self, statements: list[stmnt.Stmnt]) -> None:
        try:
            for statement in statements:
                self.execute(statement)
        except errors.LoxRuntimeError as e:
            errors.runtime_error(e)
            print("this is an error. I need to fix this message")

    def resolve(self, expr: Expr.Expr, depth: int):
        self.lox_locals[expr] = depth


class AstPrinter(Expr.Visitor[str]):
    def to_string(self, expr: Expr.Expr):
        return expr.accept(self)

    def parenthesize(self, name: str, *exprs: Expr.Expr):
        builder = [f"({name}"]

        for expr in exprs:
            builder.append(" ")
            # TODO: look into this type error
            builder.append(expr.accept(self))

        builder.append(")")

        return "".join(builder)

    def visit_BinaryExpr(self, expr: Expr.Binary):
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_GroupingExpr(self, expr: Expr.Grouping):
        return self.parenthesize("group", expr.expression)

    def visit_LiteralExpr(self, expr: Expr.Literal):
        if not expr.value:
            return "nil"

        return str(expr.value)

    def visit_UnaryExpr(self, expr: Expr.Unary):
        return self.parenthesize(expr.operator.lexeme, expr.right)

    def printer(self, expr: Expr.Expr):
        return expr.accept(self)


def run_prompt():
    # read evaluate print loop
    print("lox repl started! ")
    while True:
        sys.stdout.write("> ")
        sys.stdout.flush()
        line = sys.stdin.readline()
        if any((exit_word == line for exit_word in ["exit\n", "stop\n", "exit()\n"])):
            break
        result = run(line)
        print(">> ", result)
        errors.had_error = False


def run(lox_program: str) -> str | None:
    LOGGER.debug("running program: %s", lox_program)
    scanner = scan.Scanner(lox_program)
    tokens = scanner.scan_tokens()

    LOGGER.debug("begin parsing")
    parser = parser_mod.Parser(tokens)
    statements = parser.parse()

    if errors.had_error or statements is None:
        return "there was some error"

    interp = Interpreter()
    resolver = Resolver(interp)
    resolver.resolve(statements)

    if errors.had_error:
        return

    interp.interpret(statements)
    return ""


def test_ast_printer():
    # test the printer works as expected
    expression = Expr.Binary(
        Expr.Unary(
            scan.Token(scan.TokenType.MINUS, "-", None, 1),
            Expr.Literal("123"),
        ),
        scan.Token(scan.TokenType.STAR, "*", None, 1),
        Expr.Grouping(Expr.Literal("45.67")),
    )
    print(AstPrinter().printer(expression))


@click.group()
def lox():
    pass


@click.command()
def repl():
    run_prompt()


@click.command()
@click.argument("lox_file")
def scanner(lox_file_path: str):
    lox_file = Path(lox_file_path)
    if not lox_file.exists():
        raise ValueError("file doesn't exist - this is the wrong error")
    run_file(lox_file)


@click.command()
def code_gen():
    LOGGER.debug("code_gen")
    pylox.code_gen.generate_ast()


@click.command()
def parser():
    LOGGER.debug("parser")


@click.command()
@click.argument("lox_file")
def run_file(lox_file):
    src_file = Path(lox_file)
    if not src_file.exists():
        raise FileNotFoundError(f"{lox_file} - does not exist")

    run(src_file.read_text())


lox.add_command(scanner)
lox.add_command(parser)
lox.add_command(code_gen)
lox.add_command(repl)
lox.add_command(run_file)


if __name__ == "__main__":
    lox()
