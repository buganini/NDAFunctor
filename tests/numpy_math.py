from tester_numpy import *

def add1(np):
    return np.add(np.array([[4,5],[6,7]]), 1)

test_func("add1", add1)

def add2(np):
    return np.array([[4,5],[6,7]]) + 2

test_func("add2", add2)

def add3(np):
    return np.array([[4,5],[6,7]]) + 2 + 3

test_func("add3", add3)

def stack_add(np):
    return np.stack([np.array([[1,2,3],[4,5,6]]), np.array([[7,8,9],[10,11,12]])], axis=0) + 1

test_func("stack_add", stack_add)

def stack_transpose_add(np):
    return np.transpose(np.stack([np.array([[1,2],[4,5]]), np.array([[7,8],[10,11]])], axis=0), (1,0,2)) + 1

test_func("stack_transpose_add", stack_transpose_add)

def repeat_repeat_add(np):
    return np.repeat(np.repeat(np.array([[1,2],[4,5]]), 3, axis=0), 2, axis=1) + 1

test_func("repeat_repeat_add", repeat_repeat_add)

def repeat_add_reshape_add_repeat_add(np):
    return np.repeat(np.reshape(np.repeat(np.array([[1,2],[4,5]]), 3, axis=0) + 2, (3,4)) + 3, 2, axis=1) + 5

test_func("repeat_add_reshape_add_repeat_add", repeat_add_reshape_add_repeat_add)