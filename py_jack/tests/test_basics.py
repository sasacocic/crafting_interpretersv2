import py_jack.scanner as jack_scanner
import py_jack.parser as jack_parser
import sys


valid_programs = {
    "subroutineDec": """
    function void main() {
        var SquareGame game;
        let game = game;
        do game.run();
        do game.dispose();
        return;
    }
    """,
    "parameter_list3": """
        int myInt, char myChar, Square mySquare
    """,
}


"""
TODO: figure out how to unit test scanner and parser - I feel like if I can do that I can actually,
do that then I can bring the feedback loop down quite a bit and get a tighter loop and experiment
faster.
"""


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


def test_class_var_dec():
    """
    TODO: figure out how to test this better. This is a good isolated test case for this rule.
    just need to figure out how I can easily read in things to test this against
    """

    scanner = jack_scanner.Scanner(src="static boolean test;")
    scanner.scan()

    parser = jack_parser.Parser(tokens=scanner.tokens)

    n = parser.parse_class_var_dec()  # should not fail
    n.write_xml(file=sys.stdout, indent=0)


# TODO: was going to parse subRoutineDec, but that requires all statements, so going to do that first
def test_parameter_list():
    # int myInt, char myChar, "Square mySquare"
    parameter_list = valid_programs["parameter_list3"]

    scanner = jack_scanner.Scanner(src=parameter_list)
    scanner.scan()

    token_iter = iter(scanner.tokens)

    assert next(token_iter).lexeme == "int"
    assert next(token_iter).lexeme == "myInt"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "char"
    assert next(token_iter).lexeme == "myChar"
    assert next(token_iter).lexeme == ","
    assert next(token_iter).lexeme == "Square"
    assert next(token_iter).lexeme == "mySquare"
    assert next(token_iter, None) is None

    parser = jack_parser.Parser(tokens=scanner.tokens)
    result = parser.parse_parameter_list()

    def map_lexemes(pl):
        return (pl[0].lexeme, pl[1].lexeme)

    parameters = iter(result.parameters)

    assert map_lexemes(next(parameters)) == ("int", "myInt")
    assert map_lexemes(next(parameters)) == ("char", "myChar")
    assert map_lexemes(next(parameters)) == ("Square", "mySquare")


def test_simple_scan():
    scanner = jack_scanner.Scanner(src="char myChar, Square mySquare")
    scanner.scan()

    token_iter = iter(scanner.tokens)

    assert next(token_iter).lexeme == "char"


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

# def test_parse_string_expression():
#     # true, false, null, this - all keyword consts
#     scanner = jack_scanner.Scanner(src='"hello"')
#     scanner.scan()

#     token_iter = iter(scanner.tokens)
#     assert next(token_iter).lexeme == "hello"

#     parser = jack_parser.Parser(scanner.tokens)

#     r = parser.expression()

#     assert r.lexeme == "hello"
#     assert r.token_type == jack_scanner.TokenType.STRING_CONSTANT
