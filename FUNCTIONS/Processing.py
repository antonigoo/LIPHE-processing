# -*- co++ng: utf-8 -*-
"""
PROGRAMMERS:

MARIANA BATISTA CAMPOS - mariana.campos@nls.fi
RESEARCHER AT FINNISH GEOSPATIAL INSTITUTE - NATIONAL LAND OF SURVEY

RAMI ECHRITI - rami.echriti@nls.fi
RESEARCHER AT FINNISH GEOSPATIAL INSTITUTE - NATIONAL LAND OF SURVEY

THIS SCRIPT IS AN COLLECTION OF PYTHON FUNCTION TO PROCESS LIPHE DATA FROM FULL POINT CLOUD TO INDIVIDUAL TREES

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

LIST OF FUNCTIONS:

1. Resample (random point cloud resample)
3. Spatial_sample (Voxel-based resample)
4. RectifLaz
5. HELMERT3D (point cloud georeferencing based on control points)
6. ClippingTree (Tree segmentation based on tree map)
7. COMPUTE_EXTRA_PARAMETERS
8. Stastitic_voxel
9. TreeParameters

"""


""" 
PROCESSING: STRUCTURAL REDUCTION SCRIPT

OPTIONS:
1. RESAMPLE POINT CLOUD RANDOMICALLY : Take every N:th point (exists)
2. RANDOM SAMPLE: Select wanted point proportion randomly - Fixed number of points
3. RANDOM SAMPLE: Select wanted point proportion randomly - Percentage of points
4. Selected points based on their list indices

MANDATORY: LAZCONTENT, PCD 
           E.G: TESTE=Processing.Resample(LAZCONTENT, PCD)
OPTIONAL: Extra, ExtraBytes_name
          IF EXTRABYTES CREATE A GENERAL ARRAY AND SET THE NUMBER OF POINTS
          E.G:TESTE, EXTRA=Processing.Resample(LAZCONTENT, PCD, Extra, ExtraBytes_name)
"""


def add_extra_bytes(las_content, extra_bytes_names):
    import numpy as np
    
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
    return extra_bytes_array


def Resample(LAZCONTENT, useroption, PCD, EXTRA=[], ExtraBytes_name=[]):
    import numpy as np

    size = len(LAZCONTENT.x)

    class RESAMPLE:
        pass

    if useroption == 1:
        if hasattr(LAZCONTENT, "x") == True:
            x = LAZCONTENT.x[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "x", x)
        if hasattr(LAZCONTENT, "y") == True:
            y = LAZCONTENT.y[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "y", y)
        if hasattr(LAZCONTENT, "z") == True:
            z = LAZCONTENT.z[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "z", z)
        if hasattr(LAZCONTENT, "return_number") == True:
            rn = LAZCONTENT.return_number[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "return_number", rn)
        if hasattr(LAZCONTENT, "number_of_returns") == True:
            nr = LAZCONTENT.number_of_returns[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "number_of_returns", nr)
        if hasattr(LAZCONTENT, "intensity") == True:
            intensity = LAZCONTENT.intensity[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "intensity", intensity)
        if hasattr(LAZCONTENT, "scan_direction_flag") == True:
            scan_direction_flag = LAZCONTENT.scan_direction_flag[
                np.arange(0, size, PCD)
            ]
            setattr(RESAMPLE, "scan_direction_flag", scan_direction_flag)
        if hasattr(LAZCONTENT, "edge_of_flight_line") == True:
            edge_of_flight_line = LAZCONTENT.edge_of_flight_line[
                np.arange(0, size, PCD)
            ]
            setattr(RESAMPLE, "edge_of_flight_line", edge_of_flight_line)
        if hasattr(LAZCONTENT, "classification") == True:
            classification = LAZCONTENT.classification[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "classification", classification)
        if hasattr(LAZCONTENT, "scan_angle_rank") == True:
            scan_angle_rank = LAZCONTENT.scan_angle_rank[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "scan_angle_rank", scan_angle_rank)
        if hasattr(LAZCONTENT, "user_data") == True:
            user_data = LAZCONTENT.user_data[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "user_data", user_data)
        if hasattr(LAZCONTENT, "gps_time") == True:
            gps_time = LAZCONTENT.gps_time[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "gps_time", gps_time)
        if hasattr(LAZCONTENT, "rgb") == True:
            rgb = LAZCONTENT.rgb[np.arange(0, size, PCD)]
            setattr(RESAMPLE, "rgb", rgb)
        if len(ExtraBytes_name) > 0:
            number_attributes = len(EXTRA)
            NP = len(x)
            EXTRA_R = np.empty((number_attributes, NP), dtype=np.float32)
            for i in range(number_attributes):
                default = EXTRA[i]
                default = default[np.arange(0, size, PCD)]
                EXTRA_R[i] = default
                setattr(RESAMPLE, ExtraBytes_name[i], default)
            setattr(RESAMPLE, "ExtraBytes_name", ExtraBytes_name)

    if useroption == 2 or useroption == 3 or useroption == 4:
        # CHECKING USER OPTIONS >> INPUT PCD
        if useroption == 3:
            # PCD IS A PERCENTAGE OF POINTS
            PCD = int(round((PCD * size) / 100))

        if useroption == 2 or useroption == 3:
            indices = np.random.choice(LAZCONTENT.x.shape[0], PCD)

        if useroption == 4:
            indices = PCD

        # REDUCE CLOUD
        if hasattr(LAZCONTENT, "x") == True:
            x = LAZCONTENT.x[indices]
            setattr(RESAMPLE, "x", x)
        if hasattr(LAZCONTENT, "y") == True:
            y = LAZCONTENT.y[indices]
            setattr(RESAMPLE, "y", y)
        if hasattr(LAZCONTENT, "z") == True:
            z = LAZCONTENT.z[indices]
            setattr(RESAMPLE, "z", z)
        if hasattr(LAZCONTENT, "return_number") == True:
            rn = LAZCONTENT.return_number[indices]
            setattr(RESAMPLE, "return_number", rn)
        if hasattr(LAZCONTENT, "number_of_returns") == True:
            nr = LAZCONTENT.number_of_returns[indices]
            setattr(RESAMPLE, "number_of_returns", nr)
        if hasattr(LAZCONTENT, "intensity") == True:
            intensity = LAZCONTENT.intensity[indices]
            setattr(RESAMPLE, "intensity", intensity)
        if hasattr(LAZCONTENT, "scan_direction_flag") == True:
            scan_direction_flag = LAZCONTENT.scan_direction_flag[indices]
            setattr(RESAMPLE, "scan_direction_flag", scan_direction_flag)
        if hasattr(LAZCONTENT, "edge_of_flight_line") == True:
            edge_of_flight_line = LAZCONTENT.edge_of_flight_line[indices]
            setattr(RESAMPLE, "edge_of_flight_line", edge_of_flight_line)
        if hasattr(LAZCONTENT, "classification") == True:
            classification = LAZCONTENT.classification[indices]
            setattr(RESAMPLE, "classification", classification)
        if hasattr(LAZCONTENT, "scan_angle_rank") == True:
            scan_angle_rank = LAZCONTENT.scan_angle_rank[indices]
            setattr(RESAMPLE, "scan_angle_rank", scan_angle_rank)
        if hasattr(LAZCONTENT, "user_data") == True:
            user_data = LAZCONTENT.user_data[indices]
            setattr(RESAMPLE, "user_data", user_data)
        if hasattr(LAZCONTENT, "gps_time") == True:
            gps_time = LAZCONTENT.gps_time[indices]
            setattr(RESAMPLE, "gps_time", gps_time)
        if hasattr(LAZCONTENT, "rgb") == True:
            rgb = LAZCONTENT.rgb[indices]
            setattr(RESAMPLE, "rgb", rgb)
        if len(ExtraBytes_name) > 0:
            number_attributes = len(EXTRA)
            NP = len(x)
            EXTRA_R = np.empty((number_attributes, NP), dtype=np.float32)
            for i in range(number_attributes):
                default = EXTRA[i]
                default = default[indices]
                EXTRA_R[i] = default
                setattr(RESAMPLE, ExtraBytes_name[i], default)
            setattr(RESAMPLE, "ExtraBytes_name", ExtraBytes_name)

    if len(ExtraBytes_name) > 0:
        return RESAMPLE, EXTRA_R

    if len(ExtraBytes_name) == 0:
        return RESAMPLE


"""
PROCESSING: RESAMPLE POINT CLOUD BASED ON THE DENSITY

MANDATORY: LAZCONTENT, PCD
           E.G: TESTE=Processing.Resample(LAZCONTENT, PCD)

OPTIONAL: Extra, ExtraBytes_name
          IF EXTRABYTES CREATE A GENERAL ARRAY AND SET THE NUMBER OF POINTS
          E.G:TESTE, EXTRA=Processing.Resample(LAZCONTENT, PCD, Extra, ExtraBytes_name)

REQUIREMENTS: Numba and pykdtree

"""


def Spatial_sample(
    LAZCONTENT, useroption, pts_min, vs, npoints, EXTRA, ExtraBytes_name, n_jobs=1
):
    import numba_algorithms as na
    from pykdtree.kdtree import KDTree
    import time
    import numpy as np

    # CREATE GRID CELL
    start = time.perf_counter()
    fields = [
        f
        for f in dir(LAZCONTENT)
        if not callable(getattr(LAZCONTENT, f)) and not f.startswith("__")
    ]

    LAZ_fields = ["Reflectance", "reflectance", "intensity", "z"]
    LAZ_fields = np.array(LAZ_fields)
    fields = np.array(fields)

    if len(np.where(fields == LAZ_fields[3])[0]) > 0:
        ATRIBUTE = LAZCONTENT.z
    if len(np.where(fields == LAZ_fields[2])[0]) > 0:
        ATRIBUTE = LAZCONTENT.intensity
    if len(np.where(fields == LAZ_fields[1])[0]) > 0:
        ATRIBUTE = LAZCONTENT.reflectance
    if len(np.where(fields == LAZ_fields[0])[0]) > 0:
        ATRIBUTE = LAZCONTENT.Reflectance

    means, MeanReflec = na.compute_grid_means(
        LAZCONTENT.x, LAZCONTENT.y, LAZCONTENT.z, ATRIBUTE, vs, pts_min
    )
    DATA_MEAN = means
    print(f"Grid means computed, took {time.perf_counter()-start:.2f} s")
    # print(d)
    # ESTIMATED TIME = 7min for 42G las file

    if useroption == "neighbour" or useroption == "mean":
        start = time.perf_counter()
        # Large leafsize since only one query is done
        tree = KDTree(
            np.vstack([LAZCONTENT.x, LAZCONTENT.y, LAZCONTENT.z]).T, leafsize=256
        )

        print(f"Neighbor setup complete, took {time.perf_counter()-start:.2f} s")
        start = time.perf_counter()
        _, neighbour_indices = tree.query(means, k=npoints)

        if npoints > 1:
            neighbour_indices = neighbour_indices.flatten()

        if npoints == 1:
            for k in range(len(ExtraBytes_name)):
                if ExtraBytes_name[k] == "Reflectance":
                    EXTRA[k][neighbour_indices] = MeanReflec

        del means, tree, MeanReflec
        print(f"Neighbor search complete, took {time.perf_counter()-start:.2f} s")

        class SPATIAL_RESAMPLE:
            pass

        if useroption == "neighbour":
            lx = len(LAZCONTENT.x[neighbour_indices])
            setattr(SPATIAL_RESAMPLE, "x", LAZCONTENT.x[neighbour_indices])
            setattr(SPATIAL_RESAMPLE, "y", LAZCONTENT.y[neighbour_indices])
            setattr(SPATIAL_RESAMPLE, "z", LAZCONTENT.z[neighbour_indices])

        if useroption == "mean":
            lx = len(DATA_MEAN[:, 0])
            setattr(SPATIAL_RESAMPLE, "x", DATA_MEAN[:, 0])
            setattr(SPATIAL_RESAMPLE, "y", DATA_MEAN[:, 1])
            setattr(SPATIAL_RESAMPLE, "z", DATA_MEAN[:, 2])

        if hasattr(LAZCONTENT, "return_number"):
            rn = LAZCONTENT.return_number[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "return_number", rn)

        if hasattr(LAZCONTENT, "number_of_returns"):
            nr = LAZCONTENT.number_of_returns[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "number_of_returns", nr)

        if hasattr(LAZCONTENT, "intensity"):
            intensity = LAZCONTENT.intensity[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "intensity", intensity)

        if hasattr(LAZCONTENT, "Amplitude"):
            intensity = LAZCONTENT.Amplitude[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "intensity", intensity)

        if hasattr(LAZCONTENT, "scan_direction_flag"):
            scan_direction_flag = LAZCONTENT.scan_direction_flag[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "scan_direction_flag", scan_direction_flag)

        if hasattr(LAZCONTENT, "edge_of_flight_line"):
            edge_of_flight_line = LAZCONTENT.edge_of_flight_line[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "edge_of_flight_line", edge_of_flight_line)

        if hasattr(LAZCONTENT, "classification"):
            classification = LAZCONTENT.classification[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "classification", classification)

        if hasattr(LAZCONTENT, "scan_angle_rank"):
            scan_angle_rank = LAZCONTENT.scan_angle_rank[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "scan_angle_rank", scan_angle_rank)

        if hasattr(LAZCONTENT, "user_data"):
            user_data = LAZCONTENT.user_data[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "user_data", user_data)

        if hasattr(LAZCONTENT, "gps_time"):
            gps_time = LAZCONTENT.gps_time[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "gps_time", gps_time)

        if hasattr(LAZCONTENT, "rgb"):
            rgb = LAZCONTENT.rgb[neighbour_indices]
            setattr(SPATIAL_RESAMPLE, "rgb", rgb)

        if ExtraBytes_name:
            number_attributes = len(EXTRA)
            NP = lx
            EXTRA_R = np.empty((number_attributes, NP), dtype=np.float32)
            for i in range(number_attributes):
                default = EXTRA[i][neighbour_indices]
                default = np.reshape(default, (len(default),))
                EXTRA_R[i] = default
                setattr(SPATIAL_RESAMPLE, ExtraBytes_name[i], default)
        setattr(SPATIAL_RESAMPLE, "ExtraBytes_name", ExtraBytes_name)

    # ESTIMATED TIME = 463s - 7 MIN
    if useroption == "dist":
        from scipy import stats

        binsx = np.arange(min(LAZCONTENT.x), max(LAZCONTENT.x), vs)
        binsy = np.arange(min(LAZCONTENT.y), max(LAZCONTENT.y), vs)
        binsz = np.arange(min(LAZCONTENT.z), max(LAZCONTENT.z), vs)

        # BinnedStatisticResult: statistic, bin_edges, binnumber
        resx = stats.binned_statistic(LAZCONTENT.x, None, "count", binsx)
        resy = stats.binned_statistic(LAZCONTENT.y, None, "count", binsy)
        resz = stats.binned_statistic(LAZCONTENT.z, None, "count", binsz)

        idx = resx.binnumber - 1
        nx = len(binsx)
        idy = resy.binnumber - 1
        ny = len(binsy)
        idz = resz.binnumber - 1
        nz = len(binsz)

        # CREATE GRID CELL
        idgrid = idx + (idy * nx) + (idz * nx * ny)
        _, unique_indices, unique_counts = np.unique(
            idgrid, return_index=True, return_counts=True
        )
        P = unique_indices[unique_counts > pts_min]

        class SPATIAL_RESAMPLE:
            pass

        x = LAZCONTENT.x[P]
        y = LAZCONTENT.y[P]
        z = LAZCONTENT.z[P]
        setattr(SPATIAL_RESAMPLE, "x", x)
        setattr(SPATIAL_RESAMPLE, "y", y)
        setattr(SPATIAL_RESAMPLE, "z", z)

        if hasattr(LAZCONTENT, "return_number") == True:
            rn = LAZCONTENT.return_number[P]
            setattr(SPATIAL_RESAMPLE, "return_number", rn)
        if hasattr(LAZCONTENT, "number_of_returns") == True:
            nr = LAZCONTENT.number_of_returns[P]
            setattr(SPATIAL_RESAMPLE, "number_of_returns", nr)
        if hasattr(LAZCONTENT, "intensity") == True:
            intensity = LAZCONTENT.intensity[P]
            setattr(SPATIAL_RESAMPLE, "intensity", intensity)
        if hasattr(LAZCONTENT, "Amplitude") == True:
            intensity = LAZCONTENT.Amplitude[P]
            setattr(SPATIAL_RESAMPLE, "intensity", intensity)
        if hasattr(LAZCONTENT, "scan_direction_flag") == True:
            scan_direction_flag = LAZCONTENT.scan_direction_flag[P]
            setattr(SPATIAL_RESAMPLE, "scan_direction_flag", scan_direction_flag)
        if hasattr(LAZCONTENT, "edge_of_flight_line") == True:
            edge_of_flight_line = LAZCONTENT.edge_of_flight_line[P]
            setattr(SPATIAL_RESAMPLE, "edge_of_flight_line", edge_of_flight_line)
        if hasattr(LAZCONTENT, "classification") == True:
            classification = LAZCONTENT.classification[P]
            setattr(SPATIAL_RESAMPLE, "classification", classification)
        if hasattr(LAZCONTENT, "scan_angle_rank") == True:
            scan_angle_rank = LAZCONTENT.scan_angle_rank[P]
            setattr(SPATIAL_RESAMPLE, "scan_angle_rank", scan_angle_rank)
        if hasattr(LAZCONTENT, "user_data") == True:
            user_data = LAZCONTENT.user_data[P]
            setattr(SPATIAL_RESAMPLE, "user_data", user_data)
        if hasattr(LAZCONTENT, "gps_time") == True:
            gps_time = LAZCONTENT.gps_time[P]
            setattr(SPATIAL_RESAMPLE, "gps_time", gps_time)
        if hasattr(LAZCONTENT, "rgb") == True:
            rgb = LAZCONTENT.rgb[P]
            setattr(SPATIAL_RESAMPLE, "rgb", rgb)

        if len(ExtraBytes_name) > 0:
            number_attributes = len(EXTRA)
            NP = len(x)
            EXTRA_R = np.empty((number_attributes, NP), dtype=np.float32)
            for i in range(number_attributes):
                default = EXTRA[i]
                default = default[P]
                EXTRA_R[i] = default
                setattr(SPATIAL_RESAMPLE, ExtraBytes_name[i], default)
        setattr(SPATIAL_RESAMPLE, "ExtraBytes_name", ExtraBytes_name)

    if len(ExtraBytes_name) > 0:
        return SPATIAL_RESAMPLE, EXTRA_R

    if len(ExtraBytes_name) == 0:
        return SPATIAL_RESAMPLE


""" 

PROCESSING: RECTIFY OBLIQUE POINT CLOUD FOR A NORMALIZED LOCAL SYSTEMS ALIGN TO THE GROUND

INPUT: COORDINATES (LAZCONTENT.x, LAZCONTENT.y, LAZCONTENT.z) AND TRANSFORMATION PARAMETERS (Class)
        Transformation is a class that contains the rigid body transformation (rotation in degrees and translation in meters) to normalize the point cloud

OUTPUT: RECTIFIED COORDINATES

"""


def RectifLaz(x, y, z, transformation):
    import math
    import numpy as np

    w = transformation.w * math.pi / 180
    fi = transformation.fi * math.pi / 180
    k = transformation.k * math.pi / 180

    aX = transformation.x
    aY = transformation.y
    aZ = transformation.z

    Rotfi = np.empty((3, 3), dtype="float32")
    Rotfi[0, 0] = math.cos(fi)
    Rotfi[0, 1] = 0
    Rotfi[0, 2] = math.sin(fi)
    Rotfi[1, 0] = 0
    Rotfi[1, 1] = 1
    Rotfi[1, 2] = 0
    Rotfi[2, 0] = -math.sin(fi)
    Rotfi[2, 1] = 0
    Rotfi[2, 2] = math.cos(fi)

    Rotw = np.empty((3, 3), dtype="float32")
    Rotw[0, 0] = 1
    Rotw[0, 1] = 0
    Rotw[0, 2] = 0
    Rotw[1, 0] = 0
    Rotw[1, 1] = math.cos(w)
    Rotw[1, 2] = -math.sin(w)
    Rotw[2, 0] = 0
    Rotw[2, 1] = math.sin(w)
    Rotw[2, 2] = math.cos(w)

    Rotk = np.empty((3, 3), dtype="float32")
    Rotk[0, 0] = math.cos(k)
    Rotk[0, 1] = -math.sin(k)
    Rotk[0, 2] = 0
    Rotk[1, 0] = math.sin(k)
    Rotk[1, 1] = math.cos(k)
    Rotk[1, 2] = 0
    Rotk[2, 0] = 0
    Rotk[2, 1] = 0
    Rotk[2, 2] = 1

    x1 = []
    y1 = []
    z1 = []

    for X in zip(x, y, z):
        # PASSIVE ROTATION
        X = Rotw.dot(X)
        X = Rotfi.dot(X)
        X = Rotk.dot(X)
        # ADD TRANSLATION TO AVOID NEGATIVE VALUES
        x1.append(X[0] + aX)
        y1.append(X[1] + aY)
        z1.append(X[2] + aZ)

    x1 = np.array(x1, dtype=np.float64)
    y1 = np.array(y1, dtype=np.float64)
    z1 = np.array(z1, dtype=np.float64)

    return x1, y1, z1


""" 
----------------------------POINT CLOUD GEOREFERENCING----------------------------
THIS FUNCTION CAN BE USED TO REGISTER OR GEOREFERENCE A POINT CLOUD CONSIDERING KNOWN MATCHING POINTS OR CONTROL POINTS

TRANSFORMATIONS: Helmert3D

INPUT:LASCONTENT.x, LASCONTENT.z, LASCONTENT.z 
MATCH POINTS OR CONTROL POINTS IN BOTH CLOUDS.

OUTPUT:X, Y, Z at ETRS89-TM35FIN reference system
-----------------------------------------------------------------------------------
"""


def HELMERT3D(LAZCONTENT, MatchPoints):
    import numpy as np

    Lb = MatchPoints[
        0
    ]  # NP.ARRAY WITH THE lOCAL POINT COORDINATES MASURED IN THE POINT CLOUD
    Ref = MatchPoints[1]  # NP.ARRAY WITH THE POINT COORDINATES IN THE REFERENCE SYSTEM

    # BUNDLE ADJUSTMENT PARAMETERS
    n = int(len(MatchPoints[0]) / 3)
    Ne = n * 3
    A = np.zeros((Ne, 12), dtype=float)
    i = 0
    AFIM = np.zeros((3, 3), dtype=float)

    for k in range(n):
        A[i][0] = Ref[i]
        A[i][1] = Ref[i + 1]
        A[i][2] = Ref[i + 2]
        A[i][3] = 0
        A[i][4] = 0
        A[i][5] = 0
        A[i][6] = 0
        A[i][7] = 0
        A[i][8] = 0
        A[i][9] = 1
        A[i][10] = 0
        A[i][11] = 0
        # TRANSLATION
        j = i + 1
        A[j][0] = 0
        A[j][1] = 0
        A[j][2] = 0
        A[j][3] = Ref[i]
        A[j][4] = Ref[i + 1]
        A[j][5] = Ref[i + 2]
        A[j][6] = 0
        A[j][7] = 0
        A[j][8] = 0
        A[j][9] = 0
        A[j][10] = 1
        A[j][11] = 0
        # TRANSLATION
        j = j + 1
        A[j][0] = 0
        A[j][1] = 0
        A[j][2] = 0
        A[j][3] = 0
        A[j][4] = 0
        A[j][5] = 0
        A[j][6] = Ref[i]
        A[j][7] = Ref[i + 1]
        A[j][8] = Ref[i + 2]
        A[j][9] = 0
        A[j][10] = 0
        A[j][11] = 1
        # TRANSLATION
        i = i + 3

    N = np.transpose(A).dot(A)
    U = np.transpose(A).dot(Lb)
    NI = np.linalg.inv(N)
    X = NI.dot(U)

    # Point Cloud
    # a=X[0]; b=X[1]; c=X[2]; d=X[3]; e=X[4]; f=X[5]; g=X[6]; h=X[7]; i=X[8];
    AFIM[0][0] = X[0]
    AFIM[0][1] = X[1]
    AFIM[0][2] = X[2]

    AFIM[1][0] = X[3]
    AFIM[1][1] = X[4]
    AFIM[1][2] = X[5]

    AFIM[2][0] = X[6]
    AFIM[2][1] = X[7]
    AFIM[2][2] = X[8]

    AFIM_I = np.linalg.inv(AFIM)
    print("DONE - ISOGONAL PARAMETERS ESTIMATION")

    x1 = []
    y1 = []
    z1 = []
    # 3D-TRANSFORMATION ISO
    x = LAZCONTENT.x - X[9]
    y = LAZCONTENT.y - X[10]
    z = LAZCONTENT.z - X[11]

    print("RUNNING CLOUD TRANSFORMATION")
    for P in zip(x, y, z):
        ##3D TRANSFORMATION
        P_fid = AFIM_I.dot(P)
        x1.append(P_fid[0])
        y1.append(P_fid[1])
        z1.append(P_fid[2])

    x1 = np.array(x1, dtype=np.float64)
    y1 = np.array(y1, dtype=np.float64)
    z1 = np.array(z1, dtype=np.float64)

    return x1, y1, z1


""" 
----------------------------VORONOI CELLS----------------------------

THIS IS A HELPER FUNCTION TO CLIP TREES FROM THE FULL POINT CLOUD BASED ON VORONOI CELL CREATED BY A STEM MAP

PS: The build-in function in python creates Voronoi cells that may be infinite, and for this reason it is not explored here
REFERENCE: The function voronoi_finite_polygons_2d is gotten from github

-----------------------------------------------------------------------------------

"""


def voronoi_finite_polygons_2d(vor, radius=None):
    import numpy as np

    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            # finite region
            new_regions.append(vertices)
            continue

        # reconstruct a non-finite region
        ridges = all_ridges.get(p1)  # all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]
        TEST = all_ridges.get(p1)

        if (TEST == None) == False:
            for p2, v1, v2 in ridges:
                if v2 < 0:
                    v1, v2 = v2, v1
                if v1 >= 0:
                    # finite ridge: already in the region
                    continue

                # Compute the missing endpoint of an infinite ridge
                t = vor.points[p2] - vor.points[p1]  # tangent
                t /= np.linalg.norm(t)
                n = np.array([-t[1], t[0]])  # normal

                midpoint = vor.points[[p1, p2]].mean(axis=0)
                direction = np.sign(np.dot(midpoint - center, n)) * n
                far_point = vor.vertices[v2] + direction * radius

                new_region.append(len(new_vertices))
                new_vertices.append(far_point.tolist())

            # sort region counterclockwise
            vs = np.asarray([new_vertices[v] for v in new_region])
            c = vs.mean(axis=0)
            angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
            new_region = np.array(new_region)[np.argsort(angles)]

            # finish
            new_regions.append(new_region.tolist())

    return new_regions, np.asarray(new_vertices)


"""
PROCESSING: CLIPPING TREES FROM FULL POINT CLOUD BASED ON TREE STEM MAP
    
MANDATORY: LAZCONTENT and (BOX_COORD or/and BOX_ANGLES or CYLINDER or VORONOI
                           BOX_COORD AND BOX_ANGLE can be combined

OPTIONAL:Extra, ExtraBytes_name
           E.G: TREE, EXTRA=Processing.ClippingTree (LAZCONTENT, BOX_COORD[0], BOX_ANGLES[0], Extra, ExtraBytes_name)

OUTPUT:
    
    BOX_COORD or BOX_ANGLES or CYLINDER option provide one tree class with all laz paramenters >> Loop required for many trees in the main code
    VORONOI option provide multiple tree classes with all laz parameter >> LIST of Class
    
    
"""


def ClippingTree(
    LAZCONTENT,
    BOX_COORD=[],
    BOX_ANGLES=[],
    CYLINDER=[],
    VORONOI=[],
    Extra=[],
    ExtraBytes_name=[],
):
    import numpy as np
    from matplotlib.path import Path
    from scipy.spatial import Voronoi

    # CHECKING USER OPTIONS
    if (
        (len(BOX_COORD) == 0)
        and (len(BOX_ANGLES) == 0)
        and (len(CYLINDER) == 0)
        and (len(VORONOI) == 0)
    ):
        print("Please informe a valid clipping option")

    if (len(BOX_COORD) > 0) and (len(BOX_ANGLES) == 0):
        P = np.where(
            (LAZCONTENT.x > BOX_COORD[0])
            & (LAZCONTENT.y > BOX_COORD[1])
            & (LAZCONTENT.z > BOX_COORD[2])
            & (LAZCONTENT.x < BOX_COORD[3])
            & (LAZCONTENT.y < BOX_COORD[4])
            & (LAZCONTENT.z < BOX_COORD[5])
        )
        P = np.array(P[:][0])

    if (len(BOX_COORD) == 0) and (len(BOX_ANGLES) > 0):
        P = np.where(
            (LAZCONTENT.Theta > BOX_ANGLES[0])
            & (LAZCONTENT.Phi > BOX_ANGLES[1])
            & (LAZCONTENT.Range > BOX_ANGLES[2])
            & (LAZCONTENT.Theta < BOX_ANGLES[3])
            & (LAZCONTENT.Phi < BOX_ANGLES[4])
            & (LAZCONTENT.Range < BOX_ANGLES[5])
        )
        P = np.array(P[:][0])

    if (len(BOX_COORD) > 0) and (len(BOX_ANGLES) > 0):
        P = np.where(
            (LAZCONTENT.x > BOX_COORD[0])
            & (LAZCONTENT.y > BOX_COORD[1])
            & (LAZCONTENT.z > BOX_COORD[2])
            & (LAZCONTENT.x < BOX_COORD[3])
            & (LAZCONTENT.y < BOX_COORD[4])
            & (LAZCONTENT.z < BOX_COORD[5])
            & (LAZCONTENT.Theta > BOX_ANGLES[0])
            & (LAZCONTENT.Phi > BOX_ANGLES[1])
            & (LAZCONTENT.Range > BOX_ANGLES[2])
            & (LAZCONTENT.Theta < BOX_ANGLES[3])
            & (LAZCONTENT.Phi < BOX_ANGLES[4])
            & (LAZCONTENT.Range < BOX_ANGLES[5])
        )
        P = np.array(P[:][0])

    if (len(BOX_COORD) == 0) and (len(BOX_ANGLES) == 0) and (len(CYLINDER) > 0):
        Dx = LAZCONTENT.x - CYLINDER[0]
        Dy = LAZCONTENT.y - CYLINDER[1]
        Dz = LAZCONTENT.z - CYLINDER[2]
        DIST = np.sqrt((Dx * Dx) + (Dy * Dy))
        P = np.where((DIST < CYLINDER[3]) & (Dz < 50))
        P = np.array(P[:][0])

    if (
        (len(BOX_COORD) == 0)
        and (len(BOX_ANGLES) == 0)
        and (len(CYLINDER) == 0)
        and (len(VORONOI) > 0)
    ):
        print("VORONOI SEGMENTATION - MULTIPLE TREES")
        vor = Voronoi(VORONOI[0][:, 0:2])
        regions, vertices = voronoi_finite_polygons_2d(vor)
        polygon = []
        trees = []
        P = []
        Tree_Name = []

        # MAKE A POLYGON OF THE WHOLE AREA AND CHECK IF INDIVIDUAL COORDINATES ARE IN SIDE IT
        for i in range(len(regions)):
            polygon.append(vertices[regions[i]])
            xvalues = vertices[regions[i]].T[0]
            yvalues = vertices[regions[i]].T[1]
            xref = min(xvalues)
            yref = min(yvalues)
            if_edge = 0

            # The for loop gets rid of all trees at the edge of the map if their
            # Voronoi cell differs more than 15 units from the min point (it does not affect the
            # points inside the forest)

            for x in xvalues:
                if x > xref + 15 or x < -xref - 15:
                    if_edge = 1

            for y in yvalues:
                if y > yref + 15 or y < -yref - 15:
                    if_edge = 1

            trees.append(if_edge)

        # Polygon contains the information about the end point of vertices
        # a.k.a by connecting the points in polygon at the specific index, we get the voronoi cell
        # for the point in question. Notice that arrays in polygon are in order such that the first
        # tree in trees, has the voronoi cell of the first element of polygon etc.
        del i, x, y, xvalues, yvalues, xref, yref, if_edge

        for i in range(len(polygon)):
            p = Path(polygon[i])
            x, y = LAZCONTENT.x.flatten(), LAZCONTENT.y.flatten()
            points = np.vstack((x, y)).T
            grid = p.contains_points(points)
            P.append(grid)
            Tree_Name.append(VORONOI[0][i, 2])

        P = np.array(P)
        Tree_Name = np.array(Tree_Name)

    # SAVING TREE POINT CLOUD
    if len(VORONOI) == 0:

        class TREE:
            pass

        x = LAZCONTENT.x[P]
        setattr(TREE, "x", x)
        y = LAZCONTENT.y[P]
        setattr(TREE, "y", y)
        z = LAZCONTENT.z[P]
        setattr(TREE, "z", z)

        if hasattr(LAZCONTENT, "return_number"):
            rn = LAZCONTENT.return_number[P]
            setattr(TREE, "return_number", rn)
        if hasattr(LAZCONTENT, "number_of_returns"):
            nr = LAZCONTENT.number_of_returns[P]
            setattr(TREE, "number_of_returns", nr)
        if hasattr(LAZCONTENT, "intensity"):
            intensity = LAZCONTENT.intensity[P]
            setattr(TREE, "intensity", intensity)
        if hasattr(LAZCONTENT, "Amplitude"):
            intensity = LAZCONTENT.Amplitude[P]
            setattr(TREE, "intensity", intensity)
        if hasattr(LAZCONTENT, "scan_direction_flag"):
            scan_direction_flag = LAZCONTENT.scan_direction_flag[P]
            setattr(TREE, "scan_direction_flag", scan_direction_flag)
        if hasattr(LAZCONTENT, "edge_of_flight_line"):
            edge_of_flight_line = LAZCONTENT.edge_of_flight_line[P]
            setattr(TREE, "edge_of_flight_line", edge_of_flight_line)
        if hasattr(LAZCONTENT, "classification"):
            classification = LAZCONTENT.classification[P]
            setattr(TREE, "classification", classification)
        if hasattr(LAZCONTENT, "scan_angle_rank"):
            scan_angle_rank = LAZCONTENT.scan_angle_rank[P]
            setattr(TREE, "scan_angle_rank", scan_angle_rank)
        if hasattr(LAZCONTENT, "user_data"):
            user_data = LAZCONTENT.user_data[P]
            setattr(TREE, "user_data", user_data)
        if hasattr(LAZCONTENT, "gps_time"):
            gps_time = LAZCONTENT.gps_time[P]
            setattr(TREE, "gps_time", gps_time)
        if hasattr(LAZCONTENT, "rgb"):
            rgb = LAZCONTENT.rgb[P]
            setattr(TREE, "rgb", rgb)

        if len(ExtraBytes_name) > 0:
            number_attributes = len(Extra)
            NP = len(x)
            EXTRA_TREE = np.empty((number_attributes, NP), dtype=np.float32)
            for i in range(number_attributes):
                default = Extra[i]
                default = default[P]
                EXTRA_TREE[i] = default
                setattr(TREE, ExtraBytes_name[i], default)
            setattr(TREE, "ExtraBytes_name", ExtraBytes_name)

        if len(ExtraBytes_name) > 0:
            return TREE, EXTRA_TREE
        else:
            return TREE

    if len(VORONOI) > 0:
        TREE_VORONOI = []
        TREE_EXTRA_VORONOI = []
        j = 0

        for PP in P:

            class TREE:
                pass

            x = LAZCONTENT.x[PP]
            setattr(TREE, "x", x)
            y = LAZCONTENT.y[PP]
            setattr(TREE, "y", y)
            z = LAZCONTENT.z[PP]
            setattr(TREE, "z", z)
            setattr(TREE, "name", Tree_Name[j])  # Tree_Name is not defined in all cases, be carefull 
            j = j + 1

            if hasattr(LAZCONTENT, "return_number"):
                rn = LAZCONTENT.return_number[PP]
                setattr(TREE, "return_number", rn)
            if hasattr(LAZCONTENT, "number_of_returns"):
                nr = LAZCONTENT.number_of_returns[PP]
                setattr(TREE, "number_of_returns", nr)
            if hasattr(LAZCONTENT, "intensity"):
                intensity = LAZCONTENT.intensity[PP]
                setattr(TREE, "intensity", intensity)
            if hasattr(LAZCONTENT, "Amplitude"):
                intensity = LAZCONTENT.Amplitude[PP]
                setattr(TREE, "intensity", intensity)
            if hasattr(LAZCONTENT, "scan_direction_flag"):
                scan_direction_flag = LAZCONTENT.scan_direction_flag[PP]
                setattr(TREE, "scan_direction_flag", scan_direction_flag)
            if hasattr(LAZCONTENT, "edge_of_flight_line"):
                edge_of_flight_line = LAZCONTENT.edge_of_flight_line[PP]
                setattr(TREE, "edge_of_flight_line", edge_of_flight_line)
            if hasattr(LAZCONTENT, "classification"):
                classification = LAZCONTENT.classification[PP]
                setattr(TREE, "classification", classification)
            if hasattr(LAZCONTENT, "scan_angle_rank"):
                scan_angle_rank = LAZCONTENT.scan_angle_rank[PP]
                setattr(TREE, "scan_angle_rank", scan_angle_rank)
            if hasattr(LAZCONTENT, "user_data"):
                user_data = LAZCONTENT.user_data[PP]
                setattr(TREE, "user_data", user_data)
            if hasattr(LAZCONTENT, "gps_time"):
                gps_time = LAZCONTENT.gps_time[PP]
                setattr(TREE, "gps_time", gps_time)
            if hasattr(LAZCONTENT, "rgb"):
                rgb = LAZCONTENT.rgb[PP]
                setattr(TREE, "rgb", rgb)

            if len(ExtraBytes_name) > 0:
                number_attributes = len(ExtraBytes_name)
                NP = len(x)
                EXTRA_TREE = np.empty((number_attributes, NP), dtype=np.float32)

                for i in range(number_attributes):
                    default = Extra[i]
                    default = default[PP]
                    EXTRA_TREE[i] = default
                    setattr(TREE, ExtraBytes_name[i], default)

                setattr(TREE, "ExtraBytes_name", ExtraBytes_name)
                TREE_EXTRA_VORONOI.append(EXTRA_TREE)

            TREE_VORONOI.append(TREE)

        if len(ExtraBytes_name) > 0:
            return TREE_VORONOI, TREE_EXTRA_VORONOI
        else:
            return TREE_VORONOI


"""

PROCESSING: COMPUTE_EXTRA_PARAMETERS

MANDATORY: LAZCONTENT, 
           EXTRA, 
           thetaStart,  thetaStop and thetaIncrement
           phiStart, phiStop and phiIncrement
        
"""


def COMPUTE_EXTRA_PARAMETERS(
    LAZCONTENT,
    EXTRA,
    thetaStart,
    thetaStop,
    thetaIncrement,
    phiStart,
    phiStop,
    phiIncrement,
):
    import math
    import numpy as np

    print("FOR NEW PARAMETERS RUNNING")
    aux11 = (LAZCONTENT.x) ** 2
    aux12 = (LAZCONTENT.y) ** 2
    aux13 = (LAZCONTENT.z) ** 2
    Range = np.sqrt(aux11 + aux12 + aux13)
    phi = []
    theta = []
    phi = np.arctan2(LAZCONTENT.y, LAZCONTENT.x)
    IDX1 = phi < 0
    phi[IDX1] = 2 * math.pi + phi[IDX1]
    IDX2 = phi < (phiStart * math.pi / 180)
    phi[IDX2] = phiStart * math.pi / 180
    IDX3 = phi > (phiStop * math.pi / 180)
    phi[IDX3] = phiStop * math.pi / 180
    del IDX1, IDX2, IDX3, aux11, aux12, aux13
    theta = np.arccos((LAZCONTENT.z) / Range)
    IDX1 = theta < (thetaStart * math.pi / 180)
    theta[IDX1] = thetaStart * math.pi / 180
    IDX2 = theta > (thetaStop * math.pi / 180)
    theta[IDX2] = thetaStop * math.pi / 180
    del IDX1, IDX2

    NP = len(LAZCONTENT.x)
    NEB = len(EXTRA) + 3
    EXTRA_TREE = np.empty((NEB, NP), dtype=np.float32)
    k = len(EXTRA)

    for n in range(k):
        EXTRA_TREE[n] = EXTRA[n]

    EXTRA_TREE[k] = np.array(Range)
    EXTRA_TREE[k + 1] = np.array(theta) * 180 / math.pi
    EXTRA_TREE[k + 2] = np.array(phi) * 180 / math.pi

    setattr(LAZCONTENT, "Range", Range)
    setattr(LAZCONTENT, "Theta", np.array(theta) * 180 / math.pi)
    setattr(LAZCONTENT, "Phi", np.array(phi) * 180 / math.pi)

    del Range, theta, phi
    return LAZCONTENT, EXTRA_TREE


"""
PROCESSING: NORMALIZE TREE POINT CLOUD TO THE GROUND

MANDATORY: LAZCONTENT - TREE POINT CLOUD 
           METADATA - TREE STEM

"""


def Ground_Normalize(LAZCONTENT, offsets, th, Extra=[], ExtraBytes_name=[]):
    import numpy as np

    th = offsets[2] + th
    P = LAZCONTENT.z > th

    X = LAZCONTENT.x[P] - offsets[0]
    Y = LAZCONTENT.y[P] - offsets[1]
    Z = LAZCONTENT.z[P] - offsets[2]

    class TREE:
        x = X
        y = Y
        z = Z

    if hasattr(LAZCONTENT, "return_number"):
        rn = LAZCONTENT.return_number[P]
        setattr(TREE, "return_number", rn)
    if hasattr(LAZCONTENT, "number_of_returns"):
        nr = LAZCONTENT.number_of_returns[P]
        setattr(TREE, "number_of_returns", nr)
    if hasattr(LAZCONTENT, "intensity"):
        intensity = LAZCONTENT.intensity[P]
        setattr(TREE, "intensity", intensity)
    if hasattr(LAZCONTENT, "Amplitude"):
        intensity = LAZCONTENT.Amplitude[P]
        setattr(TREE, "intensity", intensity)
    if hasattr(LAZCONTENT, "scan_direction_flag"):
        scan_direction_flag = LAZCONTENT.scan_direction_flag[P]
        setattr(TREE, "scan_direction_flag", scan_direction_flag)
    if hasattr(LAZCONTENT, "edge_of_flight_line"):
        edge_of_flight_line = LAZCONTENT.edge_of_flight_line[P]
        setattr(TREE, "edge_of_flight_line", edge_of_flight_line)
    if hasattr(LAZCONTENT, "classification"):
        classification = LAZCONTENT.classification[P]
        setattr(TREE, "classification", classification)
    if hasattr(LAZCONTENT, "scan_angle_rank"):
        scan_angle_rank = LAZCONTENT.scan_angle_rank[P]
        setattr(TREE, "scan_angle_rank", scan_angle_rank)
    if hasattr(LAZCONTENT, "user_data"):
        user_data = LAZCONTENT.user_data[P]
        setattr(TREE, "user_data", user_data)
    if hasattr(LAZCONTENT, "gps_time"):
        gps_time = LAZCONTENT.gps_time[P]
        setattr(TREE, "gps_time", gps_time)
    if hasattr(LAZCONTENT, "rgb"):
        rgb = LAZCONTENT.rgb[P]
        setattr(TREE, "rgb", rgb)

    if len(ExtraBytes_name) > 0:
        number_attributes = len(Extra)
        NP = len(X)
        EXTRA_TREE = np.empty((number_attributes, NP), dtype=np.float32)
        for i in range(number_attributes):
            default = Extra[i]
            default = default[P]
            EXTRA_TREE[i] = default
            setattr(TREE, ExtraBytes_name[i], default)
        setattr(TREE, "ExtraBytes_name", ExtraBytes_name)

    if len(ExtraBytes_name) > 0:
        return TREE, EXTRA_TREE
    else:
        return TREE


"""

INDIVIDUAL TREE POINT CLOUD PROCESSING AND ATTRIBUTE ESTIMATIONS


PROCESSING: Stastitic_voxel - ESTIMATE THE AVERAGE VALUE OF A ATTRIBUTE (e.g. Reflectance or intensity) INSIDE OF A VOXELS (useroption =='Atributes') OR
                            - ESTIMATE THE CENTROID OF A VOXEL BASED ON THE 3D COORDINATES ((useroption =='Centroid'))
                            - ESTIMATE THE DENSITE OF A VOXEL BASED ON THE 3D COORDINATES ((useroption =='Density'))                             

MANDATORY: LAZCONTENT, 
           useroption: Atributes, Centroid or Density
           pts_min: Minimum number of points to consider a voxel as valid or  not empty   
           vs: Voxel resolution (cubic)

           
OPTIONAL:ATRIBUTE is only mandatory for (useroption =='Atributes')
           
REQUIREMENTS: scipy (https://scipy.org/) and numpy

"""


def Stastitic_voxel(LAZCONTENT, useroption, pts_min, vs, ATRIBUTE=[]):
    if useroption == "Atributes":
        from scipy import stats
        import numpy as np

        binsx = np.arange(min(LAZCONTENT.x), max(LAZCONTENT.x), vs)
        binsy = np.arange(min(LAZCONTENT.y), max(LAZCONTENT.y), vs)
        binsz = np.arange(min(LAZCONTENT.z), max(LAZCONTENT.z), vs)

        # BinnedStatisticResult: statistic, bin_edges, binnumber
        resx = stats.binned_statistic(LAZCONTENT.x, None, "count", binsx)
        resy = stats.binned_statistic(LAZCONTENT.y, None, "count", binsy)
        resz = stats.binned_statistic(LAZCONTENT.z, None, "count", binsz)

        idx = resx.binnumber - 1
        nx = len(binsx)
        idy = resy.binnumber - 1
        ny = len(binsy)
        idz = resz.binnumber - 1
        nz = len(binsz)

        # CREATE GRID CELL
        idgrid = idx + (idy * nx) + (idz * nx * ny)

        summx = np.zeros(nx * ny * nz)
        count = np.zeros(nx * ny * nz)
        NP = len(LAZCONTENT.x)

        for i in range(NP):
            summx[idgrid[i]] = summx[idgrid[i]] + ATRIBUTE[i]
            count[idgrid[i]] = count[idgrid[i]] + 1

        nonzeros = np.where(count > pts_min)
        SA = summx[nonzeros] / count[nonzeros]

        class VOXEL:
            pass

        # take the atribute name - fields=[f for f in dir(ATTRIBUTES) if not callable(getattr(ATTRIBUTES,f)) and not f.startswith('__')]
        setattr(VOXEL, "Reflectance", SA)

    if useroption == "Centroid":
        from scipy import stats
        import numpy as np

        binsx = np.arange(min(LAZCONTENT.x), max(LAZCONTENT.x), vs)
        binsy = np.arange(min(LAZCONTENT.y), max(LAZCONTENT.y), vs)
        binsz = np.arange(min(LAZCONTENT.z), max(LAZCONTENT.z), vs)

        # BinnedStatisticResult: statistic, bin_edges, binnumber
        resx = stats.binned_statistic(LAZCONTENT.x, None, "count", binsx)
        resy = stats.binned_statistic(LAZCONTENT.y, None, "count", binsy)
        resz = stats.binned_statistic(LAZCONTENT.z, None, "count", binsz)

        idx = resx.binnumber - 1
        nx = len(binsx)
        idy = resy.binnumber - 1
        ny = len(binsy)
        idz = resz.binnumber - 1
        nz = len(binsz)

        # CREATE GRID CELL
        idgrid = idx + (idy * nx) + (idz * nx * ny)
        summx = np.zeros(nx * ny * nz)
        summy = np.zeros(nx * ny * nz)
        summz = np.zeros(nx * ny * nz)
        count = np.zeros(nx * ny * nz)
        NP = len(LAZCONTENT.x)

        for i in range(NP):
            summx[idgrid[i]] = summx[idgrid[i]] + LAZCONTENT.x[i]
            summy[idgrid[i]] = summy[idgrid[i]] + LAZCONTENT.y[i]
            summz[idgrid[i]] = summz[idgrid[i]] + LAZCONTENT.z[i]
            count[idgrid[i]] = count[idgrid[i]] + 1

        nonzeros = np.where(count > pts_min)
        x1 = summx[nonzeros] / count[nonzeros]
        y1 = summy[nonzeros] / count[nonzeros]
        z1 = summz[nonzeros] / count[nonzeros]
        # output=count[nonzeros]

        class VOXEL:
            pass

        setattr(VOXEL, "x", x1)
        setattr(VOXEL, "y", y1)
        setattr(VOXEL, "z", z1)

    if useroption == "Density":
        # IMPORT LIBRARIES
        import numpy as np

        GRIDX_MIN = int(min(LAZCONTENT.x)) - 0.5
        GRIDX_MAX = int(max(LAZCONTENT.x)) + 0.5
        GRIDY_MIN = int(min(LAZCONTENT.y)) - 0.5
        GRIDY_MAX = int(max(LAZCONTENT.y)) + 0.5
        GRIDZ_MIN = int(min(LAZCONTENT.z)) - 0.5
        GRIDZ_MAX = int(max(LAZCONTENT.z)) + 0.5

        XGRD, YGRD, ZGRD = np.mgrid[
            GRIDX_MIN:GRIDX_MAX:vs, GRIDY_MIN:GRIDY_MAX:vs, GRIDZ_MIN:GRIDZ_MAX:vs
        ]
        # XGRD, YGRD, ZGRD = np.mgrid[min(LAZCONTENT.x):max(LAZCONTENT.x)+vs:vs, min(LAZCONTENT.y):max(LAZCONTENT.y)+vs:vs, min(LAZCONTENT.z):max(LAZCONTENT.z)+vs:vs]
        IDX = ((LAZCONTENT.x - min(LAZCONTENT.x)) / vs).astype(int)
        IDY = ((LAZCONTENT.y - min(LAZCONTENT.y)) / vs).astype(int)
        IDZ = ((LAZCONTENT.z - min(LAZCONTENT.z)) / vs).astype(int)

        # DENS=XGRD*0
        DENS = YGRD * 0

        for k in range(len(LAZCONTENT.x)):
            DENS[IDX[k], IDY[k], IDZ[k]] = DENS[IDX[k], IDY[k], IDZ[k]] + 1

        class VOXEL:
            pass

        setattr(VOXEL, "GridX", XGRD)
        setattr(VOXEL, "GridY", YGRD)
        setattr(VOXEL, "GridZ", ZGRD)
        setattr(VOXEL, "Density", DENS)

    return VOXEL


"""
As following support function for a vertical cylinder fitting

Reference:
http://www.int-arch-photogramm-remote-sens-spatial-inf-sci.net/XXXIX-B5/169/2012/isprsarchives-XXXIX-B5-169-2012.pdf

xyz is a matrix contain at least 5 rows, and each row stores x y z of a cylindrical surface
p is initial values of the parameter;
p[0] = Xc, x coordinate of the cylinder centre
P[1] = Yc, y coordinate of the cylinder centre
P[2] = alpha, rotation angle (radian) about the x-axis
P[3] = beta, rotation angle (radian) about the y-axis
P[4] = r, radius of the cylinder

th, threshold for the convergence of the least squares
"""


def calc_plane(x, y, z):
    import numpy as np

    a = np.column_stack((x, y, z))

    return np.linalg.lstsq(a, z)[0]


def project_points(x, y, z, a, b, c):
    """
    Projects the points with coordinates x, y, z onto the plane
    defined by a*x + b*y + c*z = 1
    """
    import numpy as np

    vector_norm = a * a + b * b + c * c
    normal_vector = np.array([a, b, c]) / np.sqrt(vector_norm)
    point_in_plane = np.array([a, b, c]) / vector_norm

    points = np.column_stack((x, y, z))
    points_from_point_in_plane = points - point_in_plane
    proj_onto_normal_vector = np.dot(points_from_point_in_plane, normal_vector)
    proj_onto_plane = (
        points_from_point_in_plane - proj_onto_normal_vector[:, None] * normal_vector
    )

    return point_in_plane + proj_onto_plane


def cylinderFitting(xyz, p, th):
    import numpy as np
    from scipy.optimize import leastsq

    x = xyz[:, 0]
    y = xyz[:, 1]
    z = xyz[:, 2]

    fitfunc = (
        lambda p, x, y, z: (
            -np.cos(p[3]) * (p[0] - x)
            - z * np.cos(p[2]) * np.sin(p[3])
            - np.sin(p[2]) * np.sin(p[3]) * (p[1] - y)
        )
        ** 2
        + (z * np.sin(p[2]) - np.cos(p[2]) * (p[1] - y)) ** 2
    )  # fit function
    errfunc = lambda p, x, y, z: fitfunc(p, x, y, z) - p[4] ** 2  # error function

    est_p, success = leastsq(errfunc, p, args=(x, y, z), maxfev=1000)

    return est_p


"""
INDIVIDUAL TREE POINT CLOUD PROCESSING AND ATTRIBUTE ESTIMATIONS
PROCESSING: Tree Parameters - ESTIMATE THE HEIGHT, AREA, DBH OF THE TREE
MANDATORY: LAZCONTENT
REQUIREMENTS: Numpy, alphashape 

"""


def TreeParameters(LAZCONTENT, dim, alphavalue, lim):
    import numpy as np
    import circle_fit as cf
    import alphashape  # https://alphashape.readthedocs.io/en/latest/alphashape.html

    # Estimate tree height
    z = LAZCONTENT.z
    Height = np.percentile(z, 99.95)

    # Estimate Reflectance Value (Median)
    Value = np.median(LAZCONTENT.Reflectance)

    # Estimate Alphashape and Area
    if dim == 0:
        dim = "2dxy"
    if lim == 0:
        lim = 5
    if dim == "3d":
        alphavalue = 0

    if dim == "2dxy":
        Z = np.min(LAZCONTENT.z)
        GRID = LAZCONTENT.z > Z + 2
        points = np.dstack([LAZCONTENT.x[GRID].ravel(), LAZCONTENT.y[GRID].ravel()])[0]

    if dim == "2dxz":
        points = np.dstack([LAZCONTENT.x.ravel(), LAZCONTENT.z.ravel()])[0]

    if dim == "2dyz":
        points = np.dstack([LAZCONTENT.y.ravel(), LAZCONTENT.z.ravel()])[0]

    if dim == "3d":
        points = np.dstack(
            [LAZCONTENT.x.ravel(), LAZCONTENT.y.ravel(), LAZCONTENT.z.ravel()]
        )[0]

    # Generate the alpha shape
    if (type(alphavalue) == int) or (type(alphavalue) == float):
        alpha_shape = alphashape.alphashape(points, alphavalue)

    if alphavalue == "Auto":
        alpha = alphashape.optimizealpha(points)
        alpha_shape = alphashape.alphashape(points, alpha)

    # Estimate Area
    Area = alpha_shape.area

    # Estimate Edge
    EDGES_POLY = []
    if alpha_shape.geom_type == "MultiPolygon":
        for polygon in alpha_shape:
            AUX = polygon.exterior.coords[:-1]
            if len(AUX) > lim:
                EDGES_POLY.extend(polygon.exterior.coords[:-1])

    if alpha_shape.geom_type == "Polygon":
        EDGES_POLY = alpha_shape.exterior.coords[:-1]

    EDGES_POLY = np.array(EDGES_POLY).T

    # Estimate DBH by least square fit
    Z_DBH = np.min(LAZCONTENT.z) + 1.3
    GRID = (LAZCONTENT.z > Z_DBH - 0.3) & (LAZCONTENT.z < Z_DBH + 0.3)
    x = LAZCONTENT.x[GRID]
    y = LAZCONTENT.y[GRID]
    z = LAZCONTENT.z[GRID]

    # ALLOMETRIC ESTIMATION OF DBH - CM
    # Computing initial parameters
    data_plane = calc_plane(x, y, z)
    data = project_points(x, y, z, data_plane[0], data_plane[1], data_plane[2])

    # data=np.array((x, y)); data=data.T
    xc, yc, r, _ = cf.least_squares_circle((data))

    # Bundle Adjustment
    p = np.array([xc, yc, 0, 0, r])
    xyz = np.array([x, y, z]).T
    est_p = cylinderFitting(xyz, p, 0.00001)

    """
    Output inside est_p structure
    Stemcenter_x >> est_p[0]
    Stemcenter_y >> est_p[1]
    stem raio >> est_p[4] >> DBH = 2*est_p[4]
    """

    class TREE:
        pass

    setattr(TREE, "Height", Height)
    setattr(TREE, "Area", Area)
    setattr(TREE, "Reflectance", Value)
    setattr(TREE, "Edges", EDGES_POLY)
    setattr(TREE, "DBH", 2 * est_p[4])

    return TREE
