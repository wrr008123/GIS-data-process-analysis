import numpy as np
import rasterio

"""
计算一景图像的缺失率
"""

mask_raster_file = r'C:\Users\wrr\Documents\WeChat Files\wxid_bsczvtwojnmv22\FileStorage\File\2023-07\temp\wuqueshi.tif'
wait_estimate_raster_file = r'C:\Users\wrr\Documents\WeChat Files\wxid_bsczvtwojnmv22\FileStorage\File\2023-07\temp\queshi.tif'


def read_tif(abs_path):
    ras = rasterio.open(abs_path, nodata=np.nan)
    ras_data = ras.read(1)
    nodata = ras.nodatavals[0]
    ras_data = np.array(ras_data)

    if nodata is None:
        ras_data = np.where(ras_data <= -100000, np.nan, ras_data)
    else:
        ras_data = np.where(ras_data == nodata, np.nan, ras_data)

    ras.close()
    return ras_data


def read_tif2mask(abs_path):
    ras = rasterio.open(abs_path)
    ras_data = ras.read(1)
    nodata = ras.nodatavals[0]
    ras_data = np.array(ras_data)

    if nodata is None:
        ras_data = np.where(ras_data <= -100000, 0, 1)
    else:
        ras_data = np.where(ras_data == nodata, 0, 1)

    ras.close()
    return ras_data


arr = read_tif(wait_estimate_raster_file)
mask = read_tif2mask(mask_raster_file)

extracted_values = arr[mask.astype(bool)]
output_array = extracted_values.flatten()

missing_pixels = np.isnan(output_array)
missing_ratio = np.mean(missing_pixels, axis=-1)
print(f'The miss ratio is: {missing_ratio}')
