//! Execute tasks in the DAG.

use std::collections::{HashMap, VecDeque};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use async_trait::async_trait;
use crossbeam::channel;
use dashmap::DashMap;
use parking_lot::RwLock;
use rayon::prelude::*;
use tracing::info;

use bioworkflow_core::types::{
    ExecutionId, ExecutionStatus, Task, TaskId, WorkflowId,
};
use bioworkflow_core::Result;
use super::builder::WorkflowDag;

/// Execution strategy for tasks
pub enum ExecutionStrategy {
    /// Execute tasks in topological order with concurrency control
    Topological { concurrency: usize },
    /// Execute ready tasks with greedy scheduling
    Greedy { concurrency: usize },
    /// Execute all tasks in parallel (dependencies permitting)
    Parallel { concurrency: usize },
}

impl Default for ExecutionStrategy {
    fn default() -> Self {
        Self::Parallel { concurrency: usize::MAX }
    }
}

/// Task executor trait
#[async_trait]
pub trait TaskExecutor: Send + Sync + 'static {
    /// Execute a single task
    async fn execute_task(&self, task: &Task) -> Result<ExecutionStatus>;
}

/// Simple task executor that runs commands locally
#[derive(Debug, Default)]
pub struct LocalExecutor;

#[async_trait]
impl TaskExecutor for LocalExecutor {
    async fn execute_task(&self, task: &Task) -> Result<ExecutionStatus> {
        info!("executing_task", name = task.name.as_str());

        // In real implementation, this would execute the command
        // For now, we simulate execution

        tokio::time::sleep(Duration::from_millis(100)).await;

        Ok(ExecutionStatus::Completed)
    }
}

/// DAG execution context
#[derive(Debug, Clone)]
pub struct ExecutionContext {
    pub execution_id: ExecutionId,
    pub workflow_id: WorkflowId,
    pub strategy: ExecutionStrategy,
    pub executor: Arc<dyn TaskExecutor>,
}

impl Default for ExecutionContext {
    fn default() -> Self {
        Self {
            execution_id: ExecutionId::new(),
            workflow_id: WorkflowId::new(),
            strategy: ExecutionStrategy::default(),
            executor: Arc::new(LocalExecutor),
        }
    }
}

/// Execution statistics
#[derive(Debug, Clone, Default)]
pub struct ExecutionStats {
    pub total_tasks: usize,
    pub completed_tasks: usize,
    pub failed_tasks: usize,
    pub execution_time: Duration,
    pub task_timings: HashMap<TaskId, Duration>,
}

impl ExecutionStats {
    /// Calculate average execution time per task
    pub fn average_task_time(&self) -> Duration {
        if self.completed_tasks == 0 {
            Duration::from_secs(0)
        } else {
            let total = self.task_timings.values().sum::<Duration>();
            total / self.completed_tasks as u32
        }
    }

    /// Calculate task completion rate
    pub fn completion_rate(&self) -> f32 {
        if self.total_tasks == 0 {
            0.0
        } else {
            self.completed_tasks as f32 / self.total_tasks as f32 * 100.0
        }
    }

    /// Check if execution is complete
    pub fn is_complete(&self) -> bool {
        self.completed_tasks + self.failed_tasks == self.total_tasks
    }
}

/// DAG executor
#[derive(Debug)]
pub struct DagExecutor {
    dag: Arc<WorkflowDag>,
    context: ExecutionContext,
    stats: Arc<Mutex<ExecutionStats>>,
}

impl DagExecutor {
    /// Create new DAG executor
    pub fn new(dag: WorkflowDag, context: ExecutionContext) -> Self {
        let stats = ExecutionStats {
            total_tasks: dag.all_tasks().len(),
            ..Default::default()
        };

        Self {
            dag: Arc::new(dag),
            context,
            stats: Arc::new(Mutex::new(stats)),
        }
    }

    /// Execute the DAG
    pub async fn execute(&self) -> Result<ExecutionStats> {
        let start_time = std::time::Instant::now();

        match &self.context.strategy {
            ExecutionStrategy::Topological { concurrency } => {
                self.execute_topological(*concurrency).await?
            }
            ExecutionStrategy::Greedy { concurrency } => {
                self.execute_greedy(*concurrency).await?
            }
            ExecutionStrategy::Parallel { concurrency } => {
                self.execute_parallel(*concurrency).await?
            }
        }

        let mut stats = self.stats.lock().unwrap();
        stats.execution_time = start_time.elapsed();

        Ok(stats.clone())
    }

    /// Execute tasks in topological order
    async fn execute_topological(&self, concurrency: usize) -> Result<()> {
        let order = self.dag.topological_order();
        let semaphore = Arc::new(tokio::sync::Semaphore::new(concurrency));

        // Process tasks in batches with concurrency control
        for chunk in order.chunks(concurrency) {
            let mut handles = Vec::new();

            for task in chunk {
                let permit = semaphore.clone().acquire_owned().await.unwrap();
                let task = Arc::clone(task);
                let executor = self.context.executor.clone();
                let stats = self.stats.clone();

                let handle = tokio::spawn(async move {
                    let task_start = std::time::Instant::now();

                    match executor.execute_task(&task).await {
                        Ok(status) => {
                            let mut stats = stats.lock().unwrap();
                            stats.completed_tasks += 1;
                            stats.task_timings.insert(task.id, task_start.elapsed());
                            info!(
                                "task_completed",
                                name = task.name.as_str(),
                                duration = task_start.elapsed().as_millis()
                            );
                        }
                        Err(e) => {
                            let mut stats = stats.lock().unwrap();
                            stats.failed_tasks += 1;
                            info!(
                                "task_failed",
                                name = task.name.as_str(),
                                error = e.to_string()
                            );
                        }
                    }

                    drop(permit);
                });

                handles.push(handle);
            }

            // Wait for all tasks in this batch to complete
            for handle in handles {
                handle.await?;
            }
        }

        Ok(())
    }

    /// Execute tasks greedily
    async fn execute_greedy(&self, concurrency: usize) -> Result<()> {
        let completed_tasks = Arc::new(DashMap::new());
        let semaphore = Arc::new(tokio::sync::Semaphore::new(concurrency));

        loop {
            // Find ready tasks that have all dependencies completed
            let ready_tasks = self.find_ready_tasks(&completed_tasks);

            if ready_tasks.is_empty() {
                break; // No more tasks to execute
            }

            // Execute ready tasks
            let mut handles = Vec::new();

            for task in ready_tasks {
                let permit = semaphore.clone().acquire_owned().await.unwrap();
                let task = Arc::clone(&task);
                let executor = self.context.executor.clone();
                let stats = self.stats.clone();
                let completed_tasks = completed_tasks.clone();

                let handle = tokio::spawn(async move {
                    let task_start = std::time::Instant::now();

                    match executor.execute_task(&task).await {
                        Ok(status) => {
                            let mut stats = stats.lock().unwrap();
                            stats.completed_tasks += 1;
                            stats.task_timings.insert(task.id, task_start.elapsed());
                            completed_tasks.insert(task.id, ());
                        }
                        Err(e) => {
                            let mut stats = stats.lock().unwrap();
                            stats.failed_tasks += 1;
                        }
                    }

                    drop(permit);
                });

                handles.push(handle);
            }

            // Wait for at least one task to complete
            if !handles.is_empty() {
                let (tx, rx) = channel::unbounded();

                for handle in handles {
                    let tx = tx.clone();
                    tokio::spawn(async move {
                        let _ = tx.send(handle.await);
                    });
                }

                rx.recv()?;
            }
        }

        Ok(())
    }

    /// Find ready tasks that have all dependencies completed
    fn find_ready_tasks(&self, completed_tasks: &DashMap<TaskId, ()>) -> Vec<Arc<Task>> {
        self.dag
            .all_tasks()
            .into_par_iter()
            .filter(|task| !completed_tasks.contains_key(&task.id))
            .filter(|task| {
                let deps = self.dag.task_dependencies(task.id).unwrap_or_default();
                deps.is_empty() || deps.iter().all(|dep| completed_tasks.contains_key(&dep.id))
            })
            .collect()
    }

    /// Execute tasks in parallel with full concurrency
    async fn execute_parallel(&self, concurrency: usize) -> Result<()> {
        let completed_tasks = Arc::new(DashMap::new());
        let semaphore = Arc::new(tokio::sync::Semaphore::new(concurrency));
        let (tx, rx) = channel::unbounded();

        // Keep track of task execution
        let active_tasks = Arc::new(Mutex::new(HashMap::new()));

        // Initial ready tasks
        let ready_tasks = self.dag.ready_tasks();
        for task in ready_tasks {
            let task = Arc::clone(&task);
            let permit = semaphore.clone().acquire_owned().await.unwrap();
            self.execute_task_in_background(
                task,
                self.context.executor.clone(),
                self.stats.clone(),
                completed_tasks.clone(),
                active_tasks.clone(),
                tx.clone(),
                permit,
            );
        }

        // Wait for all tasks to complete
        let mut remaining = self.dag.all_tasks().len();
        while remaining > 0 {
            let result = rx.recv()?;

            match result {
                Ok(Some(task_id)) => {
                    remaining -= 1;

                    // Check for new ready tasks
                    let ready_tasks = self.find_ready_tasks(&completed_tasks);
                    for task in ready_tasks {
                        if !active_tasks.lock().unwrap().contains_key(&task.id) {
                            let permit = semaphore.clone().acquire_owned().await.unwrap();
                            self.execute_task_in_background(
                                task,
                                self.context.executor.clone(),
                                self.stats.clone(),
                                completed_tasks.clone(),
                                active_tasks.clone(),
                                tx.clone(),
                                permit,
                            );
                        }
                    }
                }
                Ok(None) => {}
                Err(e) => return Err(e.into()),
            }
        }

        Ok(())
    }

    /// Execute task in background
    fn execute_task_in_background(
        &self,
        task: Arc<Task>,
        executor: Arc<dyn TaskExecutor>,
        stats: Arc<Mutex<ExecutionStats>>,
        completed_tasks: Arc<DashMap<TaskId, ()>>,
        active_tasks: Arc<Mutex<HashMap<TaskId, ()>>>,
        tx: channel::Sender<Result<Option<TaskId>>>,
        permit: tokio::sync::OwnedSemaphorePermit,
    ) {
        active_tasks.lock().unwrap().insert(task.id, ());

        let handle = tokio::spawn(async move {
            let task_start = std::time::Instant::now();

            let result = executor.execute_task(&task).await;

            drop(permit);
            active_tasks.lock().unwrap().remove(&task.id);

            match result {
                Ok(status) => {
                    let mut stats = stats.lock().unwrap();
                    stats.completed_tasks += 1;
                    stats.task_timings.insert(task.id, task_start.elapsed());
                    completed_tasks.insert(task.id, ());
                }
                Err(e) => {
                    let mut stats = stats.lock().unwrap();
                    stats.failed_tasks += 1;
                }
            }

            tx.send(Ok(Some(task.id)));
        });

        // Handle execution errors
        tokio::spawn(async move {
            if let Err(e) = handle.await {
                tx.send(Err(e.into()));
            }
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use bioworkflow_core::types::ResourceRequirements;

    #[derive(Debug, Clone)]
    struct TestExecutor;

    #[async_trait]
    impl TaskExecutor for TestExecutor {
        async fn execute_task(&self, task: &Task) -> Result<ExecutionStatus> {
            tokio::time::sleep(Duration::from_millis(50)).await;
            Ok(ExecutionStatus::Completed)
        }
    }

    #[tokio::test]
    async fn test_simple_execution() {
        let tasks = vec![
            Task {
                id: 1.into(),
                workflow_id: 1.into(),
                name: "task1".to_string(),
                command: "echo task1".to_string(),
                inputs: vec![],
                outputs: vec!["out1.txt".into()],
                dependencies: vec![],
                resources: ResourceRequirements::default(),
                container: None,
                environment: None,
            },
            Task {
                id: 2.into(),
                workflow_id: 1.into(),
                name: "task2".to_string(),
                command: "echo task2".to_string(),
                inputs: vec!["out1.txt".into()],
                outputs: vec!["out2.txt".into()],
                dependencies: vec![1.into()],
                resources: ResourceRequirements::default(),
                container: None,
                environment: None,
            },
        ];

        let dag = WorkflowDag::new(tasks).unwrap();
        let executor = TestExecutor;

        let context = ExecutionContext {
            strategy: ExecutionStrategy::Topological { concurrency: 1 },
            executor: Arc::new(executor),
            ..Default::default()
        };

        let executor = DagExecutor::new(dag, context);
        let stats = executor.execute().await.unwrap();

        assert_eq!(stats.completed_tasks, 2);
        assert_eq!(stats.failed_tasks, 0);
        assert!(stats.execution_time.as_millis() >= 100); // 2 tasks * 50ms each
    }

    #[tokio::test]
    async fn test_parallel_execution() {
        let tasks = vec![
            Task {
                id: 1.into(),
                workflow_id: 1.into(),
                name: "task1".to_string(),
                command: "echo task1".to_string(),
                inputs: vec![],
                outputs: vec!["out1.txt".into()],
                dependencies: vec![],
                resources: ResourceRequirements::default(),
                container: None,
                environment: None,
            },
            Task {
                id: 2.into(),
                workflow_id: 1.into(),
                name: "task2".to_string(),
                command: "echo task2".to_string(),
                inputs: vec![],
                outputs: vec!["out2.txt".into()],
                dependencies: vec![],
                resources: ResourceRequirements::default(),
                container: None,
                environment: None,
            },
        ];

        let dag = WorkflowDag::new(tasks).unwrap();
        let executor = TestExecutor;

        let context = ExecutionContext {
            strategy: ExecutionStrategy::Parallel { concurrency: 2 },
            executor: Arc::new(executor),
            ..Default::default()
        };

        let executor = DagExecutor::new(dag, context);
        let stats = executor.execute().await.unwrap();

        assert_eq!(stats.completed_tasks, 2);
        // Should complete in around 50ms with parallel execution
        assert!(stats.execution_time.as_millis() < 100);
    }

    #[tokio::test]
    async fn test_execution_statistics() {
        let tasks = vec![
            Task {
                id: 1.into(),
                workflow_id: 1.into(),
                name: "task1".to_string(),
                command: "echo task1".to_string(),
                inputs: vec![],
                outputs: vec!["out1.txt".into()],
                dependencies: vec![],
                resources: ResourceRequirements::default(),
                container: None,
                environment: None,
            },
        ];

        let dag = WorkflowDag::new(tasks).unwrap();
        let executor = TestExecutor;

        let context = ExecutionContext {
            strategy: ExecutionStrategy::Parallel { concurrency: 1 },
            executor: Arc::new(executor),
            ..Default::default()
        };

        let executor = DagExecutor::new(dag, context);
        let stats = executor.execute().await.unwrap();

        assert_eq!(stats.total_tasks, 1);
        assert_eq!(stats.completed_tasks, 1);
        assert!(!stats.task_timings.is_empty());
        assert!(stats.execution_time.as_millis() >= 50);
    }
}
