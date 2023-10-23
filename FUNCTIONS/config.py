

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
PATH = "G:/DATASET/WEEKLY/STEM_MAP_TREES/NORM"

PC_DIRECTORY = "/200704_000502"

PC_FILENAME = "/200704_000502_R_georef{TREEID}.las"

REF_DIRECTORY = "/STEM_MAP"

REF_FILENAME = "/TreeMapFiltered.xlsx"

DEST_DIRECTORY_MAIN = "/TREES_SEGMENTED"

DEST_DIRECTORY_OTHER = "/TREES_SEGMENTED/NOISE/"

REF_DIST_MAX = 2

