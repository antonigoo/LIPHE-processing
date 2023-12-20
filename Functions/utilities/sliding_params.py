"""
This module contains parameter getter functions for parameters that are dependent on some value, e.g. height
"""


"""
Return parameters used for DBSCAN clustering at the given height

------
Input:
    h               -   height in meters from the ground
 
-------
Output:
    layer_h         -   height of the next layer
    eps             -   max distance for two samples still considered to be in the
                        same neighbourhood
    min_samples     -   number of samples in a neighbourhood for a point to be considered
                        core points

!!! Note that output is returned as a tuple in the above order !!!
"""
def get_DBSCAN_params(h: float) -> tuple([int, int, int]):
    # Points are quite scarce in the lowermost regions of the point clouds, thus
    # the layers are long and min_samples is low
    if h < 6:
        layer_h, eps, min_samples = 0.8, 0.1, 12
    elif h < 10:
        layer_h, eps, min_samples = 0.6, 0.1, 16
    elif h < 25:
        layer_h, eps, min_samples = 0.4, 0.1, 10
    else:
        layer_h, eps, min_samples = 0.8, 0.3, 15

    return layer_h, eps, min_samples


"""
Return the minimum number of clusters that must be assigned to a vertical line for it to be considered a tree location,
when the highest cluster assigned to the line is on layer layer_num_max. The basic idea behind using this function for
the minimum threshold instead of some constant is the following:
    1.  Some trees can be quite low, thus they only have clusters corresponding to them on some of the lowest layers
    2.  As such, detecting these low trees is not possible without making the minimum cluster threshold quite small
    3.  Making the minimum cluster threshold small for all lines will cause the algorithm to erroneously detect trees
        that do not exist (this is a tested fact)
    4.  Making the minimum cluster threshold dependent on the highest layer circumvents the aforementioned problem, but
        improves the chances of detecting a low tree from zero to nonzero (though likely still quite difficult)

------
Input:
    layer_num_max   -   index of the highest layer of all clusters associated with some vertical line

-------
Output:
    cluster_min     -   minimum number of clusters within a vertical line such that the line is still
                        considered a tree location
"""
def get_cluster_min(layer_num_max: int) -> int:
    if layer_num_max <= 10:
        cluster_min = 5
    elif layer_num_max <= 26:
        cluster_min = 8
    else:
        # Current algorithm has at most 27 layers (index starts from 0). If parameters
        # for such layers are needed, add them here
        raise NotImplementedError("Parameter not implemented for layers above 26")
    
    return cluster_min