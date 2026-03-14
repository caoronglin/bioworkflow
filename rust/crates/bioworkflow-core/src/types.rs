//! 核心类型定义
//!
//! 定义BioWorkflow中使用的所有核心数据结构

use std::collections::HashMap;
use std::path::PathBuf;

use serde::{Deserialize, Serialize};

/// 工作流标识符
pub type WorkflowId = String;

/// 任务标识符
pub type TaskId = String;

/// 节点标识符
pub type NodeId = String;

/// 工作流定义
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Workflow {
    /// 工作流ID
    pub id: WorkflowId,
    /// 工作流名称
    pub name: String,
    /// 工作流描述
    pub description: String,
    /// 工作流版本
    pub version: String,
    /// 节点列表
    pub nodes: Vec<Node>,
    /// 边列表
    pub edges: Vec<Edge>,
    /// 配置参数
    pub config: WorkflowConfig,
    /// 元数据
    #[serde(default)]
    pub metadata: HashMap<String, String>,
}

impl Workflow {
    /// 创建新的工作流
    pub fn new(id: impl Into<String>, name: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            name: name.into(),
            description: String::new(),
            version: "1.0.0".to_string(),
            nodes: Vec::new(),
            edges: Vec::new(),
            config: WorkflowConfig::default(),
            metadata: HashMap::new(),
        }
    }

    /// 添加节点
    pub fn add_node(&mut self, node: Node) -> &mut Self {
        self.nodes.push(node);
        self
    }

    /// 添加边
    pub fn add_edge(&mut self, edge: Edge) -> &mut Self {
        self.edges.push(edge);
        self
    }

    /// 查找节点
    pub fn find_node(&self, id: &str) -> Option<&Node> {
        self.nodes.iter().find(|n| n.id == id)
    }
}

/// 节点定义
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Node {
    /// 节点ID
    pub id: NodeId,
    /// 节点类型
    pub node_type: NodeType,
    /// 节点标签
    pub label: String,
    /// 节点位置（用于可视化）
    pub position: Option<Position>,
    /// 节点数据
    #[serde(default)]
    pub data: HashMap<String, serde_json::Value>,
}

impl Node {
    /// 创建新节点
    pub fn new(id: impl Into<String>, node_type: NodeType, label: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            node_type,
            label: label.into(),
            position: None,
            data: HashMap::new(),
        }
    }
}

/// 节点类型
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(rename_all = "snake_case")]
pub enum NodeType {
    /// 输入节点
    Input,
    /// 输出节点
    Output,
    /// 处理节点
    Process,
    /// 决策节点
    Decision,
    /// 并行节点
    Parallel,
    /// 合并节点
    Merge,
    /// 自定义节点
    Custom(String),
}

/// 边定义
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Edge {
    /// 边ID
    pub id: String,
    /// 源节点ID
    pub source: NodeId,
    /// 目标节点ID
    pub target: NodeId,
    /// 边标签
    #[serde(default)]
    pub label: String,
    /// 条件（用于决策边）
    #[serde(default)]
    pub condition: Option<String>,
}

impl Edge {
    /// 创建新边
    pub fn new(
        id: impl Into<String>,
        source: impl Into<String>,
        target: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            source: source.into(),
            target: target.into(),
            label: String::new(),
            condition: None,
        }
    }
}

/// 位置（用于可视化）
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq)]
pub struct Position {
    pub x: f64,
    pub y: f64,
}

impl Position {
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }
}

/// 工作流配置
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct WorkflowConfig {
    /// 工作目录
    pub workdir: PathBuf,
    /// 最大并行度
    pub max_parallel: usize,
    /// 重试次数
    pub retries: u32,
    /// 超时时间（秒）
    pub timeout: u64,
    /// 资源限制
    pub resources: ResourceLimits,
    /// 调度策略
    pub scheduling: SchedulingPolicy,
}

impl Default for WorkflowConfig {
    fn default() -> Self {
        Self {
            workdir: PathBuf::from("./workflow"),
            max_parallel: 4,
            retries: 3,
            timeout: 3600,
            resources: ResourceLimits::default(),
            scheduling: SchedulingPolicy::default(),
        }
    }
}

/// 资源限制
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ResourceLimits {
    /// CPU核心数
    pub cpu_cores: usize,
    /// 内存限制（MB）
    pub memory_mb: usize,
    /// 磁盘空间（MB）
    pub disk_mb: usize,
    /// GPU数量
    pub gpu_count: usize,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        Self {
            cpu_cores: 4,
            memory_mb: 8192,
            disk_mb: 102400,
            gpu_count: 0,
        }
    }
}

/// 调度策略
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(rename_all = "snake_case")]
pub enum SchedulingPolicy {
    /// 先进先出
    Fifo,
    /// 优先级调度
    Priority,
    /// 最短作业优先
    ShortestJobFirst,
    /// 公平共享
    FairShare,
    /// 最早截止时间优先
    EarliestDeadlineFirst,
}

impl Default for SchedulingPolicy {
    fn default() -> Self {
        Self::Fifo
    }
}

/// 任务定义
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Task {
    /// 任务ID
    pub id: TaskId,
    /// 任务名称
    pub name: String,
    /// 任务描述
    pub description: String,
    /// 输入文件
    pub inputs: Vec<PathBuf>,
    /// 输出文件
    pub outputs: Vec<PathBuf>,
    /// 执行命令
    pub command: String,
    /// 资源需求
    pub resources: ResourceRequirements,
    /// 依赖任务
    pub dependencies: Vec<TaskId>,
    /// 优先级
    pub priority: i32,
    /// 重试次数
    pub retries: u32,
}

/// 资源需求
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ResourceRequirements {
    /// CPU核心数
    pub cpu_cores: usize,
    /// 内存需求（MB）
    pub memory_mb: usize,
    /// 磁盘需求（MB）
    pub disk_mb: usize,
    /// 运行时间估计（秒）
    pub estimated_runtime: u64,
}

impl Default for ResourceRequirements {
    fn default() -> Self {
        Self {
            cpu_cores: 1,
            memory_mb: 512,
            disk_mb: 1024,
            estimated_runtime: 300,
        }
    }
}

/// 任务状态
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(rename_all = "snake_case")]
pub enum TaskState {
    /// 等待中
    Pending,
    /// 已调度
    Scheduled,
    /// 运行中
    Running,
    /// 已完成
    Completed,
    /// 失败
    Failed,
    /// 已取消
    Cancelled,
    /// 已跳过
    Skipped,
}

/// 任务执行结果
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TaskExecutionResult {
    /// 任务ID
    pub task_id: TaskId,
    /// 最终状态
    pub state: TaskState,
    /// 开始时间
    pub started_at: Option<datetime>,
    /// 结束时间
    pub completed_at: Option<datetime>,
    /// 退出码
    pub exit_code: Option<i32>,
    /// 标准输出
    pub stdout: String,
    /// 标准错误
    pub stderr: String,
    /// 错误信息
    pub error_message: Option<String>,
    /// 资源使用统计
    pub resource_usage: ResourceUsage,
}

/// 资源使用统计
#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct ResourceUsage {
    /// CPU使用时间（秒）
    pub cpu_time_seconds: f64,
    /// 峰值内存使用（MB）
    pub peak_memory_mb: usize,
    /// 磁盘读取（MB）
    pub disk_read_mb: usize,
    /// 磁盘写入（MB）
    pub disk_write_mb: usize,
}

// Re-exports for convenience
pub use crate::error::{BioWorkflowError, Result};