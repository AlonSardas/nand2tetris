// R13=LCL
@LCL
D=M
@R13
M=D
// R14=return_address=RAM[LCL-5]
@5
A=D-A
D=M
@R14
M=D
// *ARG=pop=return_value
@SP
A=M-1
D=M
@ARG
A=M
M=D
// SP=ARG+1
D=A
@SP
M=D+1
// THAT=*(LCL-1)
@R13
AM=M-1
D=M
@THAT
M=D
// THIS=*(LCL-2)
@R13
AM=M-1
D=M
@THIS
M=D
// ARG=*(LCL-3)
@R13
AM=M-1
D=M
@ARG
M=D
// LCL=*(LCL-4)
@R13
AM=M-1
D=M
@LCL
M=D
// goto return_address
@R14
A=M
0;JMP
