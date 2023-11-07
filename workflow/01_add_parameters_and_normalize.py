import sys
import os
import gc

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

# There are a lot of variables in ReadLaz.ReadLaz function
# Let's make sure they are not in memory when we run more heavy stuff
gc.collect()

# Add extrabytes
extra_bytes_names = ["Reflectance", "Deviation"]

# create empty extrabytes_array based on number of extra bytes and size of already existing bytes
extra_bytes_array = np.empty(
    (len(extra_bytes_names), len(las_content.x)), dtype=np.float32
)

# fill extra bytes array with needed content
added_bytes = []
for x, name in enumerate(extra_bytes_names):
    if hasattr(las_content, name):
        extra_bytes_array[x] = getattr(las_content, name)
        added_bytes.append(name)
    else:
        print(f"Could not find {name} in your lasfile, skipping.")

print(f"Your extrabytes: {*added_bytes,}")

# Rename attributes
if hasattr(las_content, "Amplitude"):
    setattr(las_content, "Intensity", getattr(las_content, "Amplitude"))

# Compute extra bytes
# Add more extra bytes based on configuration file
extra_bytes_names = extra_bytes_names + ["Range", "Theta", "Phi"]
las_content, extra_bytes_array = Processing.COMPUTE_EXTRA_PARAMETERS(
    las_content,
    extra_bytes_array,
    config["thetaStart"],
    config["thetaStop"],
    config["thetaIncrement"],
    config["phiStart"],
    config["phiStop"],
    config["phiIncrement"],
)


# Normalize point cloud local reference system
# create class from transformation parameters in configuration file
class Transformation:
    def __init__(self, config):
        for k, v in config["transformation"].items():
            setattr(self, k, v)


x1, y1, z1 = Processing.RectifLaz(
    las_content.x, las_content.y, las_content.z, Transformation(config)
)

# Write pointcloud to file
# offset is 0 for local coordinate system
zero_offsets = np.zeros((3), dtype=np.float32)


class MainContent:
    x = x1 - zero_offsets[0]
    y = y1 - zero_offsets[1]
    z = z1 - zero_offsets[2]
    return_number = las_content.return_number
    number_of_returns = las_content.number_of_returns
    intensity = las_content.intensity
    ExtraBytes_name = extra_bytes_names


WriteLaz.WriteLaz(
    output_las_filename, config["DLLPATH"], MainContent, zero_offsets, extra_bytes_array
)
