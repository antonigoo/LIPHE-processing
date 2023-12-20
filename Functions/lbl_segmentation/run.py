from lbl_segmentation import config
from lbl_segmentation import voxel
from lbl_segmentation import detect
from lbl_segmentation import segment
from lbl_segmentation import data
import time
import laspy
import numpy as np

"""
Run the entire segmentation process

------
Input:
    pc                  -   point cloud object of the forest plot to segment

-------
Output:
    tree_pcs            -   point clouds of the formed tree segments
    tree_coords         -   array that contains the locations of each tree segment, such that row i contains the
                            x, y and z (height) coordinates of the tree segment at index i of tree_pcs
"""
def run(pc: laspy.LasData, verbose: bool = True):
    # We begin by removing points below 2 meters
    pc = pc[pc.z >= 2]
    if verbose:
        print("Clustering layers...")
        cluster_time = time.time()
    # Cluster layers
    clusters = detect.cluster_layers(pc, config.MIN_H, config.MAX_H)
    if verbose:
        print(f"Finish in {(time.time() - cluster_time):.3f} s")
        print("Finding local maxima...")
        maxima_time = time.time()
    # Find local maxima and add them as additional clusters
    clusters = detect.local_max_clusters(pc, clusters)
    if verbose:
        print(f"Finish in {(time.time() - maxima_time):.3f} s")
        print("Detecting trees...")
        location_time = time.time()
    # Find tree locations
    locations = detect.find_tree_locations(clusters, config.DIST_MAX, config.TREE_DIST_MIN, verbose)
    if verbose:
        print(f"Finish in {(time.time() - location_time):.3f} s")
    training_data = data.refine_training_data(locations, config.GAP_MAX, config.GAP_MIN)
    # Voxelize point cloud
    if verbose:
        print("Creating voxels...")
        voxel_time = time.time()
    voxel_space, voxel_search_list, _, voxel_img, _ = voxel.create_voxels(
        pc.xyz, config.VOXEL_RESOLUTION, return_img = True
    )
    if verbose:
        print(f"Finish in {(time.time() - voxel_time):.3f} s")
    extent = np.concatenate([np.min(pc.xyz, axis = 0), np.max(pc.xyz, axis = 0)]).reshape(2, 3)
    if verbose:
        print("Forming tree segments...")
        segment_time = time.time()
    tree_pcs = segment.segment_trees_voxelized(
        training_data, voxel_img.shape[0], config.VOXEL_RESOLUTION, extent, voxel_space, voxel_search_list, pc, verbose
    )
    if verbose:
        print(f"Finish in {(time.time() - segment_time):.3f} s")
    # Remove those locations with no point cloud associated with them
    no_pc_mask = (tree_pcs == None)
    locations = locations[~no_pc_mask]
    tree_pcs = tree_pcs[~no_pc_mask]
    # Refine segments
    if verbose:
        print("Refining tree segments...")
        refine_time = time.time()
    tree_pcs, locations = data.refine_segments(tree_pcs, locations, 0.3, verbose)
    if verbose:
        print(f"Finish in {(time.time() - refine_time):.3f} s")
    heights = np.empty(len(locations), dtype = float)
    for i in range(0, len(tree_pcs)):
        heights[i] = np.max(tree_pcs[i].xyz[:, 2])
    tree_coords = np.concatenate([
        locations["line_x"].to_numpy().reshape(-1, 1),
        locations["line_y"].to_numpy().reshape(-1, 1),
        heights.reshape(-1, 1)
    ], axis = 1)

    return tree_pcs, tree_coords