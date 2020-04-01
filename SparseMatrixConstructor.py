import numpy as numpy
import array
from scipy import sparse as sp


class SparseMatrix(object):

    def __init__(self, shape, dtype):

        if dtype is numpy.int32:
            type_flag = 'i'
        elif dtype is numpy.int64:
            type_flag = 'l'
        elif dtype is numpy.float32:
            type_flag = 'f'
        elif dtype is numpy.float64:
            type_flag = 'd'
        else:
            raise Exception('Dtype not supported.')

        self.dtype = dtype
        self.shape = shape

        self.rows = array.array('i')
        self.cols = array.array('i')
        self.data = array.array(type_flag)

    def append(self, i, j, v):

        m, n = self.shape

        if (i >= m or j >= n):
            raise Exception('Index out of bounds')

        self.rows.append(i)
        self.cols.append(j)
        self.data.append(v)

    def tocoo(self):

        rows = numpy.frombuffer(self.rows, dtype=numpy.int32)
        cols = numpy.frombuffer(self.cols, dtype=numpy.int32)
        data = numpy.frombuffer(self.data, dtype=self.dtype)

        return sp.coo_matrix((data, (rows, cols)),
                             shape=self.shape)

    def __len__(self):

        return len(self.data)
