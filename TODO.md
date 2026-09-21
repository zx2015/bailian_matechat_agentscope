# TODO

## 进行中

## 待办
- [ ] **【需用户操作】登录百炼控制台，为已部署应用（Deploy ID `24927e7f-143a-4d95-b097-c7d0d7d013d9`）配置环境变量** — `DASHSCOPE_API_KEY`、`ALIBABA_CLOUD_ACCESS_KEY_ID`/`_SECRET`、`BAILIAN_WORKSPACE_ID`、`BAILIAN_INDEX_ID` 等；`runtime-fc-deploy --whl-path` 模式无法通过命令行传递这些变量，`config.py` 是 fail-fast 设计，配置好之前应用会启动失败 — 优先级：高
- [ ] 配置好环境变量后，验证百炼应用中心里该应用的 `/health`、对话面板是否正常 — 优先级：高
- [ ] 评估是否迁移到 AgentScope 2.0 自带的部署能力（`agentscope-runtime` 仓库已被官方标记 archived，长期看 `runtime-fc-deploy` 可能停止维护）— 优先级：中
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
- [x] **RAG 检索已验证真正生效**：用户将知识库重新配置为文本可提取的索引方式（新 IndexId=4hzya44m4u，embedding 模型改为 `text-embedding-v4`），`Retrieve` 返回 5 条真实文本片段（score 0.77~0.88）；`/process` 端到端验证：`input_tokens` 从约 60 跃升到 1800~2400+（证明真实上下文被注入），回答明确标注"根据提供的资料"，且能准确回答文档具体细节（如"中国工会章程是2023年修改的"），与知识库真实文档内容一致 — 2026-09-21
- [x] 修复 MateChat 前端 Vue 响应式 bug：`onSubmit` 中在 push 后直接修改原始对象引用（而非通过数组下标访问的响应式代理），导致界面永远停留在加载状态，看起来"发消息无反应"；改为通过 `messages.value[idx]` 修改，用真实无头浏览器验证修复生效 — 2026-09-21
- [x] 新增引用来源展示：`RuntimeAgent` 检索片段现在带来源标签拼进 prompt，系统提示要求模型注明引用文档；`ProcessResponse` 新增 `references` 字段（按来源去重、按分数排序）；MateChat 界面在回答下方显示"参考资料：文档名（相关度）"；用真实问题验证回答正确引用了具体政策文件名 — 2026-09-21
- [x] 阶段 1.3：真实部署到百炼平台。发现并修复关键 bug——`pyproject.toml` 原来没有 `[project.dependencies]`，而 `runtime-fc-deploy --whl-path` 只上传 wheel 本身、不读 requirements.txt，导致云端装不到任何依赖；补上直接依赖声明后用真实凭据部署成功（Deploy ID `24927e7f-143a-4d95-b097-c7d0d7d013d9`，`agentscope list` 显示 running）。同时发现部署工具本机需要额外装 `alibabacloud-oss-v2`/`alibabacloud-credentials`/`alibabacloud-tea-util`，以及部署工具用的是 `MODELSTUDIO_WORKSPACE_ID`（区别于应用运行时用的 `BAILIAN_WORKSPACE_ID`）。发现 `--whl-path` 模式无法通过 CLI 传递应用运行时环境变量，需要用户在控制台手动配置 — 2026-09-21
