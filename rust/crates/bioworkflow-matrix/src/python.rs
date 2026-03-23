//! Python 绑定 - 使用 PyO3
//!
//! 提供 Python 可调用的接口

use ndarray::{Array2, Axis};
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray2};
use pyo3::prelude::*;

use crate::{
    clustering::Linkage,
    correlation::correlation_matrix,
    distance::{distance_matrix, DistanceMetric},
    error::MatrixError,
    hierarchical_cluster,
};

/// Python 异常类型映射
fn to_pyerr(py: Python, err: MatrixError) -> PyErr {
    PyErr::new::<pyo3::exceptions::PyValueError, _>(err.to_string())
}

/// 计算相关系数矩阵
///
/// # 参数
/// * `py` - Python 解释器
/// * `data` - NumPy 数组 (样本 x 特征)
/// * `method` - 相关系数类型："pearson" 或 "spearman"
///
/// # 返回
/// NumPy 数组（相关系数矩阵）
///
/// # 示例
/// ```python
/// import numpy as np
/// import bioworkflow
///
/// data = np.array([
///     [1.0, 2.0, 3.0],
///     [4.0, 5.0, 6.0],
///     [7.0, 8.0, 9.0],
///     [10.0, 11.0, 12.0]
/// ])
///
/// corr = bioworkflow.correlation_matrix(data, "pearson")
/// print(corr.shape)  # (4, 4)
/// ```
#[pyfunction]
#[pyo3(name = "correlation_matrix")]
fn py_correlation_matrix<'py>(
    py: Python<'py>,
    data: PyReadonlyArray2<'py, f64>,
    method: &str,
) -> PyResult<&'py PyArray2<f64>> {
    let view = data.as_array();
    let result = correlation_matrix(&view, method).map_err(|e| to_pyerr(py, e))?;
    Ok(result.into_pyarray(py))
}

/// 计算距离矩阵
///
/// # 参数
/// * `py` - Python 解释器
/// * `data` - NumPy 数组 (样本 x 特征)
/// * `metric` - 距离度量："euclidean", "manhattan", "cosine", "correlation"
///
/// # 返回
/// NumPy 数组（距离矩阵）
///
/// # 示例
/// ```python
/// import numpy as np
/// import bioworkflow
///
/// data = np.array([
///     [0.0, 0.0],
///     [3.0, 4.0],
///     [6.0, 8.0]
/// ])
///
/// dist = bioworkflow.distance_matrix(data, "euclidean")
/// print(dist[0, 1])  # 5.0
/// ```
#[pyfunction]
#[pyo3(name = "distance_matrix")]
fn py_distance_matrix<'py>(
    py: Python<'py>,
    data: PyReadonlyArray2<'py, f64>,
    metric: &str,
) -> PyResult<&'py PyArray2<f64>> {
    let view = data.as_array();

    let metric = match metric.to_lowercase().as_str() {
        "euclidean" => DistanceMetric::Euclidean,
        "manhattan" => DistanceMetric::Manhattan,
        "cosine" => DistanceMetric::Cosine,
        "correlation" => DistanceMetric::Correlation,
        _ => {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "不支持的距离度量：{}. 支持的选项：euclidean, manhattan, cosine, correlation",
                metric
            )))
        }
    };

    let result = distance_matrix(&view, metric).map_err(|e| to_pyerr(py, e))?;
    Ok(result.into_pyarray(py))
}

/// 执行层次聚类
///
/// # 参数
/// * `py` - Python 解释器
/// * `data` - NumPy 数组 (样本 x 特征)
/// * `method` - 连接方式："single", "complete", "average", "ward"
/// * `metric` - 距离度量："euclidean", "manhattan", "cosine", "correlation"
///
/// # 返回
/// 包含聚类结果的字典：
/// - merges: 合并历史列表
/// - n_samples: 样本数量
///
/// # 示例
/// ```python
/// import numpy as np
/// import bioworkflow
///
/// data = np.array([
///     [1.0, 2.0],
///     [1.5, 1.8],
///     [5.0, 8.0],
///     [8.0, 8.0],
///     [1.0, 0.6],
///     [9.0, 11.0]
/// ])
///
/// result = bioworkflow.hierarchical_cluster(data, "average", "euclidean")
/// print(len(result["merges"]))  # 5 (n-1 次合并)
/// ```
#[pyfunction]
#[pyo3(name = "hierarchical_cluster")]
fn py_hierarchical_cluster<'py>(
    py: Python<'py>,
    data: PyReadonlyArray2<'py, f64>,
    method: &str,
    metric: &str,
) -> PyResult<PyObject> {
    let view = data.as_array();

    let linkage = match method.to_lowercase().as_str() {
        "single" => Linkage::Single,
        "complete" => Linkage::Complete,
        "average" => Linkage::Average,
        "ward" => Linkage::Ward,
        _ => {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "不支持的连接方式：{}. 支持的选项：single, complete, average, ward",
                method
            )))
        }
    };

    let dist_metric = match metric.to_lowercase().as_str() {
        "euclidean" => DistanceMetric::Euclidean,
        "manhattan" => DistanceMetric::Manhattan,
        "cosine" => DistanceMetric::Cosine,
        "correlation" => DistanceMetric::Correlation,
        _ => {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "不支持的距离度量：{}. 支持的选项：euclidean, manhattan, cosine, correlation",
                metric
            )))
        }
    };

    let result = hierarchical_cluster(&view, linkage, dist_metric).map_err(|e| to_pyerr(py, e))?;

    // 转换为 Python 字典
    let merges_list = result
        .merges
        .iter()
        .map(|m| {
            pyo3::types::PyDict::new_bound(py);
            let dict = pyo3::types::PyDict::new_bound(py);
            dict.set_item("cluster1", m.cluster1).unwrap();
            dict.set_item("cluster2", m.cluster2).unwrap();
            dict.set_item("distance", m.distance).unwrap();
            dict.set_item("size", m.size).unwrap();
            dict.to_object(py)
        })
        .collect::<Vec<PyObject>>();

    let result_dict = pyo3::types::PyDict::new_bound(py);
    result_dict.set_item("merges", merges_list).unwrap();
    result_dict.set_item("n_samples", result.n_samples).unwrap();

    Ok(result_dict.to_object(py))
}

/// 演示性能对比
#[pyfunction]
#[pyo3(name = "benchmark_correlation")]
fn py_benchmark_correlation(py: Python<'py>, size: usize) -> PyResult<&'py PyArray2<f64>> {
    // 生成随机数据
    let data: Vec<f64> = (0..size * size).map(|i| (i as f64 * 0.01).sin()).collect();
    let data_array = Array2::from_shape_vec((size, size), data).unwrap();

    // 计算相关系数矩阵并计时
    let start = std::time::Instant::now();
    let result = correlation_matrix(&data_array.view(), "pearson").unwrap();
    let duration = start.elapsed();

    eprintln!(
        "Rust correlation_matrix ({}x{}): {:.4} 秒",
        size,
        size,
        duration.as_secs_f64()
    );

    Ok(result.into_pyarray(py))
}

/// bioworkflow Python 模块
///
/// 提供高性能矩阵操作功能：
/// - correlation_matrix: 相关系数矩阵
/// - distance_matrix: 距离矩阵
/// - hierarchical_cluster: 层次聚类
#[pymodule]
fn bioworkflow(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_correlation_matrix, m)?)?;
    m.add_function(wrap_pyfunction!(py_distance_matrix, m)?)?;
    m.add_function(wrap_pyfunction!(py_hierarchical_cluster, m)?)?;
    m.add_function(wrap_pyfunction!(py_benchmark_correlation, m)?)?;

    // 添加版本信息
    m.add("__version__", crate::VERSION)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use numpy::PyArray;
    use pyo3::types::IntoPyDict;

    #[test]
    fn test_python_bindings() {
        Python::with_gil(|py| {
            // 创建测试数据
            let data = vec![1.0f64, 2.0, 3.0, 4.0, 5.0, 6.0];
            let py_data = PyArray::from_vec_bound(py, data).reshape([2, 3]).unwrap();

            // 调用相关系数函数
            let locals = [("data", py_data)].into_py_dict_bound(py);
            let result = py
                .eval_bound(
                    pyo3::ffi::c_str!("bioworkflow.correlation_matrix(data, 'pearson')"),
                    Some(&locals),
                    None,
                )
                .unwrap();

            let result_array = result.downcast::<PyArray2<f64>>().unwrap();
            assert_eq!(result_array.shape(), &[2, 2]);
        });
    }
}
