# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 17:33:50 2017

@author: dan
"""

from rasterstats import zonal_stats
import pandas as pd
from scipy.stats.mstats import mode
import pytablewriter
from osgeo import ogr
import numpy as np

def mymode(x):
    return mode(x.compressed())

def get_subs(shp):
    ds = ogr.Open(shp)
    lyr = ds.GetLayer(0)
    a=[]
    for row in lyr:
        a.append(row.substrate)
    lyr.ResetReading()
    del ds
    return a

if __name__ == '__main__':

    sedclass_raster = r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\may2014_mb6086r_sedclass\mb_sed3class_2014_05_raster.tif"
    ss_raster = r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\may2014_mb6086r_sedclass\ss_R01349.tif"
    seg_shp = r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\output\shapefiles\visual_seg.shp"
    
    cmap = {1.0: 'Sand', 3.0: 'Gravel', 5.0: 'Boulders'}
    stats = zonal_stats(seg_shp,sedclass_raster,categorical=True,nodata=-99,category_map = cmap)
    
    merge_df = pd.DataFrame(stats)
    merge_df['Substrate'] = get_subs(seg_shp)
    merge_df = merge_df[['Sand','Gravel','Boulders','Substrate']]
    
    pvt = pd.pivot_table(merge_df, index=['Substrate'],values=['Sand','Gravel','Boulders'],aggfunc=np.nansum)

    #Percentage classification table
    class_df = pvt.div(pvt.sum(axis=1), axis=0).reset_index()

    writer = pytablewriter.MarkdownTableWriter()
    writer.table_name = "Visual Segmentation Ground Truthing Results"
    writer.header_list = list(class_df.columns.values)
    writer.value_matrix = class_df.values.tolist()
    writer.write_table()   
        



