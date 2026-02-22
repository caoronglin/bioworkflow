//! Parse workflow definitions from various formats.

use std::collections::HashMap;
use std::path::Path;

use anyhow::Context;
use serde::Deserialize;
use serde_json::Value;

use bioworkflow_core::types::{
    Task, TaskId, Workflow, WorkflowId, ResourceRequirements,
};
use bioworkflow_core::Result;

/// Snakemake workflow parser
pub struct SnakemakeParser;

impl SnakemakeParser {
    /// Parse Snakemake file
    pub fn parse<P: AsRef<Path>>(path: P) -> Result<Workflow> {
        let snakefile = std::fs::read_to_string(path)?;
        Self::parse_str(&snakefile)
    }

    /// Parse Snakemake content from string
    pub fn parse_str(content: &str) -> Result<Workflow> {
        // TODO: Implement proper Snakemake parser
        // This is a simplified version for demonstration

        let mut tasks = Vec::new();
        let mut task_map = HashMap::new();

        // Extract rules from Snakefile
        let rules = Self::extract_rules(content);

        for (index, rule) in rules.iter().enumerate() {
            let task = Self::parse_rule(rule, index as u32)?;
            task_map.insert(rule.name.clone(), task.clone());
            tasks.push(task);
        }

        // Resolve dependencies between tasks
        Self::resolve_dependencies(&mut tasks, &task_map)?;

        Ok(Workflow {
            id: WorkflowId::new(),
            name: "Snakemake Workflow".to_string(),
            description: Some("Generated from Snakefile".to_string()),
            snakefile: Path::new("Snakefile").to_path_buf(),
            config: HashMap::new(),
            env_vars: HashMap::new(),
            created_at: std::time::SystemTime::now(),
            updated_at: std::time::SystemTime::now(),
            tags: vec!["snakemake".to_string()],
        })
    }

    /// Extract rules from Snakefile content
    fn extract_rules(content: &str) -> Vec<Rule> {
        let mut rules = Vec::new();
        let mut current_rule = None;

        for line in content.lines() {
            let line = line.trim();

            if line.starts_with("rule ") && !line.starts_with("rule ") && !line.contains(":") {
                if let Some(rule) = current_rule.take() {
                    rules.push(rule);
                }

                let name = line.strip_prefix("rule ").unwrap_or_default()
                    .split_whitespace()
                    .next()
                    .unwrap_or_default();
                current_rule = Some(Rule::new(name.to_string()));
            } else if let Some(rule) = current_rule.as_mut() {
                Self::parse_rule_line(rule, line);
            }
        }

        if let Some(rule) = current_rule.take() {
            rules.push(rule);
        }

        rules
    }

    /// Parse rule line
    fn parse_rule_line(rule: &mut Rule, line: &str) {
        let line = line.trim();

        if line.starts_with("input:") {
            Self::parse_inputs_outputs(rule, line.strip_prefix("input:").unwrap_or_default(), true);
        } else if line.starts_with("output:") {
            Self::parse_inputs_outputs(rule, line.strip_prefix("output:").unwrap_or_default(), false);
        } else if line.starts_with("params:") {
            rule.params = Self::parse_key_value(line.strip_prefix("params:").unwrap_or_default());
        } else if line.starts_with("shell:") || line.starts_with("run:") {
            let cmd = line.strip_prefix("shell:").unwrap_or(
                line.strip_prefix("run:").unwrap_or_default()
            );
            rule.command = cmd.trim().to_string();
        }
    }

    /// Parse inputs/outputs
    fn parse_inputs_outputs(rule: &mut Rule, content: &str, is_input: bool) {
        let items: Vec<_> = content
            .split(',')
            .map(|s| s.trim())
            .filter(|s| !s.is_empty())
            .map(|s| Self::parse_file_spec(s))
            .collect();

        if is_input {
            rule.inputs.extend(items);
        } else {
            rule.outputs.extend(items);
        }
    }

    /// Parse file specification
    fn parse_file_spec(spec: &str) -> String {
        let trimmed = spec.trim();
        if trimmed.starts_with('"') && trimmed.ends_with('"') ||
            trimmed.starts_with('\'') && trimmed.ends_with('\'') {
            trimmed.trim_matches(|c| c == '\'' || c == '"').to_string()
        } else {
            trimmed.to_string()
        }
    }

    /// Parse key-value pairs
    fn parse_key_value(content: &str) -> HashMap<String, String> {
        let mut map = HashMap::new();
        let pairs: Vec<_> = content.split(',').map(|s| s.trim()).filter(|s| !s.is_empty());

        for pair in pairs {
            let parts: Vec<_> = pair.split('=').map(|s| s.trim()).collect();
            if parts.len() >= 2 {
                map.insert(parts[0].to_string(), parts[1].to_string());
            }
        }

        map
    }

    /// Parse rule to Task
    fn parse_rule(rule: &Rule, index: u32) -> Result<Task> {
        Ok(Task {
            id: TaskId::new(),
            workflow_id: WorkflowId::new(),
            name: rule.name.clone(),
            command: rule.command.clone(),
            inputs: rule.inputs.iter().map(|s| s.into()).collect(),
            outputs: rule.outputs.iter().map(|s| s.into()).collect(),
            dependencies: Vec::new(),
            resources: ResourceRequirements {
                cpu: rule.params.get("cpu").and_then(|v| v.parse().ok()),
                memory: rule.params.get("memory").and_then(|v| v.parse().ok()),
                gpu: None,
                disk: None,
                tmpdir: None,
                custom: HashMap::new(),
            },
            container: rule.params.get("container").cloned(),
            environment: rule.params.get("environment").cloned(),
        })
    }

    /// Resolve task dependencies
    fn resolve_dependencies(tasks: &mut [Task], task_map: &HashMap<String, Task>) -> Result<()> {
        // Simple dependency resolution based on file dependencies
        for task in tasks.iter_mut() {
            let mut dependencies = Vec::new();

            // Look for tasks that produce inputs to this task
            for input in &task.inputs {
                for (name, other_task) in task_map {
                    if other_task.outputs.iter().any(|out| {
                        out.to_string_lossy().contains(input.to_string_lossy().as_ref())
                    }) {
                        if other_task.id != task.id {
                            dependencies.push(other_task.id);
                        }
                    }
                }
            }

            task.dependencies = dependencies;
        }

        Ok(())
    }
}

/// Intermediate rule representation
#[derive(Debug, Clone)]
struct Rule {
    pub name: String,
    pub inputs: Vec<String>,
    pub outputs: Vec<String>,
    pub params: HashMap<String, String>,
    pub command: String,
    pub dependencies: Vec<String>,
}

impl Rule {
    /// Create new rule
    pub fn new(name: String) -> Self {
        Self {
            name,
            inputs: Vec::new(),
            outputs: Vec::new(),
            params: HashMap::new(),
            command: String::new(),
            dependencies: Vec::new(),
        }
    }
}

/// YAML workflow parser
#[derive(Deserialize, Debug)]
struct YamlWorkflow {
    name: String,
    description: Option<String>,
    version: Option<String>,
    tasks: Vec<YamlTask>,
}

#[derive(Deserialize, Debug)]
struct YamlTask {
    name: String,
    command: String,
    inputs: Vec<String>,
    outputs: Vec<String>,
    dependencies: Vec<String>,
    resources: Option<HashMap<String, serde_json::Value>>,
    container: Option<String>,
    environment: Option<String>,
}

/// YAML workflow parser
pub struct YamlParser;

impl YamlParser {
    /// Parse YAML workflow file
    pub fn parse<P: AsRef<Path>>(path: P) -> Result<Workflow> {
        let content = std::fs::read_to_string(path)?;
        Self::parse_str(&content)
    }

    /// Parse YAML content from string
    pub fn parse_str(content: &str) -> Result<Workflow> {
        let yaml_workflow: YamlWorkflow = serde_yaml::from_str(content)?;

        let mut task_map = HashMap::new();
        let mut tasks = Vec::new();

        // First pass: Create tasks without dependencies
        for yaml_task in yaml_workflow.tasks {
            let task = Self::parse_yaml_task(yaml_task, &task_map)?;
            task_map.insert(task.name.clone(), task.clone());
            tasks.push(task);
        }

        // Second pass: Resolve dependencies using task names
        for task in &mut tasks {
            let mut resolved_deps = Vec::new();
            for dep_name in &task.dependencies {
                if let Some(dep_task) = task_map.get(dep_name) {
                    resolved_deps.push(dep_task.id);
                } else {
                    return Err(bioworkflow_core::BioWorkflowError::NotFound(
                        format!("Dependency '{}' not found for task '{}'", dep_name, task.name)
                    ));
                }
            }
            task.dependencies = resolved_deps;
        }

        Ok(Workflow {
            id: WorkflowId::new(),
            name: yaml_workflow.name,
            description: yaml_workflow.description,
            snakefile: Path::new("workflow.yaml").to_path_buf(),
            config: HashMap::new(),
            env_vars: HashMap::new(),
            created_at: std::time::SystemTime::now(),
            updated_at: std::time::SystemTime::now(),
            tags: Vec::new(),
        })
    }

    /// Parse YAML task to Task
    fn parse_yaml_task(yaml_task: YamlTask, task_map: &HashMap<String, Task>) -> Result<Task> {
        Ok(Task {
            id: TaskId::new(),
            workflow_id: WorkflowId::new(),
            name: yaml_task.name,
            command: yaml_task.command,
            inputs: yaml_task.inputs.iter().map(|s| s.into()).collect(),
            outputs: yaml_task.outputs.iter().map(|s| s.into()).collect(),
            dependencies: Vec::new(), // Will be resolved later
            resources: Self::parse_resources(yaml_task.resources),
            container: yaml_task.container,
            environment: yaml_task.environment,
        })
    }

    /// Parse resources from YAML
    fn parse_resources(resources: Option<HashMap<String, Value>>) -> ResourceRequirements {
        let mut req = ResourceRequirements::default();
        if let Some(res) = resources {
            for (key, value) in res {
                match key.as_str() {
                    "cpu" => req.cpu = value.as_f64(),
                    "memory" => req.memory = value.as_u64(),
                    "gpu" => req.gpu = value.as_u64().map(|v| v as u32),
                    "disk" => req.disk = value.as_u64(),
                    "tmpdir" => req.tmpdir = value.as_u64(),
                    _ => req.custom.insert(key, value),
                }
            }
        }
        req
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;

    #[test]
    fn test_parse_simple_workflow() {
        let snakefile = r#"
rule all:
    input:
        "result.txt"

rule generate:
    output:
        "temp.txt"
    shell:
        "echo 'data' > temp.txt"

rule process:
    input:
        "temp.txt"
    output:
        "result.txt"
    shell:
        "cat temp.txt | grep 'data' > result.txt"
"#;

        let workflow = SnakemakeParser::parse_str(snakefile).unwrap();
        assert_eq!(workflow.name, "Snakemake Workflow");
    }

    #[test]
    fn test_parse_yaml_workflow() {
        let yaml_content = r#"
name: "Test Workflow"
description: "Test workflow for parsing"
version: "1.0"

tasks:
  - name: "generate"
    command: "echo 'data' > temp.txt"
    inputs: []
    outputs: ["temp.txt"]
    dependencies: []
    resources:
      cpu: 1
      memory: 1024
    container: "python:3.11"
    environment: "test_env"

  - name: "process"
    command: "cat temp.txt | grep 'data' > result.txt"
    inputs: ["temp.txt"]
    outputs: ["result.txt"]
    dependencies: ["generate"]
    resources:
      cpu: 2
      memory: 2048
"#;

        let workflow = YamlParser::parse_str(yaml_content).unwrap();
        assert_eq!(workflow.name, "Test Workflow");
        assert_eq!(workflow.description, Some("Test workflow for parsing".to_string()));
    }
}
