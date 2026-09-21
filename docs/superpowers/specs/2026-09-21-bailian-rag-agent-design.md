# 设计规格：百炼高代码 RAG 应用（阶段 1：百炼 RAG）

**日期**：2026-09-21
**状态**：已批准，待撰写实施计划
**作者**：Claude (brainstorming + research)
**项目路径**：`/media/data/git/bailian_demo`

---

## 1. 目标与范围

### 1.1 业务目标

实现一个**阿里云百炼平台高代码应用（Rich Code Application）**，提供 RAG 问答能力。具备：

1. 可在**本地**用 AgentScope 调试（含真实 RAG 检索）
2. 可通过**命令行**（`Makefile` + `runtime-fc-deploy`）打包为 `.whl` 并上传到百炼托管运行
3. 上传后在百炼应用中心可对话、可调用 API（`/process`、`/health`）

### 1.2 范围声明

**本期（阶段 1）范围内**：

- 项目骨架：src-layout Python 包 + pyproject.toml + Makefile
- 百炼高代码应用入口（`main.py`，含 `/health`、`/process`）
- `KnowledgeBase` 抽象接口 + `BaiLianKB` 实现（仅百炼 RAG）
- AgentScope 本地调试 Agent（不要求上传）
- 打包 & 上传命令链
- 单元测试 + 集成测试
- 样例文档（2-3 份通用文本）作为初始 RAG 数据

**不在本期范围内（阶段 2 处理）**：

- `RAGFlowKB` 实现及切换
- 多会话/多用户隔离
- 自定义前端 Spark Design 集成
- MCP 工具接入

---

## 2. 架构

### 2.1 双模式架构

```
┌────────────────────────────────────────────────────────────────────┐
│                    本地开发环境（Python ≥ 3.10）                    │
│                                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ AgentScope    │    │ RAG 抽象层   │    │ FastAPI 应用         │  │
│  │ ReAct Agent  │───▶│ KnowledgeBase├───▶│ main.py (入口)       │  │
│  │ (本地调试)    │    │  interface   │    │ ├─ GET /health       │  │
│  └──────────────┘    └──────┬───────┘    │ └─ POST /process     │  │
│                             │            └──────────┬───────────┘  │
│                             ▼                       ▼              │
│                     ┌──────────────┐       ┌──────────────────────┐│
│                     │ BaiLianKB    │       │ dashscope SDK        ││
│                     │ (阶段1实现)  │       │ (云端运行时等价实现)  ││
│                     └──────────────┘       └──────────────────────┘│
└────────────────────────────────────────────────────────────────────┘
                          │                ▲
                          ▼                │
                  pyproject 构建 wheel      │
                          │                │
                          ▼                │
                  runtime-fc-deploy ────────┘
                  (AgentScope Runtime 1.0.0+)
```

**关键决策**：

- **同一份代码、两种运行模式**：本地直接 `python -m bailian_rag_demo.main`，云端百炼运行时通过同样的入口拉起 FastAPI
- **RAG 抽象**：`KnowledgeBase` 接口隔离检索实现，本地与云端共享接口契约
- **依赖管理**：云端运行时需要 dashscope + 百炼 OpenAPI SDK；AgentScope 仅本地使用，云端 wheel 排除（详见 §6）

### 2.2 模块职责

| 模块 | 职责 |
|------|------|
| `bailian_rag_demo.main` | 启动 FastAPI 应用（含 `/health`、`/process`），是百炼运行时唯一识别的入口 |
| `bailian_rag_demo.app.api` | 路由层：解析 Agent API 协议、调用 agent 层、格式化响应 |
| `bailian_rag_demo.app.agent` | AgentScope Agent 本地实现（仅本地使用） |
| `bailian_rag_demo.app.runtime_agent` | 云端运行时等价实现（dashscope + RAG 注入），保证本地/云端行为一致 |
| `bailian_rag_demo.rag.base` | `KnowledgeBase` 抽象接口 |
| `bailian_rag_demo.rag.bailian_kb` | `BaiLianKB`：通过百炼 OpenAPI 调用知识库检索 |
| `bailian_rag_demo.config` | 环境变量加载与校验（fail-fast） |

---

## 3. 关键设计点

### 3.1 百炼高代码应用硬性约束（来自阿里云官方文档）

| 约束 | 本项目如何满足 |
|------|---------------|
| 必须有 `GET /health` | `app/api.py` 中注册 `@app.get("/health")` |
| 入口文件必须为 `main.py` | 包根目录提供 `main.py`，内含 `app = FastAPI()` 实例 |
| 默认对话接口 `/process` | `app/api.py` 中 `@app.post("/process")` |
| 输入输出遵循 Agent API 协议 | `pydantic` 模型定义 request/response schema |
| Python ≥ 3.10 | `pyproject.toml` 中 `requires-python = ">=3.10"` |
| 依赖必须锁定版本 | `requirements.txt` 由 `pip freeze` 生成 |
| 打包为 `.whl` | `python -m build` 或 `setup.py bdist_wheel` |
| 上传工具 | `runtime-fc-deploy`（由 `agentscope-runtime[deployment]` 提供） |

### 3.2 `KnowledgeBase` 接口

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class RetrievalHit:
    content: str
    source: str
    score: float

class KnowledgeBase(ABC):
    """RAG 后端抽象接口。"""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalHit]:
        """检索语义相关文档。"""

    @abstractmethod
    def add_documents(
        self,
        docs: List[str],
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        """入库（本地阶段使用）。"""

    @abstractmethod
    def name(self) -> str:
        """后端标识，用于日志与 metrics。"""
```

### 3.3 `BaiLianKB` 实现策略

- **本地模式**：通过 `dashscope` SDK 调用 `Application.call()`，传入绑定到指定 RAG 知识库的应用 ID
- **云端模式**：百炼运行时已经在百炼网络内，**无需额外 HTTP 调用**，直接 `dashscope.Application.call(..., app_id=BAILIAN_APP_ID)`
- **配置**：
  - `BAILIAN_APP_ID`：绑定了知识库的应用 ID（必填）
  - `BAILIAN_RAG_TOP_K`：默认 5

### 3.4 `/process` 输入输出契约（Agent API 协议）

**请求**：

```json
{
  "input": [
    {"role": "user", "content": [{"type": "text", "text": "什么是百炼高代码应用？"}]}
  ],
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

**响应**：

```json
{
  "output": [
    {"role": "assistant", "content": [{"type": "text", "text": "..."}]}
  ],
  "session_id": "...",
  "usage": {"input_tokens": 0, "output_tokens": 0}
}
```

**实现位置**：`bailian_rag_demo/app/api.py`，使用 `pydantic.BaseModel` 定义 schema。

### 3.5 配置加载（fail-fast）

`bailian_rag_demo/config.py`：

```python
class Settings:
    DASHSCOPE_API_KEY: str  # 必填
    BAILIAN_APP_ID: str      # 必填（绑定了 RAG 的应用）
    BAILIAN_RAG_TOP_K: int   # 默认 5
    LOG_LEVEL: str           # 默认 INFO
    RAG_TIMEOUT_SEC: float   # 默认 5.0
```

启动时检查必填项，缺失立即 `raise SystemExit(1)` 并 stderr 输出明确缺失项。

### 3.6 命令行与上传流程

通过 `Makefile` 提供：

```makefile
install:        ## 安装依赖
	pip install -r requirements.txt

dev:            ## 本地启动（uvicorn 热重载）
	uvicorn bailian_rag_demo.main:app --reload --host 127.0.0.1 --port 8000

test:           ## 跑测试
	pytest tests/ -v

test-upload:    ## 本地 curl 测试 /health 和 /process
	bash scripts/test_local.sh

build:          ## 打 whl
	python -m build

upload:         ## 上传到百炼（make upload NAME=my-agent）
	runtime-fc-deploy --deploy-name $(NAME) --whl-path dist/*.whl

update:         ## 更新已部署应用（make update APP_ID=xxx）
	runtime-fc-deploy --update $(APP_ID) --whl-path dist/*.whl

clean:          ## 清理构建产物
	rm -rf build/ dist/ *.egg-info src/*.egg-info
```

### 3.7 错误处理

| 场景 | 行为 |
|------|------|
| `/health` 失败 | 百炼判定启动失败 → main.py 启动后**必须立即**注册健康路由且不阻塞 |
| `DASHSCOPE_API_KEY` 缺失 | 启动 fail-fast，stderr 输出 "ERROR: DASHSCOPE_API_KEY is required" |
| `BAILIAN_APP_ID` 缺失 | 启动 fail-fast |
| RAG 检索超时（>5s） | 降级为空 context，不阻塞主 LLM 调用，记录 warning 日志 |
| 检索 top_k=0 | 允许，prompt 中不带 RAG 上下文 |
| whl 上传失败 | 捕获 `RuntimeError`，打印阿里云官方排查提示（来自 API 开发指南 FAQ） |

---

## 4. 目录结构

```
bailian_demo/
├── src/
│   └── bailian_rag_demo/              # 可打包为 .whl 的 Python 包
│       ├── __init__.py
│       ├── main.py                     # ⭐ 百炼运行时入口（顶层 app 实例）
│       ├── app/
│       │   ├── __init__.py
│       │   ├── api.py                  # FastAPI 路由：/health、/process
│       │   ├── schemas.py              # Agent API 协议 pydantic 模型
│       │   ├── agent.py                # AgentScope 本地调试 Agent
│       │   └── runtime_agent.py        # 云端运行时等价实现（dashscope）
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── base.py                 # KnowledgeBase 抽象接口 + RetrievalHit
│       │   └── bailian_kb.py           # BaiLianKB 实现
│       ├── config.py                   # 环境变量加载与校验
│       └── version.py
├── scripts/
│   ├── setup_env.sh                    # 环境变量模板（仅 echo，不存真实值）
│   ├── upload_to_bailian.sh            # 包装 runtime-fc-deploy 的可选脚本
│   └── test_local.sh                   # 本地 curl 快速测试
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # pytest fixtures
│   ├── test_api.py                     # FastAPI 集成测试（TestClient）
│   ├── test_bailian_kb.py              # BaiLianKB 单元测试（mock）
│   └── test_config.py                  # 配置加载与 fail-fast 测试
├── examples/
│   └── sample_docs/                    # 通用样例文档
│       ├── product_faq.md
│       └── technical_guide.md
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-09-21-bailian-rag-agent-design.md  # 本文档
├── .env.example                        # 环境变量示例（不含真实密钥）
├── .gitignore
├── pyproject.toml                      # 现代 Python 打包
├── requirements.txt                    # 锁定版本（pip freeze 生成）
├── Makefile
├── README.md
└── CLAUDE.md
```

---

## 5. 数据流：用户提问 → RAG → 回复

```
[Client] ──POST /process──▶ [FastAPI api.py]
                              │
                              ├─ 解析 request body（schemas.py）
                              ▼
                          [runtime_agent.run]
                              │
                              ├─ KnowledgeBase.retrieve(query, top_k=5)
                              │     │
                              │     ▼
                              │  [BaiLianKB → 百炼 OpenAPI → 检索]
                              │     │
                              │     ▼
                              │  List[RetrievalHit]
                              │
                              ├─ 拼接 prompt：system + context(RAG) + user_query
                              │
                              ├─ dashscope.Generation.call(...)
                              │
                              ▼
                          [组装 Agent API 响应]
                              │
[Client] ◀──200 OK──────────┘
```

**超时与降级**：检索步骤独立 try/except，超时或异常时以 `List[RetrievalHit] = []` 继续调用 LLM，记录 warning。

---

## 6. 依赖管理

### 6.1 阶段 1 所需依赖

| 依赖 | 用途 | 锁定策略 |
|------|------|----------|
| `fastapi` | Web 框架 | `==` 锁 |
| `uvicorn[standard]` | ASGI 服务器（本地） | `==` 锁 |
| `pydantic` | 数据模型 | `==` 锁 |
| `dashscope` | 百炼 SDK（含 RAG、Generation） | `==` 锁 |
| `agentscope` | 本地调试 Agent | `==` 锁 |
| `httpx` | HTTP 客户端（如需） | `==` 锁 |
| `pytest` | 测试 | `==` 锁（dev） |
| `pytest-asyncio` | 异步测试 | `==` 锁（dev） |
| `build` | 构建 whl | `==` 锁（dev） |

### 6.2 关键约束

- `agentscope` 仅本地使用，云端 wheel **包含**它也无害，但**主调用路径必须不依赖 AgentScope**（用 `runtime_agent`）
- 所有版本用 `==` 锁，从干净的 venv 中 `pip freeze > requirements.txt`

### 6.3 Python 版本

`pyproject.toml` 中：

```toml
[project]
requires-python = ">=3.10"
```

---

## 7. 测试策略

### 7.1 测试金字塔

| 层级 | 内容 | 工具 | 是否需要外部凭据 |
|------|------|------|------------------|
| 单元 | `BaiLianKB.retrieve` mock | pytest + unittest.mock | 否 |
| 单元 | config fail-fast 逻辑 | pytest | 否 |
| 集成 | `/health` 返回 "OK" | FastAPI TestClient | 否 |
| 集成 | `/process` 请求/响应契约 | TestClient + mock RAG | 否 |
| 端到端（可选） | 真实 `/process` 调用百炼 | 标记 `@pytest.mark.e2e`，默认跳过 | 是 |

### 7.2 必须满足的覆盖率

- `rag/base.py`：接口定义，无逻辑，跳过
- `rag/bailian_kb.py`：≥ 80%
- `app/api.py`：≥ 80%
- `config.py`：≥ 90%（fail-fast 必须全覆盖）

### 7.3 关键测试用例（必须写）

1. `test_health_returns_ok` — `GET /health` 返回 "OK"
2. `test_process_with_rag_context` — mock RAG 命中 → 响应包含 RAG 上下文
3. `test_process_without_rag_hits` — RAG 返回空 → 仍正常返回（降级）
4. `test_process_invalid_request` — 输入不符合 schema → 422
5. `test_config_missing_api_key` — 缺失 DASHSCOPE_API_KEY → SystemExit
6. `test_bailian_kb_retrieve` — mock 外部 API → 正确解析返回
7. `test_bailian_kb_timeout` — 模拟超时 → 返回空 list + warning 日志

---

## 8. 文档与交付物

| 文档 | 内容 |
|------|------|
| `README.md` | 项目简介、环境准备、Makefile 用法、上传步骤、常见问题 |
| `CLAUDE.md` | 给未来 Claude Code 实例的指引（命令、架构、约定） |
| `.env.example` | 环境变量示例及说明 |
| `docs/superpowers/specs/` | 本设计文档 |

---

## 9. 验收标准（Definition of Done）

- [ ] `make install` 在干净 venv 中成功
- [ ] `make test` 全部通过
- [ ] `make dev` 启动后 `curl 127.0.0.1:8000/health` 返回 "OK"
- [ ] `curl -X POST .../process` 按 Agent API 协议返回正确结构
- [ ] `make build` 产出 `dist/*.whl`
- [ ] `make upload NAME=test-rag-agent`（前提：已配置 AK/SK/Workspace）成功在百炼控制台看到应用
- [ ] 上传后百炼应用 `/health` 返回 200
- [ ] 百炼应用调试面板可对话
- [ ] 所有代码无 AgentScope 硬依赖（即云端运行时不必安装 AgentScope 也可运行——保留为软依赖亦可，但调用路径不能依赖）

---

## 10. 风险与缓解

| 风险 | 缓解 |
|------|------|
| `runtime-fc-deploy` 安装失败或文档过时 | 在 `scripts/upload_to_bailian.sh` 中打印命令手动备用；同时 README 列出原始命令 |
| 百炼 RAG OpenAPI 鉴权复杂度 | 用 `dashscope.Application.call(..., app_id=...)` 简化鉴权，无需直接 HTTP |
| whl 体积过大 | 暂不处理；阶段 2 评估排除 AgentScope |
| `main.py` 必须位于包根目录（src-layout 兼容性） | 验证：在 `pyproject.toml` 中配置 `package-dir` 与 `packages`，确保 `main.py` 被 wheel 包含并可通过 `bailian_rag_demo.main:app` 引用 |
| 阿里云 AK/SK 误提交 | `.gitignore` 排除 `.env`；`README.md` 明确警示 |

---

## 11. 后续阶段预告（不在本次实施）

- **阶段 2**：RAGFlowKB 实现 + 抽象切换；增加本地命令行工具管理知识库索引
- **阶段 3**：Spark Design 自定义前端 WebUI
- **阶段 4**：MCP 工具接入（如联网搜索、计算器）