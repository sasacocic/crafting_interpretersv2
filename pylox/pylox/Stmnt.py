from __future__ import annotations
from pylox.Expr import Expr
from pylox.tokens import Token
import typing
class Stmnt(typing.Protocol):
   def accept[T](self, visitor: Visitor[T]) -> T:...

class Visitor[T]:
   def visit_ExpressionStmnt(self, stmnt:Expression) -> T:...

   def visit_PrintStmnt(self, stmnt:Print) -> T:...

   def visit_VarStmnt(self, stmnt:Var) -> T:...

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
class Var(Stmnt):
   def __init__(self, name: Token, initializer: Expr):
      self.name = name
      self.initializer = initializer
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_VarStmnt(self)
