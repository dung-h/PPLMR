.source TyC.java
.class public TyC
.super java/lang/Object

.method public static total(LPoint;)I
Label0:
.var 0 is p LPoint; from Label0 to Label1
Label2:
.var 1 is i I from Label2 to Label3
	iconst_0
	istore_1
Label4:
	iload_1
	iconst_2
	if_icmpge Label7
	iconst_1
	goto Label8
Label7:
	iconst_0
Label8:
	ifle Label6
Label9:
	aload_0
	aload_0
	getfield Point/x I
	iload_1
	iadd
	dup_x1
	putfield Point/x I
	pop
Label10:
Label5:
	iload_1
	dup
	iconst_1
	iadd
	istore_1
	pop
	goto Label4
Label6:
	aload_0
	getfield Point/x I
	aload_0
	getfield Point/y I
	iadd
	ireturn
Label3:
Label1:
.limit stack 3
.limit locals 2
.end method

.method public static main([Ljava/lang/String;)V
Label0:
.var 0 is args [Ljava/lang/String; from Label0 to Label1
Label2:
.var 1 is p LPoint; from Label2 to Label3
	new Point
	dup
	invokespecial Point/<init>()V
	dup
	iconst_3
	putfield Point/x I
	dup
	iconst_4
	putfield Point/y I
	astore_1
	aload_1
	invokestatic TyC/total(LPoint;)I
	invokestatic io/printInt(I)V
	aload_1
	getfield Point/x I
	invokestatic io/printInt(I)V
Label3:
	return
Label1:
.limit stack 3
.limit locals 2
.end method
