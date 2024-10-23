import py_jack.jack_scanner as jack_scanner
import py_jack.jack_parser as jack_parser
import pathlib
import typing
import os
import logging.config

# had to paste this in here, because the logging setup for tests is different than for __main__ - need to see if I can't do this for every single test
# in my pytest suite
LOG_LEVEL: typing.Final[str | None] = os.environ.get("LOG_LEVEL")

logging.config.dictConfig({
    "version": 1,
    "formatters": {
        "default": {"format": "[%(levelname)s][%(funcName)s:%(lineno)d] %(message)s"}
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    # TODO: notes py_jack.scanner and py_jack.parser do not exist I changed the names
    "loggers": {
        "py_jack.jack_scanner": {"level": logging.ERROR},
        "py_jack.jack_parser": {"level": logging.ERROR},
        "py_jack.ast_nodes": {"level": LOG_LEVEL or logging.INFO},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL or logging.INFO},
})

test_file = (
    "testing_output.vm"  # I could also just mock this so it doesn't get used right
)


def test_expression_code_gen():
    simple_prog = """
class Main {
    function void main() {
        var int some;
        let some = 1+1;
        return;
   }
}
    """
    scanner = jack_scanner.Scanner(src=simple_prog)
    scanner.scan()

    parser = jack_parser.Parser(tokens=scanner.tokens)

    class_node = parser.parse()

    global test_file
    test_file = pathlib.Path(test_file)

    class_node.compile(test_file)


def test_expression_multiplication():
    simple_prog = """
    class Main {
        function void main() {
            do Output.printInt(1 + (2 * 3));
            return;
        }
    }
    """
    scanner = jack_scanner.Scanner(src=simple_prog)
    scanner.scan()

    parser = jack_parser.Parser(tokens=scanner.tokens)

    class_node = parser.parse()

    global test_file
    test_file = pathlib.Path(test_file)

    class_node.compile(test_file)
