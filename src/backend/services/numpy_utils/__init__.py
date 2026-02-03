"""
NumPy 数据处理工具模块

提供生物信息学数据处理的常用 NumPy 操作
"""

from .processor import (
    DataProcessor,
    DataFormat,
    array_to_dataframe,
    dataframe_to_array,
    normalize_data,
    calculate_statistics,
)
from .matrix_ops import (
    MatrixOperations,
    correlation_matrix,
    distance_matrix,
    pca_transform,
)

__all__ = [
    "DataProcessor",
    "DataFormat",
    "array_to_dataframe",
    "dataframe_to_array",
    "normalize_data",
    "calculate_statistics",
    "MatrixOperations",
    "correlation_matrix",
    "distance_matrix",
    "pca_transform",
]
