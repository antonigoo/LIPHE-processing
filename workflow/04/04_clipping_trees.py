#!/usr/bin/env python

import sys
import os

# load user configurations from external file
import yaml

# Add the script directory to the Python path, so the user_config can be located
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "user_config.yml"), "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


# add functions to path
sys.path.append(os.path.join(config["function_path"], "Functions"))

# custom packages
import ReadLaz
import Processing
import WriteLaz


# other python libraries
import numpy as np
import pandas as pd


input_las_filename = sys.argv[1]
output_dir = sys.argv[2]

las_content = ReadLaz.ReadLaz(input_las_filename, config["DLLPATH"])

# Add extrabytes
extra_bytes_names = ["Reflectance", "Deviation", "Deviation", "Range", "Theta", "Phi"]
extra_bytes_array = Processing.add_extra_bytes(las_content, extra_bytes_names)

# Load stem map
df = pd.read_excel(config["tree_map"])
ID = np.array(df.TREE_ID)
x_stem = np.array(df.E)
y_stem = np.array(df.N)
z_stem = np.array(df.H)
species = np.array(df.Species)
N_trees = len(x_stem)

# create cylinders around trees
BOX_COORD = []
BOX_ANGLES = []
CYLINDER = []
VORONOI = []
RAIO = np.full(
    (len(x_stem),), 2.2
)  # Define radius for the cylinder cut - 3.5 radius around the stem position
CYLINDER = np.dstack((x_stem,y_stem, z_stem, RAIO))[0]
# VORONOI = np.dstack((x_stem, y_stem, ID))

# Defining offset - global coordinate system
offsets = np.array([357676.852, 6860035.171, 0], dtype=np.float32)

for k in range(N_trees):
    # clip the tree
    tree, extra_tree = Processing.ClippingTree(
        las_content,
        BOX_COORD,
        BOX_ANGLES,
        CYLINDER[k],
        VORONOI,
        extra_bytes_array,
        extra_bytes_names,
    )
    # write the tree to file
    output_las_filename = (
        output_dir
        + os.path.split(input_las_filename)[-1].split(".")[0]
        + "_"
        + str(ID[k])
        + ".laz"
    )

    # Write single tree pointcloud to file
    class MainContent:
        x = tree.x - offsets[0]
        y = tree.y - offsets[1]
        z = tree.z - offsets[2]
        return_number = tree.return_number
        number_of_returns = tree.number_of_returns
        intensity = tree.intensity
        ExtraBytes_name = extra_bytes_names

    WriteLaz.WriteLaz(
        output_las_filename, config["DLLPATH"], MainContent, offsets, extra_tree
    )
