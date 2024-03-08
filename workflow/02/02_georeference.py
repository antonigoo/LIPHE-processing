import sys
import os

# load user configurations from external file
import yaml

script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "user_config.yml"), "r") as f:
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
import csv


input_las_filename = sys.argv[1]
output_las_filename = sys.argv[2]

las_content = ReadLaz.ReadLaz(input_las_filename, config["DLLPATH"])

## Georeference based on ground control points

# Defining offset - Local coordinate system
offsets = np.array([357676.852, 6860035.171, 0], dtype=np.float32)

# Declaring control points or match points
# As example we had  literally declared the control points but it can easily be read from a file
# This code can also be use to register two point cloud based on know matching point betwee two clouds.
local_reference_points = []
global_reference_points = []

# Declare point in the cloud in the local reference system, X, Y, Z
with open(os.path.join(script_dir, "reference_points_local.csv"), "r") as inputfile:
    for row in csv.reader(inputfile, quoting=csv.QUOTE_NONNUMERIC):
        print(row)
        local_reference_points.extend(row)

# Declare the same points in the georef. reference system >> ETRS89-TM35FIN reference system, E, N, H
with open(os.path.join(script_dir, "reference_points_global.csv"), "r") as inputfile:
    for row in csv.reader(inputfile, quoting=csv.QUOTE_NONNUMERIC):
        print(row)
        global_reference_points.extend(row)

ReferencePoints = np.array([local_reference_points, global_reference_points], dtype=np.float32)
x1, y1, z1 = Processing.HELMERT3D(las_content, ReferencePoints)

# Add extrabytes
extra_bytes_names = ["Reflectance", "Deviation", "Deviation", "Range", "Theta", "Phi"]
extra_bytes_array = Processing.add_extra_bytes(las_content, extra_bytes_names)

# Write pointcloud to file
class MainContent:
    x = x1 - offsets[0]
    y = y1 - offsets[1]
    z = z1 - offsets[2]
    return_number = las_content.return_number
    number_of_returns = las_content.number_of_returns
    intensity = las_content.intensity
    ExtraBytes_name = extra_bytes_names

WriteLaz.WriteLaz(
    output_las_filename, config["DLLPATH"], MainContent, offsets, extra_bytes_array
)
