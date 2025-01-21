import rasterio
import numpy as np
import os
from tqdm import tqdm

def crop_and_pad_tif(input_tif, output_dir, crop_size):
    """
    裁剪并填充 TIFF 文件，并显示进度条。

    Args:
        input_tif (str): 输入 TIFF 文件路径。
        output_dir (str): 输出 TIFF 文件目录。
        crop_size (tuple): 裁剪尺寸 (width, height)。
    """

    with rasterio.open(input_tif) as src:
        # 读取元数据
        metadata = src.meta.copy()

        # 计算裁剪块的数量
        width = src.width
        height = src.height
        crop_width, crop_height = crop_size

        n_cols = int(np.ceil(width / crop_width))
        n_rows = int(np.ceil(height / crop_height))

        total_crops = n_rows * n_cols  # 计算总的裁剪块数量

        with tqdm(total=total_crops, desc="裁剪进度", unit="块") as pbar:  # 使用 tqdm 创建进度条
            for i in range(n_rows):
                for j in range(n_cols):
                    # 计算裁剪窗口的边界
                    left = j * crop_width
                    top = i * crop_height
                    right = min((j + 1) * crop_width, width)
                    bottom = min((i + 1) * crop_height, height)

                    window = rasterio.windows.Window(left, top, right - left, bottom - top)

                    # 读取裁剪区域的数据
                    try:
                        crop_data = src.read(window=window)
                    except ValueError as e:
                        print(f"Error reading window: {e}")
                        pbar.update(1) #即使出错也要更新进度条
                        continue

                    # 创建填充后的数据
                    padded_data = np.zeros((src.count, crop_height, crop_width), dtype=src.dtypes[0])

                    # 将裁剪的数据复制到填充后的数据中
                    pad_left = 0
                    pad_top = 0
                    data_width = crop_data.shape[2]
                    data_height = crop_data.shape[1]

                    padded_data[:, pad_top:pad_top+data_height, pad_left:pad_left+data_width] = crop_data


                    # 更新元数据
                    metadata.update({
                        'width': crop_width,
                        'height': crop_height,
                        'transform': rasterio.transform.from_origin(src.bounds.left + j * crop_width * src.res[0],
                                                                     src.bounds.top - i * crop_height * src.res[1],
                                                                     src.res[0], src.res[1]),
                        'count': src.count
                    })

                    # 构建输出文件名
                    output_filename = os.path.join(output_dir, f"crop_{i}_{j}.tif")

                    # 写入输出 TIFF 文件
                    with rasterio.open(output_filename, 'w', **metadata) as dst:
                        dst.write(padded_data)

                    pbar.update(1)  # 更新进度条

if __name__ == "__main__":
    # 示例用法
    input_tif = "input.tif"  #TIFF 文件路径
    output_dir = "output_crops"  # 输出目录
    crop_size = (256, 256)  # 裁剪尺寸
    
    os.makedirs(output_dir, exist_ok=True)
    
    crop_and_pad_tif(input_tif, output_dir, crop_size)
    print("裁剪完成！")
