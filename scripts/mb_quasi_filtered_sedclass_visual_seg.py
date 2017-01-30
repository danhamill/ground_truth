# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 16:31:25 2017

@author: dan
"""
from osgeo import ogr,gdal
from rasterstats import zonal_stats

import pandas as pd
import numpy as np
import os
import glob
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

def assign_class(row):
    if row.sed3class == 1:
        return 'sand'
    if row.sed3class == 2:
        return 'gravel'
    if row.sed3class == 3:
        return 'gravel'
    if row.sed3class == 4:
        return 'gravel'
    if row.sed3class == 5:
        return 'rock'    


if __name__ == '__main__':
    
    root = r'C:\workspace\gound_truth\output\visual_seg_med_filter_plots'
    files = glob.glob(r'C:\workspace\gound_truth\input\med_filter\quasi*.tif')
    ss_raster = r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\may2014_mb6086r_sedclass\ss_R01349.tif"
    seg_shp = r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\output\shapefiles\visual_seg_2.shp"
    trans =  pyproj.Proj(init="epsg:26949") 
    cs2cs_args = "epsg:26949"
    
    for thing in files:
        
        meter = thing.split('\\')[-1].split('_')[-3]
        ds = gdal.Open(thing)
        may_sed_class = ds.GetRasterBand(1).ReadAsArray()
        may_sed_class[may_sed_class<=0]=np.nan
        may_sed_class[may_sed_class ==2]=3
        may_sed_class[may_sed_class ==4]=3
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
        m.readshapefile(r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\output\shapefiles\visual_seg_2_geo","layer",drawbounds = False)
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
        plt.savefig(root + os.sep + 'quasi_mb_5_Class_filt_' + str(meter) +'_sq_meters_lowres.png',dpi=200)
        
        
        may_df = pd.DataFrame(may_sed_class.flatten())
        may_df.rename(columns={0:'sed3class'}, inplace=True)
        may_df = may_df.dropna()
        may_df['sed3name'] = may_df.apply(lambda row: assign_class(row), axis=1)
        
        fig,ax =plt.subplots()
        may_df.groupby('sed3name').size().plot(kind='bar', ax=ax,rot=45)
        table_may = pd.pivot_table(may_df,index=['sed3name'], values = ['sed3class'],aggfunc='count')
        table_may['Percent_Area'] = table_may['sed3class']/may_df.sed3name.count()
        table_may = table_may[['Percent_Area']]
        table2 = table(ax, np.round(table_may,3), loc='upper center',colWidths=[0.2])
        ax.set_ylabel('Frequency')
        ax.set_xlabel('Substrate Type')
        plt.tight_layout()
        plt.savefig(root + os.sep + 'quasi_mb_5_Class_filt_' + str(meter) +'_sq_meters_distributions.png')
        
        
        
        cmap = {1.0: 'Sand',2.0:'Sand_Gravel', 3.0: 'Gravel',4.0:'Sand_Rock', 5.0: 'Boulders'}
        stats = zonal_stats(seg_shp,thing,categorical=True,nodata=-99,category_map = cmap)
        
        merge_df = pd.DataFrame(stats)
        
        
        #merge_df['Gravel2'] = merge_df['Sand_Gravel'] + merge_df['Sand_Rock'] +merge_df['Gravel']
        merge_df['Substrate'] = get_subs(seg_shp)
        merge_df = merge_df[['Sand','Gravel','Boulders','Substrate']]
        #merge_df = merge_df.rename(columns={'Gravel2':'Gravel'})
        pvt = pd.pivot_table(merge_df, index=['Substrate'],values=['Sand','Gravel','Boulders'],aggfunc=np.nansum)
    
        #Percentage classification table
        class_df = pvt.div(pvt.sum(axis=1), axis=0).reset_index()
    
        writer = pytablewriter.MarkdownTableWriter()
        writer.table_name = "Visual Segmentation " + str(meter) + " Square Meter Filter"
        writer.header_list = list(class_df.columns.values)
        writer.value_matrix = class_df.values.tolist()
        writer.write_table()   