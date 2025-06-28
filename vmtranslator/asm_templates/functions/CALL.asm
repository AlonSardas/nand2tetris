// push {return_label}
@{return_label}
D=A
@SP
A=M
M=D
@SP
M=M+1
// push LCL
@LCL
D=M
@SP
A=M
M=D
@SP
M=M+1
// push ARG
@ARG
D=M
@SP
A=M
M=D
@SP
M=M+1
// push THIS
@THIS
D=M
@SP
A=M
M=D
@SP
M=M+1
// push THAT
@THAT
D=M
@SP
A=M
M=D
@SP
MD=M+1
// LCL=SP
@LCL
M=D
// ARG=SP-5-n_args
@5
D=A
@{n_args}
D=D+A
@SP
D=M-D
@ARG
M=D
// LCL=SP
@SP
D=M
@LCL
M=D
// goto {func_name}
@{func_name}
0;JMP
({return_label})
