import math
import laspy
import numpy as np
import cv2 as cv
from scipy.ndimage import rank_filter
from scipy.interpolate import griddata


"""
Rasterize the given point cloud such that the size of one pixel in the raster is resolution x resolution
meters. The raster is created by choosing the value of the highest point in that raster cell as the value
of the cell and then smoothing the resulting raster using a gaussian filter

------
Input:
    pc                      -   normalized point cloud of the forest plot (i.e. the height of the ground has been
                                subtracted from the heights of the points)
    resolution              -   resolution of the rasterized point cloud (pixel size resolution x resolution meters)
    sigma                   -   standard deviation used when a gaussian filter is applied to the raster
    window_size             -   window size used for gaussian filtering

-------
Output:
    raster                  -   smoothed raster of the point cloud z-coordinates
    rasterized_pc           -   rasterized point cloud, such that one raster cell contains the indices of all points
                                within that cell
"""
def create_raster(pc: laspy.LasData, resolution: float, sigma: float, window_size: int) -> tuple([np.ndarray, np.ndarray]):

    x_min = int(np.min(pc.x) / resolution) * resolution
    y_min = int(np.min(pc.y) / resolution) * resolution
    x_max = (int(np.max(pc.x) / resolution) + 1) * resolution
    y_max = (int(np.max(pc.y) / resolution) + 1) * resolution
    # Compute the dimensions of the raster (in pixels of size resolution x resolution)
    raster_y_dim = int(round((y_max - y_min) / resolution))
    raster_x_dim = int(round((x_max - x_min) / resolution))
    init_value = np.min(pc.z) - 1 # Placeholder value
    # Create raster and fill it with the initial placeholder value
    raster = np.full([raster_y_dim, raster_x_dim], init_value)
    # Initialize a 3D list such that first 2 dimensions match the raster, but each cell contains a list as well.
    # In the list we save the indices of each point in the point cloud that is part of the particular cell
    rasterized_pc = [[[] for _ in range(raster_x_dim)] for _ in range(raster_y_dim)]
    # We create separate numpy arrays for storing the necessary information from the point cloud object, since
    # accessing the points from the object itself is much slower (I believe this has something to do with how
    # the lasdata class handles data, but I don't know the exact reason)
    x_coords = np.array(pc.x)
    y_coords = np.array(pc.y)
    z_coors = np.array(pc.z)
    ret_num = np.array(pc.points.return_number)
    # Loop through all points in the point cloud
    for k in range(0, pc.header.point_count):
        # Extract coordinates of the current point from the point cloud object
        x, y, z = x_coords[k], y_coords[k], z_coors[k]
        # Compute the location of the current point in the raster
        j = math.floor((y_max - y) / resolution)
        i = math.floor((x - x_min) / resolution)
        # Check whether the point is within the raster
        if j >= 0 and j < raster_y_dim and i >= 0 and i < raster_x_dim:
            # If the current point is higher than the highest known point in the current raster cell, update the value
            # to the height of the current point (the point must also be a first return)
            if ret_num[k] == 1 and z > raster[j, i]:
                raster[j, i] = z
            # Save point index at the correct coordinate
            rasterized_pc[j][i].append(k)

    # Raster cells that still have the initial value contain no points. Replace the value of such cells with nan
    raster[raster == init_value] = np.nan
    # Indices of raster cells that are not empty (i.e. value is not nan)
    full_cell_indices = np.argwhere(~np.isnan(raster))
    full_cell_values = raster[tuple(full_cell_indices.T)]
    xi, yi = np.meshgrid(range(0, raster.shape[1]), range(0, raster.shape[0]))
    # Interpolate the values of empty raster cells
    raster = griddata(np.flip(full_cell_indices, axis = 1), full_cell_values, (xi, yi), method = 'linear')
    # Smoothen raster by applying a gaussian filter
    raster = cv.GaussianBlur(src = raster, ksize = (window_size, window_size), sigmaX = sigma, borderType = cv.BORDER_REPLICATE)
    # Return smoothed raster
    return raster, rasterized_pc


"""
Find local maxima within the raster

------
Input:
    raster                  -   raster created from the forest plot point cloud (output of create_raster)
    window_size             -   window_size used for maximum filtering
    max_point_diff          -   maximum difference between the maximum filtered and original value of each
                                raster cell such that the cell is still considered a local maxima
    bg_thresh               -   points below this height are considered background -> can't be local maxima

-------
Output:
    max_points              -   coordinates and values of the local maxima
    markers                 -   binary raster with the cells containing the local maxima labelled with distinct positive integers
                                (each maxima has it's own label) and background labelled with 1. Points that are neither local
                                maxima, nor background are labelled with 0
"""
def find_local_maxima(raster: np.ndarray, window_size: int, max_point_diff: float, bg_thresh: float) -> tuple ([np.ndarray, np.ndarray]):
    # Begin by applying a maximum filter to the image, i.e. replace each element in the image with the largest element
    # in a neighbourhood of size WINDOW_SIZE x WINDOW_SIZE
    filtered_raster = rank_filter(input = raster, rank = -1, size = (window_size, window_size), mode = "reflect")
    max_point_ind = tuple(np.argwhere(np.abs(filtered_raster - raster) < max_point_diff).T)
    # Initialize the marker raster by creating a raster filled with zeros
    markers = np.zeros(raster.shape, dtype = np.int32)
    # Find values of the local maxima from the original raster
    max_point_values = raster[max_point_ind]
    # We create distinct labels for each local maxima and add them to the marker raster. (markers have value >= 2)
    markers[max_point_ind] = np.array(range(2, len(max_point_ind[0]) + 2), dtype = np.int32)
    # Concatenate the coordinates of the local maxima with the values
    max_points = np.concatenate([np.array(max_point_ind).T, max_point_values.reshape(-1, 1)], axis = 1)
    # Filter out local maxima lower than the background threshold
    max_points = max_points[max_points[:, 2] > bg_thresh]
    # Cells of the original raster that have a value below the background threshold are classified as background in
    # the marker raster
    markers[(raster <= bg_thresh) | np.isnan(raster)] = 1
    return max_points, markers


"""
Convert raster coordinates back into regular coordinates to allow matching segments to reference data

------
Input:
    rasterized_coordinates  -   array of rasterized coordinates to convert back to the original coordinate system
                                of the point cloud (x and y coordinates only)
    pc                      -   original forest plot point cloud
    resolution              -   resolution of the raster

-------
Output:
    coordinates             -   unrasterized coordinates
"""
def unrasterize_coordinates(rasterized_coordinates: np.ndarray, pc: laspy.LasData, resolution: float) -> np.ndarray:
    x_min = int(np.min(pc.x) / resolution) * resolution
    y_max = (int(np.max(pc.y) / resolution) + 1) * resolution
    coordinates = np.concatenate([
        (x_min + (rasterized_coordinates[:, 1] - 1) * resolution).reshape(-1, 1),
        (y_max + (rasterized_coordinates[:, 0] - 1) * -resolution).reshape(-1, 1)
    ], axis = 1)

    return coordinates