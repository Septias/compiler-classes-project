
	.globl	f
	.align	8
f: 
	sd	ra,-8(sp)
	sd	fp,-16(sp)
	sd	zero,-24(sp)
	sd	zero,-32(sp)
	addi	fp,sp,0
	addi	sp,sp,-32
	j	f_start
f_start: 
	add	a0,zero,a0
	add	t0,zero,a1
	sd	t0,-32(fp)
	la	t0,g
	sd	t0,-24(fp)
	la	a0,gc_free_ptr
	ld	a0,0(a0)
	addi	a1,a0,16
	la	a0,gc_fromspace_end
	ld	a0,0(a0)
	blt	a1,a0,body_0
	j	orelse_1
body_0: 
	j	cont_2
orelse_1: 
	add	a0,zero,sp
	li	a1,2
	call	gc_collect
	j	cont_2
cont_2: 
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
	ld	t0,-24(fp)
	sd	t0,7(a0)
	add	a0,zero,a0
	ld	a2,7(a0)
	ld	t0,-32(fp)
	addi	a1,t0,2
	add	a0,zero,a0
	add	a1,zero,a1
	addi	sp,sp,32
	jr	a2, 8
	j	f_conclusion
f_conclusion: 
	addi	sp,sp,32
	ld	ra,-8(sp)
	ld	fp,-16(sp)
	ret

	.globl	g
	.align	8
g: 
	sd	ra,-8(sp)
	sd	fp,-16(sp)
	addi	fp,sp,0
	addi	sp,sp,-16
	j	g_start
g_start: 
	add	a0,zero,a0
	add	a0,zero,a1
	li	t1,0
	beq	a0,t1,body_3
	j	orelse_4
body_3: 
	li	a0,0
	add	a0,zero,a0
	j	g_conclusion
	j	cont_5
orelse_4: 
	la	sp,exc_sp
	ld	sp,0(sp)
	la	fp,exc_fp
	ld	fp,0(fp)
	li	a0,84
	la	t0,exc_handler
	ld	t0,0(t0)
	jr	t0, 0
	j	cont_5
cont_5: 
	j	g_conclusion
g_conclusion: 
	addi	sp,sp,16
	ld	ra,-8(sp)
	ld	fp,-16(sp)
	ret

	.globl	program_main
	.align	8
program_main: 
	sd	ra,-8(sp)
	sd	fp,-16(sp)
	sd	zero,-24(sp)
	sd	zero,-32(sp)
	sd	zero,-40(sp)
	sd	zero,-48(sp)
	sd	zero,-56(sp)
	sd	zero,-64(sp)
	addi	fp,sp,0
	addi	sp,sp,-64
	j	program_main_start
program_main_start: 
	add	a0,zero,a0
	la	t0,f
	sd	t0,-24(fp)
	la	a0,gc_free_ptr
	ld	a0,0(a0)
	addi	a0,a0,16
	la	a1,gc_fromspace_end
	ld	a1,0(a1)
	blt	a0,a1,body_6
	j	orelse_7
body_6: 
	j	cont_8
orelse_7: 
	add	a0,zero,sp
	li	a1,2
	call	gc_collect
	j	cont_8
cont_8: 
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
	ld	t0,-24(fp)
	sd	t0,7(a0)
	add	a0,zero,a0
	ld	a2,7(a0)
	li	t0,0
	addi	a1,t0,-2
	add	a0,zero,a0
	add	a1,zero,a1
	jalr	a2
	add	a0,zero,a0
	add	a0,zero,a0
	li	t0,2
	div	a0,a0,t0
	call	print_int64
	la	t0,exc_sp
	ld	t0,0(t0)
	sd	t0,-32(fp)
	la	t0,exc_fp
	ld	t0,0(t0)
	sd	t0,-40(fp)
	la	t0,exc_handler
	ld	t0,0(t0)
	sd	t0,-56(fp)
	add	t0,zero,sp
	la	t1,exc_sp
	sd	t0,0(t1)
	add	t0,zero,fp
	la	t1,exc_fp
	sd	t0,0(t1)
	la	t0,exc_handler_9
	la	t1,exc_handler
	sd	t0,0(t1)
	la	t0,f
	sd	t0,-48(fp)
	la	a0,gc_free_ptr
	ld	a0,0(a0)
	addi	a1,a0,16
	la	a0,gc_fromspace_end
	ld	a0,0(a0)
	blt	a1,a0,body_10
	j	orelse_11
body_10: 
	j	cont_12
orelse_11: 
	add	a0,zero,sp
	li	a1,2
	call	gc_collect
	j	cont_12
cont_12: 
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
	ld	t0,-48(fp)
	sd	t0,7(a0)
	add	a0,zero,a0
	ld	a2,7(a0)
	add	a0,zero,a0
	li	a1,2
	jalr	a2
	add	a0,zero,a0
	li	t0,0
	li	t1,0
	bne	t0,t1,exc_handler_9
	j	try_cont_13
try_cont_13: 
	add	a0,zero,a0
	li	t0,2
	div	a0,a0,t0
	call	print_int64
	ld	t0,-32(fp)
	la	t1,exc_sp
	sd	t0,0(t1)
	ld	t0,-40(fp)
	la	t1,exc_fp
	sd	t0,0(t1)
	ld	t0,-56(fp)
	la	t1,exc_handler
	sd	t0,0(t1)
	j	after_try_14
exc_handler_9: 
	ld	t0,-32(fp)
	la	t1,exc_sp
	sd	t0,0(t1)
	ld	t0,-40(fp)
	la	t1,exc_fp
	sd	t0,0(t1)
	ld	t0,-56(fp)
	la	t1,exc_handler
	sd	t0,0(t1)
	add	a0,zero,a0
	add	a0,zero,a0
	li	t0,2
	div	a0,a0,t0
	call	print_int64
	j	after_try_14
after_try_14: 
	j	program_main_conclusion
program_main_conclusion: 
	addi	sp,sp,64
	ld	ra,-8(sp)
	ld	fp,-16(sp)
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
	sd	t0,-112(fp)
	la	t0,exc_fp
	ld	t0,0(t0)
	sd	t0,-120(fp)
	la	t0,exc_handler
	ld	t0,0(t0)
	sd	t0,-136(fp)
	add	t0,zero,sp
	la	t1,exc_sp
	sd	t0,0(t1)
	add	t0,zero,fp
	la	t1,exc_fp
	sd	t0,0(t1)
	la	t0,exc_handler_15
	la	t1,exc_handler
	sd	t0,0(t1)
	la	t0,program_main
	sd	t0,-128(fp)
	la	a0,gc_free_ptr
	ld	a0,0(a0)
	addi	a1,a0,16
	la	a0,gc_fromspace_end
	ld	a0,0(a0)
	blt	a1,a0,body_16
	j	orelse_17
body_16: 
	j	cont_18
orelse_17: 
	add	a0,zero,sp
	li	a1,2
	call	gc_collect
	j	cont_18
cont_18: 
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
	bne	t0,t1,exc_handler_15
	j	try_cont_19
try_cont_19: 
	ld	t0,-112(fp)
	la	t1,exc_sp
	sd	t0,0(t1)
	ld	t0,-120(fp)
	la	t1,exc_fp
	sd	t0,0(t1)
	ld	t0,-136(fp)
	la	t1,exc_handler
	sd	t0,0(t1)
	j	after_try_20
exc_handler_15: 
	ld	t0,-112(fp)
	la	t1,exc_sp
	sd	t0,0(t1)
	ld	t0,-120(fp)
	la	t1,exc_fp
	sd	t0,0(t1)
	ld	t0,-136(fp)
	la	t1,exc_handler
	sd	t0,0(t1)
	add	a0,zero,a0
	add	a0,zero,a0
	li	t0,2
	div	a0,a0,t0
	call	print_int64
	j	after_try_20
after_try_20: 
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