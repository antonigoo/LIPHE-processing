import numpy as np

"""
Creates a voxel space of a point cloud. This function is a port of the MATLAB function createVoxelSpace. The
function has been modified slightly by adding the option to also return the voxelized point cloud as a volumetric
image of sorts (3d array where each voxel is represented by the number of points it contains)
Source code of the original functions by J. Savela is available at:

https://gitlab.com/fgi_nls/kauko/fgi-remotesensing-tools/pcfumble

------
Input:
    pc                  -   point cloud xyz coordinates
    resolution          -   Defines the voxel size. Either scalar or 3 element tuple. If scalar provided, voxels
                            are cubes with edge length resolution (meters). Order of dimensions: (x, y, z)
    extent              -   numpy array of shape (2, 3). Defines a 3D rectangle such that only the points within
                            the rectangle are considered when creating the voxelized point cloud. First row should
                            contain the lower bounds of the rectangle and second row the upper bounds, i.e. the
                            format of the parameter is [[x0, y0, z0], [x1, y1, z1]], where x0 < x1, y0 < y1, z0 < z1.
                            extent is an optional parameter, if no value is provided, all points in the point cloud
                            are considered
    return_img          -   if true, return the volumetric image of the point clouds, where each voxel has a value
                            equal to the number of points it contains. Default: falses

-------
Output:
    voxel_space         -   Information about the created voxel space (numpy array of size n_voxels x 7, where n_voxels
                            is the numbe of voxels that contain at least one point).
                                * col 1:    voxel id
                                * col 2-4:  voxel coordinates (x, y, z)
                                * col 5:    number of points in the voxel
                                * col 6-7:  start and end indices of this voxels section in voxel_search_list
    voxel_search_list   -   (numpy array of size m x 2). The rows correspond to the m points inside any of the voxels
                            (i.e. points within extent)
                                * col 1:    voxel id
                                * col 2:    index of the point in the original point cloud
                            Rows are ordered by col 1.
    point_search_list   -   (numpy array of size n x 2, where n is the number of points in the original point cloud)
                                * col 1:    index of the point in the original point cloud
                                * col 2:    voxel id
    voxel_img           -   volumetric image of the point cloud. Only returned if return_img is set to true
    voxel_img_ids       -   volumetric image of the point cloud. Each voxel value is set to the id of the
                            voxel it corresponds to in voxel_space. Only returned if return_img is set
                            to true
"""
def create_voxels(pc: np.ndarray, resolution, extent: np.ndarray = np.array([]), return_img: bool = False):
    # If the given resolution is a tuple, it must contains three dimensions
    if isinstance(resolution, tuple):
        if len(resolution) != 3:
            raise ValueError("resolution must have either 1 or 3 dimensions")
        if not (all([isinstance(dim, int) for dim in resolution]) or all([isinstance(dim, float) for dim in resolution])):
            raise TypeError("resolution must be an int or float")
        # Cast dimensions to type float
        resolution = tuple([float(dim) for dim in resolution])
    # If the resolution is not a 3D tuple, it must be a single number
    elif isinstance(resolution, int) or isinstance(resolution, float):
        # Create a three element tuple out of the single dimension
        resolution = (float(resolution), ) * 3 
    else:
        raise TypeError("resolution must be an int or float")
    if extent.size == 0:
        extent = np.concatenate([np.min(pc, axis = 0), np.max(pc, axis = 0)]).reshape(2, 3)
    elif extent.shape != (2, 3):
        raise ValueError(f"shape of extent should be (2, 3), got {extent.shape} instead")
    elif not ((extent.dtype == np.int64) or (extent.dtype == np.float64)):
        raise TypeError("extent data type must be np.int64 or np.float64")
     # Range of x, y and z coordinates
    extent_range = extent[1, :] - extent[0, :]
    xyz_diff = pc - extent[0, :]
    # Logical indices pointing to the points in the point cloud that are within the given rectangle
    inside_mask = np.all(xyz_diff >= 0, axis = 1) & np.all(xyz_diff <= extent_range, axis = 1)

    n_points = len(pc) # Number of points in the point cloud
    sizes = np.ceil(extent_range / resolution).astype(np.int64) # Dimensions of the voxelized point cloud
    voxel_indices = np.zeros([n_points, 1], dtype = np.int64) # Intialize array for voxel indices
    voxel_coords = np.floor(xyz_diff[inside_mask] / resolution) # Compute the voxel coordinate of each point in the point cloud
    voxel_indices[inside_mask, :] = np.matmul(voxel_coords, np.array([1, sizes[0], sizes[0] * sizes[1]]).reshape(3, 1)) + 1

    voxel_ids = np.unique(voxel_indices)
    n_voxels = voxel_ids.size
    voxel_id_range = range(n_voxels)
    if voxel_ids[0] == 0:
        voxel_id_range = range(1, n_voxels)
        n_voxels -= 1
    voxel_space = np.zeros([n_voxels, 7], dtype = np.int64)
    voxel_space[:, 0] = voxel_ids[voxel_id_range]

    voxel_ids_zeroed = voxel_space[:, 0] - 1
    voxel_space[:, 3] = np.floor(voxel_ids_zeroed / (sizes[0] * sizes[1]))
    voxel_space[:, 2] = np.floor((voxel_ids_zeroed / sizes[0])) - sizes[1] * voxel_space[:, 3]
    voxel_space[:, 1] = voxel_ids_zeroed - sizes[0] * (sizes[1] * voxel_space[:, 3] + voxel_space[:, 2])

    sorted_ind = np.argsort(voxel_indices.reshape(1, -1))
    voxel_indices_sorted = voxel_indices[sorted_ind][0]
    change_mask = np.append(np.diff(voxel_indices_sorted, axis = 0) != 0, False)
    indices = np.array(range(n_points)).reshape(-1, 1)
    starts = np.insert(indices[change_mask] + 1, 0, 0, axis = 0)
    ends = np.append(indices[change_mask], n_points - 1).reshape(-1, 1)
    n_zeros = starts[voxel_id_range[0]][0] # Number of empty voxels
    # Insert number of points in each voxel to voxel_space
    voxel_space[:, 4] = (ends[voxel_id_range] - starts[voxel_id_range] + 1).flatten()
    # Insert start and end indices of points in the voxel to voxel_space
    voxel_space[:, 5] = (starts[voxel_id_range] - n_zeros).flatten()
    voxel_space[:, 6] = (ends[voxel_id_range] - n_zeros).flatten()

    voxel_search_list = np.concatenate([
        voxel_indices_sorted[range(n_zeros, n_points)].reshape(-1, 1),
        sorted_ind[0][range(n_zeros, n_points)].reshape(-1, 1)
    ], axis = 1)
    point_search_list = np.concatenate([
        np.array(indices).reshape(-1, 1),
        voxel_indices.reshape(-1, 1)
    ], axis = 1)

    if return_img:
        voxel_img = np.zeros([sizes[2], sizes[1], sizes[0]], dtype = np.int64)
        voxel_img_ids = np.zeros([sizes[2], sizes[1], sizes[0]], dtype = np.int64)
        # Indices of voxels that contain at least one point from voxel_space
        full_voxel_ind = np.flip(voxel_space[:, 1:4], axis = 1)
        # Add number of points in each voxel to voxel_img
        voxel_img[tuple(full_voxel_ind.T)] = voxel_space[:, 4]
        voxel_img_ids[tuple(full_voxel_ind.T)] = voxel_space[:, 0]
        return voxel_space, voxel_search_list, point_search_list, voxel_img, voxel_img_ids
    else:
        return voxel_space, voxel_search_list, point_search_list