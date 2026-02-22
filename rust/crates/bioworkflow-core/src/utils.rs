//! 工具函数模块

use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

/// 生成带时间戳的唯一文件名
pub fn timestamped_filename(prefix: &str, suffix: &str) -> String {
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or(Duration::from_secs(0))
        .as_millis();
    format!("{}_{}{}", prefix, timestamp, suffix)
}

/// 规范化路径，处理相对路径和绝对路径
pub fn normalize_path<P: AsRef<Path>>(path: P, base_dir: Option<&Path>) -> PathBuf {
    let path = path.as_ref();

    if path.is_absolute() {
        path.to_path_buf()
    } else if let Some(base) = base_dir {
        base.join(path)
    } else {
        std::env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("."))
            .join(path)
    }
}

/// 计算文件的相对路径
pub fn relative_path<P: AsRef<Path>, B: AsRef<Path>>(
    path: P,
    base: B,
) -> Option<PathBuf> {
    let path = path.as_ref();
    let base = base.as_ref();

    path.strip_prefix(base).ok().map(|p| p.to_path_buf())
}

/// 格式化持续时间
pub fn format_duration(duration: Duration) -> String {
    let total_secs = duration.as_secs();
    let hours = total_secs / 3600;
    let minutes = (total_secs % 3600) / 60;
    let seconds = total_secs % 60;
    let millis = duration.subsec_millis();

    if hours > 0 {
        format!("{}h {:02}m {:02}s", hours, minutes, seconds)
    } else if minutes > 0 {
        format!("{}m {:02}s", minutes, seconds)
    } else {
        format!("{}.{:03}s", seconds, millis)
    }
}

/// 格式化文件大小
pub fn format_file_size(size: u64) -> String {
    const UNITS: &[&str] = &["B", "KB", "MB", "GB", "TB", "PB"];

    if size == 0 {
        return "0 B".to_string();
    }

    let exp = (size as f64).log(1024.0).min(UNITS.len() as f64 - 1.0) as usize;
    let size = size as f64 / 1024f64.powi(exp as i32);

    if exp == 0 {
        format!("{} {}", size as u64, UNITS[exp])
    } else {
        format!("{:.2} {}", size, UNITS[exp])
    }
}

/// 创建父目录如果不存在
pub fn ensure_parent_dir<P: AsRef<Path>>(path: P) -> std::io::Result<()> {
    if let Some(parent) = path.as_ref().parent() {
        std::fs::create_dir_all(parent)?;
    }
    Ok(())
}

/// 原子写入文件
pub fn atomic_write<P: AsRef<Path>, C: AsRef<[u8]>>(
    path: P,
    contents: C,
) -> std::io::Result<()> {
    let path = path.as_ref();
    let temp_path = path.with_extension("tmp");

    // 写入临时文件
    std::fs::write(&temp_path, contents)?;

    // 原子重命名
    std::fs::rename(&temp_path, path)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;

    #[test]
    fn test_format_duration() {
        assert_eq!(format_duration(Duration::from_secs(30)), "30.000s");
        assert_eq!(format_duration(Duration::from_secs(90)), "1m 30s");
        assert_eq!(format_duration(Duration::from_secs(3661)), "1h 01m 01s");
    }

    #[test]
    fn test_format_file_size() {
        assert_eq!(format_file_size(0), "0 B");
        assert_eq!(format_file_size(1024), "1.00 KB");
        assert_eq!(format_file_size(1024 * 1024), "1.00 MB");
        assert_eq!(format_file_size(1536), "1.50 KB");
    }

    #[test]
    fn test_normalize_path() {
        // 绝对路径
        assert_eq!(
            normalize_path("/absolute/path", None),
            PathBuf::from("/absolute/path")
        );

        // 相对路径带基准
        assert_eq!(
            normalize_path("relative/path", Some(Path::new("/base"))),
            PathBuf::from("/base/relative/path")
        );
    }
}
