import time
import os
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
    path_to_pc: str,
    path_to_tree_map: str,
    tree_id: int,
    output_path_main: str,
    output_path_noise: str,
    x_offset: float = 0,
    y_offset: float = 0,
    verbose: bool = False,
    write_other: bool = False,
    skip_matching: bool = False,
    ref_dist_max: int = 2,
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
    pc = laspy.read(path_to_pc)
    ref_coords = util.get_ref_coords(path_to_tree_map, tree_id)
    if not skip_matching and ref_coords.size == 0:
        print(f"No matching reference data found for tree with id {tree_id}!")
        print(
            "If you want to perform segmentation without reference data, set skip matching to True."
        )
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
        matches = util.match_locations(tree_coords, ref_coords, ref_dist_max)
        if matches.size == 0:
            # Alert the user if no segment matches the reference tree
            print("WARNING: no matching segment found for the reference tree!")
    if verbose:
        print("Writing tree segments to separate .las files...")
        write_time = time.time()
    util.write_segments(
        tree_pcs, matches, output_path_main, os.path.basename(path_to_pc), output_path_noise, write_other, verbose
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
