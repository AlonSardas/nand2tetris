// R13 = {segment_pointer} + {i}
@{i}
D=A
@{segment_pointer}
D=D+M
@R13
M=D
// SP--
@SP
AM=M-1
// D = RAM[SP]
D=M
// RAM[R13]=RAM[SP]
@R13
A=M
M=D
