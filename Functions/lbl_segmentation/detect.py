from lbl_segmentation import config
from lbl_segmentation import local_maxima
import sys
import laspy
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from joblib import Parallel, delayed, parallel_backend
# Imports from other directories
sys.path.append('../utilities')
from utilities.sliding_params import get_DBSCAN_params, get_cluster_min

"""
Cut the given point cloud into layers between the given heights and and run DBSCAN for each layer

------
Input:
    pc              -   point cloud of a forest plot
    min_h           -   minimum height (in meters), i.e. lower bound of lowest layer. Default: 2
    max_h           -   maximum height (in meters), i.e. upper bound for the highest layer that is clustered. Default: 15
    parallel        -   if true, use parallel computing in sections where it's possible

-------
Output:
    layers          -   pandas dataframe of clusters containing the following information
                            * index of the layer the cluster is from
                            * cluster center coordinates
                            * cluster radius
                            *  xyz coordinates of each point in the cluster
"""
def cluster_layers(pc: laspy.lasdata.LasData, min_h: float = 2, max_h: float = 15, parallel: bool = True) -> pd.DataFrame:

    h = min_h
    layer_points = [] # List of the xyz coordinates of points in each layer
    cluster_params = [] # DBSCAN parameters of each layer
    n_layers = 0 # Number of layers to cluster
    # Begin by computing the boundaries of each layer and creating masks for points that belong to them
    while h <= max_h:
        layer_h, eps, min_samples = get_DBSCAN_params(h) # Clustering parameters for current layer
        upper_h = round(h + layer_h, 1)
        mask = (pc.xyz[:, 2] < upper_h) & (pc.xyz[:, 2] >= h) # Logical indices of points in the layer
        # While no points in current layer, grow layer size if possible
        layer_xyz = pc.xyz[mask]
        while not len(layer_xyz) and upper_h <= max_h:
            upper_h = round(upper_h + layer_h, 1)
            mask = (pc.xyz[:, 2] < upper_h) & (pc.xyz[:, 2] >= h)
            layer_xyz = pc.xyz[mask]
        if not len(layer_xyz):
            break # If no points in current layer, break
        n_layers += 1
        # Append results to list
        layer_points.append(layer_xyz)
        cluster_params.append((eps, min_samples))
        h = upper_h

    layer_centers_x = [None] * n_layers # x coordinate of each cluster center in each layer
    layer_centers_y = [None] * n_layers # y ^
    layer_radii = [None] * n_layers # Radii of clusters in each layer. Computed by fitting a circle around the cluster
    layer_clusters = [None] * n_layers # Points in each cluster in each layer (xyz coordinates)
    layer_indices = [None] * n_layers
    
    # Helper function for clustering the layers (parallelization with joblib requires using a function)
    def helper(points, eps, min_samples, i):
        # Cluster points in the current layer using DBSCAN in the xy-plane
        db = DBSCAN(eps = eps, min_samples = min_samples).fit(points[:, 0:2])
        unq_labels = list(set(db.labels_)) # List of unique labels in the layer
        # Remove noise label if it exists
        try:
            unq_labels.remove(-1)
        except ValueError:
            pass
        # Compute cluster center points by taking the mean of points in the cluster
        n_clusters = len(unq_labels)
        centers_x = [None] * n_clusters
        centers_y = [None] * n_clusters
        radii = [None] * n_clusters
        cluster_xyz = [None] * n_clusters
        for l, j in zip(unq_labels, range(n_clusters)):
            cluster_mask = db.labels_ == l
            cluster_points = points[cluster_mask]
            if len(cluster_points) == 1:
                # If cluster contains only one point, radius can not be computed, thus we remove the cluster
                n_clusters -= 1
                continue
            cluster_center = np.mean(cluster_points[:, 0:2], axis = 0)
            # Compute cluster radius by finding the smallest circle that fits all points
            dist = np.linalg.norm(cluster_points[:, 0:2] - cluster_center, axis = 1) # Distance from center to each point
            radius = np.max(dist) # Radius of circle is distance to the furthest point
            radius = np.min([radius, config.MAX_CLUSTER_RADIUS])
            centers_x[j] = cluster_center[0]
            centers_y[j] = cluster_center[1]
            radii[j] = radius
            cluster_xyz[j] = cluster_points
        
        # Remove None values from lists, if any exist
        centers_x = [x for x in centers_x if x is not None]
        centers_y = [x for x in centers_y if x is not None]
        radii = [x for x in radii if x is not None]
        cluster_xyz = [x for x in cluster_xyz if x is not None]
        ind = [i] * n_clusters
        
        return i, centers_x, centers_y, radii, cluster_xyz, ind

    if parallel:
        # Cluster layers in parallel using DBSCAN
        with parallel_backend('threading', n_jobs = config.NUM_JOBS):
            results = Parallel()(
                delayed(helper)(points, dbscan_params[0], dbscan_params[1], i) for points, dbscan_params, i in zip(
                    layer_points, cluster_params[0:n_layers], range(n_layers)
                )
            )
        # NOTE: If you are thinking: hmm..., why do it in such a janky way, just assign the results to the lists inside the
        # helper function, you would be thinking the same thing as I did initially. However, this requires passing the require = 'sharedmem'
        # argument to Parallel(), which in turn will make the program slower... Is there a better way to parallelize this program, that
        # will actually achieve significant performance improvements? Probably, I just lack the skills to program it (I wish python
        # had a simple parallel for loop like e.g. C++ and MATLAB)
        for r in results:
            i = r[0]
            layer_centers_x[i], layer_centers_y[i], layer_radii[i], layer_clusters[i], layer_indices[i] = r[1:6]
    else:
        # Cluster layers sequenatially
        for points, dbscan_params, i in zip(layer_points, cluster_params[0:n_layers], range(n_layers)):
            r = helper(points, dbscan_params[0], dbscan_params[1], i)
            layer_centers_x[i], layer_centers_y[i], layer_radii[i], layer_clusters[i], layer_indices[i] = r[1:6]


    def flatten(unflattened_list: list) -> list:
        flattened_list = [item for sublist in unflattened_list for item in sublist]
        return flattened_list

    clusters = pd.DataFrame({
        "layer_index": flatten(layer_indices), "center_x": flatten(layer_centers_x),
        "center_y": flatten(layer_centers_y), "radius": flatten(layer_radii),
        "points": flatten(layer_clusters)
    })
    clusters = clusters.loc[~pd.isnull(clusters["center_x"])]
    clusters = clusters.reset_index(drop = True)

    return clusters


"""
Find local maxima of the forest plot. A local maximum is very likely to be a tree, so we add
the positions of each local maxima as an additional cluster with the radius 0.5 m to the
clusters data frame.

------
Input:
    pc              -   point cloud of a forest plot
    clusters        -   output of cluster_layers()

-------
Output:
    clusters        -   clusters data frame with the local maxima added as additional clusters
                        on a new layer
"""
def local_max_clusters(pc: laspy.LasData, clusters: pd.DataFrame):
    # Rasterize the point clouda and smooth with a gaussian filter
    raster, _ = local_maxima.create_raster(pc, config.RESOLUTION, config.SIGMA, config.WINDOW_SIZE)
    # Find local maxima of the point cloud
    max_points, _ = local_maxima.find_local_maxima(raster, config.WINDOW_SIZE, config.MAX_POINT_DIFF, config.BACKGROUND_THRESH)
    # Unrasterize the coordinates of the local maxima
    coordinates = local_maxima.unrasterize_coordinates(max_points[:, 0:2], pc, config.RESOLUTION)
    n_maxima = len(coordinates)
    # The layer of all local maxima is set to be one above the highest layer in the clusters data frame
    layer_index = [np.max(clusters["layer_index"].to_numpy()) + 1] * n_maxima 
    # points field is filled with empty numpy arrays of shape 3
    points = [np.empty([0, 3]) for _ in range(n_maxima)]
    # radius of each local maxima is 0.5 meters
    radius = [0.5] * n_maxima
    # Create a data frame out of the local maxima
    maxima_clusters = pd.DataFrame({
        "layer_index": layer_index, "center_x": coordinates[:, 0],
        "center_y": coordinates[:, 1], "radius": radius, "points": points
    })
    maxima_clusters.index += (np.max(clusters.index) + 1)
    # Add clusters representing the local maxima to the list of clusters.
    clusters = pd.concat([clusters, maxima_clusters])

    return clusters


"""
Find the locations of trees by vertical line fitting.

------
Input:
    clusters        -   output of local_max_clusters()
    dist_max        -   maximum distance between a cluster center and vertical line such that the cluster
                        can still be assigned to the line. (unit is distance / radius of cluster)
    tree_dist_min   -   minimum distance between two tree locations. Trees closer than this are merged
    verbose         -   if true, print progress information. Default: true

"""
def find_tree_locations(clusters: pd.DataFrame, dist_max: float, tree_dist_min: float, verbose: bool = True) -> pd.DataFrame:
    # Fit vertical lines to the clusters
    lines = _fit_vert_line(clusters, dist_max, tree_dist_min, verbose)
    # Refit clusters to vertical lines and compute new locations of the lines. Clusters are split as necessary
    refitted_lines = _refit_clusters(clusters, lines, config.REFIT_DIST_MAX, verbose)
    #return locations
    return refitted_lines


"""
Find clusters that are close enough to a vertical line when stacked

------
Input:
    clusters        -   output of local_max_clusters()
    dist_max        -   see input of find_tree_locations()
    tree_dist_min   -   ^
    verbose         -   ^
-------
Output:
    lines           -   pandas dataframe of fitted veritcal lines, contains the following information:
                            * location of fitted vertical lines in the xy-plane
                            * (dataframe) indices of clusters assigned to each line
"""
def _fit_vert_line(clusters: pd.DataFrame, dist_max: float, tree_dist_min: float, verbose: bool) -> pd.DataFrame:
    # Logical indices that indicate which clusters have not yet been assigned to a vertical line.
    # We set the index to be the same as the clusters dataframe
    cluster_mask = pd.Series(np.ones(len(clusters), dtype = bool), index = clusters.index)
    vert_lines_x = [] # x coordinates of fitted vertical lines
    vert_lines_y = [] # y ^
    cluster_indices = [] # Dataframe indices of clusters assigned to each vertical line
    all_centers = clusters[["center_x", "center_y"]].to_numpy().astype(np.float64) # All cluster centers as a numpy array
    all_radii = clusters["radius"].to_numpy().astype(np.float64) # All cluster radii as a numpy array
    # Matrix of distances between the cluster centers, such that row i contains the distance from cluster center i to cluster
    # center j at index j
    dist = np.sqrt(
        np.power(all_centers[:, 0] - all_centers[:, 0].T[:, np.newaxis], 2) + 
        np.power(all_centers[:, 1] - all_centers[:, 1].T[:, np.newaxis], 2)
    )
    # Divide distances by cluster radii
    dist = dist / all_radii.T

    if verbose:
        print("Fitting vertical lines...")
    counter = 0
    while True:
        unassigned_clusters = clusters[cluster_mask]
        centers = unassigned_clusters[["center_x", "center_y"]].to_numpy().astype(np.float64) # Cluster centers of unassigned clusters
        radii = unassigned_clusters["radius"].to_numpy().astype(np.float64) # Cluster radii of unassigned clusters
        layer_indices = unassigned_clusters["layer_index"].to_numpy().astype(np.int64) # Layer that each cluster belongs to
        unq_layers = np.unique(layer_indices)
        # Distances between unassigned clusters
        active_dist = dist[cluster_mask][:, cluster_mask]
        # From each layer, only the cluster closest to the vertical line candidate should be considered. As such, we set
        # the distance from other clusters to dist_max + 1 in the dist matrix -> such clusters will not be assigned to the vertical line
        for l in unq_layers:
            current_layer_mask = layer_indices == l # Logical indices pointing to clusters in layer l
            current_layer_indices = np.nonzero(current_layer_mask)[0] # ^ as integer indices
            current_layer_dist = active_dist[:, current_layer_mask] # Matrix of distances in the current layer
            min_dist_indices = np.argmin(current_layer_dist, axis = 1) # Indices of minimum distances from each row
            # Map minimum indices to indices of the dist matrix
            min_dist_indices = np.array(list(map(lambda i: current_layer_indices[i], min_dist_indices)))
            dist_mask = np.tile(current_layer_mask, (len(current_layer_mask), 1)) # Mask matrix for the distance matrix
            # Remove minimum distances from the mask matrix
            np.put_along_axis(dist_mask, min_dist_indices[:, None], False, axis = 1)
            # For the clusters in the current layer that are not the closest to the vertical line candidate, set the distance to
            # dist_max -> clusters can not be assigned to the vertical line on this iteration
            active_dist[dist_mask] = dist_max + 1
        
        inlier_mask = active_dist <= dist_max # Logical indices of clusters within distance threshold
        inliers = np.sum(inlier_mask, axis = 1)
        max_inliers = np.max(inliers) # Maximum number of inliers
        if max_inliers > 0:
            max_index = np.argmax(inliers) # Index of max_inliers
            max_inlier_mask = inlier_mask[max_index, :]
            # Index of highest layer out of all clusters that were assigned to the vertical line with most inliers
            layer_num_max = np.max(layer_indices[max_inlier_mask])
            # Get minimum number of clusters that must be assigned to the current vertical line with the highest
            # number of inliers for it to be considered a tree location
            cluster_min = get_cluster_min(layer_num_max)
        else:
            cluster_min = -1

        if max_inliers >= cluster_min:
            counter += 1
            if verbose:
                sys.stdout.write('\rLines found: %3i' % counter)
                sys.stdout.flush()
            inlier_clusters = unassigned_clusters[max_inlier_mask] # Clusters assigned to vertical line
            inlier_centers = centers[max_inlier_mask] # Centers of said clusters
            inlier_radii = radii[max_inlier_mask] # Radii of said clusters
            inlier_clusters_index = inlier_clusters.index
            # Location of vertical line in xy-plane is the weighted mean of cluster centers
            loc_x = np.sum(inlier_centers[:, 0] * np.power(inlier_radii, -2)) / np.sum(np.power(inlier_radii, -2))
            loc_y = np.sum(inlier_centers[:, 1] * np.power(inlier_radii, -2)) / np.sum(np.power(inlier_radii, -2))
            # We set the status of clusters that were assigned to this vertical line as False. (Easy to achieve,
            # since the clusters dataframe and cluster_mask series share the same index)
            cluster_mask[inlier_clusters_index] = False

            # Distance from found line to all other lines
            dist_lines = np.linalg.norm(np.column_stack([vert_lines_x, vert_lines_y]) - [loc_x, loc_y], axis = 1)
            # Fuse tree locations that are less than tree_dist_min meters apart
            try:
                # np.argmin only works for nonempty arrays, so we call it inside try, except block to prevent errors
                closest_line_ind = np.argmin(dist_lines)
                fuse_counter = 0 # Number of lines fused with current line
                # Fuse closest line with current line, until closest line is at least tree_dist_min meters away
                while dist_lines[closest_line_ind] < tree_dist_min:
                    # Location of new line is the mean of locations of the fused lines
                    loc_x = np.mean([loc_x, vert_lines_x[closest_line_ind]])
                    loc_y = np.mean([loc_y, vert_lines_y[closest_line_ind]])
                    # Combine indices of current line and fused line
                    inlier_clusters_index = pd.Index(np.concatenate([inlier_clusters_index, cluster_indices[closest_line_ind]]))
                    # Remove lines that are fused with current line from the list of found lines
                    del vert_lines_x[closest_line_ind]
                    del vert_lines_y[closest_line_ind]
                    del cluster_indices[closest_line_ind]
                    fuse_counter += 1
                    # Compute new distances and index of closest line
                    dist_lines = np.linalg.norm(np.column_stack([vert_lines_x, vert_lines_y]) - [loc_x, loc_y], axis = 1)
                    closest_line_ind = np.argmin(dist_lines)

                counter -= fuse_counter
            except ValueError:
                pass

            # Append results to list
            vert_lines_x.append(loc_x)
            vert_lines_y.append(loc_y)
            cluster_indices.append(inlier_clusters.index)
        elif max_inliers < config.ABS_MIN_CLUSTERS:
            break # No more vertical lines can be found
        else:
            # Remove clusters assigned to current line from the list of available clusters, then continue, as it's
            # still possible to find a line with more than ABS_MIN_CLUSTERS clusters assigned to it
            inlier_clusters = unassigned_clusters[max_inlier_mask]
            inlier_clusters_index = inlier_clusters.index
            cluster_mask[inlier_clusters_index] = False
        # If no more clusters left, break loop
        if np.all(~cluster_mask):
            break

    if verbose:
        print("") # Empty print statement to exit the updating line counter print

    # Return results of line fitting as a dataframe
    lines = pd.DataFrame({
        "line_x" : vert_lines_x, "line_y": vert_lines_y, "cluster_indices": cluster_indices
    })

    return lines


"""
For each line, assign all clusters that are at most refit_dist_max units away from it to the line.
Then, for each cluster that was assigned to multiple lines, split the clusters by assigning each
point in the cluster to the line it's the closest to.

------
Input:
    clusters        -   output of local_max_clusters()
    lines           -   output of fit_vert_lines()
    refit_dist_max  -   maximum distance between a cluster center and vertical line such that the cluster
                        can still be assigned to the line.
    tree_dist_min   -   
    verbose         -   if true, print progress info. Default: true

-------
Output:
    refitted_lines  -   pandas data frame with the following information for each line:
                            1.  line coordinates (xy)
                            2.  points assigned to the line within a certain radius
"""
def _refit_clusters(clusters: pd.DataFrame, lines: pd.DataFrame, refit_dist_max: float, verbose: bool = True):
    # We compute the distances from each cluster to each line. In the matrix row i index j contains the (Eculidian)
    # distance from cluster j to line i
    dist = np.sqrt(
        np.power(lines["line_x"].to_numpy().T[:, np.newaxis] - clusters["center_x"].to_numpy(), 2) +
        np.power(lines["line_y"].to_numpy().T[:, np.newaxis] - clusters["center_y"].to_numpy(), 2)
    )
     # Divide distances by cluster radii
    dist = dist / clusters["radius"].to_numpy()
    # Clusters that are close enough to a line to be assigned to it
    inlier_mask = dist <= refit_dist_max
    # Indices of matched lines and clusters such that the first column contains the index of the line and the second column
    # contains the index of the cluster that was matched to it
    matched_clusters = np.argwhere(inlier_mask)
    # Initialize lists for clusters with only a single match and clusters with multiple matches
    # In the list that contains the clusters with only a single match, index i contains all the points that w
    single_clusters = []
    clusters_to_split = [] # Tuples where first element is line indices and second the cluster index
    n_split_clusters = 0 # Number of clusters after splitting (if only counting clusters that are split)
    # Loop through all clusters and check which were assigned to more than one line
    for i in range(len(clusters.index)):
        # Indices of lines that were matched to cluster i
        match_ind = np.nonzero(matched_clusters[:, 1] == i)[0]
        n_matches = len(match_ind)
        if n_matches > 1:
            clusters_to_split.append((matched_clusters[match_ind, 0], i))
            n_split_clusters += n_matches
        elif n_matches == 1:
            single_clusters.append(matched_clusters[match_ind[0], :])
    single_clusters = np.array(single_clusters) # Transform into numpy array

    # Dataframe for saving the split clusters
    split_clusters = pd.DataFrame(columns = clusters.columns)
    # Array for saving the match indices of split clusters
    matched_split_clusters = np.empty([0, 2], dtype = np.int64)
    # The index of the next new cluster
    new_clusters_next_ind = np.max(clusters.index) + 1

    if verbose:
        print("Splitting clusters...")
        counter = 0
    
    # Split the clusters that were assigned to more than one line simultaneously
    for line_ind, cluster_ind in clusters_to_split:
        if verbose:
            counter += 1
            sys.stdout.write('\rProcessing cluster %4i out of %4i' % (counter, len(clusters_to_split)))
            sys.stdout.flush()
        n_lines = len(line_ind) # Number of lines matched to current cluster
        # x and y coordinates of the lines
        loc_x = lines["line_x"].loc[line_ind].to_numpy()
        loc_y = lines["line_y"].loc[line_ind].to_numpy()
        # Compute the distance from each point of the cluster to each line location (Euclidian distance in the xy plane)
        cluster_xyz = clusters["points"].loc[cluster_ind]
        dist_to_points = np.sqrt(
            np.power(cluster_xyz[:, 0].T[:, np.newaxis] - loc_x, 2) + 
            np.power(cluster_xyz[:, 1].T[:, np.newaxis] - loc_y, 2)
        )
        # Divide distances by cluster radius
        dist_to_points = dist_to_points / clusters["radius"].loc[cluster_ind]
        # For each point, find the index of the line it's closest to
        closest_line_ind = np.argmin(dist_to_points, axis = 1)
        # List for saving the points in each new cluster
        new_cluster_points = [None] * n_lines
        new_cluster_centers_x = [None] * n_lines
        new_cluster_centers_y = [None] * n_lines
        new_cluster_radii = [None] * n_lines
        new_cluster_ind = [None] * n_lines
        new_cluster_layer_ind = [clusters["layer_index"].loc[cluster_ind]] * n_lines
        # Loop through all lines and save the points in the new clusters. Furthermore, calculate all necessary cluster
        # metrics, namely center coordinates and radius
        for i in range(n_lines):
            line_points_mask = closest_line_ind == i
            line_points = cluster_xyz[line_points_mask]
            if len(line_points) == 0: # No points assigned to current line
                # Number of deleted lines
                n_del = n_lines - len(line_ind)
                # Delete line from line indices associated with the new clusters                
                line_ind = np.delete(line_ind, i - n_del)
                continue
            new_center = np.mean(line_points[:, 0:2], axis = 0)
            # Compute cluster radius by finding the smallest circle that fits all points
            dist = np.linalg.norm(line_points[:, 0:2] - new_center, axis = 1) # Distance from center to each point
            radius = np.max(dist) # Radius of circle is distance to the furthest point
            radius = np.min([radius, 2.5]) # Radius is at most 2.5 meters
            new_cluster_points[i] = line_points
            new_cluster_centers_x[i] = new_center[0]
            new_cluster_centers_y[i] = new_center[1]
            new_cluster_radii[i] = radius
            new_cluster_ind[i] = new_clusters_next_ind
            new_clusters_next_ind += 1
        
        # Create a dataframe out of the new clusters created by splitting
        new_clusters = pd.DataFrame({
            "layer_index": new_cluster_layer_ind, "center_x": new_cluster_centers_x,
            "center_y": new_cluster_centers_y, "radius": new_cluster_radii,
            "points": new_cluster_points
        }, index = new_cluster_ind)
        # If the points array of some cluster is None, the cluster does not exist (since no points were assigned to
        # a particular line) -> remove such clusters from the data frame
        new_clusters = new_clusters[~pd.isnull(new_clusters["points"])]
        pd.concat([split_clusters, new_clusters])

        if len(line_ind) != n_lines:
            # Remove None values when necessary
            new_cluster_ind = [x for x in new_cluster_ind if x is not None]
        # Line index - cluster index pairs for the new matched cluster
        new_matched_clusters = np.concatenate([line_ind.reshape(-1, 1), np.array(new_cluster_ind).reshape(-1, 1)], axis = 1)
        np.concatenate([matched_split_clusters, new_matched_clusters])

    if verbose:
        print("")

    # Combine the data from the split clusters with the original clusters
    clusters = pd.concat([clusters, split_clusters])
    matched_clusters = np.concatenate([single_clusters, matched_split_clusters])
    n_lines = len(lines.index)
    new_line_x = np.empty(n_lines, dtype = np.float64)
    new_line_y = np.empty(n_lines, dtype = np.float64)
    new_points = [None] * n_lines

    for i in range(len(lines.index)):
        # Indices of clusters assigned to line i
        line_clusters_ind = matched_clusters[:, 1][np.argwhere(matched_clusters[:, 0] == i)].flatten()
        # If no clusters were assigned only to this current line and no points were assigned to the line when splitting
        # clusters, it can happen that no points are associated with the current line. In such case, the line is skipped
        # and removed later on
        if len(line_clusters_ind) == 0:
            continue
        # Extract correct rows from the data frame
        line_clusters = clusters.loc[line_clusters_ind]
        # New location of the line is a weighted mean of the cluster centers
        line_radii = line_clusters["radius"].to_numpy() # Radii of all clusters assigned to the line
        loc_x = np.sum(line_clusters["center_x"].to_numpy() * np.power(line_radii, -2)) / np.sum(np.power(line_radii, -2))
        loc_y = np.sum(line_clusters["center_y"].to_numpy() * np.power(line_radii, -2)) / np.sum(np.power(line_radii, -2))
        # Logical indices pointing to clusters that are smaller than the max cluster radius
        small_clusters_mask = line_radii < config.MAX_CLUSTER_RADIUS
        # Concatenate all points from all small clusters assigned to the line, if any exist
        if np.any(small_clusters_mask):
            line_points = np.concatenate(line_clusters.loc[small_clusters_mask]["points"].to_list())
        else:
            line_points = np.empty([0, 3])
        # For large clusters (radius == MAX_CLUSTER RADIUS), we only extract points that
        # are within MAX_CLUSTER_RADIUS meters of the tree location. This is done because large
        # clusters will almost always contain points from multiple trees, which would
        # result in a large number of points from the adjacent trees being assigned to the
        # the wrong tree in later stages of the segmentation process
        large_clusters = line_clusters.loc[line_radii == config.MAX_CLUSTER_RADIUS]["points"].to_list()
        large_cluster_points = np.empty([0, 3])
        for c in large_clusters:
            c_dist = np.linalg.norm(c[:, 0:2] - [loc_x, loc_y], axis = 1)
            c_mask = c_dist <= config.MAX_CLUSTER_RADIUS
            c_points = c[c_mask]
            large_cluster_points = np.concatenate([large_cluster_points, c_points])
        line_points = np.concatenate([line_points, large_cluster_points])
        # Add results to array
        new_line_x[i] = loc_x
        new_line_y[i] = loc_y
        # Save points, if any are within range
        if line_points.shape[0] > 0:
            new_points[i] = line_points

    # Create a data frame out of the new line locations and cluster points assigned to them
    refitted_lines = pd.DataFrame({
        "line_x": new_line_x, "line_y": new_line_y, "points": new_points
    })
    # Lines where coordinates are null were discarded because no points within MAX_CLUSTER_RADIUS were assigned to them,
    # delete such lines
    refitted_lines = refitted_lines[~pd.isnull(refitted_lines["points"])]
    refitted_lines = refitted_lines.reset_index(drop = True)
    
    return refitted_lines