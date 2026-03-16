//! DAG (Directed Acyclic Graph) engine for BioWorkflow
//!
//! Provides functionality for workflow parsing, DAG construction,
//! task scheduling, and execution management.

#![warn(missing_docs)]
#![deny(unsafe_code)]

use std::collections::{HashMap, HashSet, VecDeque};
use std::fmt;

use petgraph::algo::{kosaraju_scc, toposort};
use petgraph::graph::{DiGraph, NodeIndex};
use petgraph::Direction;
use serde::{Deserialize, Serialize};
use thiserror::Error;

pub mod builder;
pub mod executor;
pub mod parser;
pub mod scheduler;
pub mod visualization;

pub use builder::*;
pub use executor::*;
pub use parser::*;
pub use scheduler::*;
pub use visualization::*;

/// DAG Error types
#[derive(Error, Debug, Clone, PartialEq)]
pub enum DagError {
    /// Cycle detected in graph
    #[error("Cycle detected in workflow DAG: {0}")]
    CycleDetected(String),
    
    /// Node not found
    #[error("Node not found: {0}")]
    NodeNotFound(String),
    
    /// Invalid edge
    #[error("Invalid edge: {0}")]
    InvalidEdge(String),
    
    /// Topology error
    #[error("Topology error: {0}")]
    TopologyError(String),
    
    /// Parse error
    #[error("Parse error: {0}")]
    ParseError(String),
}

/// Result type for DAG operations
pub type DagResult<T> = Result<T, DagError>;

/// Task definition for DAG nodes
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Task {
    /// Task ID
    pub id: String,
    /// Task name
    pub name: String,
    /// Task command
    pub command: String,
    /// Input files
    pub inputs: Vec<String>,
    /// Output files
    pub outputs: Vec<String>,
    /// Resource requirements
    pub resources: ResourceRequirements,
    /// Priority (higher = more important)
    pub priority: i32,
    /// Retry count
    pub retries: u32,
    /// Environment variables
    pub env: HashMap<String, String>,
}

impl Task {
    /// Create a new task
    pub fn new(id: impl Into<String>, name: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            name: name.into(),
            command: String::new(),
            inputs: Vec::new(),
            outputs: Vec::new(),
            resources: ResourceRequirements::default(),
            priority: 0,
            retries: 3,
            env: HashMap::new(),
        }
    }
    
    /// Set command
    pub fn with_command(mut self, command: impl Into<String>) -> Self {
        self.command = command.into();
        self
    }
    
    /// Add input
    pub fn add_input(mut self, input: impl Into<String>) -> Self {
        self.inputs.push(input.into());
        self
    }
    
    /// Add output
    pub fn add_output(mut self, output: impl Into<String>) -> Self {
        self.outputs.push(output.into());
        self
    }
}

/// Resource requirements for tasks
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ResourceRequirements {
    /// CPU cores
    pub cpu_cores: usize,
    /// Memory in MB
    pub memory_mb: usize,
    /// Disk space in MB
    pub disk_mb: usize,
    /// GPU count
    pub gpu_count: usize,
    /// Estimated runtime in seconds
    pub estimated_runtime: u64,
}

impl Default for ResourceRequirements {
    fn default() -> Self {
        Self {
            cpu_cores: 1,
            memory_mb: 512,
            disk_mb: 1024,
            gpu_count: 0,
            estimated_runtime: 300,
        }
    }
}

/// DAG structure for workflow management
#[derive(Debug, Clone)]
pub struct Dag {
    /// Petgraph directed graph
    graph: DiGraph<Task, ()>,
    /// Node index mapping from task ID
    node_map: HashMap<String, NodeIndex>,
    /// Task ID mapping from node index
    id_map: HashMap<NodeIndex, String>,
}

impl Dag {
    /// Create a new empty DAG
    pub fn new() -> Self {
        Self {
            graph: DiGraph::new(),
            node_map: HashMap::new(),
            id_map: HashMap::new(),
        }
    }
    
    /// Add a task to the DAG
    pub fn add_task(&mut self, task: Task) -> NodeIndex {
        let id = task.id.clone();
        let node_idx = self.graph.add_node(task);
        self.node_map.insert(id.clone(), node_idx);
        self.id_map.insert(node_idx, id);
        node_idx
    }
    
    /// Add a dependency edge between tasks
    pub fn add_dependency(
        &mut self,
        from_task: &str,
        to_task: &str,
    ) -> DagResult<()> {
        let from_idx = self.node_map.get(from_task);
        let to_idx = self.node_map.get(to_task);
        
        match (from_idx, to_idx) {
            (Some(&from), Some(&to)) => {
                self.graph.add_edge(from, to, ());
                Ok(())
            }
            (None, _) => Err(DagError::NodeNotFound(from_task.to_string())),
            (_, None) => Err(DagError::NodeNotFound(to_task.to_string())),
        }
    }
    
    /// Get task by ID
    pub fn get_task(&self, id: &str) -> Option<&Task> {
        self.node_map.get(id).and_then(|&idx| self.graph.node_weight(idx))
    }
    
    /// Get task by node index
    pub fn get_task_by_index(&self, idx: NodeIndex) -> Option<&Task> {
        self.graph.node_weight(idx)
    }
    
    /// Get all tasks
    pub fn get_all_tasks(&self) -> Vec<&Task> {
        self.graph.node_weights().collect()
    }
    
    /// Get dependencies of a task
    pub fn get_dependencies(&self, id: &str) -> Vec<&Task> {
        let mut deps = Vec::new();
        if let Some(&idx) = self.node_map.get(id) {
            for neighbor in self.graph.neighbors_directed(idx, Direction::Incoming) {
                if let Some(task) = self.graph.node_weight(neighbor) {
                    deps.push(task);
                }
            }
        }
        deps
    }
    
    /// Get dependents of a task
    pub fn get_dependents(&self, id: &str) -> Vec<&Task> {
        let mut dependents = Vec::new();
        if let Some(&idx) = self.node_map.get(id) {
            for neighbor in self.graph.neighbors_directed(idx, Direction::Outgoing) {
                if let Some(task) = self.graph.node_weight(neighbor) {
                    dependents.push(task);
                }
            }
        }
        dependents
    }
    
    /// Perform topological sort
    pub fn topological_sort(&self) -> DagResult<Vec<&Task>> {
        match toposort(&self.graph, None) {
            Ok(order) => {
                let tasks: Vec<&Task> = order
                    .iter()
                    .filter_map(|&idx| self.graph.node_weight(idx))
                    .collect();
                Ok(tasks)
            }
            Err(cycle) => {
                let node_idx = cycle.node_id();
                let task_id = self.id_map.get(&node_idx).cloned()
                    .unwrap_or_else(|| "unknown".to_string());
                Err(DagError::CycleDetected(task_id))
            }
        }
    }
    
    /// Detect cycles using Kosaraju's algorithm
    pub fn has_cycle(&self) -> bool {
        let scc = kosaraju_scc(&self.graph);
        // If any SCC has more than one node, there's a cycle
        scc.iter().any(|component| component.len() > 1)
    }
    
    /// Get critical path (longest path in terms of estimated runtime)
    pub fn get_critical_path(&self) -> Vec<&Task> {
        // This is a simplified implementation
        // A full implementation would use dynamic programming
        // to find the longest weighted path
        match self.topological_sort() {
            Ok(order) => order,
            Err(_) => Vec::new(),
        }
    }
    
    /// Get ready tasks (all dependencies satisfied)
    pub fn get_ready_tasks(&self, completed: &HashSet<String>) -> Vec<&Task> {
        let mut ready = Vec::new();
        
        for task in self.graph.node_weights() {
            let deps = self.get_dependencies(&task.id);
            let all_deps_satisfied = deps.iter()
                .all(|dep| completed.contains(&dep.id));
            
            if all_deps_satisfied && !completed.contains(&task.id) {
                ready.push(task);
            }
        }
        
        ready
    }
    
    /// Get task count
    pub fn task_count(&self) -> usize {
        self.graph.node_count()
    }
    
    /// Get edge count
    pub fn edge_count(&self) -> usize {
        self.graph.edge_count()
    }
    
    /// Check if task exists
    pub fn has_task(&self, id: &str) -> bool {
        self.node_map.contains_key(id)
    }
}

impl Default for Dag {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for Dag {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Dag {{ tasks: {}, dependencies: {} }}",
            self.task_count(),
            self.edge_count()
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_dag_creation() {
        let dag = Dag::new();
        assert_eq!(dag.task_count(), 0);
        assert_eq!(dag.edge_count(), 0);
    }
    
    #[test]
    fn test_add_task() {
        let mut dag = Dag::new();
        let task = Task::new("task1", "Task 1");
        dag.add_task(task);
        
        assert_eq!(dag.task_count(), 1);
        assert!(dag.has_task("task1"));
    }
    
    #[test]
    fn test_add_dependency() {
        let mut dag = Dag::new();
        
        let task1 = Task::new("task1", "Task 1");
        let task2 = Task::new("task2", "Task 2");
        
        dag.add_task(task1);
        dag.add_task(task2);
        
        let result = dag.add_dependency("task1", "task2");
        assert!(result.is_ok());
        assert_eq!(dag.edge_count(), 1);
    }
    
    #[test]
    fn test_topological_sort() {
        let mut dag = Dag::new();
        
        // Create a simple DAG: A -> B -> C
        dag.add_task(Task::new("A", "Task A"));
        dag.add_task(Task::new("B", "Task B"));
        dag.add_task(Task::new("C", "Task C"));
        
        dag.add_dependency("A", "B").unwrap();
        dag.add_dependency("B", "C").unwrap();
        
        let sorted = dag.topological_sort().unwrap();
        assert_eq!(sorted.len(), 3);
        
        // Verify order: A should come before B, B before C
        let ids: Vec<_> = sorted.iter().map(|t| t.id.as_str()).collect();
        let pos_a = ids.iter().position(|&id| id == "A").unwrap();
        let pos_b = ids.iter().position(|&id| id == "B").unwrap();
        let pos_c = ids.iter().position(|&id| id == "C").unwrap();
        
        assert!(pos_a < pos_b);
        assert!(pos_b < pos_c);
    }
    
    #[test]
    fn test_cycle_detection() {
        let mut dag = Dag::new();
        
        // Create a cycle: A -> B -> C -> A
        dag.add_task(Task::new("A", "Task A"));
        dag.add_task(Task::new("B", "Task B"));
        dag.add_task(Task::new("C", "Task C"));
        
        dag.add_dependency("A", "B").unwrap();
        dag.add_dependency("B", "C").unwrap();
        dag.add_dependency("C", "A").unwrap();
        
        assert!(dag.has_cycle());
        
        // Topological sort should fail
        let result = dag.topological_sort();
        assert!(result.is_err());
    }
}