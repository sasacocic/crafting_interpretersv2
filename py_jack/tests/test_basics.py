import py_jack.scanner as jack_scanner
import py_jack.parser as jack_parser
import py_jack.ast_nodes as jack_ast

"""
TODO: figure out how to unit test scanner and parser - I feel like if I can do that I can actually,
do that then I can bring the feedback loop down quite a bit and get a tighter loop and experiment
faster.
"""

token_types = jack_scanner.TokenType


def test_scanner():
    scanner = jack_scanner.Scanner(src="class Main { static boolean test; }")
    scanner.scan()

    assert len(scanner.tokens) > 3
    token_iter = iter(scanner.tokens)
    token = next(token_iter)
    assert token.lexeme == "class"
    token = next(token_iter)
    assert token.lexeme == "Main"
    token = next(token_iter)
    assert token.lexeme == "{"
    token = next(token_iter)
    assert token.lexeme == "static"

    token = next(token_iter)
    assert token.lexeme == "boolean"

    token = next(token_iter)
    assert token.lexeme == "test"
    token = next(token_iter)
    assert token.lexeme == ";"
    token = next(token_iter)
    assert token.lexeme == "}"
    token = next(token_iter, None)
    assert token is None

    """
    IDC about this too much. It serves as a decent example though.
    """
    # parser = jack_parser.Parser(tokens=scanner.tokens)
    # class_node = parser.parse_class() # parse_class is the top most "statement"
    # xml_file = p.Path("test-out.xml")
    # class_node.write_xml()


def test_parse_let_statement():
    scanner = jack_scanner.Scanner(src="let thing = 1;")
    scanner.scan()


def test_parse_keyword_consts():
    # true, false, null, this - all keyword consts
    scanner = jack_scanner.Scanner(src="true")
    scanner.scan()


def test_parse_integer_constants():
    # true, false, null, this - all keyword consts
    scanner = jack_scanner.Scanner(src="true")
    scanner.scan()


def test_parse_string_consts():
    # true, false, null, this - all keyword consts
    scanner = jack_scanner.Scanner(src='"hello"')
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "hello"

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.parse_constant()

    assert r.lexeme == "hello"
    assert r.token_type == jack_scanner.TokenType.STRING_CONSTANT


"""
stopped - basically was doing tests for expressions starting off with string literals
"""


def test_parse_string_expression():
    scanner = jack_scanner.Scanner(src='"hello"')
    scanner.scan()
    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "hello"

    parser = jack_parser.Parser(scanner.tokens)
    r = parser.string_constant()
    assert r.token_type == token_types.STRING_CONSTANT

    parser = jack_parser.Parser(scanner.tokens)
    r = parser.term()
    assert r.term.token_type == token_types.STRING_CONSTANT


def test_parse_keyword_expression():
    # true, false, null, this - all keyword consts
    scanner = jack_scanner.Scanner(src="null")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "null"

    parser = jack_parser.Parser(scanner.tokens)
    r = parser.keyword_constant()
    assert r.lexeme == "null"
    assert r.token_type == jack_scanner.TokenType.NULL

    parser = jack_parser.Parser(scanner.tokens)
    r = parser.term()
    assert r.term.token_type == token_types.NULL


def test_simple_integer_expression():
    scanner = jack_scanner.Scanner(src="1")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "1"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.expression()
    assert r.term.term.token_type == token_types.INTEGER_CONSTANT
    assert len(r.op_terms) == 0


def test_expression_integer_expressions():
    scanner = jack_scanner.Scanner(src="1 + 1")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "1"
    assert next(token_iter).lexeme == "+"
    assert next(token_iter).lexeme == "1"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.expression()
    assert r.term.term.token_type == token_types.INTEGER_CONSTANT
    assert len(r.op_terms) == 1
    assert r.op_terms[0][0].token_type == token_types.PLUS
    assert r.op_terms[0][1].term.token_type == token_types.INTEGER_CONSTANT


def test_expression_integer_expressions_more():
    scanner = jack_scanner.Scanner(src='"hello" + 1 + true')
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "hello"
    assert next(token_iter).lexeme == "+"
    assert next(token_iter).lexeme == "1"
    assert next(token_iter).lexeme == "+"
    assert next(token_iter).lexeme == "true"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.expression()
    assert r.term.term.token_type == token_types.STRING_CONSTANT
    assert len(r.op_terms) == 2
    assert r.op_terms[0][0].token_type == token_types.PLUS
    assert r.op_terms[0][1].term.token_type == token_types.INTEGER_CONSTANT
    assert r.op_terms[1][0].token_type == token_types.PLUS
    assert r.op_terms[1][1].term.token_type == token_types.TRUE


def test_identifier_expression():
    scanner = jack_scanner.Scanner(src="some_var")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "some_var"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.expression()
    assert r.term.term.token_type == token_types.IDENTIFIER
    assert len(r.op_terms) == 0


def test_array_index_expression():
    scanner = jack_scanner.Scanner(src="somevar[another_var]")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "somevar"
    assert next(token_iter).lexeme == "["
    assert next(token_iter).lexeme == "another_var"
    assert next(token_iter).lexeme == "]"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.expression()

    assert isinstance(r.term.term, tuple)
    assert len(r.term.term) == 4

    assert r.term.term[0].token_type == token_types.IDENTIFIER
    assert r.term.term[1].token_type == token_types.LEFT_SQUARE_BRACKET
    expression = r.term.term[2]
    assert isinstance(expression, jack_ast.Expression)
    assert expression.term.term.token_type == token_types.IDENTIFIER
    assert len(expression.op_terms) == 0
    assert r.term.term[3].token_type == token_types.RIGHT_SQUARE_BRACKET

    assert len(r.op_terms) == 0


def test_unary_expression():
    scanner = jack_scanner.Scanner(src="-1")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "-"
    assert next(token_iter).lexeme == "1"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.expression()

    assert r.term.term[0].token_type == token_types.MINUS
    assert r.term.term[1].term.token_type == token_types.INTEGER_CONSTANT


def test_term_expression():
    scanner = jack_scanner.Scanner(src="(some_var + 1)")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "("
    assert next(token_iter).lexeme == "some_var"
    assert next(token_iter).lexeme == "+"
    assert next(token_iter).lexeme == "1"
    assert next(token_iter).lexeme == ")"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.expression()
    assert isinstance(r.term.term, tuple)
    assert len(r.term.term) == 3
    left_paren, expr, right_paren = r.term.term
    assert left_paren.token_type == token_types.LEFT_PAREN
    assert isinstance(expr, jack_ast.Expression)
    term, [[op, terms], *remaining] = expr.term, expr.op_terms
    assert term.term.token_type == token_types.IDENTIFIER
    assert op.token_type == token_types.PLUS
    assert terms.term.token_type == token_types.INTEGER_CONSTANT
    assert right_paren.token_type == token_types.RIGHT_PAREN


def test_empty_expression_list():
    scanner = jack_scanner.Scanner(src="()")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "("
    assert next(token_iter).lexeme == ")"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.expression_list()
    assert r == jack_ast.ExpressionList()


def test_expression_list():
    scanner = jack_scanner.Scanner(src='(some_var, 1, 9, "hello")')
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "("
    assert next(token_iter).lexeme == "some_var"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "1"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "9"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "hello"
    assert next(token_iter).lexeme == ")"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    r = parser.expression_list()
    assert r.expression.term.term.lexeme == "some_var"


def test_subroutine_call():
    scanner = jack_scanner.Scanner(src='mything(some_var, 1, 9, "hello")')
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "mything"
    assert next(token_iter).lexeme == "("
    assert next(token_iter).lexeme == "some_var"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "1"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "9"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "hello"
    assert next(token_iter).lexeme == ")"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    sub_call = parser.term()
    assert isinstance(sub_call.term, jack_ast.SubroutineCall)
    assert (
        sub_call.term.subroutine_name.lexeme,
        sub_call.term.subroutine_name.token_type,
    ) == ("mything", token_types.IDENTIFIER)


def test_empty_subroutine_call():
    scanner = jack_scanner.Scanner(src="mything()")
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "mything"
    assert next(token_iter).lexeme == "("
    assert next(token_iter).lexeme == ")"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    sub_call = parser.term()
    assert isinstance(sub_call.term, jack_ast.SubroutineCall)
    assert (
        sub_call.term.subroutine_name.lexeme,
        sub_call.term.subroutine_name.token_type,
    ) == ("mything", token_types.IDENTIFIER)


def test_subroutine_method_call():
    scanner = jack_scanner.Scanner(src='myclass.myMethod(some_var, 1, 9, "hello")')
    scanner.scan()

    parser = jack_parser.Parser(scanner.tokens)

    sub_call = parser.term()

    assert isinstance(sub_call.term, jack_ast.SubroutineCall)
    subroutine_call = sub_call.term
    assert subroutine_call.subroutine_source.lexeme == "myclass"
    assert subroutine_call.subroutine_name.lexeme == "myMethod"


def test_general_expression():
    scanner = jack_scanner.Scanner(src='myclass.myMethod(some_var, 1, 9, "hello") + 99')
    scanner.scan()

    token_iter = iter(scanner.tokens)
    assert next(token_iter).lexeme == "myclass"
    assert next(token_iter).lexeme == "."
    assert next(token_iter).lexeme == "myMethod"
    assert next(token_iter).lexeme == "("
    assert next(token_iter).lexeme == "some_var"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "1"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "9"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "hello"
    assert next(token_iter).lexeme == ")"
    assert next(token_iter).lexeme == "+"
    assert next(token_iter).lexeme == "99"
    assert next(token_iter, None) == None

    parser = jack_parser.Parser(scanner.tokens)

    expression = parser.expression()

    assert isinstance(expression.term.term, jack_ast.SubroutineCall)
    subroutine_call = expression.term.term
    assert subroutine_call.subroutine_source.lexeme == "myclass"
    assert subroutine_call.subroutine_name.lexeme == "myMethod"
    assert len(expression.op_terms) == 1
    # [[op, term], *_unused] = expression.op_terms
    # assert op.token_type == token_types.PLUS
    # assert term.term.token_type == token_types.INTEGER_CONSTANT
