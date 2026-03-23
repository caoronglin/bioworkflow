//! 矩阵操作错误处理

use thiserror::Error;

/// 矩阵操作错误类型
#[derive(Error, Debug)]
pub enum MatrixError {
    #[error("维度不匹配：期望 {expected}，实际得到 {actual}")]
    DimensionMismatch { expected: usize, actual: usize },

    #[error("数据包含 NaN 或无穷大值")]
    InvalidData { message: String },

    #[error("不支持的度量方法：{0}")]
    UnsupportedMetric(String),

    #[error("不支持的相关系数方法：{0}")]
    UnsupportedMethod(String),

    #[error("样本数量不足：至少需要 {min} 个样本")]
    InsufficientSamples { min: usize },

    #[error("特征数量不足：至少需要 {min} 个特征")]
    InsufficientFeatures { min: usize },

    #[error("矩阵奇异，无法计算逆矩阵")]
    SingularMatrix,

    #[error("数值计算错误：{0}")]
    NumericalError(String),

    #[error("Python 互操作错误：{0}")]
    #[cfg(feature = "python")]
    PythonError(#[from] pyo3::PyErr),

    #[error("NumPy 数组转换错误：{0}")]
    #[cfg(feature = "python")]
    NumPyError(#[from] numpy::FromVecArrayError),

    #[error("IO 错误：{0}")]
    IoError(#[from] std::io::Error),
}

/// 结果类型别名
pub type Result<T> = std::result::Result<T, MatrixError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_messages() {
        let err = MatrixError::DimensionMismatch {
            expected: 10,
            actual: 5,
        };
        assert!(err.to_string().contains("维度不匹配"));

        let err = MatrixError::InsufficientSamples { min: 3 };
        assert!(err.to_string().contains("样本数量不足"));
    }
}
