//! 矩阵运算性能基准测试
//!
//! 比较 Rust 实现与 Python 实现的性能差异

use bioworkflow_matrix::{correlation_matrix, distance_matrix, DistanceMetric};
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use ndarray::{array2, Array2};
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};

/// 生成随机测试数据
fn generate_random_data(rows: usize, cols: usize) -> Array2<f64> {
    let mut rng = StdRng::seed_from_u64(42);
    let data: Vec<f64> = (0..rows * cols)
        .map(|_| rng.gen_range(-10.0..10.0))
        .collect();
    Array2::from_shape_vec((rows, cols), data).unwrap()
}

/// correlation_matrix 基准测试
fn bench_correlation_matrix(c: &mut Criterion) {
    let mut group = c.benchmark_group("correlation_matrix");

    for size in [100, 500, 1000].iter() {
        let data = generate_random_data(*size, 50);

        group.bench_with_input(BenchmarkId::new("pearson", size), &data, |b, data| {
            b.iter(|| correlation_matrix(&black_box(data.view()), "pearson"))
        });
    }

    group.finish();
}

/// distance_matrix 基准测试
fn bench_distance_matrix(c: &mut Criterion) {
    let mut group = c.benchmark_group("distance_matrix");

    for size in [100, 500, 1000].iter() {
        let data = generate_random_data(*size, 50);

        group.bench_with_input(BenchmarkId::new("euclidean", size), &data, |b, data| {
            b.iter(|| distance_matrix(&black_box(data.view()), DistanceMetric::Euclidean))
        });
    }

    group.finish();
}

/// 小规模数据测试
fn bench_small_data(c: &mut Criterion) {
    let mut group = c.benchmark_group("small_dataset");

    let data = array2![
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
        [7.0, 8.0, 9.0],
        [10.0, 11.0, 12.0]
    ];

    group.bench_function("correlation_4x3", |b| {
        b.iter(|| correlation_matrix(&black_box(data.view()), "pearson"))
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_correlation_matrix,
    bench_distance_matrix,
    bench_small_data,
);
criterion_main!(benches);
