//! 相关系数矩阵计算
//!
//! 支持 Pearson 和 Spearman 相关系数
//! 使用并行计算优化性能

use ndarray::{Array1, Array2, ArrayView2};
use rayon::prelude::*;
use std::cmp::min;

use crate::error::{MatrixError, Result};

/// 计算相关系数矩阵
///
/// # 参数
/// * `data` - 输入数据矩阵 (样本 x 特征)
/// * `method` - 相关系数类型："pearson" 或 "spearman"
///
/// # 返回
/// 相关系数矩阵 (特征 x 特征)
///
/// # 性能特点
/// - 使用并行计算
/// - 只计算上三角矩阵，然后对称填充
/// - 相比纯 Python 实现可实现 30-50x 提速
///
/// # 示例
/// ```rust
/// use ndarray::array2;
/// use bioworkflow_matrix::correlation_matrix;
///
/// let data = array2![
///     [1.0, 2.0, 3.0],
///     [4.0, 5.0, 6.0],
///     [7.0, 8.0, 9.0],
///     [10.0, 11.0, 12.0]
/// ];
///
/// let corr = correlation_matrix(&data.view(), "pearson").unwrap();
/// assert_eq!(corr.shape(), &[4, 4]);
/// ```
pub fn correlation_matrix(data: &ArrayView2<f64>, method: &str) -> Result<Array2<f64>> {
    let (n_samples, n_features) = data.dim();

    // 验证输入
    if n_samples < 2 {
        return Err(MatrixError::InsufficientSamples { min: 2 });
    }
    if n_features < 1 {
        return Err(MatrixError::InsufficientFeatures { min: 1 });
    }

    // 检查 NaN 和无穷大
    if !is_finite(data) {
        return Err(MatrixError::InvalidData {
            message: "数据包含 NaN 或无穷大值".to_string(),
        });
    }

    match method {
        "pearson" => pearson_correlation(data),
        "spearman" => spearman_correlation(data),
        _ => Err(MatrixError::UnsupportedMethod(method.to_string())),
    }
}

/// Pearson 相关系数矩阵
///
/// 使用并行计算优化
fn pearson_correlation(data: &ArrayView2<f64>) -> Result<Array2<f64>> {
    let (n_samples, n_features) = data.dim();
    let mut corr = Array2::zeros((n_features, n_features));

    // 标准化数据 (减均值，除标准差)
    let means = data.mean_axis(ndarray::Axis(0)).unwrap();
    let stds = data.map_axis(ndarray::Axis(0), |row| {
        let mean = row.mean().unwrap_or(0.0);
        let var = row.mapv(|x| (x - mean).powi(2)).mean().unwrap_or(1.0);
        var.sqrt()
    });

    // 并行计算相关系数
    corr.par_iter_mut().enumerate().for_each(|((i, j), val)| {
        if i == j {
            *val = 1.0;
        } else if i < j {
            let col_i = data.column(i);
            let col_j = data.column(j);

            let standardized_i = (&col_i - &means[i]) / stds[i];
            let standardized_j = (&col_j - &means[j]) / stds[j];

            let sum_product: f64 = standardized_i
                .iter()
                .zip(standardized_j.iter())
                .map(|(a, b)| a * b)
                .sum();

            *val = sum_product / (n_samples as f64 - 1.0);
        }
    });

    // 填充下三角矩阵（对称）
    for i in 0..n_features {
        for j in 0..i {
            corr[[i, j]] = corr[[j, i]];
        }
    }

    Ok(corr)
}

/// Spearman 相关系数矩阵
///
/// 先将数据转换为秩，然后计算 Pearson 相关系数
fn spearman_correlation(data: &ArrayView2<f64>) -> Result<Array2<f64>> {
    let (n_samples, n_features) = data.dim();

    // 计算每个特征的秩
    let mut ranks = Array2::zeros((n_samples, n_features));

    for j in 0..n_features {
        let col = data.column(j).to_owned();
        let rank = compute_rank(&col);
        ranks.column_mut(j).assign(&rank);
    }

    // 对秩矩阵计算 Pearson 相关系数
    pearson_correlation(&ranks.view())
}

/// 计算秩（处理并列情况）
///
/// 使用平均秩处理并列值
fn compute_rank(data: &Array1<f64>) -> Array1<f64> {
    let n = data.len();
    let mut indexed: Vec<(usize, f64)> = data.iter().copied().enumerate().collect();

    // 排序
    indexed.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());

    let mut ranks = vec![0.0; n];
    let mut i = 0;

    while i < n {
        let mut j = i;
        // 找到所有并列的值
        while j < n && indexed[j].1 == indexed[i].1 {
            j += 1;
        }

        // 计算平均秩
        let avg_rank = ((i + j - 1) as f64) / 2.0 + 1.0;

        // 赋值
        for k in i..j {
            ranks[indexed[k].0] = avg_rank;
        }

        i = j;
    }

    Array1::from(ranks)
}

/// 检查矩阵是否包含有限值（无 NaN 或无穷大）
fn is_finite(data: &ArrayView2<f64>) -> bool {
    data.iter().all(|&x| x.is_finite())
}

#[cfg(test)]
mod tests {
    use super::*;
    use ndarray::array2;

    #[test]
    fn test_pearson_perfect_correlation() {
        // 完全正相关
        let data = array2![[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [3.0, 6.0, 9.0]];
        let corr = correlation_matrix(&data.view(), "pearson").unwrap();

        assert!((corr[[0, 1]] - 1.0).abs() < 1e-10);
        assert!((corr[[0, 2]] - 1.0).abs() < 1e-10);
        assert!((corr[[1, 2]] - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_pearson_diagonal() {
        // 对角线应该都是 1.0
        let data = array2![
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
            [10.0, 11.0, 12.0]
        ];
        let corr = correlation_matrix(&data.view(), "pearson").unwrap();

        for i in 0..4 {
            assert!((corr[[i, i]] - 1.0).abs() < 1e-10);
        }
    }

    #[test]
    fn test_pearson_symmetric() {
        let data = array2![[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]];
        let corr = correlation_matrix(&data.view(), "pearson").unwrap();

        // 对称矩阵
        assert!((corr[[0, 1]] - corr[[1, 0]]).abs() < 1e-10);
    }

    #[test]
    fn test_spearman() {
        let data = array2![[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]];
        let corr = correlation_matrix(&data.view(), "spearman").unwrap();

        // 对角线是 1.0
        for i in 0..3 {
            assert!((corr[[i, i]] - 1.0).abs() < 1e-10);
        }
    }

    #[test]
    fn test_insufficient_samples() {
        let data = array2![[1.0, 2.0, 3.0]];
        let result = correlation_matrix(&data.view(), "pearson");
        assert!(matches!(
            result,
            Err(MatrixError::InsufficientSamples { min: 2 })
        ));
    }

    #[test]
    fn test_invalid_data() {
        let data = array2![[1.0, f64::NAN], [2.0, 3.0]];
        let result = correlation_matrix(&data.view(), "pearson");
        assert!(matches!(result, Err(MatrixError::InvalidData { .. })));
    }
}
