//! 错误处理模块

use std::fmt;
use thiserror::Error;

/// BioWorkflow 统一的错误类型
#[derive(Error, Debug)]
pub enum BioWorkflowError {
    /// IO 错误
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    /// 序列化/反序列化错误
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    /// DAG 相关错误
    #[error("DAG error: {0}")]
    Dag(String),

    /// 工作流执行错误
    #[error("Workflow execution error: {0}")]
    WorkflowExecution(String),

    /// 任务调度错误
    #[error("Task scheduling error: {0}")]
    TaskScheduling(String),

    /// 资源不足
    #[error("Insufficient resources: {0}")]
    InsufficientResources(String),

    /// 配置错误
    #[error("Configuration error: {0}")]
    Configuration(String),

    /// 未找到
    #[error("Not found: {0}")]
    NotFound(String),

    /// 无效操作
    #[error("Invalid operation: {0}")]
    InvalidOperation(String),

    /// 外部服务错误
    #[error("External service error: {source}")]
    ExternalService {
        /// 服务名称
        service: String,
        /// 错误源
        source: Box<dyn std::error::Error + Send + Sync>,
    },

    /// 其他错误
    #[error("{0}")]
    Other(String),
}

/// 方便的结果类型别名
pub type Result<T> = std::result::Result<T, BioWorkflowError>;

/// 用于 Python 绑定的错误转换
#[cfg(feature = "python")]
impl From<BioWorkflowError> for pyo3::PyErr {
    fn from(err: BioWorkflowError) -> pyo3::PyErr {
        pyo3::exceptions::PyRuntimeError::new_err(err.to_string())
    }
}

/// 错误扩展 trait
pub trait ResultExt<T> {
    /// 添加上下文信息
    fn context(self, msg: &str) -> Result<T>;

    /// 使用闭包添加上下文
    fn with_context<F>(self, f: F) -> Result<T>
    where
        F: FnOnce() -> String;
}

impl<T> ResultExt<T> for Result<T> {
    fn context(self, msg: &str) -> Result<T> {
        self.map_err(|e| BioWorkflowError::Other(format!("{}: {}", msg, e)))
    }

    fn with_context<F>(self, f: F) -> Result<T>
    where
        F: FnOnce() -> String,
    {
        self.map_err(|e| BioWorkflowError::Other(format!("{}: {}", f(), e)))
    }
}
