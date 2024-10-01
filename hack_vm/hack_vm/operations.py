"""
implements vm commands

push segment i
pop segment i

todo: learn this, that, pointer, temp
do: sub

"""


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


def push_val(segment: int, val: int):
    """
    push segment i - push the value at segment[i] onto the stack
    """

    match segment:
        case 0:  # constant
            return f"""
            @{val}
            D=A
            @0
            A=M
            M=D
            """ + increment_segment(0)
        case 5:
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
        case _:  # static segment
            pass
            raise Exception("this should never happen")


def pop_val(segment: int, index: int):
    """
    pop segment i - pops the top element off of the stack and pushes it onto the segment
    """
    match segment:
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
