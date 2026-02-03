# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-02-03

### Added
- 核心架构初始化
  - SQLAlchemy 异步数据库模型（User, Pipeline, Document等）
  - Pydantic 配置管理
  - 依赖注入容器，支持单例/瞬态/作用域生命周期
  - 事件总线系统，实现模块解耦

- 认证模块
  - JWT Token 认证和权限检查
  - Token 刷新和角色权限控制
  - 高性能异步 Token 验证机制

- 缓存服务
  - 内存缓存后端，支持高并发访问
  - 装饰器缓存支持
  - TTL 过期、标签批量删除
  - 序列化/反序列化支持

- Snakemake 引擎
  - 异步工作流执行
  - 并发控制（信号量）
  - 取消功能和资源限制
  - 执行状态跟踪和进度回调

- 流水线服务
  - 完整的 CRUD 操作
  - 异步执行管理
  - 执行状态跟踪
  - 事件总线集成

- Conda 服务
  - 环境生命周期管理
  - 包安装/卸载/搜索
  - 频道配置管理

- 主应用优化
  - 全局异常处理和请求日志中间件
  - Gzip 压缩提升传输性能
  - 详细健康检查端点
  - 生产环境优化配置

### Features
- 模块化高并发设计
- 完全解耦的架构
- 高性能异步处理
- 可扩展的插件系统

[0.0.1]: https://github.com/bioworkflow-platform/bioworkflow/releases/tag/v0.0.1
