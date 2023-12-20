from lbl_segmentation import config
import sys
import laspy
import numpy as np
import pandas as pd
# Imports from other directories
sys.path.append('../utilities')
from utilities.util import concat_point_clouds

"""
Improve the quality of the training data used for the final segmentation as follows:
    1. Slice a cylinder from the point cloud using the tree location as a center for the cylinder.
       the radius is determined as a function of the furthest points of the point cloud (in xy direction) 
       w.r.t the cylinder center
    2. If there's a considerable gap in the cylinder between higher and lower layers, remove
       the higher layers from the cylinder
    3. Use data augmentation to fill in considerable gaps within the cylinders

------
Input:
    locations       -   locations of trees along with intial training data points. output of refind_tree_locations()
    gap_max         -   max gap length within a cylinder
    gap_min         -   min gap length for which data augmentation is applied within cylinder

-------
Output:
    new_tree_pcs    -   refined training data array
"""
def refine_training_data(locations: pd.DataFrame, gap_max: float, gap_min: float) -> np.ndarray:
    # Initialize an empty array for the new training data
    refined_data = np.empty(len(locations), dtype = laspy.LasData)
    init_data = locations["points"].to_numpy()
    for i in range(len(locations)):
        center_x = locations["line_x"][i]
        center_y = locations["line_y"][i]
        init_pc = init_data[i]
        # Function works for point clouds of just xyz coordinates and laspy.LasData objects
        if type(init_pc) == laspy.LasData:
            pc_xyz = init_pc.xyz
        else:
            pc_xyz = init_pc
        dist_to_center = np.linalg.norm(pc_xyz[:, 0:2] - [center_x, center_y], axis = 1)
        # Radius of cylinder is 0.5 * the distance to the furthest point of the point cloud w.r.t. to the center
        max_dist = np.max(dist_to_center)
        cylinder_radius = max_dist * 0.5
        within_cylinder_mask = dist_to_center <= cylinder_radius # Logical indices of points within the cylinder
        new_pc = init_pc[within_cylinder_mask] # Point cloud of points within the cylinder
        if type(init_pc) == laspy.LasData:
            n_points = len(new_pc.xyz)
            pc_xyz = new_pc.xyz
        else:
            n_points = len(new_pc)
            pc_xyz = new_pc
        if n_points > 0:
            # Remove gaps from the point cloud. If no gap is found, no points are removed (shocking)
            pc_no_gaps, gap_locs = _find_gaps(new_pc, pc_xyz, gap_max, gap_min)
            if type(pc_no_gaps) == laspy.LasData:
                pc_xyz = pc_no_gaps.xyz
            else:
                pc_xyz = pc_no_gaps
            # Use data augmentation to fill possible gaps in data
            augmented_pc = _augment_data(pc_no_gaps, pc_xyz, gap_locs)
            refined_data[i] = augmented_pc
        else:
            refined_data[i] = new_pc
    
    return refined_data


"""
Augment data to the given point cloud in places where gaps have been detected

------
Input:
    pc              -   point cloud object
    pc_xyz          -   array of point cloud xyz coordinates
    gap_locs        -   locations of gaps in the point cloud, outpu of _find_gaps()
-------
Output:
    augmented_pc    -   augmented point cloud
"""
def _augment_data(pc: laspy.LasData, pc_xyz: np.ndarray, gap_locs: np.ndarray) -> laspy.LasData:
    augmented_pc = pc # Set agumented point cloud to the initial point cloud
    for gap in gap_locs:
        gap_start = gap[0]
        gap_end = gap[1]
        # Take slices of length config.AUGMENT_DIST from above and below the gap, then use those points
        # as data for creating the data augmentation sample
        slice_above = pc[(pc_xyz[:, 2] >= gap_end) & (pc_xyz[:, 2] <= (gap_end + config.AUGMENT_DIST))]
        slice_below = pc[(pc_xyz[:, 2] <= gap_start) & (pc_xyz[:, 2] >= (gap_start - config.AUGMENT_DIST))]
        dataset_pc = concat_point_clouds(slice_above, slice_below)
        # Determine required number of points (at least one)
        if type(pc) == laspy.LasData:
            point_count = len(dataset_pc.xyz)
        else:
            point_count = len(dataset_pc)
        dataset_density = point_count / (2 * config.AUGMENT_DIST)
        n_points = np.max([int(dataset_density * (gap_end - gap_start)), 1])
        # Pick n_points randomly from dataset_pc with replacement
        sample_indices = config.RNG_GEN.choice(range(point_count), size = n_points, replace = True)
        sample_pc = dataset_pc[sample_indices]
        # Generate n_points random heights between gap_start and gap_end using a uniform distribution
        sample_h = config.RNG_GEN.uniform(gap_start, gap_end, size = n_points)
        # Insert new heights into sample point cloud
        if type(pc) == laspy.LasData:
            sample_pc.Z = (sample_h / sample_pc.points.scales[2]).astype(np.int32)
        else:
            sample_pc[:, 2] = sample_h
        # Add the sample to the augmented point cloud
        augmented_pc = concat_point_clouds(augmented_pc, sample_pc)
    
    return augmented_pc


"""
Look for gaps in the given point cloud object, i.e. places, where the vertical distance between adjacent points in the
point cloud is large. The function look for two kinds of gaps, small and large. The procedure for these two types of
gaps is as follows:
    1.  Large gap: look for places where the distance from point X in the point cloud to the next lowest point
        is more than gap_max -> a gap starts from point X, thus all points above it are removed
    2.  Same as above, but look for places where the distance is more than gap_min
In case 1., we consider the points above the gap outliers (most likely part of some larger tree above the current one
and remove them from the point cloud). In case 2., we simply save the starting and ending point of the gap for data
augmentation purposes.

------
Input:
    pc              -   point cloud object from which to find the gaps
    pc_xyz          -   array of point cloud xyz coordinates
    gap_max         -   maximum distance that is not yet considered a large gap
    gap_min         -   minimum distance that is considered a small gap

-------
Output:
    pc_no_gaps      -   point cloud with gaps removed. If no gaps where found, return the original point cloud
    gap_locs        -   array of gap locations (each entry contains the starting and ending height)
"""
def _find_gaps(pc: laspy.LasData, pc_xyz: np.ndarray, gap_max: float, gap_min: float) -> tuple([laspy.LasData, np.ndarray]):
    # z coordinates of the point cloud from highest to lowest
    dist_sorted = np.sort(pc_xyz[:, 2])
    l_gap_loc = np.inf # Location of large gap initially set to np.inf
    gap_locs = [] # Initialize a list for saving small gap locations
    for i in range((len(dist_sorted) - 1)):
        diff = dist_sorted[i + 1] - dist_sorted[i]
        if diff > gap_max:
            l_gap_loc = dist_sorted[i] # Gap found, stop search
            break
        # For smaller gaps, we save the end and start point for data augmentation purposes
        if diff > gap_min:
            gap_locs.append([dist_sorted[i], dist_sorted[i + 1]])
    # Filter out points above the large gap (if gap was found)
    pc_no_gaps = pc[pc_xyz[:, 2]  <= l_gap_loc]
    gap_locs = np.array(gap_locs).reshape(-1, 2)
    # Lastly we check whether the lowest point in the point cloud is considerably above the ground (i.e. min_h)
    # used for the layer clustering. If this is the case we add a small gap location starting from 2 meters and ending
    # at the lowest point in the point cloud
    if (dist_sorted[0] - config.MIN_H) > gap_min:
        gap_locs = np.concatenate([np.array([2, dist_sorted[0]]).reshape(-1, 2), gap_locs])
    
    return pc_no_gaps, gap_locs


"""
For a tree segment point cloud, remove points for which the location in xy direction clearly differs from the location of other
points associated with the point cloud. For best results, the outliers should be filtered for layers of the tree rather than all
at once, since a point that could be considered an outlier in xy direction in lower sections of the tree would not be considered
one in the crown section (think of crown vs stem region of a tree). Specifically the outlier detection works as follows:
    1.  Look for places where the distance from point X to the center of the point cloud is considerably
        smaller than the distance from point Y to the center, where Y is the next closest point to the center
        (considerably being outlier_thresh)
    2.  Once such point is found, we consider all points that are further from the center than X to be outliers and remove
        remove them from the point cloud

-----
Input:
    pc              -   point cloud object from which to find the gaps
    gap_max         -   maximum distance that is not yet considered a gap
    center          -   coordinates of the point cloud center (tree location)

-------
Output:
    pc_no_outliers  -   point cloud with the outlier points removed
"""
def _remove_outliers(pc: laspy.LasData, outlier_thresh: float, center: np.ndarray) -> laspy.LasData:
    # Distance to the center of the point cloud from each point
    dist = np.linalg.norm(pc.xyz[:, 0:2] - center, axis = 1)
    dist_sorted = np.sort(dist)
    gap_loc = np.inf # Distance of outliers initially set to np.inf
    # Find distance from center where the gap starts
    for i in range((len(dist_sorted) - 1)):
        diff = dist_sorted[i + 1] - dist_sorted[i]
        if diff > outlier_thresh:
            gap_loc = dist_sorted[i] # Gap found, stop search
            break
    pc_no_outliers = pc[dist  <= gap_loc]

    return pc_no_outliers


"""
Refine the tree segment point clouds, i.e. remove any clear outliers

------
Input:
    tree_pcs            -   array containing the point cloud objects of segmented trees
    locations           -   locations of the tree segments
    outlier_thresh      -   threshold for outlier points (in meters). Works as follows:
                                1.  Let X and Y be points in the point cloud and let x and y be the distances
                                    from the aforementioned points to the center (tree location) respectively.
                                2.  Let us assume that we have sorted the points based on their distance to the
                                    center and that X and Y are consecutive points in such arrangement (i.e. Y is
                                    the closest point to the center right after X)
                                3.  Now, if the difference in distances to the center between X and Y is greater
                                    than the  outlier threshold, all points that are further from the center than
                                    X are classified as outliers
    verbose             -   if true, print progress information. Default: true

-------
Output:
    refined_tree_pcs    -   array of refined tree segment point clouds
    locations           -   locations such that all locations with no points assigned to them have been removed
"""
def refine_segments(tree_pcs: np.ndarray, locations: pd.DataFrame, outlier_thresh: float, verbose: bool = True) -> np.ndarray:
    refined_tree_pcs = np.empty(len(tree_pcs), dtype = laspy.LasData)
    for i in range(len(tree_pcs)):
        if verbose:
            sys.stdout.write('\rProcessing segment %3i out of %3i' % ((i + 1), len(tree_pcs)))
            sys.stdout.flush()
        pc = tree_pcs[i]
        tree_location = locations[["line_x", "line_y"]].iloc[i].to_numpy()
        # We process the point cloud in layers of height 4 m to improve the outlier detection accuracy
        layer_start = np.min(pc.xyz[:, 2])
        layer_end = layer_start + 2
        pc_height = np.max(pc.xyz[:, 2]) # Highest point of the point cloud
        refined_pc = None
        while layer_start < pc_height:
            layer_mask = (pc.xyz[:, 2] < layer_end) | (pc.xyz[:, 2] >= layer_start)
            layer_pc = pc[layer_mask]
            refined_layer_pc = _remove_outliers(layer_pc, outlier_thresh, tree_location)
            if refined_pc == None:
                refined_pc = refined_layer_pc
            else:
                refined_pc = concat_point_clouds(refined_pc, refined_layer_pc)
            layer_start = layer_end
            layer_end += 4
        refined_tree_pcs[i] = refined_pc
    if verbose:
        print("")

    no_pc_mask = (refined_tree_pcs == None)
    locations = locations[~no_pc_mask]
    refined_tree_pcs = refined_tree_pcs[~no_pc_mask]
    
    return refined_tree_pcs, locations