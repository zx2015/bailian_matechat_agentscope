# TODO

## 进行中

## 待办
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
