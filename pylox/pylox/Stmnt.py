from __future__ import annotations
from pylox.Expr import Expr
import typing


class Stmnt(typing.Protocol):
    def accept[T](self, visitor: Visitor[T]) -> T: ...


class Visitor[T]:
    def visit_ExpressionStmnt(self, stmnt: Expression) -> T: ...

    def visit_PrintStmnt(self, stmnt: Print) -> T: ...


class Expression(Stmnt):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept[T](self, visitor: Visitor[T]):
        return visitor.visit_ExpressionStmnt(self)


class Print(Stmnt):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept[T](self, visitor: Visitor[T]):
        return visitor.visit_PrintStmnt(self)
