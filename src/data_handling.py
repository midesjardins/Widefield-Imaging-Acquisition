import numpy as np

def shrink_array(array, extents):
    return array[:,extents[0]:extents[1], extents[2]:extents[3]]