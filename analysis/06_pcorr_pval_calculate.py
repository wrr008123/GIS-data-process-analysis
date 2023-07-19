import os.path

import pingouin as pg
import rasterio
import numpy as np
from tqdm import tqdm
from my_utils import FileUtils
from my_utils import BaseUtils

"""
多变量偏相关分析计算,连带输出检验p值
"""

y_root_dir = r'D:\project\wrr\data_npp\基础数据_对齐_贵州\01_npp'
x_root_dir = r'D:\project\wrr\data_npp\基础数据_对齐_贵州\02_气象数据'
out_dir = r'D:\project\wrr\data_npp\基础数据_对齐_贵州\08_pcorr_pval'
y_name = 'npp'
element_names = ['降水量', '平均气温', '平均相对湿度', '日照时数']
template_raster = r'D:\project\wrr\data_npp\基础数据_对齐_贵州\01_npp\2000.tif'

r = rasterio.open(template_raster)
template_transform = r.transform
template_height = r.height
template_width = r.width
r.close()


def stack_imgs(img_paths: list[str]):
    arr_list = []
    for img_p in img_paths:
        img = rasterio.open(img_p)
        arr = img.read()
        arr = np.squeeze(arr)
        arr[arr == img.nodata] = np.nan
        img.close()
        arr_list.append(arr)

    return np.stack(arr_list, axis=2)


def _p_corr(df):
    multi_p_corr_result = []
    for i in range(len(element_names)):
        covar_arr = element_names[:i] + element_names[i + 1:]
        p_corr_result = pg.partial_corr(data=df, x=element_names[i], y=y_name, covar=covar_arr).round(4)
        multi_p_corr_result.append(p_corr_result)
    return multi_p_corr_result


def _save_img(image_save_path, img_arr):
    with rasterio.open(
            image_save_path,
            'w',
            driver='GTiff',
            height=template_height,
            width=template_width,
            count=1,
            dtype=img_arr.dtype,
            crs='+proj=latlong',
            nodata=np.nan,
            transform=template_transform,
    ) as dst:
        dst.write_band(1, img_arr)
        dst.set_band_description(1, '')
    del dst


y_file_list = FileUtils.list_full_dir(y_root_dir, '*.tif')
x_file_2d_list = []

for element_name in element_names:
    x_file_list = FileUtils.list_full_dir(os.path.join(x_root_dir, element_name), '*.tif')
    x_file_2d_list.append(x_file_list)

y_imgs = stack_imgs(y_file_list)
x_2d_imgs = []

for x_file_list in x_file_2d_list:
    x_2d_imgs.append(stack_imgs(x_file_list))

df_colum_names = [n for n in element_names]
df_colum_names.insert(0, y_name)

# 偏相关系数容器
_p_corr_out_frame_list = []
# 检验p值容器
_p_corr_pval_out_frame_list = []
for i in range(len(element_names)):
    out_frame = np.full((y_imgs.shape[0], y_imgs.shape[1]), np.nan)
    _p_corr_out_frame_list.append(out_frame)

    out_frame_pval = np.full((y_imgs.shape[0], y_imgs.shape[1]), np.nan)
    _p_corr_pval_out_frame_list.append(out_frame_pval)

# 逐像素计算各个因子的偏相关值
pbar = tqdm(total=y_imgs.shape[0] * y_imgs.shape[1])
for i in range(y_imgs.shape[0]):
    for j in range(y_imgs.shape[1]):
        df_colum_data_arr = []
        y = y_imgs[i, j, :]
        df_colum_data_arr.append(y)

        for x_imgs in x_2d_imgs:
            x = x_imgs[i, j, :]
            df_colum_data_arr.append(x)

        # 到这里一个像素位置的值都准备好了,生成pandas中的dataframe
        df = BaseUtils.build_pandas_df(df_colum_names, df_colum_data_arr)
        df = df.dropna()

        # 最低大于3行才计算偏相关
        if df.shape[0] > 3:
            # 根据df计算出各个因子与y的偏相关
            p_corr_result_list = _p_corr(df)
            for k in range(len(p_corr_result_list)):
                _p_corr_out_frame_list[k][i, j] = p_corr_result_list[k].iloc[:, 1].values[0]
                _p_corr_pval_out_frame_list[k][i, j] = p_corr_result_list[k].iloc[:, 3].values[0]

        pbar.update(1)
pbar.close()

# todo write p_corr_img
for i in range(len(_p_corr_out_frame_list)):
    out_img_arr = _p_corr_out_frame_list[i]
    ele_name = element_names[i]
    out_target = os.path.join(out_dir, 'pcorr_' + ele_name + '.tif')
    _save_img(out_target, out_img_arr)

    out_img_pval_arr = _p_corr_pval_out_frame_list[i]
    pval_out_target = os.path.join(out_dir, 'pcorr_pval_' + ele_name + '.tif')
    _save_img(pval_out_target, out_img_pval_arr)

print('----------end-------------')
