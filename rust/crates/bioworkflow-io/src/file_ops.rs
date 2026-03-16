use std::path::Path;
use tokio::fs;

pub async fn exists<P: AsRef<Path>>(path: P) -> bool {
    fs::try_exists(path).await.unwrap_or(false)
}

pub async fn create_dir_all<P: AsRef<Path>>(path: P) -> std::io::Result<()> {
    fs::create_dir_all(path).await
}

pub async fn remove_file<P: AsRef<Path>>(path: P) -> std::io::Result<()> {
    fs::remove_file(path).await
}

pub async fn remove_dir_all<P: AsRef<Path>>(path: P) -> std::io::Result<()> {
    fs::remove_dir_all(path).await
}

pub async fn copy<P: AsRef<Path>, Q: AsRef<Path>>(from: P, to: Q) -> std::io::Result<u64> {
    fs::copy(from, to).await
}