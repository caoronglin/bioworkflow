use std::path::Path;
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncWriteExt, BufReader, BufWriter};

pub async fn read_file<P: AsRef<Path>>(path: P) -> std::io::Result<Vec<u8>> {
    let mut file = File::open(path).await?;
    let mut buffer = Vec::new();
    file.read_to_end(&mut buffer).await?;
    Ok(buffer)
}

pub async fn write_file<P: AsRef<Path>>(path: P, data: &[u8]) -> std::io::Result<()> {
    let mut file = File::create(path).await?;
    file.write_all(data).await?;
    Ok(())
}

pub async fn read_file_string<P: AsRef<Path>>(path: P) -> std::io::Result<String> {
    let mut file = File::open(path).await?;
    let mut content = String::new();
    file.read_to_string(&mut content).await?;
    Ok(content)
}