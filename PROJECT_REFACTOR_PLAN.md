# BioWorkflow 重构计划

## 项目概述

将 BioWorkflow 从单体架构改造为微服务架构，主要改造包括：
1. **conda → miniforge** 替换
2. **模块化/微服务化** 各板块独立部署
3. **Rust 核心** 重写性能关键模块

---

## 📅 执行阶段

### Phase 1: 基础架构改造 (Week 1-2)

#### 1.1 项目目录结构重构 ✅

```
bioworkflow/
├── rust/                           # Rust 核心
│   ├── Cargo.toml                  # Workspace 配置
│   └── crates/
│       ├── bioworkflow-core/       # 共享核心库
│       ├── bioworkflow-dag/        # DAG 引擎
│       ├── bioworkflow-io/         # 高性能 I/O
│       ├── bioworkflow-scheduler/  # 任务调度器
│       └── bioworkflow-python/     # PyO3 Python 绑定
│
├── services/                       # 微服务
│   ├── workflow-service/           # 工作流服务 (Rust核心)
│   ├── miniforge-service/          # Miniforge 环境服务
│   ├── knowledge-service/          # 知识库服务
│   ├── mcp-gateway/                # MCP 网关服务
│   └── auth-service/               # 认证服务
│
├── shared/                         # 共享组件
│   ├── models/                     # 共享数据模型 (protobuf)
│   ├── utils/                      # 共享工具函数
│   └── proto/                      # gRPC protobuf 定义
│
├── deploy/                         # 部署配置
│   ├── docker/
│   ├── kubernetes/
│   └── helm/
│
└── docs/                           # 文档
    ├── api/
    ├── architecture/
    └── deployment/
```

#### 1.2 Miniforge 服务实现

**目标**: 将现有的 conda 服务替换为 miniforge/mamba 服务

**关键变更**:
- 使用 `condaforge/miniforge` 作为基础镜像
- 将 `conda` 命令替换为 `mamba` (更快)
- 更新 API 端点: `/api/v1/conda/*` → `/api/v1/miniforge/*`
- 支持多架构: x86_64, arm64 (Apple Silicon)

**文件变更**:
```
src/backend/services/conda/ → services/miniforge-service/
- conda_manager.py → miniforge_manager.py
- Add mamba support for faster package resolution
```

#### 1.3 Rust 开发环境设置

**工具链**:
```bash
# Rust 工具链
rustup default stable
rustup component add rustfmt clippy

# 交叉编译支持
rustup target add x86_64-unknown-linux-gnu
rustup target add aarch64-unknown-linux-gnu
rustup target add aarch64-apple-darwin

# WebAssembly (如果需要)
rustup target add wasm32-unknown-unknown

# 有用工具
cargo install cargo-watch cargo-workspaces cargo-expand
```

**Workspace 配置**:
```toml
# rust/Cargo.toml
[workspace]
members = [
    "crates/bioworkflow-core",
    "crates/bioworkflow-dag",
    "crates/bioworkflow-io",
    "crates/bioworkflow-scheduler",
    "crates/bioworkflow-python",
]
resolver = "2"

[workspace.dependencies]
# 核心依赖
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.35", features = ["full"] }
pyo3 = { version = "0.20", features = ["extension-module"] }
parking_lot = "0.12"
dashmap = "5.5"
rayon = "1.8"
```

---

### Phase 2: 微服务拆分 (Week 3-4)

#### 2.1 服务边界划分

| 服务 | 职责 | 技术栈 | 端口 |
|------|------|--------|------|
| `workflow-service` | 工作流定义、执行、DAG | Rust + gRPC | 50051 |
| `miniforge-service` | 环境管理、包安装 | Python + FastAPI | 8001 |
| `knowledge-service` | 知识库、文档检索 | Python + FastAPI | 8002 |
| `mcp-gateway` | MCP 协议网关 | Rust + WebSocket | 8003 |
| `auth-service` | 认证授权 | Python + FastAPI | 8004 |
| `api-gateway` | 统一入口 | Kong/Nginx | 80/443 |

#### 2.2 通信协议

**服务间通信**:
```protobuf
// shared/proto/workflow.proto
syntax = "proto3";
package bioworkflow;

service WorkflowService {
    rpc ExecuteWorkflow(ExecuteRequest) returns (ExecuteResponse);
    rpc GetWorkflowStatus(StatusRequest) returns (stream StatusResponse);
    rpc CancelWorkflow(CancelRequest) returns (CancelResponse);
}

message ExecuteRequest {
    string workflow_id = 1;
    string snakemake_file = 2;
    map<string, string> config = 3;
}
```

**事件驱动**:
```python
# 使用 Redis Pub/Sub 或 RabbitMQ
EVENTS = {
    "workflow.started",
    "workflow.completed",
    "workflow.failed",
    "env.created",
    "env.deleted",
}
```

#### 2.3 独立部署配置

每个服务独立容器化:
```dockerfile
# services/workflow-service/Dockerfile
FROM rust:1.75-slim AS builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
COPY --from=builder /app/target/release/workflow-service /usr/local/bin/
EXPOSE 50051
CMD ["workflow-service"]
```

---

### Phase 3: Rust 核心实现 (Week 5-8)

#### 3.1 核心模块设计

**DAG 引擎** (`crates/bioworkflow-dag`):
```rust
use petgraph::graph::DiGraph;
use rayon::prelude::*;

pub struct DagEngine {
    graph: DiGraph<Task, Dependency>,
    scheduler: Box<dyn Scheduler>,
}

impl DagEngine {
    pub fn execute(&self) -> ExecutionResult {
        // 并行执行无依赖任务
        self.get_ready_tasks()
            .par_iter()
            .map(|task| self.execute_task(task))
            .collect()
    }
}
```

**高性能 I/O** (`crates/bioworkflow-io`):
```rust
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use memmap2::Mmap;

pub struct FileManager {
    cache: DashMap<PathBuf, Arc<Mmap>>,
}

impl FileManager {
    pub async fn read_cached(&self, path: &Path) -> Result<Arc<Mmap>> {
        // 内存映射文件缓存
    }
}
```

**任务调度器** (`crates/bioworkflow-scheduler`):
```rust
pub trait Scheduler: Send + Sync {
    fn schedule(&self, tasks: Vec<Task>) -> SchedulePlan;
}

pub struct PriorityScheduler {
    resource_manager: Arc<ResourceManager>,
}

impl Scheduler for PriorityScheduler {
    fn schedule(&self, tasks: Vec<Task>) -> SchedulePlan {
        // 基于资源可用性的智能调度
    }
}
```

#### 3.2 Python 绑定

```rust
// crates/bioworkflow-python/src/lib.rs
use pyo3::prelude::*;

#[pymodule]
fn bioworkflow(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyDagEngine>()?;
    m.add_class::<PyTaskScheduler>()?;
    m.add_class::<PyFileManager>()?;
    Ok(())
}

#[pyclass]
struct PyDagEngine {
    inner: DagEngine,
}

#[pymethods]
impl PyDagEngine {
    #[new]
    fn new() -> Self {
        Self { inner: DagEngine::new() }
    }

    fn execute(&self, py: Python) -> PyResult<PyObject> {
        // 释放 GIL 允许并行执行
        py.allow_threads(|| {
            self.inner.execute()
        })
    }
}
```

#### 3.3 性能基准测试

```rust
// benches/dag_benchmark.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use bioworkflow_dag::DagEngine;

fn dag_execution_benchmark(c: &mut Criterion) {
    c.bench_function("dag_100_nodes", |b| {
        let engine = create_test_dag(100);
        b.iter(|| engine.execute())
    });

    c.bench_function("dag_1000_nodes", |b| {
        let engine = create_test_dag(1000);
        b.iter(|| engine.execute())
    });
}

criterion_group!(benches, dag_execution_benchmark);
criterion_main!(benches);
```

---

### Phase 4: 集成与测试 (Week 9-10)

#### 4.1 端到端测试

```python
# tests/e2e/test_workflow_execution.py
import pytest
import asyncio

@pytest.mark.asyncio
async def test_complete_workflow():
    """测试完整的 Snakemake 工作流执行"""
    # 1. 通过 API 上传工作流
    workflow_id = await upload_workflow("test_workflow.smk")

    # 2. 创建 miniforge 环境
    env_id = await create_environment("test_env", ["python=3.11", "snakemake"])

    # 3. 执行工作流
    execution_id = await execute_workflow(workflow_id, env_id)

    # 4. 等待完成并验证
    result = await wait_for_completion(execution_id, timeout=300)
    assert result.status == "completed"
    assert result.output_files_exist()
```

#### 4.2 性能测试

```python
# tests/performance/test_throughput.py
import time
import statistics

class TestThroughput:
    """性能吞吐量测试"""

    def test_dag_execution_throughput(self):
        """测试 DAG 执行吞吐量"""
        execution_times = []

        for i in range(100):
            start = time.perf_counter()
            execute_test_dag(nodes=50)
            elapsed = time.perf_counter() - start
            execution_times.append(elapsed)

        avg_time = statistics.mean(execution_times)
        throughput = 1 / avg_time  # workflows per second

        print(f"平均执行时间: {avg_time:.3f}s")
        print(f"吞吐量: {throughput:.2f} workflows/second")

        # 性能回归检查
        assert throughput > 10, f"吞吐量低于预期: {throughput}"
```

#### 4.3 部署验证

```bash
#!/bin/bash
# scripts/verify_deployment.sh

echo "=== 部署验证 ==="

# 1. 检查所有服务健康状态
echo "检查服务健康状态..."
curl -sf http://localhost:8001/health || exit 1  # miniforge
curl -sf http://localhost:8002/health || exit 1  # knowledge
curl -sf http://localhost:8003/health || exit 1  # mcp
curl -sf http://localhost:50051 || exit 1        # workflow (gRPC)

# 2. 端到端功能测试
echo "运行端到端测试..."
pytest tests/e2e/ -v || exit 1

# 3. 性能基准测试
echo "运行性能测试..."
pytest tests/performance/ -v || exit 1

echo "=== 部署验证通过 ==="
```

---

## 📊 进度追踪

| Phase | 任务 | 状态 | 完成度 |
|-------|------|------|--------|
| Phase 1 | 项目目录结构创建 | 🔄 进行中 | 20% |
| Phase 1 | Miniforge 服务实现 | ⏳ 待开始 | 0% |
| Phase 1 | Rust 开发环境设置 | ⏳ 待开始 | 0% |
| Phase 2 | 微服务拆分 | ⏳ 待开始 | 0% |
| Phase 2 | 服务间通信实现 | ⏳ 待开始 | 0% |
| Phase 3 | DAG 引擎 (Rust) | ⏳ 待开始 | 0% |
| Phase 3 | I/O 模块 (Rust) | ⏳ 待开始 | 0% |
| Phase 3 | Python 绑定 | ⏳ 待开始 | 0% |
| Phase 4 | 端到端测试 | ⏳ 待开始 | 0% |
| Phase 4 | 部署验证 | ⏳ 待开始 | 0% |

---

## 📝 下一步行动

1. **创建 Rust Workspace 配置** (`rust/Cargo.toml`)
2. **创建 miniforge-service** Python 微服务框架
3. **配置 gRPC/Protobuf** 服务间通信
4. **实现基础 DAG 引擎** (Rust)

---

**创建时间**: 2024-02-20
**最后更新**: 2024-02-20
**版本**: v0.1.0-alpha
