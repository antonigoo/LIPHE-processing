from lbl_segmentation import config
from lbl_segmentation import voxel
import sys
import laspy
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier

"""
Segment trees using a KNN classifier. The points of the clusters assigned to each tree location
are used as training data. To speed up the segmentation process, the point cloud and training
data are voxelized.

------
Input:
    training_data       -   list that contains all points associated with tree i as a 3d numpy array
                            at index i
    n_voxel_layers      -   number of "layers" in the voxelized point cloud, i.e. number of voxels
                            in the z-direction
    resolution          -   resolution of voxel_space
    extent              -   extent of voxel_space
    voxel_space         -   voxelized point cloud, output of create_voxels()
    voxel_search_list   -   array of indices for extracting original points from the voxels, output
                            create_voxels()
    pc                  -   original forest plot point cloud
    verbose             -   if true, print progress info. Default: true
"""
def segment_trees_voxelized(
    training_data: pd.DataFrame, n_voxel_layers: int, resolution, extent: np.ndarray, voxel_space: np.ndarray,
    voxel_search_list: np.ndarray, pc: laspy.LasData, verbose: bool = True
):
    n_trees = len(training_data) # Number of trees in the training data
    # Initialize empty arrays for training data
    training_labels = np.array([], dtype = np.int32)
    training_points = np.array([], dtype = float).reshape(0, 3)
    # Loop through each location point cloud and voxelize it
    for i in range(n_trees):
        loc_voxel_space, _, _ = voxel.create_voxels(training_data[i], resolution, extent)
        # Create training data for the KNN classifier out of the full voxels 
        full_voxel_ind = loc_voxel_space[:, 1:4]
        training_points = np.concatenate([training_points, full_voxel_ind])
        training_labels = np.concatenate([training_labels, np.full(len(full_voxel_ind), i)])
    
    knn = KNeighborsClassifier(n_neighbors = config.N_NEIGHBORS, weights = 'distance', n_jobs = config.NUM_JOBS).fit(training_points, training_labels)
    # List for saving the voxel ids of voxels assigned to each label. Index i of the list contains
    # the ids of all voxels assigned to tree i of the training data
    tree_voxel_ids = [[] for _ in range(n_trees)]
    # Loop through all voxel layers
    for k in range(n_voxel_layers):
        if verbose:
            sys.stdout.write('\rProcessing layer %3i out of %3i' % ((k + 1), n_voxel_layers))
            sys.stdout.flush()
        # Choose voxels in current layer
        layer_voxel_space = voxel_space[voxel_space[:, 3] == k]
        layer_voxels = layer_voxel_space[:, 1:4] # Xyz coordinates of the points
        if layer_voxels.shape[0] == 0:
            # No voxels with points in current layer
            continue
        # For each voxel in this layer predict the probability that it belongs to each tree segment
        labels = knn.predict_proba(layer_voxels)
        unq_labels = list(range(n_trees))

        for l in unq_labels:
            label_probs = labels[:, l]
            # If the probability that a voxel belongs to a certain tree is high enough, assign
            # the voxel to that tree and save the id. Note that this means that voxels for which
            # the label can not determined with a high enough probability are discarded
            label_mask = (label_probs >= config.MIN_PROB).flatten()
            label_voxel_ids = layer_voxel_space[label_mask, 0].tolist()
            tree_voxel_ids[l].extend(label_voxel_ids)
            training_points = np.concatenate([training_points, layer_voxels[label_mask]])
            training_labels = np.concatenate([training_labels, np.full(len(layer_voxels[label_mask]), l)])

        # Retrain model with the new data (results of this layer conacatenated to old training data)
        knn = KNeighborsClassifier(n_neighbors = config.N_NEIGHBORS, weights = 'distance', n_jobs = config.NUM_JOBS).fit(training_points, training_labels)
    if verbose:
        print("")
        print("Extracting point clouds from voxels...")

    tree_pcs = np.empty(n_trees, dtype = laspy.LasData)
    # Extract tree segment point clouds from voxels
    for l in range(n_trees):
        if verbose:
            sys.stdout.write('\rProcessing segment %3i out of %3i' % ((l + 1), n_trees))
            sys.stdout.flush()
        # Indices of voxels with the current label
        voxel_ids = tree_voxel_ids[l]
        start_end_ind = voxel_space[np.isin(voxel_space[:, 0], voxel_ids), 5:7]
        pc_ind = []
        for start, end in start_end_ind:
            pc_ind.extend(list(voxel_search_list[start:(end + 1), 1]))
        # Get the point cloud corresponding to the current label
        tree = pc[pc_ind]
        # Add to point cloud array if the point cloud contains at least one point
        if len(tree) > 0:
            tree_pcs[l] = tree
    if verbose:
        print("")

    return tree_pcs