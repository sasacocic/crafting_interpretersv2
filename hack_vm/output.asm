
            @17
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @17
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
    
            @17
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @16
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
    
            @16
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @17
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
        @EQUAL3
        D;JEQ
        @0
        A=M
        M=0 // not equal return 0
        @END3
        0;JMP
        (EQUAL3)
            @0
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END3)
    
    @0
    M=M+1
    
            @892
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @891
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
        D=M-D // x > y -> (X ->D) (Y -> M) if x > 0 implies x > y if x < 0 implies y > x
        @LESS4
        D;JLT
        @0
        A=M
        M=0 // not equal return 0
        @END4
        0;JMP
        (LESS4)
            @0
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END4)
    
    @0
    M=M+1
    
            @891
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @892
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
        D=M-D // x > y -> (X ->D) (Y -> M) if x > 0 implies x > y if x < 0 implies y > x
        @LESS5
        D;JLT
        @0
        A=M
        M=0 // not equal return 0
        @END5
        0;JMP
        (LESS5)
            @0
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END5)
    
    @0
    M=M+1
    
            @891
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @891
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
        D=M-D // x > y -> (X ->D) (Y -> M) if x > 0 implies x > y if x < 0 implies y > x
        @LESS6
        D;JLT
        @0
        A=M
        M=0 // not equal return 0
        @END6
        0;JMP
        (LESS6)
            @0
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END6)
    
    @0
    M=M+1
    
            @32767
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @32766
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
        D=M-D // x > y -> (X ->D) (Y -> M) if x > 0 implies x > y if x < 0 implies y > x
        @GREATER7
        D;JGT
        @SP
        A=M
        M=0 // not equal return 0
        @END7
        0;JMP
        (GREATER7)
            @SP
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END7)
    
    @0
    M=M+1
    
            @32766
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @32767
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
        D=M-D // x > y -> (X ->D) (Y -> M) if x > 0 implies x > y if x < 0 implies y > x
        @GREATER8
        D;JGT
        @SP
        A=M
        M=0 // not equal return 0
        @END8
        0;JMP
        (GREATER8)
            @SP
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END8)
    
    @0
    M=M+1
    
            @32766
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @32766
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
        D=M-D // x > y -> (X ->D) (Y -> M) if x > 0 implies x > y if x < 0 implies y > x
        @GREATER9
        D;JGT
        @SP
        A=M
        M=0 // not equal return 0
        @END9
        0;JMP
        (GREATER9)
            @SP
            A=M
            M=-1 // equal return -1 as -1 = 111111111... in binary
        (END9)
    
    @0
    M=M+1
    
            @57
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @31
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @53
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
    
    @0
    M=M+1
    
            @112
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
        D=D-M // makes it 0
        D=D-M // makes it negative
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
        D=D&M
        @0
        A=M
        M=D
    
    @0
    M=M+1
    
            @82
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
        D=D|M
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
        D=!D
        @0
        A=M
        M=D
        
    @0
    M=M+1
    