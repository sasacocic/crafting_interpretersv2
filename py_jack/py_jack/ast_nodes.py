from __future__ import annotations
import py_jack.scanner as scanner
import pathlib
import typing
import dataclasses
import contextlib


class XmlWriter(typing.Protocol):
    def write_xml(self, file: typing.IO, indent: int = 0): ...
    def write_token(self, token: scanner.Token, file: typing.IO, indent: int = 0):
        if token.token_type in scanner.token_variants["keywords"]:
            file.write(f"{' ' * indent}<keyword> {token.lexeme} </keyword>\n")
        elif token.token_type in scanner.token_variants["symbols"]:
            file.write(f"{' ' * indent}<symbol> {token.lexeme} </symbol>\n")
        elif token.token_type in [
            scanner.TokenType.INTEGER_CONSTANT,
            scanner.TokenType.STRING_CONSTANT,
        ]:
            tag = token.token_type.name.lower().split("_")
            new_tag = "".join([tag[0], tag[1][0].upper() + tag[1][1:]])
            file.write(f"{' ' * indent}<{new_tag}> {token.lexeme} </{new_tag}>\n")
        else:
            file.write(
                f"{' ' * indent}<{token.token_type.name.lower()}> {token.lexeme} </{token.token_type.name.lower()}>\n"
            )

    def write_string(
        self, surround: str, element: str, file: typing.IO, indent: int = 0
    ):
        file.write(f"{' ' * indent}<{surround}> {element} </{surround}>\n")

    @contextlib.contextmanager
    def write_node(self, file, indent: int):
        file.write(f"{' ' * indent}<{self.camel_case()}>\n")
        yield
        file.write(f"{' ' * indent}</{self.camel_case()}>\n")

    def camel_case(self):
        name = type(self).__name__
        return name[0].lower() + name[1:]


@dataclasses.dataclass
class ClassNode(XmlWriter):
    class_kw: scanner.Token
    class_name: scanner.Token
    left_squerly: scanner.Token
    right_squerly: scanner.Token
    class_var_dec: list[ClassVarDec] | None = None
    subroutine_dec: list[SubroutineDec] | None = None

    def __repr__(self):
        return f"{self.__class__.__name__}( class {self.class_name.lexeme} {{ }} len: {len(self.class_var_dec)})"

    # why pass a file? Why not return a string or write to stdout? Could also be useful.
    def write_xml(self, file_path: pathlib.Path, indent: int):
        mode = "w"
        # if file_path.exists():
        #     mode = "w"
        with file_path.open(mode) as xml_file:
            xml_file.write(f"<{self.class_kw.lexeme}>\n")
            indent += 1
            self.write_token(self.class_kw, xml_file, indent=indent)
            self.write_token(self.class_name, xml_file, indent=indent)
            self.write_string(
                "symbol", self.left_squerly.lexeme, xml_file, indent=indent
            )
            for class_var_dec in self.class_var_dec or []:
                class_var_dec.write_xml(xml_file, indent=indent)

            for subroutine_dec in self.subroutine_dec or []:
                subroutine_dec.write_xml(xml_file, indent=indent)
            self.write_string(
                "symbol", self.right_squerly.lexeme, xml_file, indent=indent
            )
            xml_file.write(f"</{self.class_kw.lexeme}>\n")


@dataclasses.dataclass
class ClassVarDec(XmlWriter):
    field_type: scanner.Token
    type_: scanner.Token
    var_name: scanner.Token
    semi_colon: scanner.Token
    var_names: list[tuple[scanner.Token, scanner.Token]] | None = None

    def write_xml(self, file: typing.IO, indent: int):
        # file.write(f"{' ' * indent}<classVarDec>\n")
        with self.write_node(file, indent=indent):
            indent += 2
            self.write_token(self.field_type, file, indent=indent)
            self.write_token(self.type_, file, indent=indent)
            self.write_token(self.var_name, file, indent=indent)

            for comma, var_name in self.var_names or []:
                self.write_token(var_name, file, indent=indent)
                self.write_token(comma, file, indent=indent)

            self.write_string(
                "symbol", self.semi_colon.lexeme, file=file, indent=indent
            )
        # file.write(f"{' ' * indent}</classVarDec>\n")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}( {self.field_type}  | {self.field_type} | {self.var_name}) "


@dataclasses.dataclass
class SubroutineDec(XmlWriter):
    subroutine_variant: scanner.Token
    return_type: scanner.Token
    name: scanner.Token
    left_paren: scanner.Token
    right_paren: scanner.Token
    subroutine_body: SubroutineBody
    parameter_list: ParameterList

    def write_xml(self, file: typing.IO, indent: int):
        with self.write_node(file, indent=indent):
            indent += 2
            self.write_token(self.subroutine_variant, file, indent)
            self.write_token(self.return_type, file, indent)
            self.write_token(self.name, file, indent)
            self.write_token(self.left_paren, file, indent)
            self.parameter_list.write_xml(file, indent)
            self.write_token(self.right_paren, file, indent)
            self.subroutine_body.write_xml(file, indent)
            # self.write_node(file, indent=indent, is_opening_tag=False)


@dataclasses.dataclass
class ParameterList(XmlWriter):
    _type: scanner.Token | None = None
    varname: scanner.Token | None = None
    parameters: list[tuple[scanner.Token, scanner.Token, scanner.Token]] = (
        dataclasses.field(default_factory=list)
    )

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent) as t:
            if self._type is None or self.varname is None:
                # self.write_node(file, indent, is_opening_tag=False)
                return
            indent += 2
            self.write_token(self._type, file, indent)
            self.write_token(self.varname, file, indent)
            for comma, next_type, next_varname in self.parameters:
                self.write_token(comma, file, indent)
                self.write_token(next_type, file, indent)
                self.write_token(next_varname, file, indent)
            # self.write_node(file, indent, is_opening_tag=False)


@dataclasses.dataclass
class VarDec(XmlWriter):
    var_kw: scanner.Token
    _type: scanner.Token
    var_name: scanner.Token
    var_names: list[tuple[scanner.Token, scanner.Token]]
    semi_colon: scanner.Token

    def write_xml(self, file: typing.IO, indent: int):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.var_kw, file, indent)
            self.write_token(self._type, file, indent)
            self.write_token(self.var_name, file, indent)
            for comma, var_name in self.var_names:
                self.write_token(comma, file, indent)
                self.write_token(var_name, file, indent)
            self.write_token(self.semi_colon, file, indent)


@dataclasses.dataclass
class SubroutineBody(XmlWriter):
    left_squerly: scanner.Token
    var_decs: list[VarDec]
    statements: list[Statement]
    right_squerly: scanner.Token

    def write_xml(self, file: typing.IO, indent: int):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.left_squerly, file, indent)
            for var_dec in self.var_decs:
                var_dec.write_xml(file, indent)
            for statement in self.statements:
                statement.write_xml(file, indent)
            self.write_token(self.right_squerly, file, indent)


@dataclasses.dataclass
class Expression(XmlWriter):
    term: Term
    op_terms: list[tuple[scanner.Token, Term]]

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.term.write_xml(file, indent)
            for op, term in self.op_terms:
                self.write_token(op, file, indent)
                term.write_xml(file, indent)


@dataclasses.dataclass
class Term(XmlWriter):
    # terms: scanner.Token | ArrayOperation | subroutineCall | '(' expression ')' | expressionList
    term: (
        scanner.Token
        | tuple[scanner.Token, Term]
        | tuple[scanner.Token, Expression, scanner.Token]
        | tuple[scanner.Token, scanner.Token, Expression, scanner.Token]
        | SubroutineCall
    )

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            # TODO: good place to do pattern matching on types / tuples ???
            indent += 2
            match self.term:
                case scanner.Token():
                    self.write_token(self.term, file, indent)
                case (token, term):
                    self.write_token(token, file, indent)
                    term.write_xml(file, indent)
                case (token, expression, token_end):
                    self.write_token(token, file, indent)
                    expression.write_xml(file, indent)
                    self.write_token(token_end, file, indent)
                case (token, token_two, expression, token_end):
                    self.write_token(token, file, indent)
                    self.write_token(token_two, file, indent)
                    expression.write_xml(file, indent)
                    self.write_token(token_end, file, indent)
                case SubroutineCall():
                    self.term.write_xml(file, indent)


@dataclasses.dataclass
class ExpressionList(XmlWriter):
    expression: Expression | None = None
    expression_list: list[tuple[scanner.Token, Expression]] | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            if self.expression:
                self.expression.write_xml(file, indent)
                if self.expression_list:
                    for comma, expr in self.expression_list:
                        self.write_token(comma, file, indent)
                        expr.write_xml(file, indent)


@dataclasses.dataclass
class SubroutineCall(XmlWriter):
    subroutine_name: scanner.Token
    left_paren: scanner.Token
    right_paren: scanner.Token
    dot: scanner.Token | None = None
    subroutine_source: scanner.Token | None = None
    expression_list: ExpressionList = dataclasses.field(
        default_factory=lambda: ExpressionList()
    )

    def write_xml(self, file: typing.IO, indent: int = 0):
        if self.subroutine_source:
            self.write_token(self.subroutine_source, file, indent)
            self.write_token(self.dot, file, indent)
        self.write_token(self.subroutine_name, file, indent)
        self.write_token(self.left_paren, file, indent)
        self.expression_list.write_xml(file, indent)
        self.write_token(self.right_paren, file, indent)


type StatementType = (
    LetStatement | IfStatement | WhileStatement | DoStatement | ReturnStatement
)


@dataclasses.dataclass
class Statements(XmlWriter):
    statement: StatementType

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.statement.write_xml(file, indent)


# This is a hack - everywhere in code I use the work "Statement", but when writing xml we want to see "Statements"
Statement = Statements


@dataclasses.dataclass
class ReturnStatement(XmlWriter):
    return_kw: scanner.Token
    semicolon: scanner.Token
    expression: Expression | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.return_kw, file, indent)
            if self.expression:
                self.expression.write_xml(file, indent)
            self.write_token(self.semicolon, file, indent)


@dataclasses.dataclass
class DoStatement(XmlWriter):
    do_kw: scanner.Token
    subroutine_call: SubroutineCall
    semicolon: scanner.Token

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.do_kw, file, indent)
            self.subroutine_call.write_xml(file, indent)
            self.write_token(self.semicolon, file, indent)


@dataclasses.dataclass
class LetStatement(XmlWriter):
    let_kw: scanner.Token
    var_name: scanner.Token
    equal: scanner.Token
    expression: Expression
    semi_colon: scanner.Token
    index_var: tuple[scanner.Token, Expression, scanner.Token] | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.let_kw, file, indent)
            self.write_token(self.var_name, file, indent)
            if self.index_var:
                left_square, expression, right_square = self.index_var
                self.write_token(left_square, file, indent)
                expression.write_xml(file, indent)
                self.write_token(right_square, file, indent)
            self.write_token(self.equal, file, indent)
            self.expression.write_xml(file, indent)
            self.write_token(self.semi_colon, file, indent)


@dataclasses.dataclass
class IfStatement(XmlWriter):
    if_kw: scanner.Token
    left_paren: scanner.Token
    expression: Expression
    right_paren: scanner.Token
    left_curly: scanner.Token
    right_curly: scanner.Token
    statements: list[Statement] | None = None
    optional_else: (
        tuple[scanner.Token, scanner.Token, list[Statement], scanner.Token] | None
    ) = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.if_kw, file, indent)
            self.write_token(self.left_paren, file, indent)
            self.expression.write_xml(file, indent)
            self.write_token(self.right_paren, file, indent)
            self.write_token(self.left_curly, file, indent)
            for statement in self.statements or []:
                statement.write_xml(file, indent)
            self.write_token(self.right_curly, file, indent)
            if self.optional_else:
                else_kw, left_curly, statements, right_curly = self.optional_else
            self.write_token(else_kw, file, indent)
            self.write_token(left_curly, file, indent)
            for statement in statements:
                statement.write_xml(file, indent)
            self.write_token(right_curly, file, indent)


@dataclasses.dataclass
class WhileStatement(XmlWriter):
    while_kw: scanner.Token
    left_paren: scanner.Token
    expression: Expression
    right_paren: scanner.Token
    left_curly: scanner.Token
    right_curly: scanner.Token
    statements: list[Statement] | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 1
            self.write_token(self.while_kw, file, indent)
            self.write_token(self.left_paren, file, indent)
            self.expression.write_xml(file, indent)
            self.write_token(self.right_paren, file, indent)
            self.write_token(self.left_curly, file, indent)
            for statement in self.statements or []:
                statement.write_xml(file, indent)
            self.write_token(self.right_curly, file, indent)
