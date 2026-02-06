# 配置指南

本文档详细介绍 BioWorkflow 的配置选项。

## 配置文件

BioWorkflow 支持多种配置方式（按优先级排序）：

1. 环境变量（最高优先级）
2. `.env` 文件
3. 配置文件（`config.yaml`）
4. 默认值（最低优先级）

## 环境变量

### 核心配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `DEBUG` | 调试模式 | `false` | 否 |
| `VERSION` | 应用版本 | `0.1.0` | 否 |
| `ENVIRONMENT` | 运行环境 | `development` | 否 |

### 服务器配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `HOST` | 监听地址 | `0.0.0.0` | 否 |
| `PORT` | 监听端口 | `8000` | 否 |
| `WORKERS` | 工作进程数 | `4` | 否 |

### 数据库配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `DATABASE_URL` | 数据库连接 URL | `sqlite:///./bioworkflow.db` | 否 |

支持的数据库：

- **SQLite**: `sqlite:///./path/to/database.db`
- **PostgreSQL**: `postgresql+asyncpg://user:password@localhost/dbname`
- **MySQL**: `mysql+aiomysql://user:password@localhost/dbname`

### Redis 配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `REDIS_URL` | Redis 连接 URL | `redis://localhost:6379/0` | 否 |

### JWT 认证配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `SECRET_KEY` | JWT 签名密钥 | - | **是** |
| `ALGORITHM` | 签名算法 | `HS256` | 否 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `30` | 否 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 刷新 Token 过期时间（天） | `7` | 否 |

### Snakemake 配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `SNAKEMAKE_WORKDIR` | 工作流工作目录 | `./workflows` | 否 |
| `SNAKEMAKE_CONDA_PREFIX` | Conda 环境目录 | `./conda_envs` | 否 |
| `SNAKEMAKE_DEFAULT_CORES` | 默认核心数 | `4` | 否 |
| `SNAKEMAKE_DEFAULT_MEM_MB` | 默认内存（MB） | `8192` | 否 |

### Conda 配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `CONDA_CHANNELS` | Conda 频道（逗号分隔） | `conda-forge,bioconda,defaults` | 否 |
| `CONDA_TIMEOUT` | 下载超时（秒） | `60` | 否 |

### 知识库配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `ELASTICSEARCH_HOST` | Elasticsearch 主机 | `localhost` | 否 |
| `ELASTICSEARCH_PORT` | Elasticsearch 端口 | `9200` | 否 |
| `ELASTICSEARCH_INDEX_PREFIX` | 索引前缀 | `bioworkflow` | 否 |
| `KNOWLEDGE_BASE_DIR` | 知识库文件目录 | `./knowledge_base` | 否 |

### MCP 配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `MCP_SERVICE_TIMEOUT` | 服务调用超时（秒） | `30` | 否 |
| `MCP_MAX_RETRIES` | 最大重试次数 | `3` | 否 |

### 日志配置

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `LOG_LEVEL` | 日志级别 | `INFO` | 否 |
| `LOG_FILE` | 日志文件路径 | `./logs/bioworkflow.log` | 否 |
| `LOG_ROTATION` | 日志轮转 | `7 days` | 否 |
| `LOG_RETENTION` | 日志保留 | `30 days` | 否 |

## 配置文件

除了环境变量，您还可以使用 YAML 配置文件：

```yaml
# config.yaml
app:
  name: BioWorkflow
  debug: false
  version: 0.1.0

server:
  host: 0.0.0.0
  port: 8000
  workers: 4

database:
  url: sqlite:///./data/bioworkflow.db
  pool_size: 10
  max_overflow: 20

redis:
  url: redis://localhost:6379/0

security:
  secret_key: your-secret-key
  algorithm: HS256
  access_token_expire_minutes: 30

snakemake:
  workdir: ./workflows
  conda_prefix: ./conda_envs
  default_cores: 4
  default_mem_mb: 8192

logging:
  level: INFO
  file: ./logs/bioworkflow.log
  rotation: 7 days
  retention: 30 days
```

加载配置文件：

```bash
# 通过环境变量指定配置文件
export CONFIG_FILE=/path/to/config.yaml

# 或者在 .env 文件中
CONFIG_FILE=/path/to/config.yaml
```

## 配置优先级

配置值的优先级（从高到低）：

1. **环境变量**: `export PORT=9000`
2. **.env 文件**: `PORT=9000`
3. **配置文件**: `config.yaml` 中的值
4. **默认值**: 代码中定义的默认值

## 安全配置检查清单

生产环境部署前，请确认：

- [ ] 修改了默认的 `SECRET_KEY`
- [ ] 关闭了 `DEBUG` 模式
- [ ] 使用了强密码的数据库
- [ ] 启用了 HTTPS
- [ ] 配置了防火墙规则
- [ ] 设置了日志轮转
- [ ] 配置了监控告警

## 故障排除

### 环境变量不生效

```bash
# 检查环境变量是否正确设置
echo $SECRET_KEY

# 重新加载 .env 文件
source .env

# 在 Docker 中检查
 docker exec bioworkflow-app env | grep SECRET
```

### 配置文件解析错误

```bash
# 验证 YAML 语法
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 或者使用 yamllint
yamllint config.yaml
```

### 配置热重载

某些配置支持热重载（无需重启服务）：

```bash
# 发送 SIGHUP 信号触发重载
kill -HUP $(pgrep -f "uvicorn")
```

支持热重载的配置：
- 日志级别
- 某些功能开关
- 限流阈值

不支持热重载的配置（需要重启）：
- 数据库连接
- 端口绑定
- 安全密钥

---

更多配置细节，请参考 [API 文档](../api/index.md) 和 [开发文档](../development/architecture.md)。
