# coding=utf-8
import fnmatch
import os

import numpy as np
import pandas as pd
import rasterio


class FileUtils:
    """
     pat: 过滤关键字
     path: 如果是文件的话则表示文件全路径
     dir: 仅仅表示为路径
    """

    @staticmethod
    def listdir(dir, pat):
        """
        example: FileUtils.listdir(img_dir, '*.tif')

        :param dir:
        :param pat: 过滤关键字
        :return:
        """
        dirs = os.listdir(dir)
        return fnmatch.filter(dirs, pat)

    @staticmethod
    def list_full_dir(dir, pat):
        names = FileUtils.listdir(dir, pat)
        result = []
        for n in names:
            result.append(os.path.join(dir, n))
        return result

    @staticmethod
    def file_rename(file_dir, old_name, new_name):
        os.rename(os.path.join(file_dir, old_name), os.path.join(file_dir, new_name))

    @staticmethod
    def mkdirs(dir):
        if not os.path.exists(dir):
            os.makedirs(dir)


class RasterUtils:

    @staticmethod
    def stack_rasters(tif_path_list, nodata_replace=np.nan):
        """
        将多个单波段的栅格堆叠为一个多波段的三维数组，如图像大小1025*900，共30景，最终结果为（1025，900，30）
        :param tif_path_list:
        :param nodata_replace:
        :return:
        """
        list = []
        for tif in tif_path_list:
            arr = RasterUtils.read2arr(tif, nodata_replace)
            list.append(arr)

        return np.stack(list, axis=-1)

    @staticmethod
    def read2arr(tif_path, nodata_replace=np.nan):
        """
        读取栅格图像的第一个波段为一个二维数组
        :param tif_path: tif路径
        :param nodata_replace: nodata值替换为某个值，默认为np.nan
        :return:
        """
        with rasterio.open(tif_path) as ras:
            ras_data = ras.read(1)
            nodata = ras.nodatavals[0]
            ras_data = np.array(ras_data)
            ras_data = np.where(ras_data == nodata, nodata_replace, ras_data)
            return ras_data

    @staticmethod
    def write2tif(output_path, data, template, dtype='float32'):
        """
        根据 {template} 的宽高和投影等输出一个同样大小的tif数据
        :param output_path: 输出结果路径，如./xx.tif
        :param data: 一个二维数组，表示栅格数据
        :param template: rasterio.open() 所读取的datasets对象
        :param dtype: 输出结果数据类型，默认 float32
        :return:
        """

        with rasterio.open(output_path, 'w', driver='GTiff', height=template.height, width=template.width, count=1,
                           dtype=dtype, crs=template.crs, transform=template.transform) as dst:
            dst.write(data, 1)  # 写入数据到第一个波段


class BaseUtils:

    @staticmethod
    def parallel_remove_none(x, y):
        new_x = []
        new_y = []

        for a, b in zip(x, y):
            if a is not None and b is not None:
                new_x.append(a)
                new_y.append(b)
        return new_x, new_y

    @staticmethod
    def save2csv(csv_file, *colum_arr):

        data_map = {}
        columns = []
        for i in range(len(colum_arr)):
            colum_data = colum_arr[i]
            colum_name = 'col_' + str(i)
            columns.append(colum_name)
            data_map[colum_name] = colum_data

        df = pd.DataFrame(data_map, columns=columns)
        df.to_csv(csv_file)

    @staticmethod
    def save2csv_columns(csv_file, column_names, colum_data_arr, drop_row_by_none=False, encoding='GB2312'):

        df = BaseUtils.build_pandas_df(column_names, colum_data_arr)

        if drop_row_by_none:
            df = df.dropna()

        df.to_csv(csv_file, encoding=encoding)

    @staticmethod
    def build_pandas_df(column_names, colum_data_arr):
        if len(column_names) != len(colum_data_arr):
            raise Exception('column name length != column data length!')
        data_map = {}
        for i in range(len(colum_data_arr)):
            colum_data = colum_data_arr[i]
            colum_name = column_names[i]
            data_map[colum_name] = colum_data

        df = pd.DataFrame(data_map, columns=column_names)
        return df

    @staticmethod
    def write_to_csv(data, filename):
        """
        数据为多行数据，包括列名的
        :param data:
        :param filename:
        :return:
        """
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, header=False)


if __name__ == '__main__':

    dir = r'E:\research_code\sundries_process\result\radiation_2'
    names = os.listdir(dir)
    for n in names:
        FileUtils.file_rename(dir, n, n.replace('.xlsx', '.csv'))
