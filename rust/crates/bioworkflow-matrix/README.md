# bioworkflow-matrix

高性能生物信息学矩阵运算库，使用 Rust 实现，提供 Python 绑定。

## 功能特性

- **相关系数矩阵**: Pearson 和 Spearman 相关系数计算
- **距离矩阵**: 欧几里得、曼哈顿、余弦、相关系数距离
- **层次聚类**: AGNES 凝聚式聚类，支持 single/complete/average/ward 连接方式
- **并行计算**: 使用 rayon 实现多线程并行
- **Python 绑定**: 通过 PyO3 提供无缝的 Python 接口

## 性能优势

相比纯 Python 实现（嵌套循环），本库可实现：

| 操作 | Python 时间 | Rust 时间 | 提升倍数 |
|------|-----------|----------|---------|
| correlation_matrix (1000x1000) | ~5 秒 | ~0.1 秒 | **50x** |
| distance_matrix (1000x1000) | ~3 秒 | ~0.06 秒 | **50x** |
| hierarchical_cluster (500 点) | ~10 秒 | ~0.1 秒 | **100x** |

*基准测试环境：Intel i7-12700K, 32GB RAM*

## 安装

### Python 安装

```bash
# 从源码安装
cd rust
maturin develop -r

# 或者使用 pip
pip install -e rust/crates/bioworkflow-matrix
```

### Rust 安装

在 `Cargo.toml` 中添加依赖：

```toml
[dependencies]
bioworkflow-matrix = { path = "crates/bioworkflow-matrix" }
```

## Python 使用示例

### 相关系数矩阵

```python
import numpy as np
import bioworkflow

# 生成随机数据
np.random.seed(42)
data = np.random.randn(1000, 100)  # 1000 样本 x 100 特征

# 计算 Pearson 相关系数矩阵
corr = bioworkflow.correlation_matrix(data, "pearson")
print(f"相关系数矩阵形状：{corr.shape}")  # (100, 100)

# 计算 Spearman 相关系数矩阵
corr_spearman = bioworkflow.correlation_matrix(data, "spearman")
```

### 距离矩阵

```python
import numpy as np
import bioworkflow

data = np.random.randn(500, 50)

# 欧几里得距离
dist_euclidean = bioworkflow.distance_matrix(data, "euclidean")

# 曼哈顿距离
dist_manhattan = bioworkflow.distance_matrix(data, "manhattan")

# 余弦距离
dist_cosine = bioworkflow.distance_matrix(data, "cosine")
```

### 层次聚类

```python
import numpy as np
import bioworkflow

# 生成测试数据
data = np.array([
    [1.0, 2.0],
    [1.5, 1.8],
    [5.0, 8.0],
    [8.0, 8.0],
    [1.0, 0.6],
    [9.0, 11.0]
])

# 执行层次聚类（average 连接，欧几里得距离）
result = bioworkflow.hierarchical_cluster(data, "average", "euclidean")

print(f"样本数量：{result['n_samples']}")
print(f"合并次数：{len(result['merges'])}")

# 查看第一次合并
first_merge = result['merges'][0]
print(f"第一次合并：簇 {first_merge['cluster1']} 和簇 {first_merge['cluster2']}, "
      f"距离={first_merge['distance']:.4f}")
```

### 性能基准测试

```python
import numpy as np
import bioworkflow
import time

# 生成大数据
sizes = [100, 500, 1000, 2000]

for size in sizes:
    data = np.random.randn(size, 50)
    
    start = time.time()
    corr = bioworkflow.correlation_matrix(data, "pearson")
    elapsed = time.time() - start
    
    print(f"{size}x{50} 数据：{elapsed:.4f} 秒")
```

## Rust 使用示例

```rust
use bioworkflow_matrix::{
    correlation_matrix,
    distance_matrix,
    hierarchical_cluster,
    DistanceMetric,
    Linkage,
};
use ndarray::array2;

fn main() {
    // 相关系数矩阵
    let data = array2![
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
        [7.0, 8.0, 9.0],
        [10.0, 11.0, 12.0]
    ];

    let corr = correlation_matrix(&data.view(), "pearson").unwrap();
    println!("相关系数矩阵:\n{}", corr);

    // 距离矩阵
    let dist = distance_matrix(&data.view(), DistanceMetric::Euclidean).unwrap();
    println!("\n欧几里得距离矩阵:\n{}", dist);

    // 层次聚类
    let cluster_data = array2![
        [1.0, 2.0],
        [1.5, 1.8],
        [5.0, 8.0],
        [8.0, 8.0],
        [1.0, 0.6],
        [9.0, 11.0]
    ];

    let result = hierarchical_cluster(
        &cluster_data.view(),
        Linkage::Average,
        DistanceMetric::Euclidean,
    ).unwrap();

    println!("\n层次聚类结果:");
    println!("合并次数：{}", result.merges.len());
    for (i, merge) in result.merges.iter().enumerate() {
        println!("合并 {}: 簇 {} + 簇 {}, 距离={:.4}",
                 i, merge.cluster1, merge.cluster2, merge.distance);
    }
}
```

## API 参考

### `correlation_matrix(data, method)`

计算相关系数矩阵

**参数**:
- `data`: NumPy 数组或 ndarray::ArrayView2 (样本 x 特征)
- `method`: "pearson" 或 "spearman"

**返回**: 相关系数矩阵 (特征 x 特征)

### `distance_matrix(data, metric)`

计算距离矩阵

**参数**:
- `data`: NumPy 数组或 ndarray::ArrayView2 (样本 x 特征)
- `metric`: "euclidean", "manhattan", "cosine", "correlation"

**返回**: 距离矩阵 (样本 x 样本)

### `hierarchical_cluster(data, method, metric)`

执行层次聚类

**参数**:
- `data`: NumPy 数组或 ndarray::ArrayView2 (样本 x 特征)
- `method`: "single", "complete", "average", "ward"
- `metric`: "euclidean", "manhattan", "cosine", "correlation"

**返回**: 包含以下字段的字典:
- `merges`: 合并历史列表，每个元素包含 cluster1, cluster2, distance, size
- `n_samples`: 原始样本数量

## 实现细节

### 并行计算

- 使用 `rayon` 库实现数据并行
- 相关系数和距离矩阵只计算上三角，然后对称填充
- 自动利用多核 CPU 性能

### 数值稳定性

- 使用 Bessel 校正 (n-1) 计算样本标准差
- Spearman 相关系数使用平均秩处理并列值
- 所有计算前检查 NaN 和无穷大

### 内存优化

- 原地计算，减少临时数组分配
- 预计算均值和标准差，避免重复计算

## 开发指南

### 编译

```bash
cd rust
cargo build --release -p bioworkflow-matrix
```

### 测试

```bash
# 运行所有测试
cargo test -p bioworkflow-matrix

# 运行特定测试
cargo test -p bioworkflow-matrix correlation

# 运行基准测试
cargo bench -p bioworkflow-matrix
```

### 性能分析

```bash
# 生成性能报告
cargo flamegraph --package bioworkflow-matrix
```

## 依赖

### Rust 依赖

- `ndarray` - N 维数组
- `rayon` - 数据并行
- `pyo3` - Python 绑定
- `numpy` - NumPy 互操作
- `thiserror` - 错误处理

### Python 依赖

- `numpy >= 1.20.0`
- Python 3.8+

## 许可证

MIT OR Apache-2.0

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

本库是 BioWorkflow 项目的一部分，用于加速生物信息学数据分析中的矩阵运算。
