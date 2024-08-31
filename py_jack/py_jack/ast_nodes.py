from __future__ import annotations
import py_jack.jack_scanner as jack_scanner
import pathlib
import typing
import dataclasses
import contextlib


class XmlWriter(typing.Protocol):
    def write_xml(self, file: typing.IO, indent: int = 0): ...
    def write_token(self, token: jack_scanner.Token, file: typing.IO, indent: int = 0):
        if token.token_type in jack_scanner.token_variants["keywords"]:
            file.write(f"{' ' * indent}<keyword> {token.lexeme} </keyword>\n")
        elif token.token_type in jack_scanner.token_variants["symbols"]:
            match token.token_type:
                case jack_scanner.TokenType.AMPERSAND:
                    file.write(f"{' ' * indent}<symbol> {'&amp;'} </symbol>\n")
                case jack_scanner.TokenType.GREATER_THAN:
                    file.write(f"{' ' * indent}<symbol> {'&gt;'} </symbol>\n")
                case jack_scanner.TokenType.LESS_THAN:
                    file.write(f"{' ' * indent}<symbol> {'&lt;'} </symbol>\n")
                case jack_scanner.TokenType() if token.lexeme == '"':
                    file.write(f"{' ' * indent}<symbol> {'&quot;'} </symbol>\n")
                case _:
                    file.write(f"{' ' * indent}<symbol> {token.lexeme} </symbol>\n")
        elif token.token_type in [
            jack_scanner.TokenType.INTEGER_CONSTANT,
            jack_scanner.TokenType.STRING_CONSTANT,
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
    class_kw: jack_scanner.Token
    class_name: jack_scanner.Token
    left_squerly: jack_scanner.Token
    right_squerly: jack_scanner.Token
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
    field_type: jack_scanner.Token
    type_: jack_scanner.Token
    var_name: jack_scanner.Token
    semi_colon: jack_scanner.Token
    var_names: list[tuple[jack_scanner.Token, jack_scanner.Token]] | None = None

    def write_xml(self, file: typing.IO, indent: int):
        # file.write(f"{' ' * indent}<classVarDec>\n")
        with self.write_node(file, indent=indent):
            indent += 2
            self.write_token(self.field_type, file, indent=indent)
            self.write_token(self.type_, file, indent=indent)
            self.write_token(self.var_name, file, indent=indent)

            for comma, var_name in self.var_names or []:
                self.write_token(comma, file, indent=indent)
                self.write_token(var_name, file, indent=indent)

            self.write_string(
                "symbol", self.semi_colon.lexeme, file=file, indent=indent
            )
        # file.write(f"{' ' * indent}</classVarDec>\n")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}( {self.field_type}  | {self.field_type} | {self.var_name}) "


@dataclasses.dataclass
class SubroutineDec(XmlWriter):
    subroutine_variant: jack_scanner.Token
    return_type: jack_scanner.Token
    name: jack_scanner.Token
    left_paren: jack_scanner.Token
    right_paren: jack_scanner.Token
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
    _type: jack_scanner.Token | None = None
    varname: jack_scanner.Token | None = None
    parameters: list[
        tuple[jack_scanner.Token, jack_scanner.Token, jack_scanner.Token]
    ] = dataclasses.field(default_factory=list)

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
    var_kw: jack_scanner.Token
    _type: jack_scanner.Token
    var_name: jack_scanner.Token
    var_names: list[tuple[jack_scanner.Token, jack_scanner.Token]]
    semi_colon: jack_scanner.Token

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
    left_squerly: jack_scanner.Token
    var_decs: list[VarDec]
    statements: Statements
    right_squerly: jack_scanner.Token

    def write_xml(self, file: typing.IO, indent: int):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.left_squerly, file, indent)
            for var_dec in self.var_decs:
                var_dec.write_xml(file, indent)
            self.statements.write_xml(file, indent)
            self.write_token(self.right_squerly, file, indent)


@dataclasses.dataclass
class Expression(XmlWriter):
    term: Term
    op_terms: list[tuple[jack_scanner.Token, Term]]

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.term.write_xml(file, indent)
            for op, term in self.op_terms:
                self.write_token(op, file, indent)
                term.write_xml(file, indent)


@dataclasses.dataclass
class Term(XmlWriter):
    term: (
        jack_scanner.Token
        | tuple[jack_scanner.Token, Term]
        | tuple[jack_scanner.Token, Expression, jack_scanner.Token]
        | tuple[jack_scanner.Token, jack_scanner.Token, Expression, jack_scanner.Token]
        | SubroutineCall
    )

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            match self.term:
                case jack_scanner.Token():
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
    expression_list: list[tuple[jack_scanner.Token, Expression]] | None = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            if self.expression:
                self.expression.write_xml(file, indent)
                if self.expression_list:
                    for comma, expr in self.expression_list:
                        self.write_token(comma, file, indent)
                        expr.write_xml(file, indent)


@dataclasses.dataclass
class SubroutineCall(XmlWriter):
    subroutine_name: jack_scanner.Token
    left_paren: jack_scanner.Token
    right_paren: jack_scanner.Token
    dot: jack_scanner.Token | None = None
    subroutine_source: jack_scanner.Token | None = None
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
    statements: list[StatementType]

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            for statement in self.statements:
                statement.write_xml(file, indent)


@dataclasses.dataclass
class ReturnStatement(XmlWriter):
    return_kw: jack_scanner.Token
    semicolon: jack_scanner.Token
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
    do_kw: jack_scanner.Token
    subroutine_call: SubroutineCall
    semicolon: jack_scanner.Token

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.do_kw, file, indent)
            self.subroutine_call.write_xml(file, indent)
            self.write_token(self.semicolon, file, indent)


@dataclasses.dataclass
class LetStatement(XmlWriter):
    let_kw: jack_scanner.Token
    var_name: jack_scanner.Token
    equal: jack_scanner.Token
    expression: Expression
    semi_colon: jack_scanner.Token
    index_var: tuple[jack_scanner.Token, Expression, jack_scanner.Token] | None = None

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
    if_kw: jack_scanner.Token
    left_paren: jack_scanner.Token
    expression: Expression
    right_paren: jack_scanner.Token
    left_curly: jack_scanner.Token
    right_curly: jack_scanner.Token
    statements: Statements
    optional_else: (
        tuple[jack_scanner.Token, jack_scanner.Token, Statements, jack_scanner.Token]
        | None
    ) = None

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.if_kw, file, indent)
            self.write_token(self.left_paren, file, indent)
            self.expression.write_xml(file, indent)
            self.write_token(self.right_paren, file, indent)
            self.write_token(self.left_curly, file, indent)
            self.statements.write_xml(file, indent)
            self.write_token(self.right_curly, file, indent)
            if self.optional_else:
                else_kw, left_curly, statements, right_curly = self.optional_else
                self.write_token(else_kw, file, indent)
                self.write_token(left_curly, file, indent)
                statements.write_xml(file, indent)
                self.write_token(right_curly, file, indent)


@dataclasses.dataclass
class WhileStatement(XmlWriter):
    while_kw: jack_scanner.Token
    left_paren: jack_scanner.Token
    expression: Expression
    right_paren: jack_scanner.Token
    left_curly: jack_scanner.Token
    right_curly: jack_scanner.Token
    statements: Statements

    def write_xml(self, file: typing.IO, indent: int = 0):
        with self.write_node(file, indent):
            indent += 2
            self.write_token(self.while_kw, file, indent)
            self.write_token(self.left_paren, file, indent)
            self.expression.write_xml(file, indent)
            self.write_token(self.right_paren, file, indent)
            self.write_token(self.left_curly, file, indent)
            self.statements.write_xml(file, indent)
            self.write_token(self.right_curly, file, indent)
