
	.globl	program_main
	.align	8
program_main: 
	sd	ra,-8(sp)
	sd	fp,-16(sp)
	sd	s1,-24(sp)
	sd	zero,-32(sp)
	addi	fp,sp,0
	addi	sp,sp,-32
	j	program_main_start
program_main_start: 
	add	a0,zero,a0
	call	input_int64
	li	t0,2
	mul	a0,a0,t0
	add	s1,zero,a0
	call	input_int64
	li	t0,2
	mul	a0,a0,t0
	add	a1,zero,a0
	li	t0,0
	li	t1,0
	bne	t0,t1,body_0
	j	orelse_1
body_0: 
	li	a0,2
	j	cont_2
orelse_1: 
	sub	a0,s1,a1
	sltu	a0,zero,a0
	slli	a0,a0,1
	add	a0,zero,a0
	j	cont_2
cont_2: 
	li	t1,0
	bne	a0,t1,body_3
	j	orelse_4
body_3: 
	beq	s1,a1,body_6
	j	orelse_7
orelse_4: 
	li	a0,0
	j	cont_5
body_6: 
	li	a0,2
	j	cont_8
orelse_7: 
	li	a0,2
	j	cont_8
cont_8: 
	add	a0,zero,a0
	j	cont_5
cont_5: 
	li	t1,0
	bne	a0,t1,body_9
	j	orelse_10
body_9: 
	slt	a0,s1,a1
	slli	a0,a0,1
	slt	a4,a1,s1
	xori	a4,a4,1
	slli	a4,a4,1
	slt	a2,a1,s1
	slli	a2,a2,1
	slt	a3,s1,a1
	xori	a3,a3,1
	slli	a3,a3,1
	j	cont_11
orelse_10: 
	li	a0,2
	li	a4,2
	li	a2,2
	li	a3,2
	j	cont_11
cont_11: 
	li	t1,0
	bne	a0,t1,body_12
	j	orelse_13
body_12: 
	add	a0,zero,a4
	j	cont_14
orelse_13: 
	li	a0,0
	j	cont_14
cont_14: 
	li	t1,0
	bne	a0,t1,body_15
	j	orelse_16
body_15: 
	li	t1,0
	bne	a2,t1,body_18
	j	orelse_19
orelse_16: 
	li	a0,0
	j	cont_17
body_18: 
	add	a0,zero,a3
	j	cont_20
orelse_19: 
	li	a0,0
	j	cont_20
cont_20: 
	add	a0,zero,a0
	j	cont_17
cont_17: 
	li	t1,0
	beq	a0,t1,body_21
	j	orelse_22
body_21: 
	sub	a0,s1,a1
	add	a0,zero,a0
	li	t0,2
	div	a0,a0,t0
	call	print_int64
	j	cont_23
orelse_22: 
	li	a0,0
	li	t0,2
	div	a0,a0,t0
	call	print_int64
	j	cont_23
cont_23: 
	j	program_main_conclusion
program_main_conclusion: 
	addi	sp,sp,32
	ld	ra,-8(sp)
	ld	fp,-16(sp)
	ld	s1,-24(sp)
	ret

	.globl	main
	.align	8
main: 
	sd	ra,-8(sp)
	sd	fp,-16(sp)
	sd	s3,-24(sp)
	sd	s2,-32(sp)
	sd	s6,-40(sp)
	sd	s11,-48(sp)
	sd	s1,-56(sp)
	sd	s4,-64(sp)
	sd	s9,-72(sp)
	sd	s8,-80(sp)
	sd	s5,-88(sp)
	sd	s10,-96(sp)
	sd	s7,-104(sp)
	sd	zero,-112(sp)
	sd	zero,-120(sp)
	sd	zero,-128(sp)
	sd	zero,-136(sp)
	sd	zero,-144(sp)
	addi	fp,sp,0
	addi	sp,sp,-144
	add	s3,zero,zero
	add	s2,zero,zero
	add	s6,zero,zero
	add	s11,zero,zero
	add	s1,zero,zero
	add	s4,zero,zero
	add	s9,zero,zero
	add	s8,zero,zero
	add	s5,zero,zero
	add	s10,zero,zero
	add	s7,zero,zero
	addi	a0,fp,-104
	li	a1,8
	call	gc_init
	j	main_start
main_start: 
	add	a0,zero,a0
	la	t0,exc_sp
	ld	t0,0(t0)
	sd	t0,-136(fp)
	la	t0,exc_fp
	ld	t0,0(t0)
	sd	t0,-120(fp)
	la	t0,exc_handler
	ld	t0,0(t0)
	sd	t0,-112(fp)
	add	t0,zero,sp
	la	t1,exc_sp
	sd	t0,0(t1)
	add	t0,zero,fp
	la	t1,exc_fp
	sd	t0,0(t1)
	la	t0,exc_handler_24
	la	t1,exc_handler
	sd	t0,0(t1)
	la	t0,program_main
	sd	t0,-128(fp)
	la	a0,gc_free_ptr
	ld	a0,0(a0)
	addi	a1,a0,16
	la	a0,gc_fromspace_end
	ld	a0,0(a0)
	blt	a1,a0,body_25
	j	orelse_26
body_25: 
	j	cont_27
orelse_26: 
	add	a0,zero,sp
	li	a1,2
	call	gc_collect
	j	cont_27
cont_27: 
	la	t0,gc_free_ptr
	ld	t0,0(t0)
	addi	a0,t0,1
	la	t0,gc_free_ptr
	ld	t0,0(t0)
	addi	t0,t0,16
	la	t1,gc_free_ptr
	sd	t0,0(t1)
	li	t0,2
	sd	t0,-1(a0)
	add	a0,zero,a0
	ld	t0,-128(fp)
	sd	t0,7(a0)
	add	a0,zero,a0
	ld	a1,7(a0)
	add	a0,zero,a0
	jalr	a1
	add	a0,zero,a0
	li	t0,0
	li	t1,0
	bne	t0,t1,exc_handler_24
	j	try_cont_28
try_cont_28: 
	ld	t0,-136(fp)
	la	t1,exc_sp
	sd	t0,0(t1)
	ld	t0,-120(fp)
	la	t1,exc_fp
	sd	t0,0(t1)
	ld	t0,-112(fp)
	la	t1,exc_handler
	sd	t0,0(t1)
	j	after_try_29
exc_handler_24: 
	ld	t0,-136(fp)
	la	t1,exc_sp
	sd	t0,0(t1)
	ld	t0,-120(fp)
	la	t1,exc_fp
	sd	t0,0(t1)
	ld	t0,-112(fp)
	la	t1,exc_handler
	sd	t0,0(t1)
	add	a0,zero,a0
	add	a0,zero,a0
	li	t0,2
	div	a0,a0,t0
	call	print_int64
	j	after_try_29
after_try_29: 
	j	main_conclusion
main_conclusion: 
	addi	a0,zero,0
	addi	sp,sp,144
	ld	ra,-8(sp)
	ld	fp,-16(sp)
	ld	s3,-24(sp)
	ld	s2,-32(sp)
	ld	s6,-40(sp)
	ld	s11,-48(sp)
	ld	s1,-56(sp)
	ld	s4,-64(sp)
	ld	s9,-72(sp)
	ld	s8,-80(sp)
	ld	s5,-88(sp)
	ld	s10,-96(sp)
	ld	s7,-104(sp)
	ret