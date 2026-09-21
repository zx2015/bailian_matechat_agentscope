# TODO

## 进行中

## 待办
- [ ] **【需用户决定】"政策法规"知识库（IndexId=4e25svhqsl）的 4 篇 PDF 均用 `DOCMIND`（图像解析）建索引，检索片段 `Text` 恒为空，无法用于当前纯文本 RAG 流程** — 需要用户决定：① 重新配置解析方式为可提取文本的方式并重建索引；② 或上传纯文本/Markdown 文档（如 `examples/sample_docs/`）到新知识库做验证；③ 或接受当前"检索为空→模型用通用知识回答"的降级行为 — 优先级：高
- [ ] 阶段 2：实现 RAGFlowKB（独立的 KnowledgeBase 子类），增加本地切换开关 — 优先级：高
- [ ] 给 `src/bailian_rag_demo/app/agent.py`（终端调试循环）加单元测试 — 优先级：中
- [ ] 给 `frontend/` 加基础组件测试（当前无前端测试覆盖） — 优先级：中
- [ ] 评估 MateChat 前端产物体积（>500KB 的 mermaid 相关 chunk 未做代码分割） — 优先级：低
- [ ] ruff 静态检查：`tests/test_api.py` 等未使用 `import pytest` 等清理 — 优先级：低

## 已完成
- [x] Task 1: 项目骨架 + wheel 配置 — 2026-09-21（commit d5e5e3b）
- [x] Task 2: 配置模块 fail-fast — 2026-09-21（commit a5621b1）
- [x] Task 3: KnowledgeBase + BaiLianKB — 2026-09-21（commit 4bd1363）
- [x] Task 4: Agent API 协议 schemas — 2026-09-21（commit 8125abb）
- [x] Task 5: RuntimeAgent — 2026-09-21（commit b6267d5）
- [x] Task 6: FastAPI 路由 — 2026-09-21（commit cfc77ea）
- [x] Task 7: main.py 入口 — 2026-09-21（commit ee583ee）
- [x] Task 8: LocalAgent 调试 helper — 2026-09-21（commit 12943d7）
- [x] Task 9: Makefile、requirements、samples — 2026-09-21（commit ddbf48e）
- [x] Task 10: README + CLAUDE.md — 2026-09-21（commit 8c21f8a）
- [x] 修复代码审查 4 个 Important 项 — 2026-09-21（commit 32818c9）
- [x] 阶段 1.1：MateChat 前端 + AgentScope 云端统一运行时（RuntimeAgent 改为 ReActAgent + DashScopeChatModel，新增 frontend/，requirements.txt 重新锁定含 agentscope==1.0.21）— 2026-09-21
- [x] 修复 BaiLianKB 两个 bug：① 误将 `top_k` 当作检索文档数传给 `dashscope.Application.call`（该 API 里 `top_k` 实际是 LLM 采样参数，与检索无关），改为传 `doc_reference_type="indexed"` 以正确请求 `doc_references`；② `RAG_TIMEOUT_SEC` 默认值从 5.0s 提高到 10.0s（实测真实应用延迟 1.4s–10.8s 浮动，5s 经常导致检索被静默跳过）— 2026-09-21
- [x] 阶段 1.2：安装官方 `aliyun` CLI 排查百炼知识库绑定问题，定位到真实可用知识库（IndexId=4e25svhqsl）；将 `BaiLianKB` 从 `dashscope.Application.call()`（依赖应用-知识库控制台绑定，无法 API 验证）改为直连 `alibabacloud_bailian20231229` 的 `Retrieve` OpenAPI（AK/SK 鉴权），彻底绕开"应用绑定"这层不确定性；发现该知识库 PDF 用 `DOCMIND` 图像解析导致检索片段无文本，代码已过滤处理，需用户决定后续数据侧方案 — 2026-09-21
