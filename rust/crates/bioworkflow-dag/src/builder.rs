//! DAG construction from workflow definitions.

use std::collections::{HashMap, HashSet};
use std::path::PathBuf;
use std::sync::Arc;

use petgraph::graph::DiGraph;
use petgraph::visit::DfsPostOrder;
use thiserror::Error;

use bioworkflow_core::types::{Task, TaskId, WorkflowId};
use bioworkflow_core::Result;

/// DAG construction errors
#[derive(Error, Debug)]
pub enum DagBuilderError {
    /// Duplicate task definition
    #[error("Duplicate task definition: {0}")]
    DuplicateTask(String),

    /// Cycle detected in workflow
    #[error("Workflow contains cycle: {0}")]
    Cycle(String),

    /// Invalid task dependency
    #[error("Task {0} depends on unknown task {1}")]
    InvalidDependency(String, String),

    /// Task has no inputs or outputs
    #[error("Task {0} must have at least one input or output")]
    NoInputsOutputs(String),

    /// Workflow has no tasks
    #[error("Workflow must contain at least one task")]
    NoTasks,

    /// Invalid workflow definition
    #[error("Invalid workflow definition: {0}")]
    InvalidDefinition(String),
}

impl From<DagBuilderError> for bioworkflow_core::BioWorkflowError {
    fn from(err: DagBuilderError) -> Self {
        Self::Dag(err.to_string())
    }
}

/// DAG representation of a workflow
#[derive(Debug, Clone)]
pub struct WorkflowDag {
    /// Internal graph representation
    pub(crate) graph: DiGraph<Arc<Task>, ()>,

    /// Task ID to graph index map
    pub(crate) task_index_map: HashMap<TaskId, petgraph::graph::NodeIndex>,
}

impl WorkflowDag {
    /// Create a new DAG from tasks
    pub fn new(tasks: Vec<Task>) -> Result<Self> {
        let mut builder = DagBuilder::default();
        builder.add_tasks(tasks)
    }

    /// Get task by ID
    pub fn get_task(&self, task_id: TaskId) -> Option<&Arc<Task>> {
        self.task_index_map.get(&task_id).map(|&idx| &self.graph[idx])
    }

    /// Get all tasks in topological order
    pub fn topological_order(&self) -> Vec<Arc<Task>> {
        let mut order = Vec::new();
        let dfs = DfsPostOrder::new(&self.graph, self.graph.node_indices().next()?);

        for idx in dfs {
            order.push(Arc::clone(&self.graph[idx]));
        }

        order.reverse();
        Some(order).unwrap_or_default()
    }

    /// Get task dependencies
    pub fn task_dependencies(&self, task_id: TaskId) -> Result<Vec<Arc<Task>>> {
        let idx = self
            .task_index_map
            .get(&task_id)
            .ok_or_else(|| bioworkflow_core::BioWorkflowError::NotFound("Task not found".into()))?;

        self.graph
            .neighbors_directed(*idx, petgraph::Direction::Incoming)
            .map(|dep_idx| Arc::clone(&self.graph[dep_idx]))
            .collect()
    }

    /// Get task dependents
    pub fn task_dependents(&self, task_id: TaskId) -> Result<Vec<Arc<Task>>> {
        let idx = self
            .task_index_map
            .get(&task_id)
            .ok_or_else(|| bioworkflow_core::BioWorkflowError::NotFound("Task not found".into()))?;

        self.graph
            .neighbors_directed(*idx, petgraph::Direction::Outgoing)
            .map(|dep_idx| Arc::clone(&self.graph[dep_idx]))
            .collect()
    }

    /// Get all tasks
    pub fn all_tasks(&self) -> Vec<Arc<Task>> {
        self.graph.node_weights().cloned().collect()
    }

    /// Get ready tasks (no dependencies)
    pub fn ready_tasks(&self) -> Vec<Arc<Task>> {
        self.graph
            .node_indices()
            .filter(|&idx| self.graph.neighbors_directed(idx, petgraph::Direction::Incoming).count() == 0)
            .map(|idx| Arc::clone(&self.graph[idx]))
            .collect()
    }

    /// Check if task has dependencies
    pub fn has_dependencies(&self, task_id: TaskId) -> bool {
        self.task_dependencies(task_id).map_or(false, |deps| !deps.is_empty())
    }
}

/// DAG builder
#[derive(Debug, Default)]
pub struct DagBuilder {
    tasks: Vec<Task>,
    task_map: HashMap<TaskId, usize>,
    dependencies: HashMap<TaskId, Vec<TaskId>>,
}

impl DagBuilder {
    /// Create a new DAG builder
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a single task
    pub fn add_task(&mut self, task: Task) -> Result<&mut Self> {
        // Validate task
        self.validate_task(&task)?;

        // Check for duplicates
        if self.task_map.contains_key(&task.id) {
            return Err(DagBuilderError::DuplicateTask(task.name.clone()).into());
        }

        self.task_map.insert(task.id, self.tasks.len());
        self.dependencies.insert(task.id, task.dependencies.clone());
        self.tasks.push(task);

        Ok(self)
    }

    /// Add multiple tasks
    pub fn add_tasks(&mut self, tasks: Vec<Task>) -> Result<WorkflowDag> {
        for task in tasks {
            self.add_task(task)?;
        }

        self.build()
    }

    /// Build the DAG
    pub fn build(self) -> Result<WorkflowDag> {
        if self.tasks.is_empty() {
            return Err(DagBuilderError::NoTasks.into());
        }

        let mut graph = DiGraph::new();
        let mut task_index_map = HashMap::new();

        // Add all nodes first
        for task in &self.tasks {
            let idx = graph.add_node(Arc::new(task.clone()));
            task_index_map.insert(task.id, idx);
        }

        // Add edges
        for task in &self.tasks {
            let task_idx = task_index_map.get(&task.id).unwrap();

            for dep_id in &task.dependencies {
                if let Some(dep_idx) = task_index_map.get(dep_id) {
                    graph.add_edge(*dep_idx, *task_idx, ());
                } else {
                    return Err(DagBuilderError::InvalidDependency(
                        task.name.clone(),
                        dep_id.to_string(),
                    )
                    .into());
                }
            }
        }

        // Check for cycles
        if let Some(cycle) = petgraph::algo::find_cycle(&graph) {
            let cycle_str = cycle
                .iter()
                .map(|idx| graph[*idx].name.as_str())
                .collect::<Vec<_>>()
                .join(" → ");
            return Err(DagBuilderError::Cycle(cycle_str).into());
        }

        Ok(WorkflowDag {
            graph,
            task_index_map,
        })
    }

    /// Validate task definition
    fn validate_task(&self, task: &Task) -> Result<()> {
        if task.name.trim().is_empty() {
            return Err(DagBuilderError::InvalidDefinition(
                "Task name cannot be empty".into(),
            )
            .into());
        }

        if task.inputs.is_empty() && task.outputs.is_empty() {
            return Err(DagBuilderError::NoInputsOutputs(task.name.clone()).into());
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use bioworkflow_core::types::ResourceRequirements;

    fn create_test_task(id: u32, name: &str) -> Task {
        Task {
            id: (id as u128).into(),
            workflow_id: 1.into(),
            name: name.to_string(),
            command: format!("echo task{}", id),
            inputs: vec![],
            outputs: vec![],
            dependencies: vec![],
            resources: ResourceRequirements::default(),
            container: None,
            environment: None,
        }
    }

    #[test]
    fn test_create_simple_dag() {
        let task1 = create_test_task(1, "task1");
        let task2 = create_test_task(2, "task2");

        let dag = WorkflowDag::new(vec![task1, task2]).unwrap();

        assert_eq!(dag.all_tasks().len(), 2);
    }

    #[test]
    fn test_cyclic_dependency() {
        let mut task1 = create_test_task(1, "task1");
        let mut task2 = create_test_task(2, "task2");

        task1.dependencies = vec![task2.id];
        task2.dependencies = vec![task1.id];

        let result = WorkflowDag::new(vec![task1, task2]);
        assert!(result.is_err());
    }

    #[test]
    fn test_task_dependencies() {
        let mut task1 = create_test_task(1, "task1");
        let task2 = create_test_task(2, "task2");
        let mut task3 = create_test_task(3, "task3");

        task1.dependencies = vec![task2.id];
        task3.dependencies = vec![task1.id];

        let dag = WorkflowDag::new(vec![task1, task2, task3]).unwrap();

        let deps = dag.task_dependencies(1.into()).unwrap();
        assert_eq!(deps.len(), 1);
        assert_eq!(deps[0].name, "task2");
    }

    #[test]
    fn test_topological_order() {
        let mut task1 = create_test_task(1, "task1");
        let task2 = create_test_task(2, "task2");
        let mut task3 = create_test_task(3, "task3");

        task1.dependencies = vec![task2.id];
        task3.dependencies = vec![task1.id];

        let dag = WorkflowDag::new(vec![task1, task2, task3]).unwrap();
        let order = dag.topological_order();

        let names: Vec<_> = order.iter().map(|t| t.name.as_str()).collect();
        assert!(vec!["task2", "task1", "task3"].contains(&names.as_slice()));
    }

    #[test]
    fn test_ready_tasks() {
        let mut task1 = create_test_task(1, "task1");
        let task2 = create_test_task(2, "task2");
        let mut task3 = create_test_task(3, "task3");

        task1.dependencies = vec![task2.id];
        task3.dependencies = vec![task1.id];

        let dag = WorkflowDag::new(vec![task1, task2, task3]).unwrap();
        let ready = dag.ready_tasks();

        assert_eq!(ready.len(), 1);
        assert_eq!(ready[0].name, "task2");
    }
}
