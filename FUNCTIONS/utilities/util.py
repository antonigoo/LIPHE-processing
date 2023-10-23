import sys
import os
import config
import laspy
import numpy as np
import pandas as pd
"""
This module contains miscellaneous useful utility functions for the tree segmentation process
"""


"""


------
Input:
    segment_pcs     -   array containing the point cloud objects of each segment
    matches         -   output of match_locations()
    tree_path       -   path of the folder where the matched segment (i.e. tree) should be written.
                        The path should also include the filename for the tree point cloud
    other_path      -   path of the folder where segments other than the tree should be written. Only
                        necessary if write_other = True
    write_other     -   boolean that indicates whether segments other than the matched tree should also
                        be saved
    verbose         -   boolean that indicates whether to print info
------
Output:
    None
"""
def write_segments(
        segment_pcs: np.ndarray, matches: np.ndarray, tree_path: str, tree_filename: str,
        other_path: str = "", write_other: bool = True, verbose: bool = True
):
    # Make sure that the given directories exist and create them if not
    if not os.path.exists(tree_path):
        os.makedirs(tree_path)
    if write_other and not os.path.exists(other_path):
        os.makedirs(other_path)

    # Write tree segment, if a match was found
    for pc_ind, _ in matches:
        if verbose:
            print("Writing tree segment")
        segment_pcs[pc_ind].write(tree_path + tree_filename)

    # Write other identified segments, if necessary
    counter = 1
    tree_ind = -1
    n_segments = len(segment_pcs)
    has_match = 0
    if matches.size > 0:
        has_match = 1
        tree_ind = matches[0, 0]
    if write_other and n_segments > 0:
        for i in range(n_segments):
            if i == tree_ind:
                continue
            if verbose:
                sys.stdout.write('\rWriting other segment %3i out of %3i' % (counter, n_segments - has_match))
                sys.stdout.flush()
            segment_pcs[i].write(other_path + f"segment_{counter}.las")
            counter += 1
        if verbose:
            print("")


"""
Get the location of the given tree from the reference data

------
Input:
    filename        -   path to the file that contains the reference data
    tree_id         -   id of the tree for which to retrieve the reference location

-------
Output:
    ref_coords      -   xyz-coordinates of the reference tree in a numpy array
"""
def get_ref_coords(filename: str, tree_id: int):
    ref_data = pd.read_excel(filename)
    ref_tree = ref_data[ref_data["TREE_ID"] == tree_id]
    ref_coords = ref_tree[["E", "N", "H"]].to_numpy()
    ref_coords[:, 2] *= 0.1 # Convert to meters
    return ref_coords


"""
Match two sets of locations A and B such that two locations a and b are considered a match if b is the closest location to
a out of all locations in B and a is the closest location to b out of all locations in A. Furthermore, the locations must be at
most max_dist meters away from each other

------
Input:
    A, B            -   numpy arrays of locations
    max_dist        -   maximum distance between location and reference data point such that they are stil considered
                        a match

-------
Output:
    matches         -   numpy array where each row contains indices of matched locations. First element is the index
                        in A and second the index in B
"""
def match_locations(A: np.ndarray, B: np.ndarray, max_dist: float) -> np.ndarray:
    A_nearest = np.empty((len(A), 3), dtype = np.int32)
    for i in range(0, len(A)):
        dist = np.linalg.norm(B - A[i, :], axis = 1) # Distance from each point to point i of A
        dist_min = np.min(dist)
        index_min = np.argmin(dist)
        A_nearest[i, :] = np.array([i, index_min, dist_min])

    B_nearest = np.empty((len(B), 3), dtype = np.int32)
    for i in range(0, len(B)):
        dist = np.linalg.norm(A - B[i, :], axis = 1)
        dist_min = np.min(dist)
        index_min = np.argmin(dist)
        B_nearest[i, :] = np.array([index_min, i, dist_min])

    # Filter out matches where distance is above given threshold and remove distances from the numpy array,
    # as they are no longer necessary after this step
    A_nearest = A_nearest[A_nearest[:, 2] <= max_dist, 0:2]
    B_nearest = B_nearest[B_nearest[:, 2] <= max_dist, 0:2]

    # Find matches
    matches = []
    # Loop through locations, if any exist
    if not len(B_nearest) == 0:
        for i in range(0, len(A_nearest)):
            match_mask = np.all((B_nearest - A_nearest[i, :]) == 0, axis = 1)
            if np.any(match_mask):
                matches.append(A_nearest[i, :])

    matches = np.array(matches)
    return matches


"""
Attempts to read a file called 'filename' from config.PATH, which contains a list of (positive)
integer ids. If reading is succesful, returns the list found in the file. In the file, each id
should be stored on its own line.

------
Input:
    filename        -   name of the while which contains the integer plot ids

-------
Output:
    id_list         -   list of plot ids read from the specified file
"""
def get_id_list(filename: str) -> list([int]):
    id_list = [] # Initialize empty list for results
    invalid = False
    try:
        ids_file = open(config.PATH + filename, 'r')
        while True:
            line = ids_file.readline() # Read next line
            if not line:
                break # End of file reached
            id_str = line.strip()
            id = int(id_str) # Attempt to convert read id to an integer value
            if id <= 0:
                invalid = True
                break # Ids must all be positive integers
            id_list.append(id)
        
        ids_file.close()
        return id_list
    except FileNotFoundError:
        print(f"No file called {filename} found in {config.PATH}")
        return id_list # Return empty list
    except ValueError:
        invalid = True
    if invalid:
        raise ValueError(f"Each id should be a positive integer, got {id_str} instead")
    

"""
Concatenate two laspy point cloud objects

------
Input:
    pc_a, pc_b      -   point cloud objects, assumed to be of the same .las point format, e.g.

-------
Output:
    pc_ab           -   point cloud object created by concatenating the two point clouds given as input

!!! NOTE: It is quite possible that this function will only work with .las format 7, I haven't tested
    any other formats. However, making it work with other formats should be quite straightforward !!!
"""
def concat_point_clouds(pc_a: laspy.LasData, pc_b: laspy.LasData) -> laspy.LasData:
    # The function also works for point clouds that are simply numpy arrays (assuming the dimension
    # of the arrays are correct)
    if (type(pc_a) == np.ndarray) and (type(pc_b) == np.ndarray):
        pc_ab = np.concatenate([pc_a, pc_b])
    else:
        # We begin by pulling out the ScaleAwarePointRecord objects from each lasdata object. These objects contain all of the
        # non-header data, e.g. point coordinate, intensities, scan_angle, rgb and so on
        points_a = pc_a.points
        points_b = pc_b.points
        # Create a new lasdata object. Requires a header as an argument. Assuming that both point cloud objects are in the same
        # format, we can use either header
        pc_ab = laspy.LasData(pc_a.header)
        # We concatenate all of the data from pc_a and pc_b
        array = np.concatenate([points_a.array, points_b.array])
        # By default offsets, scales, point format and sub field dict are pulled from point cloud a. For this to work we again rely on the
        # assumption that the point clouds are in the same format
        # Create a new ScaleAwarePointRecord object from the concatenated data
        points_ab = laspy.point.record.ScaleAwarePointRecord(array, points_a.point_format, points_a.scales, points_b.offsets)
        # Add points to new lasdata object and update header
        pc_ab.points = points_ab
        pc_ab.update_header()
    return pc_ab
