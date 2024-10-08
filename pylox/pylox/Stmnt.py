from __future__ import annotations
from pylox.Expr import Expr, Variable
from pylox.tokens import Token
import typing
class Stmnt(typing.Protocol):
   def accept[T](self, visitor: Visitor[T]) -> T:...

class Visitor[T]:
   def visit_BlockStmnt(self, stmnt:Block) -> T:...

   def visit_ClassStmnt(self, stmnt:Class) -> T:...

   def visit_ExpressionStmnt(self, stmnt:Expression) -> T:...

   def visit_FunctionStmnt(self, stmnt:Function) -> T:...

   def visit_IfStmnt(self, stmnt:If) -> T:...

   def visit_PrintStmnt(self, stmnt:Print) -> T:...

   def visit_ReturnStmnt(self, stmnt:Return) -> T:...

   def visit_VarStmnt(self, stmnt:Var) -> T:...

   def visit_WhileStmnt(self, stmnt:While) -> T:...

class Block(Stmnt):
   def __init__(self, statements: list[Stmnt]):
      self.statements = statements
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_BlockStmnt(self)
class Class(Stmnt):
   def __init__(self, name: Token, methods: list[Function], superclass: Variable | None):
      self.name = name
      self.methods = methods
      self.superclass = superclass
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_ClassStmnt(self)
class Expression(Stmnt):
   def __init__(self, expression: Expr):
      self.expression = expression
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_ExpressionStmnt(self)
class Function(Stmnt):
   def __init__(self, name: Token, params: list[Token], body: list[Stmnt]):
      self.name = name
      self.params = params
      self.body = body
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_FunctionStmnt(self)
class If(Stmnt):
   def __init__(self, condition: Expr, then_branch: Stmnt, else_branch: Stmnt | None):
      self.condition = condition
      self.then_branch = then_branch
      self.else_branch = else_branch
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_IfStmnt(self)
class Print(Stmnt):
   def __init__(self, expression: Expr):
      self.expression = expression
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_PrintStmnt(self)
class Return(Stmnt):
   def __init__(self, keyword: Token, value: Expr | None):
      self.keyword = keyword
      self.value = value
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_ReturnStmnt(self)
class Var(Stmnt):
   def __init__(self, name: Token, initializer: Expr):
      self.name = name
      self.initializer = initializer
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_VarStmnt(self)
class While(Stmnt):
   def __init__(self, condition: Expr, body: Stmnt):
      self.condition = condition
      self.body = body
   def accept[T](self, visitor: Visitor[T]):
      return visitor.visit_WhileStmnt(self)
