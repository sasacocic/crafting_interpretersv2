
            @10
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
    
    @1
    D=M // holds address of RAM[segment]
    @0
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
                @top_value
                D=M
                @address
                A=M
                M=D
            
            @21
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @22
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
    
    @2
    D=M // holds address of RAM[segment]
    @2
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
                @top_value
                D=M
                @address
                A=M
                M=D
            
    @0
    M=M-1    
    
    @0
    A=M
    D=M
    @top_value
    M=D // top_value now contains top stack value
    
    @2
    D=M // holds address of RAM[segment]
    @1
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
                @top_value
                D=M
                @address
                A=M
                M=D
            
            @36
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
    
    @3
    D=M // holds address of RAM[segment]
    @6
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
                @top_value
                D=M
                @address
                A=M
                M=D
            
            @42
            D=A
            @0
            A=M
            M=D
            
    @0
    M=M+1
    
            @45
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
    
    @4
    D=M // holds address of RAM[segment]
    @5
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
                @top_value
                D=M
                @address
                A=M
                M=D
            
    @0
    M=M-1    
    
    @0
    A=M
    D=M
    @top_value
    M=D // top_value now contains top stack value
    
    @4
    D=M // holds address of RAM[segment]
    @2
    D=D+A
    @address
    M=D // @address should contain RAM[segment] + index
    
                @top_value
                D=M
                @address
                A=M
                M=D
            
            @510
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
    
            @5
            D=A
            @6
            D=D+A
            @address
            M=D
            @top_value
            D=M
            @address
            A=M
            M=D
            
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
    
    @4
    D=M // holds address of RAM[segment]
    @5
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
    
    @3
    D=M // holds address of RAM[segment]
    @6
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
    
    @3
    D=M // holds address of RAM[segment]
    @6
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
    
            @5
            D=A
            @6
            D=D+A
            A=D
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
    