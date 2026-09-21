<template>
  <!-- 拖动条：独立于侧边栏容器之外，不受 overflow:hidden 影响 -->
  <div
    v-if="sidebar.visible"
    class="resize-handle"
    :style="{ right: sidebar.width + 'px' }"
    :class="{ 'resize-active': sidebar.resizing }"
    @mousedown="sidebar.startResize"
  >
    <div class="resize-grip"></div>
  </div>

  <transition name="sidebar-slide">
    <div
      v-if="sidebar.visible"
      class="sidebar-container"
      :style="{ width: sidebar.width + 'px' }"
    >
      <!-- 顶部标题栏 -->
      <div class="sidebar-header">
        <div class="header-left">
          <span class="header-icon">⚖️</span>
          <span class="header-title">智能助手</span>
        </div>
        <div class="header-right">
          <button class="header-btn" @click="sidebar.clearMessages" title="清空对话">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M8 6V4h8v2M5 6v12a2 2 0 002 2h10a2 2 0 002-2V6" />
            </svg>
          </button>
          <button class="header-btn close-btn" @click="sidebar.close" title="关闭">
            ✕
          </button>
        </div>
      </div>

      <!-- 消息区域 -->
      <div class="messages-area" ref="messagesArea">
        <!-- 欢迎消息（空状态） -->
        <div v-if="sidebar.messages.length === 0" class="welcome-message">
          <div class="welcome-icon">👋</div>
          <h3>你好！我是智能法律助手</h3>
          <p>有任何劳动仲裁相关问题，欢迎随时咨询我。</p>
        </div>

        <!-- 消息列表 -->
        <div
          v-for="(msg, idx) in sidebar.messages"
          :key="idx"
          class="message-wrapper"
        >
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="message user-message">
            <div class="message-content">{{ msg.text }}</div>
          </div>

          <!-- 助手消息 -->
          <div v-else class="message assistant-message">
            <img src="/src/assets/lawyer.png" class="avatar-img" alt="助手" />
            <div class="message-body">
              <div class="reply-content markdown-body" v-html="parseMarkdown(msg.text)"></div>
            </div>
          </div>
        </div>

        <!-- 加载指示器 -->
        <div v-if="sidebar.sending" class="message-wrapper">
          <div class="message assistant-message">
            <img src="/src/assets/lawyer.png" class="avatar-img" alt="助手" />
            <div class="message-body">
              <div class="typing">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入区 -->
      <div class="input-area">
        <div class="input-wrapper">
          <textarea
            v-model="inputText"
            placeholder="请输入您的问题..."
            rows="1"
            @keydown.enter.exact.prevent="sendMessage"
            @input="autoResize"
            ref="inputArea"
          ></textarea>
          <button
            class="send-btn"
            @click="sendMessage"
            :disabled="!inputText.trim() || sidebar.sending"
          >
            <span class="send-icon">↑</span>
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, nextTick, watch } from "vue";
import { useSidebarStore } from "../stores/sidebar";
import http from "../api/http";

const sidebar = useSidebarStore();
const inputText = ref("");
const messagesArea = ref(null);
const inputArea = ref(null);

// 调用后端代理接口（http.js baseURL 已是 /api，不要重复加）
const SIDEBAR_API_URL = "/agent/sidebar-chat";

// Markdown 解析函数（轻量实现）
function parseMarkdown(text) {
  if (!text) return "";

  let html = text
    // 转义 HTML
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // 加粗
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    // 斜体
    .replace(/_(.+?)_/g, "<em>$1</em>")
    // 行内代码
    .replace(/`(.+?)`/g, "<code>$1</code>")
    // 标题
    .replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 class="md-h2">$1</h2>')
    // 分隔线
    .replace(/^---$/gm, "<hr>")
    // 列表
    .replace(/^- (.+)$/gm, '<li class="md-li">$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li class="md-li">$1</li>')
    // 引用
    .replace(/^> (.+)$/gm, '<blockquote class="md-blockquote">$1</blockquote>')
    // 换行
    .replace(/\n/g, "<br>");

  // 包装连续 li 为 ul
  html = html.replace(/(<li class="md-li">.*?<\/li>(?:<br>)?)+/gs, '<ul class="md-ul">$&</ul>');

  // 清理多余 br
  html = html.replace(/(<br>){3,}/g, "<br><br>");

  return html;
}

function autoResize(e) {
  const textarea = e.target;
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || sidebar.sending) return;

  // 添加用户消息
  sidebar.addUserMessage(text);
  inputText.value = "";
  sidebar.setSending(true);

  // 滚动到底部
  await nextTick();
  scrollToBottom();

  try {
    // 构建历史消息
    const history = sidebar.messages
      .slice(0, -1) // 排除刚加的
      .map((m) => ({
        role: m.role,
        content: m.text,
      }));

    // 调用后端代理接口
    const { data } = await http.post(SIDEBAR_API_URL, {
      question: text,
      history: history.length > 0 ? history : [],
    });

    // 解析响应
    let replyText = data.reply || "抱歉，我暂时无法回答这个问题。";
    sidebar.addAssistantMessage(replyText);
  } catch (err) {
    console.error("智能助手调用失败:", err);
    let errMsg = "网络连接失败，请稍后重试。";
    if (err.response?.data?.detail) {
      errMsg = err.response.data.detail;
    } else if (err.message) {
      errMsg = err.message;
    }
    sidebar.addAssistantMessage(`⚠️ ${errMsg}`);
  } finally {
    sidebar.setSending(false);
    await nextTick();
    scrollToBottom();
    // 重置输入框高度
    if (inputArea.value) {
      inputArea.value.style.height = "auto";
    }
  }
}

function scrollToBottom() {
  if (messagesArea.value) {
    messagesArea.value.scrollTop = messagesArea.value.scrollHeight;
  }
}

// 监听消息变化，自动滚动
watch(
  () => sidebar.messages.length,
  async () => {
    await nextTick();
    scrollToBottom();
  }
);
</script>

<style scoped>
/* 侧边栏容器 */
.sidebar-container {
  position: fixed;
  top: 0;
  right: 0;
  height: 100vh;
  background: #f7f8fa;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 拖动条：独立固定定位，始终位于侧边栏左边缘 */
.resize-handle {
  position: fixed;
  top: 0;
  width: 16px;
  height: 100vh;
  cursor: col-resize;
  z-index: 1001;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 12px;
  transition: background-color 0.15s;
}
.resize-handle:hover {
  background-color: rgba(57, 106, 246, 0.08);
}
.resize-handle.resize-active {
  background-color: rgba(57, 106, 246, 0.12);
}
/* 拖动图标：双向箭头 */
.resize-handle::before {
  content: "⇄";
  font-size: 13px;
  color: #c0c4cc;
  margin-bottom: 4px;
  transition: color 0.15s;
  pointer-events: none;
  user-select: none;
}
.resize-handle:hover::before,
.resize-handle.resize-active::before {
  color: #396af6;
}
.resize-grip {
  width: 3px;
  height: 32px;
  background: #c0c4cc;
  border-radius: 2px;
  transition: background-color 0.15s;
  pointer-events: none;
}
.resize-handle:hover .resize-grip,
.resize-handle.resize-active .resize-grip {
  background: #396af6;
}

/* 顶部标题栏 */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 52px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-icon {
  font-size: 20px;
}
.header-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}
.header-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  transition: all 0.2s;
}
.header-btn:hover {
  background: #f5f7fa;
  color: #303133;
}
.close-btn {
  font-size: 16px;
  font-weight: 600;
}

/* 消息区域 */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
  scroll-behavior: smooth;
}

/* 欢迎消息 */
.welcome-message {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}
.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
.welcome-message h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 8px;
}
.welcome-message p {
  font-size: 13px;
  color: #909399;
}

/* 消息包装器 */
.message-wrapper {
  margin-bottom: 20px;
}

/* 用户消息 */
.user-message {
  display: flex;
  justify-content: flex-end;
}
.user-message .message-content {
  max-width: 80%;
  padding: 10px 16px;
  background: linear-gradient(135deg, #396af6, #2952d8);
  color: #fff;
  border-radius: 18px 18px 4px 18px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

/* 助手消息 */
.assistant-message {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.avatar-img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
.message-body {
  flex: 1;
  max-width: calc(100% - 50px);
}
.reply-content {
  padding: 12px 16px;
  background: #fff;
  border-radius: 4px 18px 18px 18px;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* Markdown 样式 */
.markdown-body :deep(.md-h2) {
  font-size: 15px;
  font-weight: 600;
  color: #1e40af;
  margin: 12px 0 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid #dbeafe;
}
.markdown-body :deep(.md-h3) {
  font-size: 14px;
  font-weight: 600;
  color: #7c3aed;
  margin: 10px 0 6px;
}
.markdown-body :deep(.md-h4) {
  font-size: 14px;
  font-weight: 600;
  color: #0891b2;
  margin: 8px 0 4px;
}
.markdown-body :deep(strong) {
  color: #1e40af;
  font-weight: 600;
}
.markdown-body :deep(.md-ul) {
  list-style: none;
  padding: 0;
  margin: 8px 0;
}
.markdown-body :deep(.md-li) {
  position: relative;
  padding: 4px 0 4px 16px;
  margin: 2px 0;
  border-left: 2px solid #3b82f6;
  background: #f8fafc;
  border-radius: 0 6px 6px 0;
  margin-left: 4px;
  font-size: 13px;
}
.markdown-body :deep(.md-blockquote) {
  border-left: 3px solid #f59e0b;
  background: #fffbeb;
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 0 8px 8px 0;
  font-style: italic;
  color: #92400e;
}
.markdown-body :deep(code) {
  background: #f1f5f9;
  color: #dc2626;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
}
.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 12px 0;
}

/* 加载动画 */
.typing {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 4px 18px 18px 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.dot {
  width: 7px;
  height: 7px;
  background: #ccc;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 输入区域 */
.input-area {
  padding: 12px 16px 16px;
  background: #fff;
  border-top: 1px solid #eee;
  flex-shrink: 0;
}
.input-wrapper {
  display: flex;
  align-items: flex-end;
  position: relative;
}
.input-wrapper textarea {
  flex: 1;
  padding: 10px 50px 10px 16px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  max-height: 120px;
  font-family: inherit;
  width: 100%;
}
.input-wrapper textarea:focus {
  border-color: #396af6;
  box-shadow: 0 0 0 3px rgba(57, 106, 246, 0.1);
}
.send-btn {
  position: absolute;
  right: 6px;
  bottom: 6px;
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #396af6, #2952d8);
  color: #fff;
  border: none;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(57, 106, 246, 0.3);
}
.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
.send-icon {
  font-size: 18px;
  line-height: 1;
}

/* 滑入滑出动画 */
.sidebar-slide-enter-active,
.sidebar-slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.sidebar-slide-enter-from,
.sidebar-slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
.sidebar-slide-enter-to,
.sidebar-slide-leave-from {
  transform: translateX(0);
  opacity: 1;
}
</style>
