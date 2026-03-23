//! BioWorkflow Matrix Library - 高性能矩阵操作
//!
//! 提供生物信息学数据分析所需的矩阵操作功能：
//! - 相关系数矩阵 (Pearson, Spearman)
//! - 距离矩阵 (欧几里得，曼哈顿，余弦)
//! - 层次聚类
//!
//! # 性能特点
//! - 使用 ndarray 进行向量化计算
//! - 使用 rayon 进行并行计算
//! - 相比纯 Python 实现可实现 50-100x 提速
//!
//! # 示例
//! ```rust
//! use bioworkflow_matrix::{correlation_matrix, distance_matrix, DistanceMetric};
//! use ndarray::array2;
//!
//! let data = array2![
//!     [1.0, 2.0, 3.0],
//!     [4.0, 5.0, 6.0],
//!     [7.0, 8.0, 9.0]
//! ];
//!
//! // 计算 Pearson 相关系数矩阵
//! let corr = correlation_matrix(&data, "pearson").unwrap();
//!
//! // 计算欧几里得距离矩阵
//! let dist = distance_matrix(&data, DistanceMetric::Euclidean).unwrap();
//! ```

pub mod correlation;
pub mod distance;
pub mod clustering;
pub mod error;

#[cfg(feature = "python")]
pub mod python;

pub use correlation::correlation_matrix;
pub use distance::{distance_matrix, DistanceMetric};
pub use clustering::hierarchical_cluster;
pub use error::{MatrixError, Result};

/// 库版本
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::array2;

    #[test]
    fn test_correlation_matrix() {
        let data = array2![
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
            [10.0, 11.0, 12.0]
        ];

        let corr = correlation_matrix(&data, "pearson").unwrap();
        
        // 对角线应该都是 1.0
        for i in 0..3 {
            assert!((corr[[i, i]] - 1.0).abs() < 1e-10);
        }
    }

    #[test]
    fn test_distance_matrix() {
        let data = array2![
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0]
        ];

        let dist = distance_matrix(&data, DistanceMetric::Euclidean).unwrap();
        
        // 对角线应该都是 0.0
        for i in 0..3 {
            assert!(dist[[i, i]].abs() < 1e-10);
        }
        
        // 对称矩阵
        for i in 0..3 {
            for j in 0..3 {
                assert!((dist[[i, j]] - dist[[j, i]]).abs() < 1e-10);
            }
        }
    }
}
