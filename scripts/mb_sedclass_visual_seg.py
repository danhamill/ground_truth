# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 17:33:50 2017

@author: dan
"""
from osgeo import ogr,gdal
from rasterstats import zonal_stats

import pandas as pd
import numpy as np
import os

from mpl_toolkits.basemap import Basemap
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
import pyproj
from pandas.tools.plotting import table
import pytablewriter


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
    root  = r"C:\workspace\gound_truth\output"
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
    
    trans =  pyproj.Proj(init="epsg:26949") 
    #Load May 2014 Data
    may_sed_class_raster = r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\may2014_mb6086r_sedclass\mb_sed5class_2014_05_raster.tif"
    ds = gdal.Open(may_sed_class_raster)
    may_sed_class = ds.GetRasterBand(1).ReadAsArray()
    may_sed_class[may_sed_class<0]=np.nan
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    
    xres = gt[1]
    yres = gt[5]
    
    # get the edge coordinates and add half the resolution 
    # to go to center coordinates
    xmin = gt[0] + xres * 0.5
    xmax = gt[0] + (xres * ds.RasterXSize) - xres * 0.5
    ymin = gt[3] + (yres * ds.RasterYSize) + yres * 0.5
    ymax = gt[3] - yres * 0.5
    extent = [xmin,xmax,ymin,ymax]
    del ds
    
    xx, yy = np.mgrid[xmin:xmax+xres:xres, ymax+yres:ymin:yres]
    may_lon, may_lat = trans(xx, yy, inverse=True)
    del xx, yy, xmin, xmax, ymin, ymax
    
    #Load April_2014 SS data
    ss_plot_raster = r"C:\workspace\Merged_SS\raster\2014_04\ss_2014_04_R01349_raster.tif"
    ds = gdal.Open(ss_plot_raster)
    april_ss = ds.GetRasterBand(1).ReadAsArray()
    april_ss[april_ss<0]=np.nan
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    
    xres = gt[1]
    yres = gt[5]
    
    # get the edge coordinates and add half the resolution 
    # to go to center coordinates
    xmin = gt[0] + xres * 0.5
    xmax = gt[0] + (xres * ds.RasterXSize) - xres * 0.5
    ymin = gt[3] + (yres * ds.RasterYSize) + yres * 0.5
    ymax = gt[3] - yres * 0.5
    extent = [xmin,xmax,ymin,ymax]
    del ds
    
    xx, yy = np.mgrid[xmin:xmax+xres:xres, ymax+yres:ymin:yres]
    april_lon, april_lat = trans(xx, yy, inverse=True)
    del xx, yy, xmin, xmax, ymin, ymax
    cs2cs_args = "epsg:26949"
    
    
    
    #legend Stuff
    colors=['#ca0020','#f4a582','#f7f7f7','#92c5de','#0571b0']
    a_val=1
    circ1 = Line2D([0], [0], linestyle="none", marker="o", markersize=10, markerfacecolor=colors[0],alpha=a_val)

    circ3 = Line2D([0], [0], linestyle="none", marker="o", markersize=10, markerfacecolor=colors[2],alpha=a_val)

    circ5 = Line2D([0], [0], linestyle="none", marker="o", markersize=10, markerfacecolor=colors[4],alpha=a_val)
    #Total extents (i.e. misplaced SS and multibeam)
    fig, (ax,ax1) = plt.subplots(figsize=(10,8),ncols=2)
    
    #Start with april sidescan sonar
    ax.set_title('April 2014 \n Sidescan Sonar Imagery')
    m = Basemap(projection='merc', 
                epsg=cs2cs_args.split(':')[1], 
                llcrnrlon=np.nanmin(april_lon)-0.0006, 
                llcrnrlat=np.nanmin(april_lat)-0.0003,
                urcrnrlon=np.nanmax(april_lon)+0.0006, 
                urcrnrlat=np.nanmax(april_lat)+0.0003,ax=ax)
    m.wmsimage(server='http://grandcanyon.usgs.gov/arcgis/services/Imagery/ColoradoRiverImageryExplorer/MapServer/WmsServer?', layers=['3'], xpixels=1000)
    x,y = m.projtran(april_lon, april_lat)
    im = m.contourf(x,y,april_ss.T, cmap='Greys_r', levels=[0,2.5,5,7.5,10,12.5,15,17.5,20,22.5,25,27.5,30,32.5,35])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    cbr = plt.colorbar(im, cax=cax)
    cbr.set_label('Sidescan Intensity [dBW]')
    ax1.set_title('May 2014 Acousic \n Sediment Classifications')
    m = Basemap(projection='merc', 
                epsg=cs2cs_args.split(':')[1], 
                llcrnrlon=np.nanmin(may_lon)-0.0009, 
                llcrnrlat=np.nanmin(may_lat)-0.0006,
                urcrnrlon=np.nanmax(may_lon)+0.0009, 
                urcrnrlat=np.nanmax(may_lat)+0.0006,ax=ax1)
    m.wmsimage(server='http://grandcanyon.usgs.gov/arcgis/services/Imagery/ColoradoRiverImageryExplorer/MapServer/WmsServer?', layers=['3'], xpixels=1000)
    x,y = m.projtran(may_lon, may_lat)
    im = m.contourf(x,y,may_sed_class.T, cmap='coolwarm', levels=[0,1,2,3,4,5])
   
    ax1.legend((circ5, circ3,circ1),('Sand','Gravel','Rocks'),numpoints=1, loc='best')
    plt.tight_layout()
    plt.show()
    plt.savefig(root + os.sep + 'misaligned_ss_imagery_example.png',dpi=600)
    
#########################################################################################################################################
    #Load May 2014 Data
   
    ds = gdal.Open(r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\input\may_14_mbsed3class.tif")
    may_sed_class = ds.GetRasterBand(1).ReadAsArray()
    may_sed_class[may_sed_class<0]=np.nan
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    
    xres = gt[1]
    yres = gt[5]
    
    # get the edge coordinates and add half the resolution 
    # to go to center coordinates
    xmin = gt[0] + xres * 0.5
    xmax = gt[0] + (xres * ds.RasterXSize) - xres * 0.5
    ymin = gt[3] + (yres * ds.RasterYSize) + yres * 0.5
    ymax = gt[3] - yres * 0.5
    extent = [xmin,xmax,ymin,ymax]
    del ds
    
    xx, yy = np.mgrid[xmin:xmax+xres:xres, ymax+yres:ymin:yres]
    may_lon, may_lat = trans(xx, yy, inverse=True)
    del xx, yy, xmin, xmax, ymin, ymax
    
    #Load April_2014 SS data
   
    ds = gdal.Open(ss_raster)
    april_ss = ds.GetRasterBand(1).ReadAsArray()
    april_ss[april_ss<0]=np.nan
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    
    xres = gt[1]
    yres = gt[5]
    
    # get the edge coordinates and add half the resolution 
    # to go to center coordinates
    xmin = gt[0] + xres * 0.5
    xmax = gt[0] + (xres * ds.RasterXSize) - xres * 0.5
    ymin = gt[3] + (yres * ds.RasterYSize) + yres * 0.5
    ymax = gt[3] - yres * 0.5
    extent = [xmin,xmax,ymin,ymax]
    del ds
    
    xx, yy = np.mgrid[xmin:xmax+xres:xres, ymax+yres:ymin:yres]
    april_lon, april_lat = trans(xx, yy, inverse=True)
    del xx, yy, xmin, xmax, ymin, ymax

    colors=['#ca0020','#f4a582','#f7f7f7','#92c5de','#0571b0']
    a_val=1
    circ1 = Line2D([0], [0], linestyle="none", marker="o", markersize=10, markerfacecolor=colors[0],alpha=a_val)

    circ3 = Line2D([0], [0], linestyle="none", marker="o", markersize=10, markerfacecolor=colors[2],alpha=a_val)

    circ5 = Line2D([0], [0], linestyle="none", marker="o", markersize=10, markerfacecolor=colors[4],alpha=a_val)
   
    
    #Total extents (i.e. misplaced SS and multibeam)
    fig, (ax,ax1) = plt.subplots(figsize=(13,8),ncols=2)
    
    #Start with april sidescan sonar
    ax.set_title('April 2014 \n Sidescan Sonar Imagery')
    m = Basemap(projection='merc', 
                epsg=cs2cs_args.split(':')[1], 
                llcrnrlon=np.nanmin(april_lon)-0.0001, 
                llcrnrlat=np.nanmin(april_lat)-0.0002,
                urcrnrlon=np.nanmax(april_lon)+0.0001, 
                urcrnrlat=np.nanmax(april_lat)+0.0002,ax=ax)
    m.wmsimage(server='http://grandcanyon.usgs.gov/arcgis/services/Imagery/ColoradoRiverImageryExplorer/MapServer/WmsServer?', layers=['3'], xpixels=1000)
    x,y = m.projtran(april_lon, april_lat)
    im = m.contourf(x,y,april_ss.T, cmap='Greys_r', levels=[0,2.5,5,7.5,10,12.5,15,17.5,20,22.5,25,27.5,30,32.5,35])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    cbr = plt.colorbar(im, cax=cax)
    cbr.set_label('Sidescan Intensity [dBW]')
    m.readshapefile(r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\output\shapefiles\visual_seg_geo","layer",drawbounds = False)
    #sand, sand/gravel, gravel, sand/rock, rock
    s_patch,  g_patch, r_patch,  = [],[],[]
    for info, shape in zip(m.layer_info, m.layer):
        if info['substrate'] == 'sand' :
            s_patch.append(Polygon(np.asarray(shape),True))
       
        if info['substrate'] == 'gravel':
            g_patch.append(Polygon(np.asarray(shape),True))      
         
        if info['substrate'] == 'boulders':
            r_patch.append(Polygon(np.asarray(shape),True))             
    ax.add_collection(PatchCollection(s_patch, facecolor = colors[4],alpha=a_val, edgecolor='none',zorder=10))    
    ax.add_collection(PatchCollection(g_patch, facecolor = colors[2],alpha=a_val, edgecolor='none',zorder=10))    
    ax.add_collection(PatchCollection(r_patch, facecolor = colors[0],alpha=a_val, edgecolor='none',zorder=10)) 
    ax.legend((circ5, circ3,circ1),('Sand','Gravel','Boulders'),numpoints=1, loc='best')

    ax1.set_title('May 2014 Acousic \n Sediment Classifications')
    m = Basemap(projection='merc', 
                epsg=cs2cs_args.split(':')[1], 
                llcrnrlon=np.nanmin(may_lon)-0.0001, 
                llcrnrlat=np.nanmin(may_lat)-0.0002,
                urcrnrlon=np.nanmax(may_lon)+0.0001, 
                urcrnrlat=np.nanmax(may_lat)+0.0002,ax=ax1)
    m.wmsimage(server='http://grandcanyon.usgs.gov/arcgis/services/Imagery/ColoradoRiverImageryExplorer/MapServer/WmsServer?', layers=['3'], xpixels=1000)
    x,y = m.projtran(may_lon, may_lat)
    im = m.contourf(x,y,may_sed_class.T, cmap='coolwarm', levels=[0,1,2,3,4,5])
    
    ax1.legend((circ5, circ3,circ1),('Sand','Gravel','Rock'),numpoints=1, loc='best')
    plt.tight_layout()
    plt.show()
    plt.savefig(root + os.sep + 'mb_ss_ground_truth_area.png',dpi=600)