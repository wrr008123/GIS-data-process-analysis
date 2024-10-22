import os
import fnmatch
import numpy as np
import rasterio
from PIL import Image
from rasterio.crs import CRS
from tqdm import tqdm

"""
公式原理参考：https://blog.csdn.net/snowfallxuan/article/details/122391512
"""

class TiandituLonLatTile2TifConverter:
    def __init__(self, crs=CRS.from_epsg(4490), tile_size=(256, 256)):
        """
        天地图经纬度投影地图瓦片转geotiff
        Args:
            crs: 坐标参考系统
            tile_size: 瓦片大小 (宽度, 高度)
        """
        self.crs = crs
        self.tile_width, self.tile_height = tile_size

    @staticmethod
    def get_idx_row_col_z(tile_name):
        """
        根据文件名获取瓦片的row idx，col idx以及zoomLevel

        请注意！当文件名发生变化后，都需要重写此方法实现！！！！！！！！！！！！！！！1

        :param tile_name:
        :return:
        """
        info_arr = os.path.splitext(tile_name)[0].split('-')
        row_idx = int(info_arr[2])
        col_idx = int(info_arr[1])
        zoom = int(info_arr[3])
        return row_idx, col_idx, zoom

    @staticmethod
    def calculate_row_col_idx(lon, lat, z):
        """
        根据经纬度以及缩放级别计算瓦片索引
        :param lon:
        :param lat:
        :param z:
        :return:
        """

        # 行列数从1开始，idx索引从0开始计算的，天地图url中的值是索引值
        num_row = (90 - lat) / (180 / (2 ** (z - 1))) + 1
        num_col = (lon - (-180)) / (360 / (2 ** z)) + 1

        num_row_idx = int(num_row) - 1
        num_col_idx = int(num_col) - 1
        return num_row_idx, num_col_idx

    @staticmethod
    def calculate_lon_lat(num_row_idx, num_col_idx, z):
        """
        计算瓦片左上角的经纬度
        Args:
            num_row_idx: 行索引
            num_col_idx: 列索引
            z: 缩放级别

        Returns:
            tuple: 经度, 纬度
        """
        # 计算每个图片的经纬度步长
        lat_step = 180 / (2 ** (z - 1))
        lon_step = 360 / (2 ** z)

        # 计算纬度和经度
        lat = 90 - num_row_idx * lat_step
        lon = -180 + num_col_idx * lon_step

        return lon, lat

    @staticmethod
    def calculate_pixel_resolution(tile_width, tile_height, zoomLevel):
        """
        计算像素分辨率

        Args:
            zoomLevel: 缩放级别

        Returns:
            tuple: 经度分辨率, 纬度分辨率
        """
        lat_resolution = 180 / (2 ** (zoomLevel - 1)) / tile_height
        lon_resolution = 360 / (2 ** zoomLevel) / tile_width
        return lon_resolution, lat_resolution

    def convert_single_image(self, input_path, output_path, zoomLevel, col_idx, row_idx):
        """
        将单个图像转换为 GeoTIFF

        Args:
            input_path: 输入图像路径
            output_path: 输出 GeoTIFF 路径
            zoomLevel: 缩放级别
            col_idx: 瓦片列号
            row_idx: 瓦片行号
        """
        # 计算每个像素的经纬度值（也就是分辨率）
        lon_resolution, lat_resolution = self.calculate_pixel_resolution(self.tile_width, self.tile_height, zoomLevel)

        # 计算瓦片在世界坐标系中的左上角坐标
        left, top = self.calculate_lon_lat(row_idx, col_idx, zoomLevel)

        # 读取PNG图像
        with Image.open(input_path) as img:
            img = img.convert('RGB')  # 确保是 RGB 模式
            data = np.array(img)

            # 创建GeoTIFF文件
            profile = {
                'driver': 'GTiff',
                'height': self.tile_height,
                'width': self.tile_width,
                'count': 3,  # 3波段
                'dtype': data.dtype,
                'crs': self.crs,
                'transform': rasterio.transform.from_origin(left, top, lon_resolution, lat_resolution)
            }

        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data[:, :, 0], 1)  # 写入 R 通道
            dst.write(data[:, :, 1], 2)  # 写入 G 通道
            dst.write(data[:, :, 2], 3)  # 写入 B 通道

    def batch_convert(self, input_dir, output_dir, extension='.png'):
        """
        批量转换图像为 GeoTIFF

        Args:
            input_dir: 输入图像目录
            output_dir: 输出 GeoTIFF 目录
            extension: 输入图像扩展名
        """

        os.makedirs(output_dir, exist_ok=True)
        img_names = fnmatch.filter(os.listdir(input_dir), f'*{extension}')
        for img_n in tqdm(img_names):
            in_path = os.path.join(input_dir, img_n)
            out_path = os.path.join(output_dir, img_n.replace(extension, '.tif'))

            # 获取瓦片信息- 这一块可能需要自定义
            row_idx, col_idx, zoom = self.get_idx_row_col_z(img_n)

            self.convert_single_image(in_path, out_path, zoom, col_idx, row_idx)


if __name__ == '__main__':
    """
    时间-colIdx-rowIdx-z.png
    dir---------------------------
        201812-209624-45068-18.png
        201812-209624-45069-18.png
        201812-209624-45070-18.png
        201812-209624-45071-18.png
        201812-209624-45072-18.png
        201812-209624-45073-18.png
        201812-209624-45074-18.png
    """


    # 使用的时候根据文件名规则复写
    def new_get_idx_row_col_z(tile_name):
        """
        根据文件名获取瓦片的row idx，col idx以及zoomLevel

        请注意！当文件名发生变化后，都需要重写此方法实现！！！！！！！！！！！！！！！1

        :param tile_name:
        :return:
        """
        info_arr = os.path.splitext(tile_name)[0].split('-')
        row_idx = int(info_arr[2])
        col_idx = int(info_arr[1])
        zoom = int(info_arr[3])
        return row_idx, col_idx, zoom


    converter = TiandituLonLatTile2TifConverter()
    converter.get_idx_row_col_z = new_get_idx_row_col_z
    converter.batch_convert(
        input_dir=r'F:\test\新建文件夹\source',
        output_dir=r'F:\test\新建文件夹\target-1',
        extension='.png',
    )
