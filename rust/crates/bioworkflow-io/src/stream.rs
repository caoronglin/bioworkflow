use futures::Stream;
use std::pin::Pin;
use std::task::{Context, Poll};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::fs::File;

pub struct AsyncLineStream {
    reader: BufReader<File>,
}

impl AsyncLineStream {
    pub fn new(file: File) -> Self {
        Self {
            reader: BufReader::new(file),
        }
    }
}

impl Stream for AsyncLineStream {
    type Item = std::io::Result<String>;

    fn poll_next(mut self: Pin<&mut Self>, _cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        let mut line = String::new();
        match futures::executor::block_on(self.reader.read_line(&mut line)) {
            Ok(0) => Poll::Ready(None),
            Ok(_) => Poll::Ready(Some(Ok(line))),
            Err(e) => Poll::Ready(Some(Err(e))),
        }
    }
}