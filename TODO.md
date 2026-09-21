# TODO

## 进行中

## 待办
- [ ] 阶段 2：实现 RAGFlowKB（独立的 KnowledgeBase 子类），增加本地切换开关 — 优先级：高
- [ ] 在 .gitignore 补全 `.mypy_cache/`、`.ruff_cache/`、`.DS_Store`（Minor 建议） — 优先级：低
- [ ] 在 README.md 补充 `make test-upload` 一键启动+测试+关闭流程（Minor 建议） — 优先级：低
- [ ] 给 `src/bailian_rag_demo/app/agent.py` 加单元测试（Minor 建议，LocalAgent 当前 0% 覆盖） — 优先级：中
- [ ] ruff 静态检查：`tests/test_api.py` 等未使用 `import pytest` 等清理 — 优先级：低
- [ ] 测试断言 `tests/test_bailian_kb.py:57` 中 `or True` 永远为真，应收紧 — 优先级：中

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