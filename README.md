# Notice
* Still in pre-alpha development
* Requires Python 3.6+
* Runtime axis operations are not supported by design, such as:
    * Dynamic shape
    * Dynamic transpose

# Advantages
* Small memory footprint (less intermediate buffers, no manual handling required)
* No memory management
* No unnecessary `if` in the loop
* Side-by-side comparison with NumPy results
* Pre-runtime safety check
* No dependencies
* Pure Python, less compatibility issue
* Accountable JIT: Simple C code generation

# Supported operations
## Numpy
* creation
    * array
    * zeros
    * ones
    * full
    * arange
    * meshgrid (xy)
    * frombuffer
* manipulation
    * transpose
    * stack
    * expand_dims
    * reshape
    * concatenate
    * repeat
    * ascontiguousarray
* logic
    * greater
* slicing (positive step)
* slice assignment (step=1)
* math
    * add
    * subtract
    * multiply

## PyTorch
* Tensor (contructed from data)
* permute

# Todo
## Numpy
* slicing (negative step)
* slice assignment (step!=1)
* math
    * divide
    * reciprocal
    * exponents and logarithms
    * trigonometric functions
    * hyperbolic functions
* linalg
    * matmul
* dynamic content size
    * boolean filter
* masking (or not?)

## PyTorch
* TBD

## Others
* zero-dimentional value
* loop fusion ?
* Large buffer breakdown
* assign: AnnAssign

# License
Both DAFunctor and its generated source codes are licensed under `GNU Lesser General Public License v3.0`.

# Example
```
python3 example/example_numpy.py
```

# Interactive example
```
>>> import dafunctor.numpy as nf
>>> s = nf.meshgrid([1,2],[3,4,5])
>>> s.eval()
array([[[1., 2.],
        [1., 2.],
        [1., 2.]],

       [[3., 3.],
        [4., 4.],
        [5., 5.]]])
>>> f = s.jit()
>>> f()
array([[[1., 2.],
        [1., 2.],
        [1., 2.]],

       [[3., 3.],
        [4., 4.],
        [5., 5.]]], dtype=float32)
>>> s.print()
Functor: #3 array3
    transposed_raw_meshgrid
    shape=((0, 2, 1), (0, 3, 1), (0, 2, 1))
    partitions=[[(0, 2, 1), (0, 2, 1), (0, 3, 1)]]
    iexpr=[
            i0
            i2
            i1
    ]
    Functor[0]: #2 array2
        raw_meshgrid
        shape=((0, 2, 1), (0, 2, 1), (0, 3, 1))
        partitions=[[(0, 2, 1), (0, 3, 1)], [(0, 2, 1), (0, 3, 1)]]
        iexpr=[
                si
                i0
                i1
        ]
        Functor[0]: #0 array0
            raw_meshgrid[0]
            shape=((0, 2, 1), (0, 3, 1))
            vexpr=['ref', ['d', 'i0']]
            data=[1, 2]
        Functor[1]: #1 array1
            raw_meshgrid[1]
            shape=((0, 2, 1), (0, 3, 1))
            vexpr=['ref', ['d', 'i1']]
            data=[3, 4, 5]
>>> print(open(f.source).read())
#include <stdio.h>
#include <math.h>
#define AUTOBUF // put static here if your algorithm run with only one instance

void gen_array3(float array3[12] /* shape=[2, 3, 2] */)
{
    const static int d_meshgrid_0[] = {1,2};
    const static int d_meshgrid_1[] = {3,4,5};

    for(int i0=0;i0<2;i0+=1)
      for(int i1=0;i1<3;i1+=1)
    {
        // raw_meshgrid
        const int i0_0_1 = 0;
        const int i1_0_1 = i0;
        const int i2_0_1 = i1;

        // transpose([0, 2, 1])
        const int i0_0_2 = i0_0_1;
        const int i1_0_2 = i2_0_1;
        const int i2_0_2 = i1_0_1;

        array3[i0_0_2*3*2 + i1_0_2*2 + i2_0_2] = d_meshgrid_0[i0];
    }
    for(int i0=0;i0<2;i0+=1)
      for(int i1=0;i1<3;i1+=1)
    {
        // raw_meshgrid
        const int i0_0_1 = 1;
        const int i1_0_1 = i0;
        const int i2_0_1 = i1;

        // transpose([0, 2, 1])
        const int i0_0_2 = i0_0_1;
        const int i1_0_2 = i2_0_1;
        const int i2_0_2 = i1_0_1;

        array3[i0_0_2*3*2 + i1_0_2*2 + i2_0_2] = d_meshgrid_1[i1];
    }
}
```

# To be investigated:
## Codegen
    * CUDA
    * OpenMP
    * LLIR
## Other
    * Named tensor

# Testing
```
python3 tests/tester_numpy.py
```
