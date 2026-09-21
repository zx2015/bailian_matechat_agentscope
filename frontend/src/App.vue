<template>
  <McLayout class="container">
    <McHeader title="Bailian RAG Demo" logo-img="https://matechat.gitcode.com/logo.svg">
      <template #operationArea>
        <div class="operations">
          <i class="icon-helping" title="百炼 RAG + AgentScope + MateChat"></i>
        </div>
      </template>
    </McHeader>

    <McLayoutContent
      v-if="startPage"
      style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px"
    >
      <McIntroduction
        logo-img="https://matechat.gitcode.com/logo2x.svg"
        title="Bailian RAG Demo"
        sub-title="Hi，我是接入了百炼知识库的 RAG 助手"
        :description="description"
      ></McIntroduction>
      <McPrompt
        :list="introPrompt.list"
        :direction="introPrompt.direction"
        class="intro-prompt"
        @item-click="(e: any) => onSubmit(e.label)"
      ></McPrompt>
    </McLayoutContent>

    <McLayoutContent class="content-container" v-else>
      <template v-for="(msg, idx) in messages" :key="idx">
        <McBubble
          v-if="msg.from === 'user'"
          :content="msg.content"
          align="right"
          :avatar-config="{ name: '我' }"
        ></McBubble>
        <McBubble
          v-else
          :content="msg.content"
          :avatar-config="{ imgSrc: 'https://matechat.gitcode.com/logo.svg' }"
          :loading="msg.loading"
        ></McBubble>
      </template>
    </McLayoutContent>

    <div class="shortcut">
      <McPrompt
        v-if="!startPage"
        :list="simplePrompt"
        direction="horizontal"
        style="flex: 1"
        @item-click="(e: any) => onSubmit(e.label)"
      ></McPrompt>
      <Button icon="add" shape="round" size="sm" @click="newConversation">新建对话</Button>
    </div>

    <McLayoutSender>
      <McInput
        :value="inputValue"
        :max-length="2000"
        placeholder="输入你的问题，回车发送…"
        @change="(e: string) => (inputValue = e)"
        @submit="onSubmit"
      >
        <template #extra>
          <div class="input-foot-wrapper">
            <div class="input-foot-left">
              <span class="input-foot-maxlength">{{ inputValue.length }}/2000</span>
            </div>
            <div class="input-foot-right">
              <Button icon="op-clearup" shape="round" size="sm" :disabled="!inputValue" @click="inputValue = ''">
                清空输入
              </Button>
            </div>
          </div>
        </template>
      </McInput>
    </McLayoutSender>
  </McLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Button } from 'vue-devui/button';
import 'vue-devui/button/style.css';

interface ChatMessage {
  from: 'user' | 'assistant';
  content: string;
  loading?: boolean;
}

const description = [
  '本示例通过 MateChat 前端组件，对接部署在阿里云百炼平台上的 AgentScope 智能体，',
  '并由 BaiLianKB 检索百炼知识库为回答提供参考资料（RAG）。',
];

const introPrompt = {
  direction: 'horizontal' as const,
  list: [{ label: '百炼高代码应用是什么？' }, { label: '这个知识库里有哪些文档？' }],
};

const simplePrompt = [{ label: '继续追问' }, { label: '换个问题' }];

const startPage = ref(true);
const inputValue = ref('');
const messages = ref<ChatMessage[]>([]);

// Persist the session id for the lifetime of the tab so multi-turn
// AgentScope memory on the backend (see RuntimeAgent) stays continuous.
const sessionId =
  (crypto as any).randomUUID?.() ?? `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;

async function callProcess(text: string): Promise<string> {
  const resp = await fetch('/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      input: [{ role: 'user', content: [{ type: 'text', text }] }],
      session_id: sessionId,
    }),
  });
  if (!resp.ok) {
    throw new Error(`request failed: ${resp.status}`);
  }
  const data = await resp.json();
  const parts = data?.output?.[0]?.content ?? [];
  return parts.map((p: any) => p.text).join('') || '(空回复)';
}

async function onSubmit(text: string) {
  const query = text?.trim();
  if (!query) return;

  startPage.value = false;
  inputValue.value = '';
  messages.value.push({ from: 'user', content: query });
  const assistantMsg: ChatMessage = { from: 'assistant', content: '', loading: true };
  messages.value.push(assistantMsg);

  try {
    const answer = await callProcess(query);
    assistantMsg.content = answer;
  } catch (err) {
    assistantMsg.content = `请求失败：${(err as Error).message}`;
  } finally {
    assistantMsg.loading = false;
  }
}

function newConversation() {
  startPage.value = true;
  messages.value = [];
  inputValue.value = '';
}
</script>

<style>
body {
  margin: 0;
  background: #f5f6fa;
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    'PingFang SC',
    'Hiragino Sans GB',
    'Microsoft YaHei',
    sans-serif;
}

.container {
  width: min(1000px, 100vw - 40px);
  margin: 20px auto;
  height: calc(100vh - 40px);
  padding: 20px;
  gap: 8px;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}

.content-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: auto;
  padding: 4px 2px;
}

.intro-prompt {
  width: 100%;
  max-width: 640px;
}

.operations {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #71757f;
  font-size: 18px;
}

.shortcut {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 2px;
}

.input-foot-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  height: 100%;
  margin-right: 8px;
}

.input-foot-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-foot-maxlength {
  font-size: 12px;
  color: #71757f;
}
</style>
