// RAM[SP] = RAM[{memory}]
@{memory}
D=M
@SP
A=M
M=D
// SP++
@SP
M=M+1
