//! BioWorkflow Core Library
//!
//! 提供共享的核心类型、错误处理和工具函数

#![warn(missing_docs)]
#![deny(unsafe_code)]

pub mod error;
pub mod types;
pub mod utils;

// 条件编译 Python 绑定
#[cfg(feature = "python")]
pub mod python;

// Re-exports
pub use error::{BioWorkflowError, Result};
pub use types::*;
