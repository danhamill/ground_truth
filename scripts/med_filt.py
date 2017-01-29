# -*- coding: utf-8 -*-
"""
Created on Sun Jan 29 15:29:12 2017

@author: dan
"""
from __future__ import division
from scipy.ndimage.filters import median_filter
import numpy as np
from osgeo import gdal, osr
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

def get_raster_size(minx, miny, maxx, maxy, cell_width, cell_height):
    """
    Determine the number of rows/columns given the bounds of the point data and the desired cell size
    """
    cols = int((maxx - minx) / cell_width)
    rows = int((maxy - miny) / abs(cell_height))
    return cols, rows
    
    
if __name__ == '__main__':
    root  = r"C:\workspace\gound_truth\output\median_filter_plots"
    sed5class_raster = r"C:\workspace\Reach_4a\Multibeam\mb_sed_class\may2014_mb6086r_sedclass\mb_sed5class_2014_05_raster.tif"
    
    
    for num in [4,8,12,16,20]:
        data, xx, yy, gt, proj = read_raster(sed5class_raster)
        Ny, Nx = np.shape(data)
        a = num/Nx
        b = num/Ny
        
        data[np.isnan(data)] = 0
        data = median_filter(data,(int(Nx*a),int(Ny*b)))
        
        data[np.isnan(read_raster(sed5class_raster)[0])]= np.nan        
        fig,(ax, ax1) = plt.subplots(ncols=2)
        ax.imshow(read_raster(sed5class_raster)[0],cmap='coolwarm')
        ax1.imshow(data,cmap='coolwarm') 
        title = ' Median Filter : %s square meters' %(str(num/4),)
        ax.set_title('Oringal Raster')
        ax1.set_title(title)
        plt.tight_layout()
        oName = root + os.sep + 'scipy_median_filter_' + str(int(num/4)) + '_sq_meters.png'
        plt.savefig(oName, dpi=200)
        plt.close()
        
        proj = osr.SpatialReference()
        proj.ImportFromEPSG(26949)
        oName = r"C:\workspace\gound_truth\input\med_filter" + os.sep + 'sed5class_filtered_' + str(int(num/4)) + '_sq_meters.tif'
        c,r = get_raster_size(np.floor(np.min(xx)),np.floor(np.min(yy)),np.ceil(np.max(xx)),np.ceil(np.max(yy)),0.25,0.25)
        CreateRaster(data,gt,proj,c,r,'GTiff' ,oName)
        
        del data, Nx, Ny, oName
        
