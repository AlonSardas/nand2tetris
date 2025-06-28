// SP--
@SP
AM=M-1
// RAM[{segment_pointer}]=RAM[SP]
D=M
@{segment_pointer}
A=M
M=D
