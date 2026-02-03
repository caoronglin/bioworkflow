"""
NumPy 数据处理器
提供数据格式转换、标准化、统计分析等功能

兼容 Python 3.13/3.14 和 Pandas 3.0+
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union

import numpy as np
from loguru import logger

# Pandas 3.0+ 使用 PyArrow 作为默认后端
try:
    import pandas as pd
    # Pandas 3.0 默认使用 pyarrow 后端
    pd.options.mode.dtype_backend = "pyarrow"
    HAS_PANDAS = True
    PANDAS_VERSION = tuple(map(int, pd.__version__.split(".")[:2]))
except ImportError:
    HAS_PANDAS = False
    PANDAS_VERSION = (0, 0)

# 可选: Polars 作为高性能替代
try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False


class DataFormat(Enum):
    """数据格式枚举"""
    CSV = "csv"
    TSV = "tsv"
    JSON = "json"
    NPY = "npy"
    NPZ = "npz"


@dataclass
class StatisticsResult:
    """统计结果"""
    mean: float
    std: float
    min: float
    max: float
    median: float
    q25: float
    q75: float
    count: int
    sum: float


class DataProcessor:
    """数据处理器类"""

    def __init__(self, data: Optional[np.ndarray] = None):
        """
        初始化数据处理器
        
        Args:
            data: 初始数据数组
        """
        self.data = data
        self._history: list[np.ndarray] = []

    def load_from_file(
        self, 
        filepath: Union[str, Path], 
        format: Optional[DataFormat] = None,
        **kwargs
    ) -> np.ndarray:
        """
        从文件加载数据
        
        Args:
            filepath: 文件路径
            format: 数据格式，如不指定则从扩展名推断
            **kwargs: 额外参数传递给加载函数
        """
        filepath = Path(filepath)
        
        if format is None:
            suffix = filepath.suffix.lower()
            format_map = {
                ".csv": DataFormat.CSV,
                ".tsv": DataFormat.TSV,
                ".txt": DataFormat.TSV,
                ".json": DataFormat.JSON,
                ".npy": DataFormat.NPY,
                ".npz": DataFormat.NPZ,
            }
            format = format_map.get(suffix, DataFormat.CSV)

        if format == DataFormat.CSV:
            self.data = np.genfromtxt(filepath, delimiter=",", **kwargs)
        elif format == DataFormat.TSV:
            self.data = np.genfromtxt(filepath, delimiter="\t", **kwargs)
        elif format == DataFormat.NPY:
            self.data = np.load(filepath, **kwargs)
        elif format == DataFormat.NPZ:
            loaded = np.load(filepath, **kwargs)
            # 返回第一个数组
            self.data = loaded[list(loaded.keys())[0]]
        elif format == DataFormat.JSON:
            import json
            with open(filepath) as f:
                self.data = np.array(json.load(f))
        
        logger.info(f"加载数据: {filepath}, 形状: {self.data.shape}")
        return self.data

    def save_to_file(
        self,
        filepath: Union[str, Path],
        format: Optional[DataFormat] = None,
        **kwargs
    ) -> None:
        """保存数据到文件"""
        if self.data is None:
            raise ValueError("没有数据可保存")
        
        filepath = Path(filepath)
        
        if format is None:
            suffix = filepath.suffix.lower()
            format_map = {
                ".csv": DataFormat.CSV,
                ".tsv": DataFormat.TSV,
                ".npy": DataFormat.NPY,
                ".npz": DataFormat.NPZ,
            }
            format = format_map.get(suffix, DataFormat.CSV)

        if format == DataFormat.CSV:
            np.savetxt(filepath, self.data, delimiter=",", **kwargs)
        elif format == DataFormat.TSV:
            np.savetxt(filepath, self.data, delimiter="\t", **kwargs)
        elif format == DataFormat.NPY:
            np.save(filepath, self.data)
        elif format == DataFormat.NPZ:
            np.savez_compressed(filepath, data=self.data)
        
        logger.info(f"保存数据到: {filepath}")

    def normalize(self, method: str = "zscore", axis: int = 0) -> np.ndarray:
        """
        数据标准化
        
        Args:
            method: 标准化方法 (zscore, minmax, robust)
            axis: 操作轴
        """
        if self.data is None:
            raise ValueError("没有数据")
        
        self._save_history()
        
        if method == "zscore":
            mean = np.mean(self.data, axis=axis, keepdims=True)
            std = np.std(self.data, axis=axis, keepdims=True)
            std[std == 0] = 1  # 避免除零
            self.data = (self.data - mean) / std
            
        elif method == "minmax":
            min_val = np.min(self.data, axis=axis, keepdims=True)
            max_val = np.max(self.data, axis=axis, keepdims=True)
            range_val = max_val - min_val
            range_val[range_val == 0] = 1
            self.data = (self.data - min_val) / range_val
            
        elif method == "robust":
            median = np.median(self.data, axis=axis, keepdims=True)
            q75, q25 = np.percentile(self.data, [75, 25], axis=axis, keepdims=True)
            iqr = q75 - q25
            iqr[iqr == 0] = 1
            self.data = (self.data - median) / iqr
        else:
            raise ValueError(f"未知的标准化方法: {method}")
        
        return self.data

    def filter_by_threshold(
        self,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        replace_with: Optional[float] = None
    ) -> np.ndarray:
        """
        按阈值过滤数据
        
        Args:
            min_val: 最小值阈值
            max_val: 最大值阈值
            replace_with: 替换值，如果为 None 则用 NaN
        """
        if self.data is None:
            raise ValueError("没有数据")
        
        self._save_history()
        
        replace = replace_with if replace_with is not None else np.nan
        
        if min_val is not None:
            self.data = np.where(self.data < min_val, replace, self.data)
        
        if max_val is not None:
            self.data = np.where(self.data > max_val, replace, self.data)
        
        return self.data

    def impute_missing(self, method: str = "mean", axis: int = 0) -> np.ndarray:
        """
        填充缺失值
        
        Args:
            method: 填充方法 (mean, median, zero, interpolate)
            axis: 计算轴
        """
        if self.data is None:
            raise ValueError("没有数据")
        
        self._save_history()
        
        mask = np.isnan(self.data)
        
        if method == "mean":
            fill_values = np.nanmean(self.data, axis=axis, keepdims=True)
            fill_array = np.broadcast_to(fill_values, self.data.shape)
        elif method == "median":
            fill_values = np.nanmedian(self.data, axis=axis, keepdims=True)
            fill_array = np.broadcast_to(fill_values, self.data.shape)
        elif method == "zero":
            fill_array = np.zeros_like(self.data)
        else:
            raise ValueError(f"未知的填充方法: {method}")
        
        self.data = np.where(mask, fill_array, self.data)
        return self.data

    def calculate_statistics(self, axis: Optional[int] = None) -> Union[StatisticsResult, list[StatisticsResult]]:
        """计算统计信息"""
        if self.data is None:
            raise ValueError("没有数据")
        
        def calc_stats(arr: np.ndarray) -> StatisticsResult:
            return StatisticsResult(
                mean=float(np.nanmean(arr)),
                std=float(np.nanstd(arr)),
                min=float(np.nanmin(arr)),
                max=float(np.nanmax(arr)),
                median=float(np.nanmedian(arr)),
                q25=float(np.nanpercentile(arr, 25)),
                q75=float(np.nanpercentile(arr, 75)),
                count=int(np.count_nonzero(~np.isnan(arr))),
                sum=float(np.nansum(arr)),
            )
        
        if axis is None:
            return calc_stats(self.data.flatten())
        else:
            return [calc_stats(self.data.take(i, axis=axis)) 
                    for i in range(self.data.shape[axis])]

    def _save_history(self) -> None:
        """保存历史状态"""
        if self.data is not None:
            self._history.append(self.data.copy())
            if len(self._history) > 10:  # 最多保留 10 个历史状态
                self._history.pop(0)

    def undo(self) -> Optional[np.ndarray]:
        """撤销上一步操作"""
        if self._history:
            self.data = self._history.pop()
            return self.data
        return None


# 便捷函数
def array_to_dataframe(
    arr: np.ndarray, 
    columns: Optional[list[str]] = None, 
    index: Optional[list] = None,
    use_polars: bool = False
):
    """
    将 NumPy 数组转换为 DataFrame
    
    Args:
        arr: NumPy 数组
        columns: 列名列表
        index: 索引列表
        use_polars: 是否使用 Polars (更快的性能)
    """
    if use_polars and HAS_POLARS:
        schema = {f"col_{i}": pl.Float64 for i in range(arr.shape[1])} if columns is None else None
        return pl.DataFrame(arr, schema=columns or schema)
    
    if not HAS_PANDAS:
        raise ImportError("需要安装 pandas 或 polars")
    
    # Pandas 3.0+ 默认使用 PyArrow 后端
    return pd.DataFrame(arr, columns=columns, index=index)


def dataframe_to_array(df) -> np.ndarray:
    """将 DataFrame 转换为 NumPy 数组"""
    if HAS_POLARS and hasattr(df, 'to_numpy'):
        return df.to_numpy()
    return df.values if hasattr(df, 'values') else np.array(df)


def normalize_data(data: np.ndarray, method: str = "zscore") -> np.ndarray:
    """快捷标准化函数"""
    processor = DataProcessor(data.copy())
    return processor.normalize(method)


def calculate_statistics(data: np.ndarray) -> StatisticsResult:
    """快捷统计函数"""
    processor = DataProcessor(data)
    return processor.calculate_statistics()
