# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 14:37:20 2017

@author: dan
"""

from skimage.segmentation import slic, mark_boundaries
import numpy as np
from osgeo import gdal, osr
import PyHum.utils as utils
import matplotlib.pyplot as plt
import os


def CreateRaster(datm,gt,proj,cols,rows,driverName,outFile):  
     '''
     Exports data to GTiff Raster
     '''
     datm = np.squeeze(datm)
     datm[np.isnan(datm)] = -99
     driver = gdal.GetDriverByName(driverName)
     ds = driver.Create( outFile, cols, rows, 1, gdal.GDT_Float32)        
     if proj is not None:  
          ds.SetProjection(proj.ExportToWkt()) 
     ds.SetGeoTransform(gt)
     ss_band = ds.GetRasterBand(1)
     ss_band.WriteArray(datm)
     ss_band.SetNoDataValue(-99)
     ss_band.FlushCache()
     ss_band.ComputeStatistics(False)
     del ds
     
def read_raster(in_raster):
    in_raster=in_raster
    ds = gdal.Open(in_raster)
    data = ds.GetRasterBand(1).ReadAsArray()
    data[data==-99] = np.nan
    proj = ds.GetProjection()
    gt = ds.GetGeoTransform()
    xres = gt[1]
    yres = gt[5]
    
    # get the edge coordinates and add half the resolution 
    # to go to center coordinates
    xmin = gt[0] + xres * 0.5
    xmax = gt[0] + (xres * ds.RasterXSize) - xres * 0.5
    ymin = gt[3] + (yres * ds.RasterYSize) + yres * 0.5
    ymax = gt[3] - yres * 0.5
    del ds
    # create a grid of xy coordinates in the original projection
    xx, yy = np.mgrid[xmin:xmax+xres:xres, ymax+yres:ymin:yres]
    return data, xx, yy, gt, proj

    
if __name__ == '__main__':
    root  = r"C:\workspace\gound_truth\output\slic_seg_plots"
    sed5class_raster = r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\may2014_mb6086r_sedclass\mb_sed5class_2014_05_raster.tif"

    for num in [900,1000,1100,1200,1300,1400,1500,1600,1700,1800]:
        data, xx, yy, gt, proj = read_raster(sed5class_raster)
        data[np.isnan(data)] = 0
        data = utils.rescale(data,0,1)
        segments_slic = slic(data,n_segments=num,compactness=0.1)
        test = segments_slic.copy()
        test = test.astype('float')
        test[np.isnan(read_raster(sed5class_raster)[0])] = np.nan
        
        fig,ax = plt.subplots()
        ax.imshow(mark_boundaries(data, segments_slic,color=[1,0,0]),cmap='coolwarm') 
        title = ' n_segments = %s' %(str(num),)
        ax.set_title(title)
        plt.tight_layout()
        oName = root + os.sep + 'mkboundaries_sed5class_' + str(num) + '_segs.png'
        plt.savefig(oName,dpi=600)
        plt.close()
             
        fig,ax = plt.subplots()
        ax.imshow(read_raster(sed5class_raster)[0],cmap='Greys_r')
        ax.imshow(test %11,cmap='Set3',alpha=0.6) 
        title = ' n_segments = %s' %(str(num),)
        ax.set_title(title)
        plt.tight_layout()
        oName = root + os.sep + 'cmap_sed5class_' + str(num) + '_segs.png'
        plt.savefig(oName, dpi=200)
        plt.close()
