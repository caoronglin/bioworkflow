# MCP 服务集成

了解如何使用 Model Context Protocol (MCP) 服务扩展 BioWorkflow 的 AI 能力。

## 概述

BioWorkflow 集成了 Model Context Protocol (MCP)，支持与各种 AI 模型和工具的标准化交互。通过 MCP，可以实现工作流的智能编排、自然语言查询和自动化分析。

### 什么是 MCP？

Model Context Protocol (MCP) 是一个开放标准，定义了 AI 模型与应用程序之间的通信协议。它提供了：

- **标准化接口**: 统一的 API 规范
- **工具集成**: 支持自定义工具和功能
- **上下文管理**: 智能的对话上下文处理
- **多模型支持**: 兼容多种 AI 模型

### 主要特性

- **智能工作流编排**: 通过自然语言生成工作流
- **代码生成**: 自动生成分析代码和脚本
- **文档生成**: 自动生成工作流文档
- **错误诊断**: 智能分析执行错误
- **结果解释**: AI 辅助的结果解读

## 前置条件

在使用 MCP 服务前，请确保：

1. 已配置 AI 服务 API（OpenAI、Claude 等）
2. MCP 服务已启动并配置
3. 网络可访问 AI 服务 API
4. 具有足够的 API 调用配额

## 使用指南

### 配置 MCP 服务

#### 基本配置

```yaml
# mcp_config.yaml
providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo
    base_url: https://api.openai.com/v1
  
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-opus
    base_url: https://api.anthropic.com

tools:
  - name: workflow_generator
    description: "Generate Snakemake workflows from natural language"
  
  - name: code_explainer
    description: "Explain code and provide documentation"
  
  - name: error_analyzer
    description: "Analyze and diagnose workflow errors"
```

#### 环境变量

```bash
# .env
MCP_ENABLED=true
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
MCP_DEFAULT_PROVIDER=openai
```

### 使用 MCP 工具

#### 工作流生成

```python
# 通过 MCP 生成工作流
import requests

response = requests.post(
    "http://localhost:8000/api/mcp/tools/workflow_generator",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "prompt": "创建一个 RNA-seq 差异表达分析流程，包括质控、比对、定量和差异分析步骤",
        "parameters": {
            "species": "human",
            "sequencing_type": "paired-end"
        }
    }
)

workflow = response.json()["workflow"]
print(workflow)
```

生成的 Snakemake 工作流：

```python
# 生成的 RNA-seq 工作流
configfile: "config.yaml"

rule all:
    input:
        expand("results/{sample}_counts.txt", sample=config["samples"]),
        "results/differential_expression.csv"

rule fastqc:
    input: "data/{sample}.fastq.gz"
    output: "qc/{sample}_fastqc.html"
    conda: "envs/fastqc.yaml"
    threads: 4
    shell:
        "fastqc -t {threads} {input} -o qc/"

rule trim:
    input: "data/{sample}.fastq.gz"
    output: "trimmed/{sample}.fastq.gz"
    conda: "envs/trimmomatic.yaml"
    shell:
        """
        trimmomatic SE {input} {output} \
            LEADING:30 TRAILING:30 SLIDINGWINDOW:4:30 MINLEN:50
        """

# ... 更多规则
```

#### 错误诊断

```python
# 分析执行错误
error_log = """
Error in rule mapping:
    jobid: 0, output: results/sample1.bam

RuleException:
CalledProcessError in line 15 of workflow.smk:
Command 'bwa mem reference.fasta data/sample1.fastq' returned non-zero exit status 1
"""

response = requests.post(
    "http://localhost:8000/api/mcp/tools/error_analyzer",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "error_log": error_log,
        "workflow_id": "rna-seq-pipeline"
    }
)

analysis = response.json()
print(analysis["diagnosis"])
print(analysis["suggestions"])
```

#### 结果解释

```python
# 解释分析结果
results = {
    "differential_genes": [
        {"gene": "TP53", "log2FC": 2.5, "pvalue": 0.001},
        {"gene": "BRCA1", "log2FC": -1.8, "pvalue": 0.005}
    ]
}

response = requests.post(
    "http://localhost:8000/api/mcp/tools/result_explainer",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "results": results,
        "analysis_type": "differential_expression",
        "context": "Cancer vs Normal comparison"
    }
)

interpretation = response.json()["interpretation"]
```

## 示例

### 完整的智能分析流程

```python
import requests

BASE_URL = "http://localhost:8000/api/mcp"
HEADERS = {"Authorization": "Bearer YOUR_TOKEN"}

# 步骤 1: 描述分析需求
description = """
分析两组样本的 RNA-seq 数据：
- 对照组：3 个正常组织样本
- 实验组：3 个肿瘤组织样本
- 目标：寻找差异表达基因并进行通路富集分析
"""

# 步骤 2: 生成工作流
workflow_response = requests.post(
    f"{BASE_URL}/tools/workflow_generator",
    headers=HEADERS,
    json={"prompt": description}
)
workflow_id = workflow_response.json()["workflow_id"]

# 步骤 3: 执行工作流
execution_response = requests.post(
    f"http://localhost:8000/api/workflows/{workflow_id}/execute",
    headers=HEADERS,
    json={
        "config": {
            "control_samples": ["control_1", "control_2", "control_3"],
            "treatment_samples": ["tumor_1", "tumor_2", "tumor_3"],
            "reference": "GRCh38"
        }
    }
)

# 步骤 4: 解释结果
results = get_execution_results(execution_response.json()["execution_id"])
interpretation = requests.post(
    f"{BASE_URL}/tools/result_explainer",
    headers=HEADERS,
    json={
        "results": results,
        "analysis_type": "differential_expression"
    }
)

print(interpretation.json()["interpretation"])
```

### 自然语言查询

```python
# 使用自然语言查询工作流状态
query = "显示所有正在运行的 RNA-seq 工作流"

response = requests.post(
    f"{BASE_URL}/query",
    headers=HEADERS,
    json={"query": query}
)

print(response.json()["results"])
```

## MCP 工具开发

### 创建自定义工具

```python
# custom_tools/variant_caller.py
from mcp import Tool, ToolResponse

class VariantCallerTool(Tool):
    """变异检测工具"""
    
    name = "variant_caller"
    description = "Call variants from BAM files"
    
    parameters = {
        "bam_file": {
            "type": "string",
            "description": "Input BAM file path"
        },
        "reference": {
            "type": "string",
            "description": "Reference genome path"
        },
        "caller": {
            "type": "string",
            "enum": ["gatk", "freebayes", "varscan"],
            "default": "gatk"
        }
    }
    
    async def execute(self, bam_file: str, reference: str, caller: str = "gatk") -> ToolResponse:
        # 执行变异检测
        result = await self.run_variant_caller(bam_file, reference, caller)
        
        return ToolResponse(
            success=True,
            output=result,
            metadata={
                "caller": caller,
                "variants_count": len(result["variants"])
            }
        )
```

### 注册工具

```python
# 注册自定义工具
from bioworkflow.mcp import register_tool

register_tool(VariantCallerTool)
```

## 高级配置

### 多模型配置

```yaml
# mcp_config.yaml
routing:
  rules:
    - condition:
        tool: "workflow_generator"
        complexity: "high"
      provider: "anthropic"
      model: "claude-3-opus"
    
    - condition:
        tool: "error_analyzer"
        urgency: "high"
      provider: "openai"
      model: "gpt-4-turbo"
    
    - default: true
      provider: "openai"
      model: "gpt-3.5-turbo"
```

### 上下文管理

```python
# 配置上下文管理
context_config = {
    "max_tokens": 8000,
    "include_workflow_history": True,
    "include_knowledge_base": True,
    "summarize_threshold": 4000
}

response = requests.post(
    f"{BASE_URL}/chat",
    headers=HEADERS,
    json={
        "message": "帮我优化这个工作流",
        "workflow_id": "rna-seq-pipeline",
        "context_config": context_config
    }
)
```

## 故障排除

### 常见问题

#### 1. API 调用失败

**症状**: MCP 工具调用返回错误

**解决方案**:

```bash
# 检查 API 密钥
echo $OPENAI_API_KEY

# 测试 API 连接
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 2. 响应超时

**症状**: AI 响应时间过长

**解决方案**:

```yaml
# 增加超时时间
mcp:
  timeout: 120  # 秒
  retry_count: 3
  retry_delay: 5
```

#### 3. 上下文长度超限

**症状**: Token 限制错误

**解决方案**:

```python
# 使用上下文压缩
response = requests.post(
    f"{BASE_URL}/chat",
    headers=HEADERS,
    json={
        "message": "分析这个工作流",
        "context_compression": True,
        "max_context_tokens": 6000
    }
)
```

## 相关文档

- [知识库系统](knowledge.md)
- [工作流管理](workflows.md)
- [API 参考](../api/endpoints.md)
- [插件开发](../development/plugins.md)