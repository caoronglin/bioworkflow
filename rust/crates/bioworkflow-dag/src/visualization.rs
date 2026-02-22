//! Visualize the workflow DAG in various formats.

use std::collections::HashSet;
use std::io::Write;
use std::path::Path;

use crate::builder::WorkflowDag;
use bioworkflow_core::types::Task;
use petgraph::dot::Dot;

/// Visualization formats
pub enum VisualizationFormat {
    /// DOT format for Graphviz
    Dot,
    /// Mermaid format for Markdown diagrams
    Mermaid,
    /// JSON format
    Json,
    /// PNG image
    Png,
}

/// Graph visualization
#[derive(Debug)]
pub struct GraphVisualizer;

impl GraphVisualizer {
    /// Generate DOT format visualization
    pub fn to_dot(dag: &WorkflowDag) -> String {
        let graph = &dag.graph;
        let dot = Dot::new(graph);
        format!("{}", dot)
    }

    /// Generate Mermaid format visualization
    pub fn to_mermaid(dag: &WorkflowDag) -> String {
        let mut mermaid = String::new();

        mermaid.push_str("graph TD\n");

        // Add nodes with styling
        for idx in dag.graph.node_indices() {
            let task = &dag.graph[idx];
            let node_id = format!("task{}", task.id.0);
            let node_label = Self::escape_mermaid_label(&task.name);
            let node_style = Self::get_node_style(task);

            mermaid.push_str(&format!(
                "    {}[\"{}\"]{}\n",
                node_id, node_label, node_style
            ));
        }

        // Add edges
        for edge in dag.graph.edge_indices() {
            let (source_idx, target_idx) = dag.graph.edge_endpoints(edge).unwrap();
            let source_task = &dag.graph[source_idx];
            let target_task = &dag.graph[target_idx];

            let source_id = format!("task{}", source_task.id.0);
            let target_id = format!("task{}", target_task.id.0);

            mermaid.push_str(&format!("    {} --> {}\n", source_id, target_id));
        }

        mermaid
    }

    /// Generate JSON format
    pub fn to_json(dag: &WorkflowDag) -> String {
        use serde_json::json;

        let nodes: Vec<_> = dag
            .all_tasks()
            .iter()
            .map(|task| {
                json!({
                    "id": task.id.0,
                    "name": task.name,
                    "inputs": task.inputs,
                    "outputs": task.outputs,
                    "dependencies": task.dependencies.iter().map(|dep| dep.0).collect::<Vec<_>>(),
                    "resources": task.resources
                })
            })
            .collect();

        json!({
            "nodes": nodes
        }).to_string()
    }

    /// Generate PNG image using Graphviz (requires graphviz installed)
    #[cfg(unix)]
    pub fn to_png<P: AsRef<Path>>(dag: &WorkflowDag, output_path: P) -> std::io::Result<()> {
        use std::process::Command;

        let dot_content = Self::to_dot(dag);

        let mut child = Command::new("dot")
            .arg("-Tpng")
            .stdout(std::process::Stdio::piped())
            .stdin(std::process::Stdio::piped())
            .spawn()?;

        {
            let stdin = child.stdin.as_mut().unwrap();
            stdin.write_all(dot_content.as_bytes())?;
        }

        let output = child.wait_with_output()?;

        if !output.status.success() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                String::from_utf8_lossy(&output.stderr),
            ));
        }

        std::fs::write(output_path, output.stdout)
    }

    /// Get Mermaid node style based on task characteristics
    fn get_node_style(task: &Task) -> &'static str {
        if task.container.is_some() {
            ":::container"
        } else if task.environment.is_some() {
            ":::environment"
        } else if task.resources.cpu.is_some() || task.resources.memory.is_some() {
            ":::resource"
        } else {
            ""
        }
    }

    /// Escape special characters for Mermaid labels
    fn escape_mermaid_label(label: &str) -> String {
        label.replace('\"', "\\\"")
    }

    /// Generate Mermaid class definitions
    pub fn generate_styles() -> String {
        r#"
    classDef container fill:#f9f,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5;
    classDef environment fill:#bbf,stroke:#333,stroke-width:2px;
    classDef resource fill:#bfb,stroke:#333,stroke-width:2px;
    classDef cpu fill:#ff9,stroke:#333,stroke-width:2px;
    classDef memory fill:#9ff,stroke:#333,stroke-width:2px;
    classDef gpu fill:#f9f,stroke:#333,stroke-width:2px;
"#
    }
}

/// Render Mermaid diagram with styles
pub fn render_mermaid_with_styles(dag: &WorkflowDag) -> String {
    let mut mermaid = GraphVisualizer::to_mermaid(dag);
    mermaid.push_str(GraphVisualizer::generate_styles());
    mermaid
}

/// Generate HTML with embedded Mermaid diagram
pub fn to_html(dag: &WorkflowDag) -> String {
    let mermaid = render_mermaid_with_styles(dag);
    format!(
        r#"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Workflow Diagram</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .diagram-container {{
            max-width: 100%;
            overflow-x: auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .controls {{
            margin-bottom: 20px;
        }}
        .controls button {{
            margin-right: 10px;
            padding: 8px 16px;
            cursor: pointer;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: white;
        }}
        .controls button:hover {{
            background-color: #f5f5f5;
        }}
    </style>
</head>
<body>
    <h1>Workflow Diagram</h1>

    <div class="controls">
        <button onclick="downloadPng()">Download PNG</button>
        <button onclick="downloadJson()">Download JSON</button>
        <button onclick="downloadDot()">Download DOT</button>
    </div>

    <div class="diagram-container">
        <pre class="mermaid">{mermaid}</pre>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose'
        }});

        function downloadPng() {{
            // This requires server-side rendering
            alert('PNG download requires Graphviz installation');
        }}

        function downloadJson() {{
            const json = '{json}';
            const blob = new Blob([json], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'workflow-dag.json';
            a.click();
            URL.revokeObjectURL(url);
        }}

        function downloadDot() {{
            const dot = `{dot}`;
            const blob = new Blob([dot], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'workflow-dag.dot';
            a.click();
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>
"#,
        mermaid = mermaid,
        json = GraphVisualizer::to_json(dag),
        dot = GraphVisualizer::to_dot(dag)
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use bioworkflow_core::types::ResourceRequirements;

    #[test]
    fn test_to_dot() {
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
        let dot = GraphVisualizer::to_dot(&dag);

        assert!(!dot.is_empty());
        assert!(dot.contains("digraph"));
        assert!(dot.contains("task1"));
    }

    #[test]
    fn test_to_mermaid() {
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
        let mermaid = GraphVisualizer::to_mermaid(&dag);

        assert!(!mermaid.is_empty());
        assert!(mermaid.contains("task1"));
        assert!(mermaid.contains("task2"));
        assert!(mermaid.contains("-->"));
    }

    #[test]
    fn test_to_json() {
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
        let json = GraphVisualizer::to_json(&dag);

        assert!(!json.is_empty());
        assert!(json.contains("task1"));
        assert!(json.contains("out1.txt"));
    }
}
