import numpy as np
import pymannkendall as mk
import os
import fnmatch
import rasterio as ras
from tqdm import tqdm

"""
Theil-Sen Median趋势分析 + Mann-Kendall检验法
"""


def sen_mk_test(image_path, result_path):
    # image_path:影像的存储路径
    # result_path:结果输出路径

    filepaths = fnmatch.filter(os.listdir(image_path), '*.tif')
    _filepaths = []
    for fn in filepaths:
        _filepaths.append(os.path.join(image_path, fn))
    filepaths = _filepaths

    # 获取影像数量
    num_images = len(filepaths)
    # 读取影像数据
    img1 = ras.open(filepaths[0])
    # 获取影像的投影，高度和宽度
    crs1 = img1.crs
    transform1 = img1.transform
    height1 = img1.height
    width1 = img1.width
    array1 = img1.read()
    nodata = img1.nodata
    img1.close()

    # 读取所有影像
    print('-----读取影像------')
    for path1 in tqdm(filepaths[1:]):
        if path1[-3:] == 'tif':
            img2 = ras.open(path1)
            array2 = img2.read()
            array1 = np.vstack((array1, array2))
            img2.close()

    nums, width, height = array1.shape

    # 写影像
    def writeImage(image_save_path, height1, width1, para_array, bandDes, crs1, transform1, nodata):
        with ras.open(
                image_save_path,
                'w',
                driver='GTiff',
                height=height1,
                width=width1,
                count=1,
                dtype=para_array.dtype,
                crs=crs1,
                transform=transform1,
                nodata=nodata
        ) as dst:
            dst.write_band(1, para_array)
            dst.set_band_description(1, bandDes)
        del dst

    # 输出矩阵，无值区用-9999填充
    slope_array = np.full([width, height], np.nan)
    z_array = np.full([width, height], np.nan)
    Trend_array = np.full([width, height], np.nan)
    Tau_array = np.full([width, height], np.nan)
    s_array = np.full([width, height], np.nan)
    p_array = np.full([width, height], np.nan)
    # 只有有值的区域才进行mk检验
    c1 = np.isnan(array1)
    sum_array1 = np.sum(c1, axis=0)
    nan_positions = np.where(sum_array1 == num_images)

    positions = np.where(sum_array1 != num_images)

    # mk test
    print('-----mk-test------')
    for i in tqdm(range(len(positions[0]))):
        x = positions[0][i]
        y = positions[1][i]
        mk_list1 = array1[:, x, y]
        trend, h, p, z, Tau, s, var_s, slope, intercept = mk.original_test(mk_list1)
        '''        
        trend: tells the trend (increasing, decreasing or no trend)
                h: True (if trend is present) or False (if trend is absence)
                p: p-value of the significance test
                z: normalized test statistics
                Tau: Kendall Tau
                s: Mann-Kendal's score
                var_s: Variance S
                slope: Theil-Sen estimator/slope
                intercept: intercept of Kendall-Theil Robust Line
        '''

        if trend == "decreasing":
            trend_value = -1
        elif trend == "increasing":
            trend_value = 1
        else:
            trend_value = 0
        slope_array[x, y] = slope  # senslope
        s_array[x, y] = s
        z_array[x, y] = z
        Trend_array[x, y] = trend_value
        p_array[x, y] = p
        Tau_array[x, y] = Tau

    all_array = [slope_array, Trend_array, p_array, s_array, Tau_array, z_array]

    slope_save_path = os.path.join(result_path, "slope.tif")
    Trend_save_path = os.path.join(result_path, "Trend.tif")
    p_save_path = os.path.join(result_path, "p.tif")
    s_save_path = os.path.join(result_path, "s.tif")
    tau_save_path = os.path.join(result_path, "tau.tif")
    z_save_path = os.path.join(result_path, "z.tif")
    image_save_paths = [slope_save_path, Trend_save_path, p_save_path, s_save_path, tau_save_path, z_save_path]
    band_Des = ['slope', 'trend', 'p_value', 'score', 'tau', 'z_value']

    if not os.path.exists(result_path):
        os.makedirs(result_path)

    print('-----输出结果------')
    for i in tqdm(range(len(all_array))):
        writeImage(image_save_paths[i], height1, width1, all_array[i], band_Des[i], crs1, transform1, nodata)


# 调用

base_dir = r'D:\project\wrr\data_npp\QFY'
category_arr = ['npp_extra_tif']

for c in category_arr:
    input_dir = os.path.join(base_dir, c)
    output_dir = os.path.join(base_dir, 'trend_mk_' + c)
    sen_mk_test(input_dir, output_dir)
    print('################ \n')

print("------------------end----------------------")
