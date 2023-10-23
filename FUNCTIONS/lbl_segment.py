import config
import time
import argparse
import laspy
import numpy as np
from lbl_segmentation.run import run
from utilities import util
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

"""
Perform the entire segmentation process from start to finish for the tree with the given id.
Parameters of the different segmentation phases can be altered in lbl_segmentation/config.py.

------
Input:
    tree_id         -   id of the tree to segment (positive integer)
    x_offset        -   x offset applied to the point cloud before matching segment location to reference 
                        data. Default: 0
    y_offset        -   y ^
    verbose         -   If true, display information about the segmentation process while it's ongoing.
                        Default: False
    write_other     -   If true, write also the identified segments that could not be matched to reference
                        data. Default: False
    skip_matching   -   If true, skip matching segments to reference data. If this is set to true, write_other
                        will be forced to true automatically, regardless of the value supplied for it. (This is
                        because otherwise the algorithm does nothing at all). Default: False

"""
def lbl_segment(
    tree_id: int, x_offset: float = 0, y_offset: float = 0, verbose: bool = False, write_other = False, skip_matching = False
) -> None:
    if skip_matching and not write_other:
        write_other = True
        print("WARNING: skip_matching set to True, forcing write_other to True")
    if verbose:
        start_txt = f"Segmenting tree {tree_id}"
        print("-" * len(start_txt))
        print(start_txt)
        print("-" * len(start_txt))
        total_time = time.time()
        print("Loading data...")
        data_time = time.time()

    # Read point cloud and reference data from file
    pc = laspy.read(config.PATH + config.PC_DIRECTORY + config.PC_FILENAME.format(TREEID = tree_id))
    ref_coords = util.get_ref_coords(config.PATH + config.REF_DIRECTORY + config.REF_FILENAME, tree_id)
    if not skip_matching and ref_coords.size == 0:
        print(f"No matching reference data found for tree with id {tree_id}!")
        print("If you want to perform segmentation without reference data, set skip matching to True.")
        print("Terminating...")
        return

    if verbose:
        print(f"Finish in {(time.time() - data_time):.3f} s")
        print(f"Size of point cloud: {len(pc.xyz)}")
        print(f"Starting segmentation...")

    # Perform segmentation
    tree_pcs, tree_coords = run(pc, verbose)
    # Apply offset to tree locations
    tree_coords[:, 0] += x_offset
    tree_coords[:, 1] += y_offset
    # Match tree segments with reference data and write to file
    if skip_matching:
        matches = np.array([])
    else:
        matches = util.match_locations(tree_coords, ref_coords, config.REF_DIST_MAX)
        if matches.size == 0:
            # Alert the user if no segment matches the reference tree
            print("WARNING: no matching segment found for the reference tree!")
    if verbose:
        print("Writing tree segments to separate .las files...")
        write_time = time.time()
    util.write_segments(
        tree_pcs, matches, config.PATH + config.DEST_DIRECTORY_MAIN, config.PC_FILENAME.format(TREEID = tree_id),
        config.PATH + config.DEST_DIRECTORY_OTHER.format(TREEID = tree_id), write_other, verbose
    )
    if verbose:
        print(f"Finish in {(time.time() - write_time):.3f} s")
        total_time_fin = time.time() - total_time
        end_txt = f"Segmentation of tree {tree_id} finished!"
        end_t_txt = f"Total algorithm runtime: {total_time_fin:.3f} s"
        line_len = max(len(end_txt), len(end_t_txt))
        print("-" * line_len)
        print(end_txt)
        print(end_t_txt)
        print("-" * line_len)
    

"""
Command line executable of the segmentation process

------
Options:
    -i="tree_id" or --id="tree_id"      -   set the id of the tree for which the segmentation is performed
    -r="file"    or --read="file"       -   read a list of tree ids from a file, then perform segmentation
                                            for each of them. Default file name: id_list.txt.
    -v or --verbose                     -   if set, print information during the segmentation process
    -o or --other                       -   if set, write other identified segments aside from the tree
    -x or --xoffset                     -   define the x offset applied to the point cloud when matching to
                                            reference data
    -y or --yoffset                     -   ^ for y coordinates
    -s or --skip                        -   skip matching segments to reference data. If set, will automatically
                                            set -o as well.

!!! NOTE: -i and -r are mutually exclusive options. If both are set, only -i is taken into account. 
    Furthermore, note that -r is the default option, i.e. if no options are given, the program will
    attempt to read the plot ids from a file called id_list.txt in config.PATH !!!
"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Segment trees from a point cloud")
    parser.add_argument("-i", "--id", help = "Set id of the plot to segment", default = None)
    parser.add_argument("-r", "--read", help = "Read a list of tree ids from file", default = "id_list.txt")
    parser.add_argument("-v", "--verbose", help = "Print information during the segmentation process", action = "store_true")
    parser.add_argument("-o", "--other", help = "Write other identified segments aside from the tree", action = "store_true")
    parser.add_argument("-x", "--xoffset", help = "x offset applied to the point cloud", default = 0)
    parser.add_argument("-y", "--yoffset", help = "y offset applied to the point cloud", default = 0)
    parser.add_argument("-s", "--skip", help = "Skip matching segments to reference data. If True, will automatically set -o to True as well", action = "store_true")
    args = parser.parse_args()
    argdict = vars(args)
    tree_id, filename, verbose = argdict["id"], argdict["read"], argdict["verbose"]
    write_other, x_offset, y_offset = argdict["other"], argdict["xoffset"], argdict["yoffset"]
    skip_matching = argdict["skip"]
    if tree_id == None:
        id_list = util.get_id_list(filename)
        for tree_id in id_list:
            lbl_segment(tree_id)
    else:
        raise_error = False
        try:
            tree_id = int(tree_id)
        except ValueError:
            raise_error = True
        if tree_id <= 0:
            raise_error = True
        if raise_error:    
            raise ValueError("The tree id should be a positive integer.")
        try:
            x_offset = float(x_offset)
            y_offset = float(y_offset)
        except ValueError:
            raise ValueError("The x and y offset should be floats.")
        lbl_segment(tree_id, x_offset, y_offset, verbose, write_other, skip_matching)