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


def test_if_statement():
    simple_prog = """
class Main {
    function void main() {
        var int i;
        let i = 0;
        if (i < 10) {
            do Output.printInt(i);
            let i = i + 1;
        } else {
            do Output.printInt(99);
        }
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


def test_while_statement():
    simple_prog = """
class Main {
    function void main() {
        var int i;
        let i = 1;
        while (i < 10){
            if (i < 10) {
                do Output.printInt(i);
            } else {
                do Output.printInt(99);
            }
            let i = i + 1;
        }
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


def test_unaryops():
    simple_prog = """
class Main {
    function void main() {
            do Main.convert(999);           // performs the conversion
    }


    function void convert(int value) {
    	var int mask, position;
    	var boolean loop;
    	
    	let loop = true;
        let position = position + 1;
        let mask = Main.nextMask(mask);
        if (~(position > 16)) {
    
            if (~((value & mask) = 0)) {
                do Memory.poke(8000 + position, 1);
            }
            else {
                do Memory.poke(8000 + position, 0);
            }    
        }
        else {
            let loop = false;
        }
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
