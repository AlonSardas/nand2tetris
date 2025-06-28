// RAM[SP] = RAM[{segment_pointer}]
@{segment_pointer}
A=M
D=M
@SP
A=M
M=D
// SP++
@SP
M=M+1
