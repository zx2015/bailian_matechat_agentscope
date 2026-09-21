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
          :avatar-config="{ name: 'me' }"
        ></McBubble>
        <McBubble
          v-else
          :content="msg.content"
          :avatar-config="{ imgSrc: 'https://matechat.gitcode.com/logo.svg' }"
          :loading="msg.loading"
        ></McBubble>
      </template>
    </McLayoutContent>

    <div class="shortcut" style="display: flex; align-items: center; gap: 8px">
      <McPrompt
        v-if="!startPage"
        :list="simplePrompt"
        direction="horizontal"
        style="flex: 1"
        @item-click="(e: any) => onSubmit(e.label)"
      ></McPrompt>
      <button class="new-conversation-btn" title="新建对话" @click="newConversation">
        + 新建对话
      </button>
    </div>

    <McLayoutSender>
      <McInput
        :value="inputValue"
        :max-length="2000"
        @change="(e: string) => (inputValue = e)"
        @submit="onSubmit"
      >
        <template #extra>
          <div class="input-foot-wrapper">
            <span class="input-foot-maxlength">{{ inputValue.length }}/2000</span>
          </div>
        </template>
      </McInput>
    </McLayoutSender>
  </McLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue';

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

<style scoped>
.container {
  height: 100vh;
}
.content-container {
  padding: 16px;
}
.new-conversation-btn {
  white-space: nowrap;
  cursor: pointer;
}
</style>
