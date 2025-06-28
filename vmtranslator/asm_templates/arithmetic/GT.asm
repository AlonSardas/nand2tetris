// SP--
@SP
AM=M-1
D=M
// D-RAM[SP-1]
A=A-1
// D==0 if eq, else D!=0
D=M-D
@IF_GT_{line_number}
D;JGT
D=0
@STORE_RESULT_{line_number}
0;JMP
(IF_GT_{line_number})
D=-1
(STORE_RESULT_{line_number})
@SP
A=M-1
M=D
