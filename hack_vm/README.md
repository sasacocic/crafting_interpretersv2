# HACK VM

TODO: how does the hack vm work in general and what are it's components?



what is my understanding of how do function calls work?


- There are 3 commands 
    1. `call f k` - `k` determines the # of arguments a function takes - `function f n` - `n` determines the # of local variables
    2. `call f k` is awalys comes after `function f n` i.e. a `function` commands will never come before a `call` command
    3. `return` used to put the stack machine back into the state that is needed to continue processing instructions from the function that called this function i.e. put caller back into state it was in before it called callee 


# `call f k` is  called

_note: the below is pseudo code_

Before `call` is called k args are always pushed onto the stack.


the current stack frame must be saved - what does that mean?
    - basically all of the state for the current function must be saved so we can come back to it and continue executing from it once we complete processing our function.

saving the frame means

1. push return address onto stack i.e. @return-address
2. push LCL of calling function
3. push ARGS of calling function
4. push THIS of calling function
5. push THAT of calling function
6. ARGS = (SP - k - 5)
7. LCL = SP
8. goto f
9. (return-address) <- this is a label in hack assembly that is refered to in (1) - this 


# `function f n` is called

The function f commands starts where the previous `call f k` ended


it pushes `k` 0 values onto the stack to initialize the local variables

it should then be in a state to run all of its instructions



# return


how does return work - before it starts there will be a value on the top of the stack, and that is it's return value


1. Take the top stack value and place it in ARG[0]
2. restore the stack frame - i.e. set ARG, LCL, THIS, THAT pointers to the values you saved
3. clear the stack of the current function
4. Set the stack SP right after ARG[0] (this will be )
5. Jump to the return address within caller's code















