
    (SimpleFunction.test)
        @2
        D=A
        @count
        M=D
        
    @LOOP1
    0;JMP

    
    (LOOP1)
        @count
        D=M
        @STOP1
        D;JEQ
        // code I want to run in my loop
        @SP
        A=M
        M=0    
        
        @count
        D=M
        D=D-1
        M=D
        
    @0
    M=M+1
    
        @LOOP1
        0;JMP
          
    (STOP1)
        @LOOPCOMPLETE1
        0;JMP
    
    (LOOPCOMPLETE1)
    
            @99
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
    @1
    D=M // holds address of RAM[segment]
    @0
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
        @address
        A=M
        D=M // holds the value of segment[index]
        @selected_segment_value
        M=D
        
            @selected_segment_value
            D=M
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
    @1
    D=M // holds address of RAM[segment]
    @1
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
        @address
        A=M
        D=M // holds the value of segment[index]
        @selected_segment_value
        M=D
        
            @selected_segment_value
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
    
    @2
    D=M // holds address of RAM[segment]
    @0
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
        @address
        A=M
        D=M // holds the value of segment[index]
        @selected_segment_value
        M=D
        
            @selected_segment_value
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
    
    @2
    D=M // holds address of RAM[segment]
    @1
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
        @address
        A=M
        D=M // holds the value of segment[index]
        @selected_segment_value
        M=D
        
            @selected_segment_value
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
    
    