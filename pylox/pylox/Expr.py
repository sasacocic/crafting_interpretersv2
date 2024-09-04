from __future__ import annotations
from pylox.tokens import Token
import typing


class Expr(typing.Protocol):
    def accept[T](self, visitor: Visitor[T]) -> T: ...


class Visitor[T]:
    def visit_AssignExpr(self, expr: Assign) -> T: ...

    def visit_BinaryExpr(self, expr: Binary) -> T: ...

    def visit_GroupingExpr(self, expr: Grouping) -> T: ...

    def visit_LiteralExpr(self, expr: Literal) -> T: ...

    def visit_UnaryExpr(self, expr: Unary) -> T: ...

    def visit_VariableExpr(self, expr: Variable) -> T: ...


class Assign(Expr):
    def __init__(self, name: Token, value: Expr):
        self.name = name
        self.value = value

    def accept[T](self, visitor: Visitor[T]):
        return visitor.visit_AssignExpr(self)


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

    def accept[T](self, visitor: Visitor[T]):
        return visitor.visit_BinaryExpr(self)


class Grouping(Expr):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept[T](self, visitor: Visitor[T]):
        return visitor.visit_GroupingExpr(self)


class Literal(Expr):
    def __init__(self, value: object):
        self.value = value

    def accept[T](self, visitor: Visitor[T]):
        return visitor.visit_LiteralExpr(self)


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr):
        self.operator = operator
        self.right = right

    def accept[T](self, visitor: Visitor[T]):
        return visitor.visit_UnaryExpr(self)


class Variable(Expr):
    def __init__(self, name: Token):
        self.name = name

    def accept[T](self, visitor: Visitor[T]):
        return visitor.visit_VariableExpr(self)
