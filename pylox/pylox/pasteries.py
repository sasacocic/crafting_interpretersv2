from __future__ import annotations

import typing as t


class Pastery(t.Protocol):
    def accept(self, visitor: PastryVisitor): ...


class Beignet(Pastery):
    def accept(self, visitor: PastryVisitor):
        return visitor.visit_beignet(self)


class Cruller(Pastery):
    def accept(self, visitor: PastryVisitor):
        return visitor.visit_cruller(self)


# why do I get no warning that Pastery isn't implemented?
# I guess it will be a runtime issue but I should check this
class Teter(Pastery):
    pass


class PastryVisitor(t.Protocol):
    def visit_beignet(self, beignet: Beignet):
        print("visited beignet!!!")

    def visit_cruller(self, cruller: Cruller):
        print("visited cruller!!!")


class ConcretePastryVisitor(PastryVisitor):
    pass


if __name__ == "__main__":
    ben = Beignet()
    p_visitor = ConcretePastryVisitor()
    ben.accept(p_visitor)
