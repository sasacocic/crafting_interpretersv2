import py_jack.scanner as jack_scanner
import py_jack.parser as jack_parser
import sys


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
