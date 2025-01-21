# GIS-data-process-analysis
一些用过的GIS数据处理以及一些分析的常用代码

## analysis

1. Theil-sen趋势分析和mk检验
2. 基于像元的多变量偏相关系数计算（连带输出显著性检验p值）
3. 基于像元的长时序栅格数据缺失率统计（具体定义请查看代码内）以及基于单幅栅格影像的数据缺失率统计

## process
1. TiandituLonLatTile2TifConverter 天地图经纬度地图切片转为Geotiff文件（里面包含切片xyz和经纬度互转的方法）
2. 按指定大小分割tif文件，可处理大小无法整除情况，如图像大小（1282，2566），可以强制分割为（500，500），不足的地方使用0填充
