# -*- coding: utf-8 -*-
"""
PROGRAMMERS:

MARIANA BATISTA CAMPOS - mariana.campos@nls.fi
RESEARCHER AT FINNISH GEOSPATIAL INSTITUTE - NATIONAL LAND OF 

RAMI ECHRITI - rami.echriti@nls.fi
RESEARCHER AT FINNISH GEOSPATIAL INSTITUTE - NATIONAL LAND OF SURVEY

THIS SCRIPT IS AN PYTHON FUNCTION WHICH CALLS READ FUNCTION FROM THE DLL USING CTYPES

COPYRIGHT UNDER MIT LICENSE

Copyright (C) 2019-2020, NATIONAL LAND OF SURVEY

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

"""
EXAMPLE LIST:

EXAMPLE ONE:    Compute extra parameters (Range and Scan Angles) and Normalize the oblique point cloud 
EXAMPLE TWO:    Point cloud georeferencing 
EXAMPLE THREE:  Resample the point cloud based on a point cloud voxelization method 
EXAMPLE FOUR:   Tree segmentation from full LIPHE point cloud based on tree map and cylinder cutting
EXAMPLE FIVE:   Tree segmentation from full LIPHE point cloud based on tree map and voronoi cells cutting
EXAMPLE SIX:    Tree fine-segmentation - remove noise and neighboring trees from the cylinder cutting
EXAMPLE SEVEN:  Estimate tree parameters (e.g. tree height)
EXAMPLE EIGHT:  Tree spatial statistics (e.g. density, mean intensity value) inside a voxel.

FILE NAMES YYMMDD_hhmmss_procesingflags

"""


# %%

"""

PYTHON LIBRARY REQUIREMENTS: requirements.txt
    
"""

# FGI in-the-house functions:
import sys
import os

os.chdir(r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING")
functions = "D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\FUNCTIONS"
sys.path.append(functions)

import ReadLaz
import WriteLaz
import Processing
import numba_algorithms as na
import lbl_segment


# Other python Libraries
import os, glob, time
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import xlsxwriter
import matplotlib.pyplot as plt
import gc
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


# For tree attributes caluclated based on individual tree point clouds
import alphashape
from scipy.optimize import leastsq
import circle_fit as cf


# %%
"""
EXAMPLE ONE: 
    
    > OPEN ORIGINAL OBLIQUE POINT CLOUD FROM LIPHE STATION (SCANNER IS THE ORIGIN) - https://doi.org/10.3389/fpls.2020.606752 
    > COMPUTE EXTRA PARAMETERS 
    > NORMALIZE THE POINT CLOUD TO A LOCAL REFERENCE SYSTEM NORMAL TO THE GROUND

"""

# USER DEFINED:

# 1. Set path to laz2Np dll (Laspy can also be used here)
DLLPATH = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\LAZ2NP\OS_WIN\Las2Array_StaticLibrary.dll"

# 2. set input and output paths
Lazdir = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\ORIGINAL_LAZ"
)
outputLas = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\RECTIFIED_LAZ"
)

# 3. Declare scan angular setup and resolution - LiPhe Setup 2020-2021
thetaStart = 40
thetaStop = 127
thetaIncrement = 0.006
phiStart = 103.0
phiStop = 254.0
phiIncrement = 0.006

# ------------------------------------------------------------------------------------------------------
# Find laz point clouds
ProjList = glob.glob(Lazdir + "/*.laz")

# Defining offset - Local coordinate system
offsets = np.zeros((3), dtype=np.float32)

for i in range(len(ProjList)):
    inputLas = ProjList[i]
    outputP = os.path.basename(ProjList[i]).split(".")[0]

    t1_start = time.perf_counter()
    t2_start = time.process_time()

    """ 
    READING POINT CLOUD
    INPUT:PATH TO LAZ FILE (inputLas) AND PATH TO NP2LAZ DLL (DLLPATH)
    OUTPUT:CLASS WITH LAS CONTENT (x, y, z, return_number, number_of_returns, intensity, extra_bytes)
    """

    LAZCONTENT = ReadLaz.ReadLaz(inputLas, DLLPATH)

    # SET NAMES AND NUMBER OF EXTRABYTES TO BE SAVED
    ExtraBytes_name = ["Reflectance", "Deviation"]
    NEB = 2
    NP = len(LAZCONTENT.x)
    Extra = np.empty((NEB, NP), dtype=np.float32)
    Extra[0] = LAZCONTENT.Reflectance
    Extra[1] = LAZCONTENT.Deviation

    if hasattr(LAZCONTENT, "Amplitude"):
        setattr(LAZCONTENT, "intensity", LAZCONTENT.Amplitude)

    # IF THE POINT CLOUD HAS NO EXTRA BYTES DECLARE:
    # ExtraBytes_name=[]
    # NEB=0; Extra=np.empty((NEB,NP), dtype=np.float32);

    """ 
    COMPUTE EXTRA BYTES: RANGE AND SCAN ANGLES
    
    Processing.COMPUTE_EXTRA_PARAMETERS :The main of this function is to compute the scan angles (Phi and Theta) and the Range 
                                         based on the point coordinates (x,y,z) and save them as extra parameters in the new point cloud.  
    
    INPUT:LAZCONTENT >> POINT CLOUD STRUCTURE
          Extra >> Extra bytes array (can be empty Extra=[])
          thetaStart,  thetaStop and thetaIncrement
          phiStart, phiStop and phiIncrement
          
    OUTPUT:CLASS WITH ORIGINAL LAS CONTENT +  EXTRA PARAMETERS (RANGE AND SCAN ANGLES)
    """

    LAZCONTENT, EXTRA = Processing.COMPUTE_EXTRA_PARAMETERS(
        LAZCONTENT,
        Extra,
        thetaStart,
        thetaStop,
        thetaIncrement,
        phiStart,
        phiStop,
        phiIncrement,
    )
    ExtraBytes_name = ["Reflectance", "Deviation", "Range", "Theta", "Phi"]
    NEB = 5

    """ 
    NORMALIZE OBLIQUE POINT CLOUD
    
    Processing.RectifLaz: This function rectify a point cloud for a normalized local systems based in a passive rotation matrix. 
                          The angles and translation should be defined by the user. 
    
    INPUT: LAZCONTENT >> POINT CLOUD STRUCTURE
           TRANSFORMATION >> STRUCTURE WITH THE TRANFORMATION PARAMETERS
                             ROTATION > EULER ANGLES > DEGREES
                             TRANSLATION > METERS
    
    OUTPUT: X, Y and Z coordinates in the ground-normalized georeference system
          
    """

    class Transformation:
        w = 0
        fi = -60
        k = -90
        x = 0
        y = 0
        z = 0

    x1, y1, z1 = Processing.RectifLaz(
        LAZCONTENT.x, LAZCONTENT.y, LAZCONTENT.z, Transformation
    )

    """ 
    WRITING POINT CLOUD
    
    INPUT:CLASS WITH LAS CONTENT TO BE WRITE AS CLOUD (e.g. x, y, z, return_number, number_of_returns, intensity, extra_bytes)
    
    OUTPUT:laz or las file
    
    """

    outputLasFile = outputLas + "/" + outputP + ("_R.las")

    class MainContent:
        x = x1 - offsets[0]
        y = y1 - offsets[1]
        z = z1 - offsets[2]
        return_number = LAZCONTENT.return_number
        number_of_returns = LAZCONTENT.number_of_returns
        intensity = LAZCONTENT.intensity
        ExtraBytes_name = ExtraBytes_name

    WriteLaz.WriteLaz(outputLasFile, DLLPATH, MainContent, offsets, EXTRA)
    del LAZCONTENT, Transformation, MainContent, x1, y1, z1
    gc.collect()

    t1_stop = time.perf_counter()
    t2_stop = time.process_time()
    print("\n End of Processing: %.1f [sec]" % ((t1_stop - t1_start)))


# %%

"""

EXAMPLE TWO: 
 
    GEOREFERENCE THE POINT CLOUDS BASED ON CONTROL POINTS 
    
    THIS CODE CAN ALSO BE USED TO REGISTER 2 POINT CLOUD BASED ON MATCH POINTS
        
"""

# 1. Set path to laz2Np dll
DLLPATH = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\LAZ2NP\OS_WIN\Las2Array_StaticLibrary.dll"

# 2. set input and output paths
Lazdir = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\RECTIFIED_LAZ"
)
outputLas = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\GEOREF_LAZ"
)

# Find laz point clouds
ProjList = glob.glob(Lazdir + "/*.las")

# Defining offset - Local coordinate system
offsets = np.array([357676.852, 6860035.171, 0], dtype=np.float32)

# Declaring control points or match points
# As example we had  literally declared the control points but it can easily be read from a file
# This code can also be use to register two point cloud based on know matching point betwee two clouds.

GCP = 8  # Declare number of control points
ReferencePoints = np.empty((2, GCP * 3), dtype=np.float32)

# Declare point in the cloud in the local reference system
ReferencePoints[0] = [
    14.689000129700,
    12.536899566650,
    -30.292699813843,  # X, Y, Z - POINT 1
    15.640000343323,
    12.213899612427,
    -30.472600936890,  # X, Y, Z - POINT 2
    -27.661699295044,
    1.754400014877,
    -33.543701171875,
    -0.3602,
    0.4282,
    -32.75,
    -24.847000122070,
    -9.489500045776,
    -33.85,
    -63.188000,
    91.791000,
    -0.058000,
    -63.952999,
    90.834000,
    -2.921000,
    -89.653999,
    82.343002,
    -23.75,
]

# Declare the same points in the georef. reference system >> ETRS89-TM35FIN reference system
ReferencePoints[1] = [
    357695.087,
    6860040.222,
    192.834,  # E, N, H - POINT 1
    357695.675,
    6860039.605,
    192.784,  # E, N, H - POINT 2
    357651.844,
    6860047.925,
    189.571,
    357676.852,
    6860035.171,
    190.69,
    357649.613,
    6860036.454,
    189.66,
    357656.909000,
    6860144.787996,
    222.809998,
    357656.215000,
    6860144.193003,
    219.968994,
    357628.913000,
    6860147.159998,
    199.20,
]


for i in range(len(ProjList)):
    inputLas = ProjList[i]
    outputP = os.path.basename(ProjList[i]).split(".")[0]

    t1_start = time.perf_counter()
    t2_start = time.process_time()

    """ 
    READING POINT CLOUD
    INPUT:PATH TO LAZ FILE (inputLas) AND PATH TO NP2LAZ DLL (DLLPATH)
    OUTPUT:CLASS WITH LAS CONTENT (x, y, z, return_number, number_of_returns, intensity, extra_bytes)
    """

    LAZCONTENT = ReadLaz.ReadLaz(inputLas, DLLPATH)

    # SET NAMES AND NUMBER OF EXTRABYTES TO BE SAVED
    ExtraBytes_name = ["Reflectance", "Deviation", "Range", "Theta", "Phi"]
    NEB = 5
    NP = len(LAZCONTENT.x)
    Extra = np.empty((NEB, NP), dtype=np.float32)
    Extra[0] = LAZCONTENT.Reflectance
    Extra[1] = LAZCONTENT.Deviation
    Extra[2] = LAZCONTENT.Range
    Extra[3] = LAZCONTENT.Theta
    Extra[4] = LAZCONTENT.Phi

    """
    PROCESSING: GEO REFERENCING POINT CLOUD
    MANDATORY: LAZCONTENT and Ground control points
    
    """

    x1, y1, z1 = Processing.HELMERT3D(LAZCONTENT, ReferencePoints)

    outputLasFile = outputLas + "/" + outputP + ("_Georef.laz")

    class MainContent:
        x = x1 - offsets[0]
        y = y1 - offsets[1]
        z = z1 - offsets[2]
        return_number = LAZCONTENT.return_number
        number_of_returns = LAZCONTENT.number_of_returns
        intensity = LAZCONTENT.intensity
        ExtraBytes_name = ExtraBytes_name

    WriteLaz.WriteLaz(outputLasFile, DLLPATH, MainContent, offsets, Extra)
    del MainContent
    gc.collect()

# %%

"""
EXAMPLE THREE: 
    
    SPATIAL SAMPLE THE POINT CLOUDS BASED ON POINT CLOUD VOXELIZATION  
    The function resample a point cloud based on spatial density of user defined voxel size. 

"""

# 1. Set path to laz2Np dll
DLLPATH = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\LAZ2NP\OS_WIN\Las2Array_StaticLibrary.dll"

# 2. set input and output paths
Lazdir = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\GEOREF_LAZ"
)
outputLas = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\RESAMPLE_LAZ"
)

# Find laz point clouds
ProjList = glob.glob(Lazdir + "/*.laz")

# Defining offset - Local coordinate system
offsets = np.array([357676.852, 6860035.171, 0], dtype=np.float32)

for i in range(len(ProjList)):
    inputLas = ProjList[i]
    outputP = os.path.basename(ProjList[i]).split(".")[0]

    t1_start = time.perf_counter()
    t2_start = time.process_time()

    """ 
    READING POINT CLOUD
    INPUT:PATH TO LAZ FILE (inputLas) AND PATH TO NP2LAZ DLL (DLLPATH)
    OUTPUT:CLASS WITH LAS CONTENT (x, y, z, return_number, number_of_returns, intensity, extra_bytes)
    """

    LAZCONTENT = ReadLaz.ReadLaz(inputLas, DLLPATH)

    # SET NAMES AND NUMBER OF EXTRABYTES TO BE SAVED
    ExtraBytes_name = ["Reflectance", "Deviation", "Range", "Theta", "Phi"]
    NEB = 5
    NP = len(LAZCONTENT.x)
    Extra = np.empty((NEB, NP), dtype=np.float32)
    Extra[0] = LAZCONTENT.Reflectance
    Extra[1] = LAZCONTENT.Deviation
    Extra[2] = LAZCONTENT.Range
    Extra[3] = LAZCONTENT.Theta
    Extra[4] = LAZCONTENT.Phi

    """ 
    
    PROCESSING: RESAMPLE POINT CLOUD
    
    MANDATORY: LAZCONTENT,  
           
           
    OPTIONAL: Extra, ExtraBytes_name
          IF EXTRABYTES CREATE A GENERAL ARRAY AND SET THE NUMBER OF POINTS
          E.G:TESTE, EXTRA=Processing.Resample(LAZCONTENT, PCD, Extra, ExtraBytes_name)
          
    """

    SPATIAL_RESAMPLE, EXTRA_RESAMPLE = Processing.Spatial_sample(
        LAZCONTENT,
        useroption="neighbour",
        pts_min=1,
        vs=0.05,
        npoints=1,
        EXTRA=Extra,
        ExtraBytes_name=ExtraBytes_name,
        n_jobs=1,
    )

    outputLasFile = outputLas + "/" + outputP + ("_SpatialSample.laz")

    class MainContent:
        x = SPATIAL_RESAMPLE.x - offsets[0]
        y = SPATIAL_RESAMPLE.y - offsets[1]
        z = SPATIAL_RESAMPLE.z - offsets[2]
        return_number = SPATIAL_RESAMPLE.return_number
        number_of_returns = SPATIAL_RESAMPLE.number_of_returns
        intensity = SPATIAL_RESAMPLE.intensity
        ExtraBytes_name = ExtraBytes_name

    WriteLaz.WriteLaz(outputLasFile, DLLPATH, MainContent, offsets, EXTRA_RESAMPLE)
    del LAZCONTENT, MainContent
    gc.collect()

# %%

"""
EXAMPLE FOUR: 
    
    PROCESSING: CLIPPING TREES FROM FULL POINT CLOUD BASED ON TREE MAP AND CYLINDER CUTTING
    
    OTHER CUTTING OPTIONS: 
                        SQUARED BOUNDING BOX AROUND THE STEM POSITION
                        E.G. BOX.append([X_STEM-1, Y_STEM-1, Z_STEM-1, X_STEM+1, Y_STEM+1, Z_STEM+30]) / 1 per tree
                        ANGULAR BOUNDING BOX ACCORDING TO PHI,  THETA AND RANGE
                        BOX_ANGLES.append([min_theta, min_phi, min_range, max_theta, max_phi, max_range])
                        SQUARED AND ANGULAR BOUNDING BOX COMBINED
                        VORONOI CELL
    
    MANDATORY: LAZCONTENT, CYLINDER BOUNDING BOX 
           E.G: TREE=Processing.ClippingTree (LAZCONTENT, BOX_COORD[0], BOX_ANGLES[0])
           User option BOX_COORD, BOX_ANGLES, CYLINDER BOX, VORONOI CELLS
           E.G: TREE=Processing.ClippingTree (LAZCONTENT, BOX_COORD, BOX_ANGLES, CYLINDER[k], Extra=[], ExtraBytes_name)
   
    
    OPTIONAL:Extra, ExtraBytes_name
           E.G: TREE, EXTRA=Processing.ClippingTree (LAZCONTENT, BOX_COORD[0], BOX_ANGLES[0], Extra, ExtraBytes_name)

"""

# 1. Set path to laz2Np dll
DLLPATH = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\LAZ2NP\OS_WIN\Las2Array_StaticLibrary.dll"


# 2. Set input and output paths
Lazdir = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\RESAMPLE_LAZ"
)
outputLas = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\TREES_CYLINDER"

# 3. Defining data offset - Georef coordinate system
offsets = np.array([357676.852, 6860035.171, 0], dtype=np.float32)

# 4. Set stem map as input
Metadata = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\STEM_MAP\TreeMap.xlsx"
df = pd.read_excel(Metadata)
ID = np.array(df.TREE_ID)
x_stem = np.array(df.E)
y_stem = np.array(df.N)
z_stem = np.array(df.H)
species = np.array(df.Species)
N_trees = len(x_stem)

# 5. Creating cylinder boundary box according to the stem map
BOX_COORD = []
BOX_ANGLES = []
CYLINDER = []
VORONOI = []
RAIO = np.full(
    (len(x_stem),), 2.2
)  # Define radius for the cylinder cut - 3.5 radius around the stem position
CYLINDER = np.dstack((x_stem, y_stem, z_stem, RAIO))[0]


# 6. Search for laz files in the full point cloud directory
ProjList = glob.glob(Lazdir + "/*.laz")

# 7 . Loop tree cutting
for i in range(len(ProjList)):
    inputLas = ProjList[i]
    outputP = os.path.basename(ProjList[i]).split(".")[0]

    """ 
    READING FULL POINT CLOUD
    INPUT:PATH TO LAZ FILE (inputLas) AND PATH TO NP2LAZ DLL (DLLPATH)
    OUTPUT:CLASS WITH LAS CONTENT (x, y, z, return_number, number_of_returns, intensity, extra_bytes)
    """
    LAZCONTENT = ReadLaz.ReadLaz(inputLas, DLLPATH)

    ExtraBytes_name = ["Reflectance", "Deviation", "Range", "Theta", "Phi"]
    NEB = 5
    NP = len(LAZCONTENT.x)
    Extra = np.empty((NEB, NP), dtype=np.float32)
    Extra[0] = LAZCONTENT.Reflectance
    Extra[1] = LAZCONTENT.Deviation
    Extra[2] = LAZCONTENT.Range
    Extra[3] = LAZCONTENT.Theta
    Extra[4] = LAZCONTENT.Phi

    """EXTRACTING MULTIPLE TREES FROM THE FULL POINT CLOUD ACCORDING TO THE STEM MAP"""
    for k in range(N_trees):
        # IF EXTRA BYTES:
        TREE, EXTRA_TREE = Processing.ClippingTree(
            LAZCONTENT,
            BOX_COORD,
            BOX_ANGLES,
            CYLINDER[k],
            VORONOI,
            Extra,
            ExtraBytes_name,
        )

        # IF NO EXTRA BYTES
        # ExtraBytes_name=[]; Extra=[];
        # TREE=Processing.ClippingTree (LAZCONTENT, BOX_COORD, BOX_ANGLES, CYLINDER[k], VORONOI, Extra, ExtraBytes_name)

        """ WRITING TREES"""
        if len(TREE.x) > 0:  # Check if the tree exist in the file.
            Aux = str(ID[k])
            outputLasFile = outputLas + "\\" + outputP + "TREE_" + Aux + ".laz"

            class MainContent:
                x = TREE.x - offsets[0]
                y = TREE.y - offsets[1]
                z = TREE.z - offsets[2]
                return_number = TREE.return_number
                number_of_returns = TREE.number_of_returns
                intensity = TREE.intensity
                ExtraBytes_name = ExtraBytes_name

            # setattr (MAINCONTENT, 'edge_of_flight_line', TREE.edge_of_flight_line )
            # setattr (MAINCONTENT, 'scan_direction_flag', TREE.scan_direction_flag )
            # setattr (MAINCONTENT, 'classification', TREE.classification )
            # setattr (MAINCONTENT, 'scan_angle_rank', TREE.scan_angle_rank )
            # setattr (MAINCONTENT, 'point_source_ID', TREE.point_source_ID )
            # setattr (MAINCONTENT, 'gps_time', TIME)
            WriteLaz.WriteLaz(outputLasFile, DLLPATH, MainContent, offsets, EXTRA_TREE)
            del MainContent
            gc.collect()

    del LAZCONTENT


# %%

"""
EXAMPLE FIVE: 
    
    PROCESSING: CLIPPING TREES FROM FULL POINT CLOUD BASED ON TREE MAP AND VORONOI CELL CUTTING
    
    OTHER CUTTING OPTIONS: 
                        SQUARED BOUNDING BOX AROUND THE STEM POSITION
                        ANGULAR BOUNDING BOX ACCORDING TO PHI AND THETA
                        SQUARED AND ANGULAR BOUNDING BOX COMBINED
                        VORONOI CELL
    
    MANDATORY: LAZCONTENT, CYLINDER BOUNDING BOX 
           E.G: TREE=Processing.ClippingTree (LAZCONTENT, BOX_COORD[0], BOX_ANGLES[0])
           User option BOX_COORD, BOX_ANGLES, CYLINDER BOX, VORONOI CELLS
           E.G: TREE=Processing.ClippingTree (LAZCONTENT, BOX_COORD, BOX_ANGLES, CYLINDER[k], Extra=[], ExtraBytes_name)
   
    
    OPTIONAL:Extra, ExtraBytes_name
           E.G: TREE, EXTRA=Processing.ClippingTree (LAZCONTENT, BOX_COORD[0], BOX_ANGLES[0], Extra, ExtraBytes_name)

"""

# 1. Set path to laz2Np dll
DLLPATH = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\LAZ2NP\OS_WIN\Las2Array_StaticLibrary.dll"


# 2. Set input and output paths
Lazdir = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\RESAMPLE_LAZ"
)
outputLas = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\TREES_VORONOI"
)

# 3. Defining data offset - Georef coordinate system
offsets = np.array([357676.852, 6860035.171, 0], dtype=np.float32)

# 4. Set stem map as input
Metadata = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\STEM_MAP\TreeMap.xlsx"
df = pd.read_excel(Metadata)
ID = np.array(df.TREE_ID)
x_stem = np.array(df.E)
y_stem = np.array(df.N)
z_stem = np.array(df.H)
species = np.array(df.Species)
N_trees = len(x_stem)

# 5. Creating cylinder boundary box according to the stem map
BOX_COORD = []
BOX_ANGLES = []
CYLINDER = []
VORONOI = []

# Define voronoi array with stem coordinates
VORONOI = np.dstack((x_stem, y_stem, ID))


# 6. Search for laz files in the full point cloud directory
ProjList = glob.glob(Lazdir + "/*.laz")

# 7 . Loop tree cutting
for i in range(len(ProjList)):
    inputLas = ProjList[i]
    outputP = os.path.basename(ProjList[i]).split(".")[0]

    """ 
    READING FULL POINT CLOUD
    INPUT:PATH TO LAZ FILE (inputLas) AND PATH TO NP2LAZ DLL (DLLPATH)
    OUTPUT:CLASS WITH LAS CONTENT (x, y, z, return_number, number_of_returns, intensity, extra_bytes)
    """
    LAZCONTENT = ReadLaz.ReadLaz(inputLas, DLLPATH)

    ExtraBytes_name = ["Reflectance", "Deviation"]
    NEB = 2

    NP = len(LAZCONTENT.x)
    Extra = np.empty((NEB, NP), dtype=np.float32)
    Extra[0] = LAZCONTENT.Reflectance
    Extra[1] = LAZCONTENT.Deviation

    """EXTRACTING MULTIPLE TREES FROM THE FULL POINT CLOUD ACCORDING TO THE STEM MAP"""

    # IF EXTRA BYTES:
    TREE, EXTRA_TREE = Processing.ClippingTree(
        LAZCONTENT, BOX_COORD, BOX_ANGLES, CYLINDER, VORONOI, Extra, ExtraBytes_name
    )

    # IF NO EXTRA BYTES
    # ExtraBytes_name=[]; Extra=[];
    # TREE=Processing.ClippingTree (LAZCONTENT, BOX_COORD, BOX_ANGLES, CYLINDER, VORONOI, Extra, ExtraBytes_name)

    """ WRITING TREES"""

    for t in range(len(TREE)):
        if TREE[t].x.shape[0] > 0:  # Check if the tree exist in the file.
            Aux = str(int(TREE[t].name))
            outputLasFile = outputLas + "\\" + outputP + "TREE_" + Aux + ".laz"

            class MainContent:
                x = TREE[t].x - offsets[0]
                y = TREE[t].y - offsets[1]
                z = TREE[t].z - offsets[2]
                return_number = TREE[t].return_number
                number_of_returns = TREE[t].number_of_returns
                intensity = TREE[t].intensity
                ExtraBytes_name = ExtraBytes_name

            # setattr (MAINCONTENT, 'edge_of_flight_line', TREE.edge_of_flight_line )
            # setattr (MAINCONTENT, 'scan_direction_flag', TREE.scan_direction_flag )
            # setattr (MAINCONTENT, 'classification', TREE.classification )
            # setattr (MAINCONTENT, 'scan_angle_rank', TREE.scan_angle_rank )
            # setattr (MAINCONTENT, 'point_source_ID', TREE.point_source_ID )
            # setattr (MAINCONTENT, 'gps_time', TIME)
            WriteLaz.WriteLaz(
                outputLasFile, DLLPATH, MainContent, offsets, EXTRA_TREE[t]
            )
            del MainContent
            gc.collect()

    del LAZCONTENT

"""
EXAMPLE SIX - NORMALIZE THE POINT CLOUDS ACCORDING TO THE GROUND AND REMOVE GROUND POINTS.
PS: THIS IS A MANDATORY PROCESSING STEP REQUIRED BEFORE FINE SEGMENTATION 

MANDATORY: LAZCONTENT > INDIVIDUAL TREE POINT CLOUD
           STEM POSITION INFORMATION (x,y)
           MINIMUM THRSHOULD TO REMOVE GROUND POINTS - default=0.3m
   
OPTIONAL:Extra, ExtraBytes_name
           E.G: TREE, EXTRA=Processing.ClippingTree (LAZCONTENT, BOX_COORD[0], BOX_ANGLES[0], Extra, ExtraBytes_name)

"""

# STEP 1 - NORMALIZE TREES FOR GROUND AND SAVE SOMEWHERE THE NORM COORDINATES

# 1. Set path to laz2Np dll
DLLPATH = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\LAZ2NP\OS_WIN\Las2Array_StaticLibrary.dll"


# 2. Set input and output paths
Lazdir = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\TREES_CYLINDER"
outputLas = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\TREE_NORMALIZED"

# 3 - Set stem map as input
Metadata = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\STEM_MAP\TreeMap.xlsx"
df = pd.read_excel(Metadata)
ID = np.array(df.TREE_ID)
x_stem = np.array(df.E)
y_stem = np.array(df.N)
z_stem = np.array(df.H)
species = np.array(df.Species)
N_trees = len(x_stem)

# 4. Defining data offset
offsets_norm = np.array([357676.852, 6860035.171, 0], dtype=np.float32)
default = 1  # Define thrshould to remove the ground point

# If the gorund altitude of the tree is unkwown send DTM
DTM_NAME = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\DTM\Heli_pts_tower200m_DTM_20cm.las"
DTM = ReadLaz.ReadLaz(DTM_NAME, DLLPATH)


# 5 - SAVING OFFSETS IN A TABLE FOR FURTHER PROCESSING (IF NEED)
workbook = xlsxwriter.Workbook(
    "D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\STEM_MAP\TreeMap_Norm.xlsx"
)
worksheet = workbook.add_worksheet()
worksheet.write("A1", "ID")
worksheet.write("B1", "X")
worksheet.write("C1", "Y")
worksheet.write("D1", "Z")
worksheet.write("E1", "OFFSET_X")
worksheet.write("F1", "OFFSET_Y")
worksheet.write("G1", "OFFSET_Z")
row = 1

# 6. Loop to normalize tree point cloud to the ground and save
ProjList = glob.glob(Lazdir + "/*.laz")
offsets_local = np.zeros((3), dtype=np.float32)
for i in range(len(ProjList)):
    inputLas = ProjList[i]
    outputP = os.path.basename(ProjList[i]).split(".")[0]

    ID_TREE = int(outputP.split("_")[6].split(".")[0])
    P = ID == ID_TREE

    # READ POINT CLOUD
    LAZCONTENT = ReadLaz.ReadLaz(inputLas, DLLPATH)

    # DEFINE EXTRA BYTES
    ExtraBytes_name = ["Reflectance", "Deviation", "Range", "Theta", "Phi"]
    NEB = 5
    NP = len(LAZCONTENT.x)
    Extra = np.empty((NEB, NP), dtype=np.float32)
    Extra[0] = LAZCONTENT.Reflectance
    Extra[1] = LAZCONTENT.Deviation
    Extra[2] = LAZCONTENT.Range
    Extra[3] = LAZCONTENT.Theta
    Extra[4] = LAZCONTENT.Phi

    # If the min height is unkown it can be searched in the DTM
    offsets_norm[2] = griddata(
        (DTM.x, DTM.y), DTM.z, (x_stem[P], y_stem[P]), method="nearest"
    )

    worksheet.write(row, 0, ID_TREE)
    worksheet.write(row, 1, x_stem[P])
    worksheet.write(row, 2, y_stem[P])
    worksheet.write(row, 3, z_stem[P])
    worksheet.write(row, 4, offsets_norm[0])
    worksheet.write(row, 5, offsets_norm[1])
    worksheet.write(row, 6, offsets_norm[2])
    row = row + 1

    # offsets_norm[2]=z_stem[P]

    TREE, EXTRA_TREE = Processing.Ground_Normalize(
        LAZCONTENT,
        offsets=offsets_norm,
        th=default,
        Extra=Extra,
        ExtraBytes_name=ExtraBytes_name,
    )

    outputLasFile = outputLas + "/" + outputP + (".las")

    class MainContent:
        x = (TREE.x)
        y = (TREE.y)
        z = (TREE.z)
        return_number = TREE.return_number
        number_of_returns = TREE.number_of_returns
        intensity = TREE.intensity
        ExtraBytes_name = ExtraBytes_name

    WriteLaz.WriteLaz(outputLasFile, DLLPATH, MainContent, offsets_local, EXTRA_TREE)

workbook.close()

# %%


"""

EXAMPLE SEVEN - FINE SEGMENTATION > REMOVE NOISE AND ADJACENT TREES REMAINED FROM THE TREE CLIPPING FUNCTIONS. 
PS: EXAMPLE SIX (POINT CLOUD GROUND NORMALIZATIO) IS A PRE-REQUISITE 
REQUIRED INPUTS:
    
    PATH - Common path that all data required for the segmentation process shares (if any)
    
    PC_DIRECTORY - Name of the directory that contains the point cloud data
    
    PC_FILENAME - Template string for the filename of the point cloud. The plot id is 
    
    inserted into the string during segmentation. The same filename is
    used for saving the final tree segment (in a different directory)

    REF_DIRECTORY-Name of the directory that contains the reference data

    REF_FILENAME - Filename of the reference data excel sheet

    DEST_DIRECTORY_MAIN - Name of the directory where the main tree segment should be saved

    DEST_DIRECTORY_OTHER - Name of the directory where the other segments, i.e. the
                        identified segments that are not part of the main tree, should be
                        saved

    REF_DIST_MAX - Maximum distance between a segment and reference tree location such
                   that the two can still be considered a match (meters)


STEPS:
    
    1. INPUT PATHS AND CREATE SEGMENTATION FILES
    2. RUN THE FINE SEGMENTATION CODE FOR ALL THE TREES IN THE FOLDER
    3. SAVE THE TREES WITH GEOREFERENCE COORDINATES AGAIN > FINAL POINT CLOUDS
    
"""

# !!! --------------DEFINE USER INPUT AND CREATE CONFIGURATION FILE -------------- !!!

# PLEASE ADD HERE ALL THE REQUIRED USER INPUT
DLLPATH = "D:/SA_SILS/PROCESSING/Hyytiala_PipelinePaper/LAZ2NP/OS_WIN/Las2Array_StaticLibrary.dll"
lbl_location = r"D:/SA_SILS/PROCESSING/Hyytiala_PipelinePaper/PROCESSING/FUNCTIONS"
PATH = "D:/SA_SILS/PROCESSING/Hyytiala_PipelinePaper/PROCESSING/SAMPLE_DATA"
PC_DIRECTORY = "/TREE_NORMALIZED"
PC_FILENAME = "/200406_100502_Sample_R_Georef_SpatialSampleTREE_{TREEID}.las"
REF_DIRECTORY = "/STEM_MAP"
REF_FILENAME = "/TreeMap.xlsx"
DEST_DIRECTORY_MAIN = "/TREES_SEGMENTED"
DEST_DIRECTORY_OTHER = "/TREES_SEGMENTED/NOISE/"

# USER INPUT
user_input1 = PATH
user_input2 = PC_DIRECTORY
user_input3 = PC_FILENAME
user_input4 = REF_DIRECTORY
user_input5 = REF_FILENAME
user_input6 = DEST_DIRECTORY_MAIN
user_input7 = DEST_DIRECTORY_OTHER

FILE_LOCATION = lbl_location + "\config.py"

# File content
file_content = f'''\


"""
----------------------
SEGMENTATION CONSTANTS

Variable                |   Description
________________________|_______________________________________________________________________
                    |
PATH                    |   Common path that all data required for the segmentation process
                    |   shares (if any)
________________________|_______________________________________________________________________
                    |
PC_DIRECTORY            |   Name of the directory that contains the point cloud data
________________________|_______________________________________________________________________
                    |
                    |
PC_FILENAME             |   Template string for the filename of the point cloud. The plot id is
                    |   inserted into the string during segmentation. The same filename is
                    |   used for saving the final tree segment (in a different directory)
________________________|_______________________________________________________________________
                    |
REF_DIRECTORY           |   Name of the directory that contains the reference data
________________________|_______________________________________________________________________
                    |
REF_FILENAME            |   Filename of the reference data excel sheet
________________________|_______________________________________________________________________
                    |
DEST_DIRECTORY_MAIN     |   Name of the directory where the main tree segment should be
                    |   saved
________________________|_______________________________________________________________________
                    |
DEST_DIRECTORY_OTHER    |   Name of the directory where the other segments, i.e. the
                    |   identified segments that are not part of the main tree, should be
                    |   saved
________________________|_______________________________________________________________________
                    |
REF_DIST_MAX            |   Maximum distance between a segment and reference tree location such
                    |   that the two can still be considered a match (meters)

"""
PATH = "{user_input1}"

PC_DIRECTORY = "{user_input2}"

PC_FILENAME = "{user_input3}"

REF_DIRECTORY = "{user_input4}"

REF_FILENAME = "{user_input5}"

DEST_DIRECTORY_MAIN = "{user_input6}"

DEST_DIRECTORY_OTHER = "{user_input7}"

REF_DIST_MAX = 2

'''

# Write file
with open(FILE_LOCATION, "w") as file:
    file.write(file_content)

print("Python file written successfully!")

#  --------------CONFIGURATION FILE DONE--------------
# ---------------------------------------------------------------------------------------------------------------


# ---------------LOOP CALLING SEGMENTATION CODE FOR N TREES-------------------------------

lazdir = user_input1 + user_input2
ProjList = glob.glob(lazdir + "/*.las")
removed_ID = []

for i in range(len(ProjList)):
    outputP = os.path.basename(ProjList[i]).split(".")[0]
    ID_TREE = int(outputP.split("_")[6].split(".")[0])

    try:
        lbl_segment.lbl_segment(
            tree_id=ID_TREE, write_other=True, x_offset=357676.852, y_offset=6860035.171
        )

    except:
        removed_ID.append(ID_TREE)
        pass

# ----------------------------------------------------------------------------------------------------------
# -------------RE-WRITE THE FINAL TREES IN GEOREF COORDINATES AND SAVE THE FINAL RESULTS-------------------

# SET FINAL PATH
OutputLaz = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\TREES_FINAL"
)


# READ THE REFERENCE FILE WHERE THE OFFSETS WERE SAVED AFTER NORMALIZATION (EXAMPLE SIX)
Metadata = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\STEM_MAP\TreeMap_Norm.xlsx"
df = pd.read_excel(Metadata)
ID = np.array(df.ID)
offset_x = np.array(df.OFFSET_X)
offset_y = np.array(df.OFFSET_Y, dtype="float64")
offset_z = np.array(df.OFFSET_Z)
N_trees = len(offset_x)

# SET OFFSET TO SAVE GEOREFERENCED DATA
offsets = np.array(
    [357676.852, 6860035.171, 0], dtype=np.float32
)  # include georef offset

# MAIN LOOP
Lazdir = PATH + DEST_DIRECTORY_MAIN
ProjList = glob.glob(Lazdir + "/*.las")
for i in range(N_trees):
    outputP = outputP = os.path.basename(ProjList[i]).split(".")[0]
    LAZCONTENT = ReadLaz.ReadLaz(ProjList[i], DLLPATH)

    ID_TREE = int(outputP.split("_")[6].split(".")[0])
    P = ID == ID_TREE

    # DECLARE EXTRABYTES
    ExtraBytes_name = ["Reflectance", "Deviation", "Range", "Theta", "Phi"]
    NEB = 5
    NP = len(LAZCONTENT.x)
    Extra = np.empty((NEB, NP), dtype=np.float32)
    Extra[0] = LAZCONTENT.Reflectance
    Extra[1] = LAZCONTENT.Deviation
    Extra[2] = LAZCONTENT.Range
    Extra[3] = LAZCONTENT.Theta
    Extra[4] = LAZCONTENT.Phi

    outputLasFile = OutputLaz + "/" + outputP + (".laz")

    class MainContent:
        x = (LAZCONTENT.x)
        y = (LAZCONTENT.y)
        z = (LAZCONTENT.z + offset_z[P])
        return_number = LAZCONTENT.return_number
        number_of_returns = LAZCONTENT.number_of_returns
        intensity = LAZCONTENT.intensity
        ExtraBytes_name = ExtraBytes_name

    WriteLaz.WriteLaz(outputLasFile, DLLPATH, MainContent, offsets, Extra)

# %%

"""
EXAMPLE EIGHT: 
    
    PROCESSING: CALCULATING TREE ATTRIBUTES > HEIGHT, AREA, DBH 
    
    MANDATORY: LAZCONTENT >> LAZ FILE
    
    OUTPUT: EXCEL TABLE
    
"""

# 1. Set path to laz2Np dll
DLLPATH = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\LAZ2NP\OS_WIN\Las2Array_StaticLibrary.dll"


# 2. Set input and output paths
Lazdir = (
    r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\TREES_FINAL"
)


# 3. Set tree IDs
ID = [11816, 11777]

# 4. Declare output file
workbook = xlsxwriter.Workbook("TreeAtributes.xlsx")
worksheet = workbook.add_worksheet()
worksheet.write("A1", "ID")
worksheet.write("B1", "DATE")
worksheet.write("C1", "Height (m)")
worksheet.write("D1", "Area (m2)")
worksheet.write("E1", "Reflectance (DB)")
worksheet.write("F1", "DBH (m)")
row = 1

# DATE, HOUR, ID, X, Y, Z, SPECIES, HEIGHT, AREA, NUMBER OF NEIGHBORS, DATA QUALITY FLAG (1, 2, 3, 4, 5)

for j in range(len(ID)):
    ProjList = glob.glob(Lazdir + "/*_" + str(ID[j]) + ".laz")

    if len(ProjList) > 0:
        N_trees = len(ProjList)

        for i in range(N_trees):
            # Reading tree data - Segmented Stems
            inputLas = ProjList[i]
            DATE = os.path.basename(ProjList[0]).split(".")[0].split("_")[0]
            LAZCONTENT = ReadLaz.ReadLaz(inputLas, DLLPATH)
            TREE_Param = Processing.TreeParameters(
                LAZCONTENT,
                dim="2dxy",  # options: '2dxz', '2dyz', '3d'
                alphavalue=0.2,  # option mandatory 0=convexhull; 'Auto' = the code will estimate the optmal alpha value but can take time
                lim=5,
            )  # Minimum number of edges to consider a poligon)

            worksheet.write(row, 0, ID[j])
            worksheet.write(row, 1, DATE)
            worksheet.write(row, 2, TREE_Param.Height)
            worksheet.write(row, 3, TREE_Param.Area)
            worksheet.write(row, 4, TREE_Param.Reflectance)
            worksheet.write(row, 5, TREE_Param.DBH)
            row = row + 1

workbook.close()

# %%

"""
EXAMPLE NINE: Given a individual tree point cloud calculate the density/centroid/average attribute inside of a voxel
    
    PROCESSING: Stastitic_voxel
    
    MANDATORY: LAZCONTENT
               useroption: Atributes, Centroid or Density
               pts_min: Minimum number of points to consider a voxel as valid or  not empty   
               vs: Voxel resolution (cubic)
               
    OPTIONAL: user option Atributes >> Requires Attribute as input e.g LASCONTENT.intensity or LASCONTENT.Reflectance 
        
"""
# 1. Set path to laz2Np dll
DLLPATH = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\LAZ2NP\OS_WIN\Las2Array_StaticLibrary.dll"


# 2. Set input and output paths
inputLas = r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\TREES_FINAL\200406_100502_Sample_R_Georef_SpatialSampleTREE_11816.laz"

# 3. Read point cloud
LAZCONTENT = ReadLaz.ReadLaz(inputLas, DLLPATH)

TREE_Density = Processing.Stastitic_voxel(
    LAZCONTENT,
    useroption="Density",
    pts_min=3,  # number min of points to consider a voxel empty
    vs=0.2,  # 20 cm resolution
    ATRIBUTE=[],
)


# OUTPUT RESULT - CLASS WITH VOXEL GRID AND DENSITY
fields = [
    f
    for f in dir(TREE_Density)
    if not callable(getattr(TREE_Density, f)) and not f.startswith("__")
]
print(fields)

DENS_X = np.nansum(TREE_Density.Density, axis=0)
DENS_Y = np.nansum(TREE_Density.Density, axis=1)
DENS_Z = np.nansum(TREE_Density.Density, axis=2)

DENS_X[DENS_X == 0] = np.nan
DENS_Z[DENS_Z == 0] = np.nan


# PLOT EXAMPLE
fig = plt.figure(1)
vmin = np.nanmin(DENS_X)
vmax = np.nanmax(DENS_X)
plt.title("Voxel vizualisation YZ perspective", fontsize=12)
plt.pcolor(TREE_Density.GridY[0, :, :], TREE_Density.GridZ[0, :, :], DENS_X, cmap="jet")
plt.colorbar()
plt.clim(vmin, vmax)
plt.gca().set_aspect("equal", adjustable="box")
plt.xlabel("y [m]", fontsize=8)
plt.ylabel("z [m]", fontsize=8)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)

fig = plt.figure(2)
plt.title("Voxel vizualisation XY PERSPECTIVE", fontsize=12)
vmin = np.nanmin(DENS_Z)
vmax = np.nanmax(DENS_Z)
plt.pcolor(TREE_Density.GridX[:, :, 0], TREE_Density.GridY[:, :, 0], DENS_Z, cmap="jet")
plt.gca().set_aspect("equal", adjustable="box")
plt.colorbar()
plt.clim(vmin, vmax)
plt.xlabel("X [m]", fontsize=8)
plt.ylabel("Y [m]", fontsize=8)
plt.xticks(fontsize=8)
plt.yticks(fontsize=8)
