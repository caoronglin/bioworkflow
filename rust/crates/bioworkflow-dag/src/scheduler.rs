use crate::{Dag, DagError, DagResult, Task};
use std::collections::{HashMap, HashSet};

pub struct TaskScheduler {
    max_concurrent: usize,
}

impl TaskScheduler {
    pub fn new(max_concurrent: usize) -> Self {
        Self { max_concurrent }
    }

    pub fn get_ready_tasks(
        &self,
        dag: &Dag,
        completed: &HashSet<String>,
        running: &HashSet<String>,
    ) -> Vec<&Task> {
        let mut ready = Vec::new();
        
        for task in dag.get_all_tasks() {
            if completed.contains(&task.id) || running.contains(&task.id) {
                continue;
            }
            
            let deps = dag.get_dependencies(&task.id);
            let all_deps_done = deps.iter().all(|dep| completed.contains(&dep.id));
            
            if all_deps_done {
                ready.push(task);
            }
        }
        
        ready.into_iter().take(self.max_concurrent).collect()
    }
}

impl Default for TaskScheduler {
    fn default() -> Self {
        Self::new(4)
    }
}