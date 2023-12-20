import numpy as np
"""
------------------------
SEGMENTATION PARAMETERS:

Variable                |   Description
________________________|_______________________________________________________________________
                        |
NUM_JOBS                |   Number of jobs to run in parallel, when parallel computation is used. 
                        |   Note that many of the used library functions already invoke multiple
                        |   jobs by default. As such, setting this variable to the maximum number
                        |   of available cores will usually reduce performance.
________________________|_______________________________________________________________________
                        |
ABS_MIN_CLUSTERS        |   This should be set to the lowest value that the function
                        |   get_cluster_min() can return (not relative to height, just the
                        |   absolute lowest possible return value)
________________________|_______________________________________________________________________
                        |
MIN_H                   |   Lower bound of lowest layer that is clustered [1]
________________________|_______________________________________________________________________
                        |
MAX_H                   |   Upper bound for clusterd layers [1]
________________________|_______________________________________________________________________
                        |
DIST_MAX                |   Max distance from cluster center to line such that cluster is still
                        |   assigned to line [2]
________________________|_______________________________________________________________________
                        |
REFIT_DIST_MAX          |   ^ but for refitting clusters [2]
________________________|_______________________________________________________________________
                        |
TREE_DIST_MIN           |   Min distance for trees. Trees closer than this are merged [2]
________________________|_______________________________________________________________________
                        |
OUTLIER_THRESH          |   Threshold for outlier points [3]
________________________|_______________________________________________________________________
                        |
GAP_MAX                 |   The maximum gap length allowed, when refining training data for
                        |   segmentation purposes (z-direction) [4]
________________________|_______________________________________________________________________
                        |
GAP_MIN                 |   Minimum gap length for which data augmentation is performed when
                        |   refining training data (z-direction) [4]
________________________|_______________________________________________________________________
                        |
MAX_CLUSTER_RADIUS      |   Maximum radius of a DBSCAN cluster. For clusters larger than this,
                        |   the radius is set to this value [1]
________________________|_______________________________________________________________________
                        |
MIN_PROB                |   Minimum required probability for a voxel to be assigned to some tree
                        |   label when using fuzzy knn classifier. If no label has this
                        |   probability or higher, the voxel is discarded [5]
________________________|_______________________________________________________________________
                        |
VOXEL_RESOLUTION        |   Size of voxel in meters
________________________|_______________________________________________________________________
                        |
RESOLUTION              |   Resolution of the raster created during the tree segmentation
                        |   process. (pixel size RESOLUTION x RESOLUTION meters) [6, 8]
________________________|_______________________________________________________________________
                        |
SIGMA                   |   Value of the standard deviation used for gaussian filtering the
                        |   rasterized point cloud [6]
________________________|_______________________________________________________________________
                        |
WINDOW_SIZE             |   Window size used for applying various filters to the rasterized point
                        |   cloud, e.g. the raster is smoothed with a gaussian filter of this
                        |   size when seeking local maxima (WINDOW_SIZE x WINDOW_SIZE pixels)
                        |   !!! Note that this must be an odd number for the algorithm to
                        |       function correctly !!! [6, 7]
________________________|_______________________________________________________________________
                        |
MAX_POINT_DIFF          |   Threshold for value for determining whether a point is a local
                        |   maxima from a maximum filtered raster. If the absolute value of the
                        |   difference between the value from the original raster and the value
                        |   from a filtered raster is less than MAXPOINT_THRESH, the value is
                        |   is a local maxima [7]
________________________|_______________________________________________________________________
                        |
BACKGROUND_THRESH       |   Points below this height (in meters) are considered background, thus
                        |   local maxima of this height or lower are disregarded [7]
________________________|_______________________________________________________________________
                        |
N_NEIGHBORS             |   Value of k passed to the FkNN classifier when performing
                        |   segmentation [5]
________________________|_______________________________________________________________________
                        |
AUGMENT_DIST            |   When doing data augmentation, the sample from which we augment is
                        |   created by taking a slice of length AUGMENT_DIST from above and
                        |   below the gap which we intend to fill with data augmentation [3]
________________________|_______________________________________________________________________
                        |
RNG_GEN                 |   Numpy random generator object used for all things random and numpy
                        |   [3]

------------------------------------------------------------------------------------
For more information on the parameters, see comments of the corresponding functions:

[1] detect.cluster_layers()
[2] detect.find_tree_locations()
[3] data.refine_segments()
[4] data.refine_training_data()
[5] segment.segment_trees_voxelized()
[6] local_maxima.create_raster()
[7] local_maxima.find_local_maxima()
[8] local_maxima.unrasterize_coordinates()
"""

NUM_JOBS = 4
ABS_MIN_CLUSTERS = 5
MIN_H = 0
MAX_H = 15
DIST_MAX = 0.5
REFIT_DIST_MAX = 0.75
TREE_DIST_MIN = 0.5
OUTLIER_THRESH = 0.2
GAP_MAX = 1
GAP_MIN = 0.3
MAX_CLUSTER_RADIUS = 2.5
MIN_PROB = 0.9
VOXEL_RESOLUTION = 0.1
RESOLUTION = 0.3
SIGMA = 0.7
WINDOW_SIZE = 5
MAX_POINT_DIFF = 0.0001
BACKGROUND_THRESH = 2
N_NEIGHBORS = 7
AUGMENT_DIST = 0.4
RNG_GEN = np.random.default_rng(seed = 33)