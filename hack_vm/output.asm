
            @1
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @1
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
    @0
    M=M-1    
    
    @0
    A=M
    D=M
    @top_value
    M=D // top_value now contains top stack value
    
        @top_value
        D=M
        @before_top_value
        M=D
        
    @0
    M=M-1    
    
    @0
    A=M
    D=M
    @top_value
    M=D // top_value now contains top stack value
    
        @before_top_value
        D=M
        @top_value
        D=D-M
        @EQUAL1
        D;JEQ
        @0
        A=M
        M=0 // not equal return 0
        @END1
        0;JMP
        (EQUAL1)
            @0
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END1)
    
    @0
    M=M+1
    
            @9
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @8
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
    @0
    M=M-1    
    
    @0
    A=M
    D=M
    @top_value
    M=D // top_value now contains top stack value
    
        @top_value
        D=M
        @before_top_value
        M=D
        
    @0
    M=M-1    
    
    @0
    A=M
    D=M
    @top_value
    M=D // top_value now contains top stack value
    
        @before_top_value
        D=M
        @top_value
        D=D-M
        @EQUAL2
        D;JEQ
        @0
        A=M
        M=0 // not equal return 0
        @END2
        0;JMP
        (EQUAL2)
            @0
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END2)
    
    @0
    M=M+1
    
            @333
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    