//! 核心数据类型定义

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fmt;
use std::path::PathBuf;
use std::time::{Duration, SystemTime};

/// 工作流 ID
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct WorkflowId(pub uuid::Uuid);

impl WorkflowId {
    /// 生成新的工作流 ID
    pub fn new() -> Self {
        Self(uuid::Uuid::new_v4())
    }
}

impl Default for WorkflowId {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for WorkflowId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// 任务 ID
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TaskId(pub uuid::Uuid);

impl TaskId {
    pub fn new() -> Self {
        Self(uuid::Uuid::new_v4())
    }
}

impl Default for TaskId {
    fn default() -> Self {
        Self::new()
    }
}

/// 执行 ID
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ExecutionId(pub uuid::Uuid);

impl ExecutionId {
    pub fn new() -> Self {
        Self(uuid::Uuid::new_v4())
    }
}

impl Default for ExecutionId {
    fn default() -> Self {
        Self::new()
    }
}

/// 工作流定义
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Workflow {
    /// 工作流 ID
    pub id: WorkflowId,
    /// 工作流名称
    pub name: String,
    /// 描述
    pub description: Option<String>,
    /// Snakemake 文件路径
    pub snakefile: PathBuf,
    /// 配置文件
    pub config: HashMap<String, serde_json::Value>,
    /// 环境变量
    pub env_vars: HashMap<String, String>,
    /// 创建时间
    pub created_at: SystemTime,
    /// 更新时间
    pub updated_at: SystemTime,
    /// 标签
    pub tags: Vec<String>,
}

/// 任务定义
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    /// 任务 ID
    pub id: TaskId,
    /// 所属工作流
    pub workflow_id: WorkflowId,
    /// 任务名称
    pub name: String,
    /// 命令
    pub command: String,
    /// 输入文件
    pub inputs: Vec<PathBuf>,
    /// 输出文件
    pub outputs: Vec<PathBuf>,
    /// 依赖的任务 ID
    pub dependencies: Vec<TaskId>,
    /// 资源需求
    pub resources: ResourceRequirements,
    /// 容器镜像 (可选)
    pub container: Option<String>,
    /// 环境名称
    pub environment: Option<String>,
}

/// 资源需求
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceRequirements {
    /// CPU 核心数
    pub cpu: Option<f64>,
    /// 内存 (MB)
    pub memory: Option<u64>,
    /// GPU 数量
    pub gpu: Option<u32>,
    /// 磁盘空间 (MB)
    pub disk: Option<u64>,
    /// 临时目录大小
    pub tmpdir: Option<u64>,
    /// 自定义资源
    pub custom: HashMap<String, serde_json::Value>,
}

impl Default for ResourceRequirements {
    fn default() -> Self {
        Self {
            cpu: Some(1.0),
            memory: Some(1024),
            gpu: None,
            disk: None,
            tmpdir: None,
            custom: HashMap::new(),
        }
    }
}

/// 执行状态
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExecutionStatus {
    /// 等待中
    #[serde(rename = "pending")]
    Pending,
    /// 运行中
    #[serde(rename = "running")]
    Running,
    /// 已完成
    #[serde(rename = "completed")]
    Completed,
    /// 失败
    #[serde(rename = "failed")]
    Failed,
    /// 已取消
    #[serde(rename = "cancelled")]
    Cancelled,
    /// 暂停
    #[serde(rename = "paused")]
    Paused,
}

impl fmt::Display for ExecutionStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ExecutionStatus::Pending => write!(f, "pending"),
            ExecutionStatus::Running => write!(f, "running"),
            ExecutionStatus::Completed => write!(f, "completed"),
            ExecutionStatus::Failed => write!(f, "failed"),
            ExecutionStatus::Cancelled => write!(f, "cancelled"),
            ExecutionStatus::Paused => write!(f, "paused"),
        }
    }
}

/// 执行记录
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Execution {
    /// 执行 ID
    pub id: ExecutionId,
    /// 工作流 ID
    pub workflow_id: WorkflowId,
    /// 状态
    pub status: ExecutionStatus,
    /// 开始时间
    pub started_at: Option<SystemTime>,
    /// 结束时间
    pub ended_at: Option<SystemTime>,
    /// 任务执行记录
    pub task_executions: Vec<TaskExecution>,
    /// 输出路径
    pub output_dir: PathBuf,
    /// 日志路径
    pub log_path: Option<PathBuf>,
    /// 错误信息
    pub error_message: Option<String>,
    /// 资源使用情况
    pub resource_usage: Option<ResourceUsage>,
}

/// 任务执行记录
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskExecution {
    /// 任务 ID
    pub task_id: TaskId,
    /// 状态
    pub status: ExecutionStatus,
    /// 开始时间
    pub started_at: Option<SystemTime>,
    /// 结束时间
    pub ended_at: Option<SystemTime>,
    /// 退出码
    pub exit_code: Option<i32>,
    /// 标准输出
    pub stdout: Option<String>,
    /// 标准错误
    pub stderr: Option<String>,
    /// 资源使用
    pub resource_usage: Option<ResourceUsage>,
}

/// 资源使用统计
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceUsage {
    /// CPU 时间 (秒)
    pub cpu_time: f64,
    /// 最大内存使用 (MB)
    pub max_memory: u64,
    /// 平均内存使用 (MB)
    pub avg_memory: u64,
    /// 磁盘读取 (MB)
    pub disk_read: u64,
    /// 磁盘写入 (MB)
    pub disk_write: u64,
    /// GPU 使用统计
    pub gpu_usage: Option<GpuUsage>,
}

/// GPU 使用统计
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GpuUsage {
    /// GPU 索引
    pub gpu_index: u32,
    /// GPU 名称
    pub gpu_name: String,
    /// GPU 利用率 (%)
    pub utilization: f32,
    /// 显存使用 (MB)
    pub memory_used: u64,
    /// 显存总量 (MB)
    pub memory_total: u64,
}

// Re-export uuid for convenience
pub use uuid;
