import enum


"""
implements vm commands

push segment i
pop segment i

TODO:
    - call f n
    - function f n 
    - return
"""


class Segments(enum.Enum):
    CONSTANT = 0
    LOCAL = 1
    ARGUMENT = 2
    THIS = 3
    THAT = 4
    TEMP = 5
    POINTER = 6
    STATIC = 7


def increment_segment(segment: int):
    return f"""
    @{segment}
    M=M+1
    """


def decrement_segment(segment: int):
    return f"""
    @{segment}
    M=M-1    
    """


def value_at_segment_index(segment: int, val: int):
    return (
        set_address(segment, val)
        + """
        @address
        A=M
        D=M // holds the value of segment[index]
        @selected_segment_value
        M=D
        """
    )


def set_address(segment: int, index: int):
    """
    @address becomes RAM[segment] + index
    """

    return f"""
    @{segment}
    D=M // holds address of RAM[segment]
    @{index}
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    """


def top_stack_value():
    """
    puts the value of *RAM[0] in @top_value
    """
    return """
    @0
    A=M
    D=M
    @top_value
    M=D // top_value now contains top stack value
    """


def push_val(segment: int, val: int, file_name: str):
    """
    push segment i - push the value at segment[i] onto the stack
    """

    match segment:
        case 7:  # static - note: static not really mapped to 7
            ident = f"{file_name}.{val}"
            return f"""
            @{ident}
            D=M
            @0
            A=M
            M=D
            """ + increment_segment(0)
        case 0:  # constant
            return f"""
            @{val}
            D=A
            @0
            A=M
            M=D
            """ + increment_segment(0)
        case 5:  # temp
            return f"""
            @5
            D=A
            @{val}
            D=D+A
            A=D
            D=M
            @0
            A=M
            M=D
            """ + increment_segment(0)
        case 1 | 2 | 3 | 4:  # constant, local, argument, this, that
            return (
                value_at_segment_index(segment, val)
                + """
            @selected_segment_value
            D=M
            @0
            A=M
            M=D
            """
            ) + increment_segment(0)  # move the stack pointer up after a push onto it
        case 6:  # pointer segment
            # THIS -> RAM[3]
            # THAT -> RAM[4]
            # pointer 0 access THIS / pointer 1 access THAT
            return f"""
            @{3 if val == 0 else 4}
            D=M // base address of THIS
            @0
            A=M
            M=D
            """ + increment_segment(0)
        case _:  # static segment
            pass
            raise Exception("this should never happen")


def pop_val(segment: int, index: int, file_name: str):
    """
    pop segment i - pops the top element off of the stack and pushes it onto the segment
    """
    match segment:
        case 7:  # static - note: static isn't really 7
            ident = f"{file_name}.{index}"
            return (
                decrement_segment(0)
                + top_stack_value()
                + f"""
            @top_value
            D=M
            @{ident}
            M=D
            """
            )
        case 5:
            return (
                decrement_segment(0)
                + top_stack_value()
                + f"""
            @5
            D=A
            @{index}
            D=D+A
            @address
            M=D
            @top_value
            D=M
            @address
            A=M
            M=D
            """
            )

        case 1 | 2 | 3 | 4:
            return (
                decrement_segment(0)  # is this a problem to do first? I don't think so
                + top_stack_value()
                + set_address(segment, index)
                + """
                @top_value
                D=M
                @address
                A=M
                M=D
            """
            )
        case 6:
            #
            return (
                decrement_segment(0)
                + top_stack_value()
                + f"""
            @top_value
            D=M            
            @{3 if index == 0 else 4}
            M=D
            """
            )
        case 0:
            raise Exception("can't pop from constant segment")
        case _:
            raise Exception(f"not a valid segment: {segment}")


def add():
    return (
        decrement_segment(0)
        + """
    @0
    A=M
    D=M
    @x_temp
    M=D
    @0
    M=M-1
    @0
    A=M
    D=M
    @y_temp
    M=D
    @result
    M=D
    @x_temp
    D=M
    @result
    M=D+M // have to do D+M - M+D is invalid
    D=M
    @0
    A=M
    M=D
    """
        + increment_segment(0)
    )


def sub():
    """
    this is add but one line changed
    """
    return (
        decrement_segment(0)
        + """
    @0
    A=M
    D=M
    @x_temp
    M=D
    @0
    M=M-1
    @0
    A=M
    D=M
    @y_temp
    M=D
    @result
    M=D
    @x_temp
    D=M
    @result
    M=M-D // have to do D-M - M-D is invalid - also is this going to do subtraction in the way I think?
    D=M
    @0
    A=M
    M=D
    """
        + increment_segment(0)
    )


i = 0


def eq() -> str:
    global i
    i += 1
    return (
        decrement_segment(0)
        + top_stack_value()
        + """
        @top_value
        D=M
        @before_top_value
        M=D
        """
        + decrement_segment(0)
        + top_stack_value()
        + f"""
        @before_top_value
        D=M
        @top_value
        D=D-M
        @EQUAL{i}
        D;JEQ
        @0
        A=M
        M=0 // not equal return 0
        @END{i}
        0;JMP
        (EQUAL{i})
            @0
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END{i})
    """
        + increment_segment(0)
    )


"""
implements vm commands

push segment i
pop segment i

TODO:
    - neg ✅
    - gt - done
    - lt - done
    - and - done
    - or - done
    - not
"""


def neg() -> str:
    global i
    i += 1
    return (
        decrement_segment(0)
        + top_stack_value()
        + """
        @top_value
        D=M
        D=D-M // makes it 0
        D=D-M // makes it negative
        @0
        A=M
        M=D
    """
        + increment_segment(0)
    )


def gt() -> str:
    global i
    i += 1
    return (
        decrement_segment(0)
        + top_stack_value()
        + """
        @top_value
        D=M
        @before_top_value
        M=D
        """
        + decrement_segment(0)
        + top_stack_value()
        + f"""
        @before_top_value
        D=M
        @top_value
        D=M-D // x > y -> (X ->D) (Y -> M) if x > 0 implies x > y if x < 0 implies y > x
        @GREATER{i}
        D;JGT
        @SP
        A=M
        M=0 // not equal return 0
        @END{i}
        0;JMP
        (GREATER{i})
            @SP
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END{i})
    """
        + increment_segment(0)
    )


def lt() -> str:
    global i
    i += 1
    return (
        decrement_segment(0)
        + top_stack_value()
        + """
        @top_value
        D=M
        @before_top_value
        M=D
        """
        + decrement_segment(0)
        + top_stack_value()
        + f"""
        @before_top_value
        D=M
        @top_value
        D=M-D // x > y -> (X ->D) (Y -> M) if x > 0 implies x > y if x < 0 implies y > x
        @LESS{i}
        D;JLT
        @0
        A=M
        M=0 // not equal return 0
        @END{i}
        0;JMP
        (LESS{i})
            @0
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END{i})
    """
        + increment_segment(0)
    )


def and_() -> str:
    return (
        decrement_segment(0)
        + top_stack_value()
        + """
        @top_value
        D=M
        @before_top_value
        M=D
        """
        + decrement_segment(0)
        + top_stack_value()
        + """
        @before_top_value
        D=M
        @top_value
        D=D&M
        @0
        A=M
        M=D
    """
        + increment_segment(0)
    )


def or_() -> str:
    return (
        decrement_segment(0)
        + top_stack_value()
        + """
        @top_value
        D=M
        @before_top_value
        M=D
        """
        + decrement_segment(0)
        + top_stack_value()
        + """
        @before_top_value
        D=M
        @top_value
        D=D|M
        @0
        A=M
        M=D
    """
        + increment_segment(0)
    )


def not_() -> str:
    return (
        decrement_segment(0)
        + top_stack_value()
        + """
        @top_value
        D=M
        D=!D
        @0
        A=M
        M=D
        """
        + increment_segment(0)
    )


"""
function and branching commands
"""


def call(function_name: str, n_args: int) -> str:
    """
    function_name: name of function to call
    n_args: number of arguments the function takes



    pesudo code implementation:
        push returnAddress
        push LCL
        push ARG
        push THIS
        push THAT
        ARG = SP - 5 - n_args
        LCL = SP
        goto function_name
    """

    def push_segment(segment: str):
        """
        segments: one of LCL, ARG, THIS, THAT
        """
        return f"""
        @{segment}
        D=M
        @SP
        A=M
        M=D
        """ + increment_segment(0)

    return (
        f"""
    @{function_name}
    D=A
    @SP
    A=M
    M=D
    """
        + increment_segment(0)
        + push_segment("LCL")
        + push_segment("ARG")
        + push_segment("THIS")
        + push_segment("THAT")
        + f"""

    @SP
    D=M
    @5
    D=D-A
    @{n_args}
    D=D-A
    @ARG
    M=D // ARG = SP - 5 - n_args


    @SP
    D=M
    @LCL
    M=D // LCL = SP
    @{function_name}
    0;JMP
    """
    )

    # I couldn't use push value for the above code
    # push_val(
    #     Segments.CONSTANT,
    # )


def function(function_name: str, n_args: int) -> str:
    """
    n_args: number size of LCL segment
    name: function name


    effective to this pseudo code
    (functionName)
        repeat nVars times:
            push 0
    """

    global i
    i += 1

    def set_variable(var_name: str, number: int):
        return f"""
        @{number}
        D=A
        @{var_name}
        M=D
        """

    def dec_variable(var_name: str):
        return f"""
        @{var_name}
        D=M
        D=D-1
        M=D
        """

    return (
        f"""
    ({function_name})"""
        + set_variable("count", n_args)
        + f"""
    @LOOP{i}
    0;JMP

    """
        + f"""
    (LOOP{i})
        @count
        D=M
        @STOP{i}
        D;JEQ
        // code I want to run in my loop
        @SP
        A=M
        M=0    
        """
        + dec_variable("count")
        + increment_segment(0)
        + f"""
        @LOOP{i}
        0;JMP
         """
        + f""" 
    (STOP{i})
        @LOOPCOMPLETE{i}
        0;JMP
    """
        + f"""
    (LOOPCOMPLETE{i})
    """
    )


def return_():
    """
    endFrame = LCL
    retAddress = *(endFrame - 5)
    *ARG = pop()
    SP = ARG + 1
    THAT = *(endFrame - 1)
    THIS = *(endFrame - 2)
    ARG = *(endFrame - 3)
    LCL = *(endFrame - 4)
    goto retAddr
    """

    def set_segment(segment: str, minus_endframe: int):
        return f"""
        @endFrame
        D=M
        @{minus_endframe}
        D=D-A
        @R13
        M=D
        @R13
        A=M
        D=M
        @{segment}
        M=D
        // segment: THIS, THAT, LCL, ARG = *(endFrame - minus_endframe)
    """

    return (
        """
    @639 // debugging
    @LCL
    D=M
    @endFrame
    M=D
    // endFrame = LCL

    @endFrame
    D=M
    @5
    D=D-A
    @R13
    M=D
    @R13
    A=M
    D=M
    @retAddress
    M=D
    // retAddress = *(endFrame - 5) - not totally sure about this need to review
    """
        + decrement_segment(0)
        + top_stack_value()
        + """
    @top_value
    D=M
    @ARG
    A=M
    M=D
    // *ARG = POP()


    @ARG
    D=M
    D=D+1
    @SP
    M=D
    // SP = ARG + 1"""
        + set_segment("THAT", minus_endframe=1)
        + set_segment("THIS", minus_endframe=2)
        + set_segment("ARG", minus_endframe=3)
        + set_segment("LCL", minus_endframe=4)
        + """
    @retAddress
    0;JMP
    // goto retAddress

    """
    )
