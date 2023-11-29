"""
PROGRAMMERS:

MARIANA BATISTA CAMPOS - mariana.campos@nls.fi
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
from ctypes import *
import numpy as np
import time
import gc

def ReadLaz(inputLas, DLLPATH, n_threads=1):
    t1_start = time.perf_counter()
    t2_start = time.process_time()

    #INSERT FILE TO BE READ
    FILE_NAME=inputLas
    ExtraBytes_name=[]; x_arr=[];  y_arr=[]; z_arr=[];
    return_number_arr=[]; number_of_returns_arr=[]; intensity_arr=[]; classification_arr=[]; 
    edge_of_flight_line_arr=[]; scan_direction_flag_arr=[]; scan_angle_rank_arr=[]; user_data_arr=[]; point_source_ID_arr=[]; gps_time_arr=[]; 
    number_attributes=[];
    
    x_arr_F=[];  y_arr_F=[]; z_arr_F=[];
    return_number_arr_F=[]; number_of_returns_arr_F=[]; intensity_arr_F=[]; classification_arr_F=[]; number_attributes_F=[];
    edge_of_flight_line_arr_F=[]; scan_direction_flag_arr_F=[]; scan_angle_rank_arr_F=[]; user_data_arr_F=[]; point_source_ID_arr_F=[]; gps_time_arr_F=[]; 
    
    #LOADING C FUNCTION TO READ WITH LASZIP
    libCalc=CDLL(DLLPATH)
    
    if n_threads == 1:
       DATA = libCalc.Read
       print("\n You are running a single thread")
    else:
       DATA = libCalc.Read_Parallel
       print(f"\n You are using {n_threads} cores")

    
    FREEMEMO = libCalc.freeme

    #DECLARING NUMPY ARRAYS
    #void Data(char* name, double*&x, double*&y, double*&z, int *&return_number,  int *&number_of_returns ,float *&intensity);

    DATA.argtypes = [(c_char_p),
                 POINTER(POINTER(c_double)), POINTER(POINTER(c_double)), POINTER(POINTER(c_double)), #X,Y,Z
                 POINTER(POINTER(c_float)), #intensity
                 POINTER(POINTER(c_int)), POINTER(POINTER(c_int)), #RETURN NUMBER AND NUMBER OF RETURN
                 POINTER(POINTER(c_int)), POINTER(POINTER(c_int)), #edge_of_flight_line and scan_direction_flag
                 POINTER(POINTER(c_float)), #CLASSIFICATION
                 POINTER(POINTER(c_short)), #scan_angle_rank
                 POINTER(POINTER((c_char_p))), #user_data
                 POINTER(POINTER(c_short)), #point_source_ID
                 POINTER(POINTER(c_float)), #GPS_TIME               
                 POINTER(POINTER(POINTER(c_float))), 
                 POINTER(POINTER((c_char_p))),
                 POINTER(c_int), 
                 (c_int)] 

    
    DATA.restype = c_int
    string=(c_char_p)(FILE_NAME.encode('utf-8'))
    x=POINTER(c_double)()
    y=POINTER(c_double)()
    z=POINTER(c_double)()
    intensity=POINTER(c_float)()
    return_number=POINTER(c_int)() 
    number_of_returns=POINTER(c_int)()
    edge_of_flight_line=POINTER(c_int)()
    scan_direction_flag=POINTER(c_int)()
    classification=POINTER(c_float)()
    scan_angle_rank=POINTER(c_short)()
    user_data=POINTER(c_char_p)()
    point_source_ID=POINTER(c_short)()
    gps_time=POINTER(c_float)()
    pm=POINTER(POINTER(c_float))()
    attributes_names=POINTER(c_char_p)()
    extra=(c_int)()
    
    #CALLING FUNCTION
    npoints=DATA(string,
                 byref(x),byref(y), byref(z), 
                 byref(intensity),
                 byref(return_number), byref(number_of_returns),
                 byref(edge_of_flight_line), byref(scan_direction_flag),
                 byref(classification), 
                 byref(scan_angle_rank),byref(user_data),
                 byref(point_source_ID),byref(gps_time),                
                 byref(pm), byref(attributes_names), extra, n_threads)
    
    
    

    x_arr=np.ctypeslib.as_array((c_double*npoints).from_address(addressof(x.contents)))
    y_arr=np.ctypeslib.as_array((c_double*npoints).from_address(addressof(y.contents)))
    z_arr=np.ctypeslib.as_array((c_double*npoints).from_address(addressof(z.contents)))
    intensity_arr=np.ctypeslib.as_array((c_float*npoints).from_address(addressof(intensity.contents)))
    return_number_arr=np.ctypeslib.as_array((c_int*npoints).from_address(addressof(return_number.contents)))
    number_of_returns_arr=np.ctypeslib.as_array((c_int*npoints).from_address(addressof(number_of_returns.contents)))
    edge_of_flight_line_arr=np.ctypeslib.as_array((c_int*npoints).from_address(addressof(edge_of_flight_line.contents)))
    scan_direction_flag_arr=np.ctypeslib.as_array((c_int*npoints).from_address(addressof(scan_direction_flag.contents)))
    classification_arr=np.ctypeslib.as_array((c_float*npoints).from_address(addressof(classification.contents)))    
    scan_angle_rank_arr=np.ctypeslib.as_array((c_short*npoints).from_address(addressof(scan_angle_rank.contents)))
    #user_data
    point_source_ID_arr=np.ctypeslib.as_array((c_short*npoints).from_address(addressof(point_source_ID.contents)))
    gps_time_arr=np.ctypeslib.as_array((c_float*npoints).from_address(addressof(gps_time.contents)))
    number_attributes=extra.value
    
    
    x_arr_F=np.array(x_arr); y_arr_F=np.array(y_arr); z_arr_F=np.array(z_arr);
    return_number_arr_F=np.array(return_number_arr); number_of_returns_arr_F=np.array(number_of_returns_arr); intensity_arr_F=np.array(intensity_arr); classification_arr_F=np.array(classification_arr);
    edge_of_flight_line_arr_F=np.array(edge_of_flight_line_arr); scan_direction_flag_arr_F=np.array(scan_direction_flag_arr); 
    scan_angle_rank_arr_F=np.array(scan_angle_rank_arr); point_source_ID_arr_F=np.array(point_source_ID_arr); gps_time_arr_F=np.array(gps_time_arr);
    #user_data_arr_F=np.array(scan_angle_rank_arr); 
   
    
    class ATRIBUTES:
        
        pass
        
    setattr (ATRIBUTES, 'x', x_arr_F )        
    setattr (ATRIBUTES, 'y', y_arr_F )  
    setattr (ATRIBUTES, 'z', z_arr_F ) 
    setattr (ATRIBUTES, 'intensity', intensity_arr_F ) 
    setattr (ATRIBUTES, 'return_number', return_number_arr_F ) 
    setattr (ATRIBUTES, 'number_of_returns', number_of_returns_arr_F ) 
    setattr (ATRIBUTES, 'edge_of_flight_line', edge_of_flight_line_arr_F )
    setattr (ATRIBUTES, 'scan_direction_flag', scan_direction_flag_arr_F )
    setattr (ATRIBUTES, 'classification', classification_arr_F )
    setattr (ATRIBUTES, 'scan_angle_rank', scan_angle_rank_arr_F )
    setattr (ATRIBUTES, 'point_source_ID', point_source_ID_arr_F )
    setattr (ATRIBUTES, 'gps_time', gps_time_arr_F )
    
    default=[]; default_F=[]; 
    if number_attributes > 0:
       for i in range (number_attributes):
           ExtraBytes_name.append(attributes_names[i].decode('utf-8'))
           default=np.ctypeslib.as_array((c_float*npoints).from_address(addressof(pm[i].contents)))
           default_F=np.array(default); 
           setattr (ATRIBUTES, ExtraBytes_name[i], default_F )
           del default, default_F
       setattr (ATRIBUTES, 'ExtraBytes_name', ExtraBytes_name)    
                   
    
    t1_stop = time.perf_counter()
    t2_stop = time.process_time()
    
    fields=[f for f in dir(ATRIBUTES) if not callable(getattr(ATRIBUTES,f)) and not f.startswith('__')]
    Default_atributes=[]
    for i in fields:
        if i != 'ExtraBytes_name':
            TESTE=np.sum(getattr(ATRIBUTES,i))
            if TESTE!=0:
                Default_atributes.append(i)
    
    
    
    print("\n Reading Elapsed time: %.1f [sec]" % ((t1_stop-t1_start)))
    print("CPU process time: %.1f [sec] \n" % ((t2_stop-t2_start)))
    
    print ("LAZ CONTENT:", Default_atributes)   
    print ("LAZ EXTRA BYTES: ExtraBytes_name", ExtraBytes_name) 
    
    # This will give a segmentation fault if uncommented
    # FREEMEMO(x, y , z, 
    #         return_number, number_of_returns,
    #         intensity, pm, attributes_names, number_attributes)
    
    gc.collect() 
    del x, y, z, return_number, number_of_returns, intensity, classification, pm, attributes_names, extra
    del x_arr, y_arr, z_arr, return_number_arr, number_of_returns_arr, intensity_arr, classification_arr, ExtraBytes_name   
    del x_arr_F, y_arr_F, z_arr_F, return_number_arr_F, number_of_returns_arr_F, intensity_arr_F, classification_arr_F
    del libCalc, DATA, npoints, number_attributes
    
    return ATRIBUTES
