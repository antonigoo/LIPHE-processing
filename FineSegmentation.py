# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 15:14:01 2023

@author: Mariana Campos

PYTHON LIBRARY REQUIREMENTS: requirements.txt
    
"""

# FGI in-the-house functions:
import sys
import os
import shutil 

os.chdir(r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING")
functions=r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\FUNCTIONS"
sys.path.append(functions)

import ReadLaz
import WriteLaz
import Processing
import numba_algorithms as na
import lbl_segment


#Other python Libraries
import os, glob, time
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import xlsxwriter
import matplotlib.pyplot as plt
import gc
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


#For tree attributes caluclated based on individual tree point clouds
import alphashape
from scipy.optimize import leastsq
import circle_fit as cf    


#%%
    
"""
NORMALIZE THE POINT CLOUDS ACCORDING TO THE GROUND AND REMOVE GROUND POINTS.
PS: THIS IS A MANDATORY PROCESSING STEP REQUIRED BEFORE FINE SEGMENTATION 

MANDATORY: LAZCONTENT > INDIVIDUAL TREE POINT CLOUD
           STEM POSITION INFORMATION (x,y)
           MINIMUM THRSHOULD TO REMOVE GROUND POINTS - default=0.3m
   
OPTIONAL:Extra, ExtraBytes_name
           E.G: TREE, EXTRA=Processing.ClippingTree (LAZCONTENT, BOX_COORD[0], BOX_ANGLES[0], Extra, ExtraBytes_name)

"""

# STEP 1 - NORMALIZE TREES FOR GROUND AND SAVE SOMEWHERE THE NORM COORDINATES

# 1. Set path to laz2Np dll  
DLLPATH=r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\LAZ2NP\OS_WIN\Las2Array_StaticLibrary.dll"


# 2. Set input and output paths
Lazdir = r"G:\DATASET\WEEKLY\STEM_MAP_TREES\GEO"
outputLas=r"G:\DATASET\WEEKLY\STEM_MAP_TREES\NORM"

# 3 - Set stem map as input
Metadata=r"D:\SA_SILS\PROCESSING\Workflow\MAPS\TreeMapFiltered.xlsx"
df = pd.read_excel(Metadata);
ID=np.array(df.TREE_ID)
x_stem=np.array(df.E)
y_stem=np.array(df.N)
z_stem=np.array(df.H)
# species=np.array(df.Species)
N_trees=len(x_stem)

#4. Defining data offset
offsets_norm=np.array([357676.852, 6860035.171, 0],dtype=np.float32)
default=1 #Define thrshould to remove the ground point 

# If the gorund altitude of the tree is unkwown send DTM 
DTM_NAME=r"D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\DTM\Heli_pts_tower200m_DTM_20cm.las"
DTM=ReadLaz.ReadLaz(DTM_NAME, DLLPATH)

#5 - SAVING OFFSETS IN A TABLE FOR FURTHER PROCESSING
# workbook = xlsxwriter.Workbook('D:\SA_SILS\PROCESSING\Hyytiala_PipelinePaper\PROCESSING\SAMPLE_DATA\STEM_MAP\TreeMap_Norm.xlsx')
# worksheet = workbook.add_worksheet()
# worksheet.write('A1', 'ID')
# worksheet.write('B1', 'X')
# worksheet.write('C1', 'Y')
# worksheet.write('D1', 'Z')
# worksheet.write('E1', 'OFFSET_X')
# worksheet.write('F1', 'OFFSET_Y')
# worksheet.write('G1', 'OFFSET_Z')
# row=1;

# for i in range (len(x_stem)):
#     #If the min height is unkown it can be searched in the DTM
#     offsets_norm[2] = griddata((DTM.x, DTM.y), DTM.z,(x_stem[i], y_stem[i]), method='nearest')
    
#     worksheet.write(row, 0, ID[i])   
#     worksheet.write(row, 1, x_stem[i])
#     worksheet.write(row, 2, y_stem[i])
#     worksheet.write(row, 3, z_stem[i])
#     worksheet.write(row, 4, offsets_norm[0])
#     worksheet.write(row, 5, offsets_norm[1])
#     worksheet.write(row, 6, offsets_norm[2])
#     row=row+1
    
# workbook.close()


#6. Loop to normalize tree point cloud to the ground and save
ProjList=[];
ProjList=(glob.glob(Lazdir+"/*.laz"))
offsets_local=np.zeros((3),dtype=np.float32)
for i in range (len(ProjList)):
    
    inputLas=ProjList[i]
    outputP=os.path.basename(ProjList[i]).split('.')[0]
    
    ID_TREE=int(outputP.split('_')[3][6:].split('.')[0])
    P=ID==ID_TREE
    offsets_norm[2] = griddata((DTM.x, DTM.y), DTM.z,(x_stem[P], y_stem[P]), method='nearest')
    
    #READ POINT CLOUD
    LAZCONTENT=ReadLaz.ReadLaz(inputLas, DLLPATH)
    
    #DEFINE EXTRA BYTES
    ExtraBytes_name=['Reflectance', 'Deviation', 'Range', 'Theta', 'Phi']
    NEB=5; 
    NP=len(LAZCONTENT.x); Extra=np.empty((NEB,NP), dtype=np.float32); 
    Extra[0]=(LAZCONTENT.Reflectance)
    Extra[1]=(LAZCONTENT.Deviation)
    Extra[2]=(LAZCONTENT.Range)
    Extra[3]=(LAZCONTENT.Theta)
    Extra[4]=(LAZCONTENT.Phi)
    
    TREE, EXTRA_TREE=Processing.Ground_Normalize(LAZCONTENT, 
                                                 offsets=offsets_norm, 
                                                 th=default, 
                                                 Extra=Extra, 
                                                 ExtraBytes_name=ExtraBytes_name)
    
    outputLasFile=outputLas+ '/' + outputP+(".las")
   
    class MAINCONTENT:
    
        pass
    
    setattr (MAINCONTENT, 'x', (TREE.x))       
    setattr (MAINCONTENT, 'y', (TREE.y)) 
    setattr (MAINCONTENT, 'z', (TREE.z))
    setattr (MAINCONTENT, 'intensity', TREE.intensity )
    setattr (MAINCONTENT, 'return_number', TREE.return_number ) 
    setattr (MAINCONTENT, 'number_of_returns', TREE.number_of_returns)  
    setattr (MAINCONTENT, 'ExtraBytes_name',ExtraBytes_name) 
    WriteLaz.WriteLaz (outputLasFile, DLLPATH, MAINCONTENT, offsets_local,  EXTRA_TREE)
    gc.collect()
      
#%%

#ORGANIZE THE FILES IN NEW FOLDER

Lazdir=r"E:\TIME_SERIES\NORM_2021"

ProjList=[]; NAME=[]
ProjList=(glob.glob(Lazdir+"/*.las"))

for i in range (len(ProjList)):
    outputP=os.path.basename(ProjList[i])
    NAME.append(outputP[0:13])

NAME=np.array(NAME)
FILEs=np.unique(NAME)

i=0
for j in range (len(FILEs)):
    destination=Lazdir+"/"+FILEs[j]
    os.mkdir(destination)
    
    for i in range (len(NAME)):
        if(NAME[i]== FILEs[j]):
            shutil.move(ProjList[i], destination)

    
#%%    


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

#PLEASE ADD HERE ALL THE REQUIRED USER INPUT
DLLPATH="D:/SA_SILS/PROCESSING/Hyytiala_PipelinePaper/LAZ2NP/OS_WIN/Las2Array_StaticLibrary.dll"
lbl_location = r"D:/SA_SILS/PROCESSING/Hyytiala_PipelinePaper/PROCESSING/FUNCTIONS"
PATH = "G:/DATASET/WEEKLY/STEM_MAP_TREES/NORM" 
PC_DIRECTORY = "/200406_100502" 

PC_FILENAME = "/200406_100502_R_georef{TREEID}.las" 
REF_DIRECTORY = "/STEM_MAP"
REF_FILENAME = "/TreeMapFiltered.xlsx" 
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
#---------------------------------------------------------------------------------------------------------------



# ---------------LOOP CALLING SEGMENTATION CODE FOR N TREES-------------------------------

lazdir = user_input1 + user_input2
ProjList=[]; 
ProjList=(glob.glob(lazdir+"/*.las"))       
removed_ID = []

for i in range(len(ProjList)):
    
    outputP=os.path.basename(ProjList[i]).split('.')[0]
    ID_TREE=int(outputP.split('_')[3][6:])
    
    try:
        
        lbl_segment.lbl_segment(tree_id = ID_TREE, write_other = True,  x_offset = 357676.852, y_offset = 6860035.171)
    
    except:
        
        removed_ID.append(ID_TREE)
        
        pass
  

#----------------------------------------------------------------------------------------------------------
# -------------RE-WRITE THE FINAL TREES IN GEOREF COORDINATES AND SAVE THE FINAL RESULTS-------------------

#SET FINAL PATH
OutputLaz=r"G:\DATASET\WEEKLY\STEM_MAP_TREES\GEO"


#READ THE REFERENCE FILE WHERE THE OFFSETS WERE SAVED AFTER NORMALIZATION (EXAMPLE SIX)
Metadata=r"G:\DATASET\WEEKLY\STEM_MAP_TREES\NORM\STEM_MAP\TreeMap_Norm.xlsx"
df = pd.read_excel(Metadata);
ID=np.array(df.ID)
offset_x=np.array(df.OFFSET_X)
offset_y=np.array(df.OFFSET_Y, dtype="float64")
offset_z=np.array(df.OFFSET_Z)
N_trees=len(offset_x)

#SET OFFSET TO SAVE GEOREFERENCED DATA
offsets=np.array([357676.852, 6860035.171, 0],dtype=np.float32) #include georef offset
 
#MAIN LOOP
ProjList=[]
Lazdir=PATH+DEST_DIRECTORY_MAIN
ProjList=(glob.glob(Lazdir+"/*.las"))   
for i in range(N_trees):
    
        outputP=outputP=os.path.basename(ProjList[i]).split('.')[0]
        LAZCONTENT=ReadLaz.ReadLaz(ProjList[i], DLLPATH)
        
        ID_TREE=int(outputP.split('_')[6].split('.')[0])
        P=ID==ID_TREE
        
        #DECLARE EXTRABYTES
        ExtraBytes_name=['Reflectance', 'Deviation', 'Range', 'Theta', 'Phi']
        NEB=5; 
        NP=len(LAZCONTENT.x); Extra=np.empty((NEB,NP), dtype=np.float32); 
        Extra[0]=(LAZCONTENT.Reflectance)
        Extra[1]=(LAZCONTENT.Deviation)
        Extra[2]=(LAZCONTENT.Range)
        Extra[3]=(LAZCONTENT.Theta)
        Extra[4]=(LAZCONTENT.Phi)
        
        outputLasFile=OutputLaz + '/' + outputP+(".laz")
       
        class MAINCONTENT:
        
            pass
        
        setattr (MAINCONTENT, 'x', (LAZCONTENT.x))       
        setattr (MAINCONTENT, 'y', (LAZCONTENT.y)) 
        setattr (MAINCONTENT, 'z', (LAZCONTENT.z + offset_z[P]))
        setattr (MAINCONTENT, 'return_number', LAZCONTENT.return_number) 
        setattr (MAINCONTENT, 'number_of_returns', LAZCONTENT.number_of_returns) 
        setattr (MAINCONTENT, 'intensity', LAZCONTENT.intensity) 
        setattr (MAINCONTENT, 'ExtraBytes_name',ExtraBytes_name) 
        WriteLaz.WriteLaz (outputLasFile, DLLPATH, MAINCONTENT, offsets,  Extra)