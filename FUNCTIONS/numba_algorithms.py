import numba as nb
import math
import numpy as np
from numba import jit

@nb.njit(nb.types.UniTuple(nb.float64,2)(nb.float64[:]), fastmath=True)
def minmax(a):
    N = a.size
    odd = N % 2
    if not odd:
        N -= 1
    maxv = minv = a[0]
    #i = 1
    for i in range(1, N, 2):
    #while i < N:
        x = a[i]
        y = a[i + 1]
        if x > y:
            x, y = y, x
        minv = min(x, minv)
        maxv = max(y, maxv)
        i += 2
    
    if not odd:
        x = a[N]
        minv = min(x, minv)
        maxv = max(x, maxv)
    
    return minv, maxv


mean_count_type = nb.core.types.Tuple((nb.float64, nb.float64, nb.float64, nb.uint32, nb.float32))
#mean_count_type = nb.types.Tuple((nb.float64, nb.float64, nb.float64, nb.uint32))

#Compute the mean x,y and z for given voxel size for voxels with at least pts_min points
@nb.njit

def compute_grid_means(x,y,z, att ,voxel_size,pts_min): 
    N = len(x)
    #divide the space into uniform cubes (voxels) with side length voxel_size meters
    min_x, max_x = minmax(x)
    min_y, max_y = minmax(y)
    min_z, max_z = minmax(z)
    
#    voxel_sizez=0.5
    
    bins_x = np.arange(min_x, max_x, voxel_size, dtype = np.float64)
    bins_y = np.arange(min_y, max_y, voxel_size, dtype = np.float64)
    bins_z = np.arange(min_z, max_z, voxel_size, dtype = np.float64)

    nx = len(bins_x)
    ny = len(bins_y)
    nz = len(bins_z)
    #Hold the (linear) voxel indices and the sum of x,y,z of all points in the voxel
    #as well as the amount points
    d = nb.typed.Dict.empty(
            key_type = nb.types.uint32,
            value_type = mean_count_type) 
    #Loop over data and accumulate the dictionary
    for i in range(N):
        xx = x[i]
        yy = y[i]
        zz = z[i]
        att_voxel=att[i]
        x_voxel = np.searchsorted(bins_x, xx, side = 'right') - 1
        y_voxel = np.searchsorted(bins_y, yy, side = 'right') - 1
        z_voxel = np.searchsorted(bins_z, zz, side = 'right') - 1
        linear_index = x_voxel + y_voxel*nx + z_voxel*nx*ny
        try:
            old = d[linear_index]
            d[linear_index] = (old[0] + xx, old[1] + yy, old[2] + zz, old[3] + 1, old[4]+att_voxel) 
        except:
            d[linear_index] = (xx, yy, zz, 1, att_voxel)
    #Determine voxels that have more than pts_min points
    n = 0
    nonzeros = set()
    for key, value in d.items():
        if value[3] > pts_min:
            n+=1
            nonzeros.add(key)
    i = 0
    means = np.zeros((n,3), dtype = np.float64)
    MeanReflec = np.zeros((n,), dtype = np.float64)
    #Calculate mean x,y,z for each voxel with enough points
    for key in nonzeros:
        xx, yy, zz, count, att_mean = d[key]
        means[i] = np.array([xx, yy, zz])/count
        MeanReflec[i] = np.array(att_mean)/count
        i += 1
    return means, MeanReflec

@nb.njit
def rot_fi_k(x, y, z, fi, k):
    cos_fi = math.cos(fi)
    cos_k = math.cos(k)
    sin_fi = math.sin(fi)
    sin_k = math.sin(k)
    
    Rotfi = np.array([
            [cos_fi, 0., -sin_fi],
            [ 0.,   1.,   0.],
            [sin_fi,  0., cos_fi]
            ], dtype=np.float64)

    Rotk = np.array([
            [cos_k, sin_k, 0.],
            [-sin_k, cos_k,0.],
            [ 0.,  0., 1.]
            ], dtype=np.float64)
    Rot = np.dot(Rotfi, Rotk) 
    #Rotate first by fi and then by k
    result = np.dot(Rot, np.vstack((x,y,z)))
    return result
