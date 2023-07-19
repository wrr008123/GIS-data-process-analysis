import fnmatch
import os

import numpy as np
import rasterio

"""
基于像元的长时序数据缺失率计算

假如一共有20景数据，那么对于某一个像元而言，这个像元位置其中有12景的值为nodata，那么该像元的缺失率为 12/20

"""

def listdir(dir, pat):
    dirs = os.listdir(dir)
    return fnmatch.filter(dirs, pat)


def read_tif(abs_path):
    ras = rasterio.open(abs_path)
    ras_data = ras.read(1)
    nodata = ras.nodatavals[0]
    ras_data = np.array(ras_data)
    ras_data = np.where(ras_data == nodata, np.nan, ras_data)
    ras.close()
    return ras_data


def read_tifs(path):
    tif_names = listdir(path, '*.tif')

    list_data = []
    for tifname in tif_names:
        a = read_tif(os.path.join(path, tifname))
        list_data.append(a)

    return np.stack(list_data, axis=-1)


def write_result(output_path, data, template, dtype):
    with rasterio.open(output_path, 'w', driver='GTiff', height=template.height, width=template.width, count=1,
                       dtype=dtype, crs=template.crs, transform=template.transform) as dst:
        dst.write(data, 1)  # 写入数据到第一个波段


if __name__ == '__main__':
    template_ras = rasterio.open(r'C:\Users\wrr\Documents\Tencent Files\1148200541\FileRecv\SG\SG_001.tif')
    raster_data = read_tifs(r"C:\Users\wrr\Documents\Tencent Files\1148200541\FileRecv\SG")
    output_path = r'C:\Users\wrr\Desktop\222100090356\sg.tif'

    missing_pixels = np.isnan(raster_data)
    missing_ratio = np.mean(missing_pixels, axis=-1)
    write_result(output_path, missing_ratio, template_ras, 'float32')
    print('------------end------------')
