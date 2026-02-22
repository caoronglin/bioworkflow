//! Scheduling strategies.

use std::sync::Arc;

use crate::resource::ResourceManager;
use crate::queue::TaskQueue;
use bioworkflow_core::types::{Task, TaskId};
use bioworkflow_core::Result;

/// Scheduling strategy trait
pub trait SchedulingStrategy: Send + Sync {
    /// Select the next task to execute from the queue
    fn select_task(&self, queue: &TaskQueue, resources: &ResourceManager) -> Option<Arc<Task>>;

    /// Calculate priority score for a task
    fn calculate_priority(&self, task: &Task, resources: &ResourceManager) -> f64;

    /// Decide if a task should be scheduled now
    fn should_schedule(&self, task: &Task, resources: &ResourceManager) -> bool;

    /// Name of the strategy
    fn name(&self) -> &'static str;
}

/// First-Come-First-Serve strategy
#[derive(Debug, Clone)]
pub struct FifoStrategy;

impl SchedulingStrategy for FifoStrategy {
    fn select_task(&self, queue: &TaskQueue, resources: &ResourceManager) -> Option<Arc<Task>> {
        queue.peek(&crate::SchedulerStrategy::Fifo)
    }

    fn calculate_priority(&self, _task: &Task, _resources: &ResourceManager) -> f64 {
        0.0
    }

    fn should_schedule(&self, _task: &Task, resources: &ResourceManager) -> bool {
        true
    }

    fn name(&self) -> &'static str {
        "FIFO"
    }
}

/// Shortest Job First strategy
#[derive(Debug, Clone)]
pub struct SjfStrategy;

impl SchedulingStrategy for SjfStrategy {
    fn select_task(&self, queue: &TaskQueue, resources: &ResourceManager) -> Option<Arc<Task>> {
        queue.peek(&crate::SchedulerStrategy::Sjf)
    }

    fn calculate_priority(&self, task: &Task, resources: &ResourceManager) -> f64 {
        let cpu = task.resources.cpu.unwrap_or(0.0);
        let memory = task.resources.memory.unwrap_or(0) as f64;

        // Lower score = higher priority for shorter tasks
        cpu + (memory / 1024.0)
    }

    fn should_schedule(&self, task: &Task, resources: &ResourceManager) -> bool {
        resources.can_satisfy(&task.resources)
    }

    fn name(&self) -> &'static str {
        "SJF"
    }
}

/// Resource-aware scheduling strategy
#[derive(Debug, Clone)]
pub struct ResourceAwareStrategy;

impl SchedulingStrategy for ResourceAwareStrategy {
    fn select_task(&self, queue: &TaskQueue, resources: &ResourceManager) -> Option<Arc<Task>> {
        queue.peek(&crate::SchedulerStrategy::ResourceAware)
    }

    fn calculate_priority(&self, task: &Task, resources: &ResourceManager) -> f64 {
        let cpu_util = if resources.total_cpu > 0.0 {
            task.resources.cpu.unwrap_or(0.0) / resources.total_cpu
        } else {
            0.0
        };

        let memory_util = if resources.total_memory > 0 {
            task.resources.memory.unwrap_or(0) as f64 / resources.total_memory as f64
        } else {
            0.0
        };

        let gpu_util = if resources.total_gpu > 0 {
            task.resources.gpu.unwrap_or(0) as f64 / resources.total_gpu as f64
        } else {
            0.0
        };

        // Higher priority for tasks that use fewer resources relative to total
        1.0 - (cpu_util + memory_util + gpu_util) / 3.0
    }

    fn should_schedule(&self, task: &Task, resources: &ResourceManager) -> bool {
        let available = resources.available();

        // Schedule only if resources are under 80% utilization
        resources.utilization() < 80.0 && resources.can_satisfy(&task.resources)
    }

    fn name(&self) -> &'static str {
        "Resource-Aware"
    }
}

/// Priority-based strategy
#[derive(Debug, Clone)]
pub struct PriorityStrategy;

impl SchedulingStrategy for PriorityStrategy {
    fn select_task(&self, queue: &TaskQueue, resources: &ResourceManager) -> Option<Arc<Task>> {
        queue.peek(&crate::SchedulerStrategy::Priority)
    }

    fn calculate_priority(&self, task: &Task, resources: &ResourceManager) -> f64 {
        let mut priority = 0.0;

        // Priority for containerized tasks
        if task.container.is_some() {
            priority += 5.0;
        }

        // Priority for tasks with environments
        if task.environment.is_some() {
            priority += 3.0;
        }

        // Priority for tasks with dependencies (critical path)
        priority += task.dependencies.len() as f64 * 2.0;

        // Priority for resource efficiency
        let cpu_score = if let Some(cpu) = task.resources.cpu {
            cpu.min(4.0) / 4.0
        } else {
            1.0
        };

        let memory_score = if let Some(memory) = task.resources.memory {
            (memory as f64 / 1024.0).min(4.0) / 4.0
        } else {
            1.0
        };

        priority += (cpu_score + memory_score) / 2.0;

        priority
    }

    fn should_schedule(&self, task: &Task, resources: &ResourceManager) -> bool {
        resources.can_satisfy(&task.resources)
    }

    fn name(&self) -> &'static str {
        "Priority"
    }
}

/// Least Load strategy
#[derive(Debug, Clone)]
pub struct LeastLoadStrategy;

impl SchedulingStrategy for LeastLoadStrategy {
    fn select_task(&self, queue: &TaskQueue, resources: &ResourceManager) -> Option<Arc<Task>> {
        queue.peek(&crate::SchedulerStrategy::LeastLoad)
    }

    fn calculate_priority(&self, task: &Task, resources: &ResourceManager) -> f64 {
        let cpu = task.resources.cpu.unwrap_or(0.0);
        let memory = task.resources.memory.unwrap_or(0) as f64;

        let available_cpu = resources.total_cpu - resources.used_cpu;
        let available_memory = (resources.total_memory - resources.used_memory) as f64;

        // Score based on how much resources will remain after task
        let cpu_score = if available_cpu > 0.0 {
            (available_cpu - cpu).max(0.0) / available_cpu
        } else {
            0.0
        };

        let memory_score = if available_memory > 0.0 {
            (available_memory - memory).max(0.0) / available_memory
        } else {
            0.0
        };

        (cpu_score + memory_score) / 2.0
    }

    fn should_schedule(&self, task: &Task, resources: &ResourceManager) -> bool {
        let cpu = task.resources.cpu.unwrap_or(0.0);
        let memory = task.resources.memory.unwrap_or(0) as f64;

        let available_cpu = resources.total_cpu - resources.used_cpu;
        let available_memory = (resources.total_memory - resources.used_memory) as f64;

        cpu <= available_cpu && memory <= available_memory
    }

    fn name(&self) -> &'static str {
        "Least Load"
    }
}

/// Factory for creating scheduling strategies
pub struct StrategyFactory;

impl StrategyFactory {
    /// Create strategy from type
    pub fn create(strategy: &crate::SchedulerStrategy) -> Box<dyn SchedulingStrategy> {
        match strategy {
            crate::SchedulerStrategy::Fifo => Box::new(FifoStrategy),
            crate::SchedulerStrategy::Sjf => Box::new(SjfStrategy),
            crate::SchedulerStrategy::LeastLoad => Box::new(LeastLoadStrategy),
            crate::SchedulerStrategy::Priority => Box::new(PriorityStrategy),
            crate::SchedulerStrategy::ResourceAware => Box::new(ResourceAwareStrategy),
        }
    }

    /// Create strategy by name
    pub fn create_by_name(name: &str) -> Option<Box<dyn SchedulingStrategy>> {
        match name.to_lowercase().as_str() {
            "fifo" => Some(Box::new(FifoStrategy)),
            "sjf" | "shortest" => Some(Box::new(SjfStrategy)),
            "priority" => Some(Box::new(PriorityStrategy)),
            "load" | "leastload" => Some(Box::new(LeastLoadStrategy)),
            "resource" | "resourceaware" => Some(Box::new(ResourceAwareStrategy)),
            _ => None,
        }
    }

    /// Get all available strategies
    pub fn all_strategies() -> Vec<Box<dyn SchedulingStrategy>> {
        vec![
            Box::new(FifoStrategy),
            Box::new(SjfStrategy),
            Box::new(PriorityStrategy),
            Box::new(LeastLoadStrategy),
            Box::new(ResourceAwareStrategy),
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use bioworkflow_core::types::{ResourceRequirements, Task, TaskId, WorkflowId};

    #[test]
    fn test_strategy_factory() {
        for strategy_type in &[
            crate::SchedulerStrategy::Fifo,
            crate::SchedulerStrategy::Sjf,
            crate::SchedulerStrategy::Priority,
            crate::SchedulerStrategy::LeastLoad,
            crate::SchedulerStrategy::ResourceAware,
        ] {
            let strategy = StrategyFactory::create(strategy_type);
            assert!(!strategy.name().is_empty());
        }

        let strategy = StrategyFactory::create_by_name("SJF").unwrap();
        assert_eq!(strategy.name(), "SJF");
    }

    #[test]
    fn test_priority_calculation() {
        let task1 = Task {
            id: 1.into(),
            workflow_id: 1.into(),
            name: "task1".to_string(),
            command: "simple".to_string(),
            inputs: vec![],
            outputs: vec!["out1.txt".into()],
            dependencies: vec![],
            resources: ResourceRequirements::default(),
            container: None,
            environment: None,
        };

        let task2 = Task {
            id: 2.into(),
            workflow_id: 1.into(),
            name: "task2".to_string(),
            command: "containerized".to_string(),
            inputs: vec!["in1.txt".into()],
            outputs: vec!["out2.txt".into()],
            dependencies: vec![1.into()],
            resources: ResourceRequirements::default(),
            container: Some("python:3.11".to_string()),
            environment: Some("test_env".to_string()),
        };

        let strategy = PriorityStrategy;
        let manager = crate::ResourceManager::new();

        let score1 = strategy.calculate_priority(&task1, &manager);
        let score2 = strategy.calculate_priority(&task2, &manager);

        assert!(score2 > score1);
    }
}
