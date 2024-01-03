import sys
import os

# load user configurations from external file
import yaml

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open("user_config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# add functions to path
# os.chdir(config["function_path"])
sys.path.append(os.path.join(config["function_path"], "Functions"))

# custom packages
import ReadLaz
import Processing
import WriteLaz


# other python libraries
import numpy as np
import pandas as pd
import glob
from scipy.interpolate import griddata

input_las_dir = f"{snakemake.wildcards.BASE_PATH}/output/single_trees/"
output_dir = f"{snakemake.wildcards.BASE_PATH}/output/single_trees_normalized_to_ground/"
input_files_list = glob.glob(input_las_dir + "/*.laz")

# Load stem map
df = pd.read_excel(config["tree_map"])
stem_map = df.rename(
    columns={
        "TREE_ID": "ID",
        "E": "x_stem",
        "N": "y_stem",
        "H": "z_stem",
        "Species": "species",
    }
)

# Defining offset - global coordinate system
offsets_norm = np.array([357676.852, 6860035.171, 0], dtype=np.float32)

# needed for storing
offsets_local = np.zeros((3), dtype=np.float32)

for i, input_file in enumerate(input_files_list):
    # I guess tree_id == the number at the end of the filename of single tree las
    tree_id = int(
        os.path.basename(input_file).rsplit(".", 1)[0].split("_")[-1]
    )

    las_content = ReadLaz.ReadLaz(input_file, config["DLLPATH"])

    # Add extrabytes
    extra_bytes_names = ["Reflectance", "Deviation", "Range", "Theta", "Phi"]
    extra_bytes_array = Processing.add_extra_bytes(las_content, extra_bytes_names)

    DTM = ReadLaz.ReadLaz(config["DTM_NAME"], config["DLLPATH"])

    # If the min height is unkown it can be searched in the DTM
    x_stem = stem_map[stem_map.ID == tree_id].x_stem
    y_stem = stem_map[stem_map.ID == tree_id].y_stem
    offsets_norm[2] = griddata(
        (DTM.x, DTM.y), DTM.z, (x_stem, y_stem), method="nearest"
    )

    tree, extra_tree = Processing.Ground_Normalize(
        las_content,
        offsets=offsets_norm,
        th=config["threshold"],
        Extra=extra_bytes_array,
        ExtraBytes_name=extra_bytes_names,
    )

    # Files already have tree_id in the end, as we add them in the 04 step. 
    # We should just save the same file, but in different directory
    # Warning! This will not work if the directory does not exist!
    output_las_filename = (
        output_dir + os.path.split(input_file)[-1]
    )

    # Write single tree pointcloud to file
    class MainContent:
        x = tree.x
        y = tree.y
        z = tree.z
        return_number = tree.return_number
        number_of_returns = tree.number_of_returns
        intensity = tree.intensity
        ExtraBytes_name = extra_bytes_names

    WriteLaz.WriteLaz(
        output_las_filename, config["DLLPATH"], MainContent, offsets_local, extra_tree
    )
