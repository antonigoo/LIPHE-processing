import sys
import os

# load user configurations from external file
import yaml

with open("user_config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# add functions to path
os.chdir(config["function_path"])
sys.path.append(os.path.join(config["function_path"], "Functions"))

# custom packages
import ReadLaz
import Processing
import WriteLaz


# other python libraries
import numpy as np


input_las_filename = sys.argv[1]
output_las_filename = sys.argv[2]

las_content = ReadLaz.ReadLaz(input_las_filename, config["DLLPATH"])

# Add extrabytes
extra_bytes_names = ["Reflectance", "Deviation", "Deviation", "Range", "Theta", "Phi"]
extra_bytes_array = Processing.add_extra_bytes(las_content, extra_bytes_names)

## spatial resample
spatial_resample, extra_resample = Processing.Spatial_sample(
    las_content,
    useroption="neighbour",
    pts_min=1,
    vs=0.01,
    npoints=1,
    EXTRA=extra_bytes_array,
    ExtraBytes_name=extra_bytes_names,
    n_jobs=1,
)

# Write pointcloud to file
# Defining offset - Local coordinate system
offsets = np.array([357676.852, 6860035.171, 0], dtype=np.float32)

class MainContent:
    x = spatial_resample.x - offsets[0]
    y = spatial_resample.y - offsets[1]
    z = spatial_resample.z - offsets[2]
    return_number = spatial_resample.return_number
    number_of_returns = spatial_resample.number_of_returns
    intensity = spatial_resample.intensity
    ExtraBytes_name = extra_bytes_names

WriteLaz.WriteLaz(
    output_las_filename, config["DLLPATH"], MainContent, offsets, extra_resample
)
