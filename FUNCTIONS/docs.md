# Modified layer-by-layer segmentation documentation

Version: 1.0

Date: 9.6.2023

Author: Lassi Ruoppa

Contact: lassi.ruoppa@maanmittauslaitos.fi or lassi.ruoppa@gmail.com

## Table of contents

1. [Introduction](#1-introduction)
2. [Dependencies and system requirements](#2-dependencies-and-system-requirements)
3. [Usage](#3-usage)

    3.1 [3.1 Arguments](#31-arguments)

    3.2 [Running the algorithm](#32-running-the-algorithm)

    3.3 [Configuring the algorithm](#33-configuring-the-algorithm)


## 1. Introduction

This is a short documentation of the modified layer-by-layer segmentation algorithm. The original algorithm was propsed in [Individual tree segmentation and species classification using high-density close-range multispectral laser scanning data](https://doi.org/10.1016/j.ophoto.2023.100039), Hakula et al., 2023, ISPRS Open Journal of Photogrammetry and Remote Sensing. For an in depth look at how the algorithm functions, the reader is referred to the aforementioned article. This version was optimized for segmenting individual trees from a small group of trees from the Hyytiälä tower data. Changes include mostly minor modifications to clustering parameters and voxel size. In addition, reference data reading, segment matching and writing segments was altered slightly.

## 2. Dependencies and system requirements

The algorithm has quite a few dependencies, which can be found in the file `requirements.txt`. Note that many of the libraries listed in the file have further dependencies. Easiest way to automatically install all required libraries is to run the following command:
```
pip install -r requirements.txt
```
Note that python version 3.10 was used during development and as such functionality can not be quaranteed on earlier versions (although it should not use any version specific functionalities and if it does, changing them should be simple enough). The algorithm has been tested on Ubuntu 20.04 and 22.04 (through WSL).

## 3. Usage

## 3.1 Arguments

The table below lists the arguments the algorithm accepts:

| Name | Command line | Description | Required | Default |
| --- | --- | --- | --- | --- |
| `tree_id` | `-i`, `--id` | Id of the tree to segment | Yes | - |
| `x_offset` | `-x`, `--xoffset` | x offset that is applied to the segments before matching to reference data. The offset is added to the x-coordinate, so for a negative offset, provide a negative value | No | `0` |
| `y_offset` | `-y`, `--yoffset` | The same as `x_offset` but for y-coordinates | No | `0` |
| `verbose` | `-v`, `--verbose` | If true, print information about the progress of the segmentation process | No | `False` |
| `write_other` | `-o`, `--other` | If true, also write segments that were not matched to a reference tree | No | `True` |
| `skip_matching` | `-s`, `--skip` | If true, skip matching segments to the reference data. This argument can be useful if no reference data is available for a particular tree. **NOTE:** setting `skip_matching` to true will automatically force the value of `write_other` to true regardless of what value was provided. This is done, because otherwise the algorithm returns no output | No | `False` |
| - | `-r`, `--read` | **NOTE:** this argument is only available in the command line and is mutually exclusive with `-i`. Attempt to read a file from `config.PATH` that contains a list of tree ids. The same functionality can be achieved outside of the command line by simply iterating through a list of ids in a for loop and calling `lbl_segment()` for each of them | No | `"id_list.txt"`

## 3.2 Running the algorithm

The main script that executes the layer-by-layer segmentation is `lbl_segment.py`. The script can be used either from the command line or as a function by importing it into another python file with `from lbl_segment import lbl_segment`. Ensure that you path variables have been cofigured correctly in `config.py` before running the algorithm (see [Section 3.3](#33-configuring-the-algorithm)). Below, we list a couple of examples of running the algorithm with different options both as a function and in the command line.

---

**Example 1:** segment a tree with id 9354 and do not write segments that could not be matched to a reference tree:
*In code:*
```
lbl_segment(tree_id = 9354)
```
*In the command line:*
```
python lbl_segment.py -i=9354
```

---

**Example 2:** segment a tree with id 9354, display info during segmentation and also write segments that could not be matched to a reference tree:

*In code:*
```
lbl_segment(tree_id = 9354, verbose = True, write_other = True)
```
*In the command line:*
```
python lbl_segment.py -i=9354 -v -o
```

---

**Example 3:** segment a tree with id 9354 and use offsets 357676.852 and 6860035.171 for x and y coordinates respectively during matching:

*In code:*
```
lbl_segment(tree_id = 9354, x_offset = 357676.852, y_offset = 6860035.171)
```
*In the command line:*
```
python lbl_segment.py -i=9354 -x=357676.852 -y=6860035.171
```

---

**Example 4:** segment tree with id 9354 and skip matching to reference data:

*In code:*
```
lbl_segment(tree_id = 9354, skip_matching = True)
```
*In the command line:*
```
python lbl_segment.py -i=9354 -s
```

---

**Example 5:** read a list of tree ids from `my_id_list.txt` and segment all of them

*In the command line:*
```
python lbl_segment.py -r="my_id_list.txt"
```

---

## 3.3 Configuring the algorithm

In this section we present an example of how to configure the constants in `config.py` before running the algorithm. Let us assume that the folder structure for our data is as follows:
```
/mnt/d/data/
|
|—— point_clouds
|   |—— tower_test_data
|   |   |—— original
|   |   |   |—— 200406_100502_Sample_R_Georef_SpatialSampleTREE_9354_R.las
|   |   |   |—— 200406_100502_Sample_R_Georef_SpatialSampleTREE_9355_R.las
|   |   |   |—— 200406_100502_Sample_R_Georef_SpatialSampleTREE_9357_R.las
|   |   |—— segments
|—— reference_data
|   |—— TreeMapFiltered.xlsx
```
where `200406_100502_Sample_R_Georef_SpatialSampleTREE_9355_R.las` is the point cloud we want to segment (this means that our tree id is 9355), `TreeMapFiltered.xlsx` is our reference data and we want to save the resulting segments in the folder `segments`. Furthermore, let us assume that we want to save the segments that were not matched to a reference tree to a folder titled `segments/tree_9355_other_segments`. The values we would enter in `config.py` are then as follows:
```
PATH = "/mnt/d/data/"
PC_DIRECTORY = "point_clouds/tower_test_data/original/"
PC_FILENAME = "200406_100502_Sample_R_Georef_SpatialSampleTREE_{TREEID}_R.las"
REF_DIRECTORY = "reference_data/"
REF_FILENAME = "TreeMapFiltered.xlsx"
DEST_DIRECTORY_MAIN = "point_clouds/tower_test_data/segments/"
DEST_DIRECTORY_OTHER = "point_clouds/tower_test_data/segments/tree_{TREEID}_other_segments/"
```

Then, running the algorithm with either
```
lbl_segment(tree_id = 9355, write_other = True)
```
or
```
python lbl_segment.py -i=9355 -o
```
Will produce the following result:
```
/mnt/d/data/
|
|—— point_clouds
|   |—— tower_test_data
|   |   |—— original
|   |   |   |—— 200406_100502_Sample_R_Georef_SpatialSampleTREE_9354_R.las
|   |   |   |—— 200406_100502_Sample_R_Georef_SpatialSampleTREE_9355_R.las
|   |   |   |—— 200406_100502_Sample_R_Georef_SpatialSampleTREE_9357_R.las
|   |   |—— segments
|   |   |   |—— 200406_100502_Sample_R_Georef_SpatialSampleTREE_9355_R.las
|   |   |   |—— tree_9355_other_segments
|   |   |   |   |—— segment_1.las
|   |   |   |   |—— segment_2.las
|   |   |   |   |—— segment_3.las
|—— reference_data
|   |—— TreeMapFiltered.xlsx
```
where the folder `segments` contains the segment that was matched to the reference tree under the same name as the original point cloud, and the folder `segments/tree_9355_other_segments` contains the other segments that were identified in the point cloud (not necessarily complete trees).