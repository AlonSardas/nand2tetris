// addr = {segment_pointer} + {i}
@{i}
D=A
@{segment_pointer}
A=D+M
// RAM[SP] = RAM[addr]
D=M
@SP
A=M
M=D
// SP++
@SP
M=M+1
