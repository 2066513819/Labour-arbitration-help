<template>
  <div class="chat-container">
    <!-- 顶部标题栏 -->
    <header class="chat-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.push('/')">
          <span class="back-icon">←</span>
        </button>
        <div class="header-title">
          <span class="title-icon">⚖️</span>
          <span class="title-text">劳动法律咨询</span>
        </div>
      </div>
      <div class="header-right">
        <select v-model="selectedType" class="type-select">
          <option value="">选择劳动者类型</option>
          <option value="regular">正式工</option>
          <option value="dispatch">劳务派遣</option>
          <option value="intern">实习/兼职</option>
          <option value="platform">平台工</option>
          <option value="other_uncertain">帮我做判断</option>
          <option value="case_search">案例检索</option>
          <option value="law_search">法规检索</option>
        </select>
      </div>
    </header>

    <!-- 消息列表 -->
    <div class="messages-area" ref="messagesArea">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="welcome-message">
        <div class="welcome-icon">👋</div>
        <h2>您好，我是劳动法律咨询助手</h2>
        <p>请选择您的劳动者类型，然后描述您遇到的问题</p>
      </div>

      <!-- 消息列表 -->
      <div v-for="(msg, idx) in messages" :key="idx" class="message-wrapper">
        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="message user-message">
          <div class="message-content">{{ msg.text }}</div>
        </div>

        <!-- 助手消息 -->
        <div v-else class="message assistant-message">
          <img src="/src/assets/lawyer.png" class="avatar-img" alt="律师助手" />
          <div class="message-body">
            <!-- 主要回复内容 - Markdown解析 -->
            <div class="reply-content markdown-body" v-if="msg.reply?.interpretation" v-html="parseMarkdown(msg.reply.interpretation)"></div>
            <!-- 法律依据 -->
            <div class="law-refs" v-if="msg.reply?.law_refs?.length">
              <div class="refs-label">📚 相关法律</div>
              <div class="refs-list">
                <span v-for="ref in msg.reply.law_refs" :key="ref" class="ref-tag">{{ ref }}</span>
              </div>
            </div>
            <!-- 建议操作 -->
            <div class="suggestions" v-if="msg.reply?.suggested_actions?.length">
              <div class="suggestions-label">💡 建议操作</div>
              <div class="suggestion-item" v-for="(action, i) in msg.reply.suggested_actions" :key="i">
                {{ action }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载指示器 -->
      <div v-if="sending" class="message-wrapper">
        <div class="message assistant-message">
          <img src="/src/assets/lawyer.png" class="avatar-img" alt="律师助手" />
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
      <!-- 导入案件信息按钮（有历史消息后才显示） -->
      <div class="import-row" v-if="messages.length > 0">
        <div class="import-btn-wrapper">
          <button class="import-btn" @click="toggleImportPanel" :disabled="sending">
            <span>📋</span>
            <span>导入案件信息</span>
          </button>
          <!-- 下拉案件列表 -->
          <div class="import-panel" v-if="showImportPanel">
            <div class="import-panel-header">选择案件导入</div>
            <div class="import-panel-body">
              <div v-if="loadingCases" class="import-loading">加载中...</div>
              <div v-else-if="caseList.length === 0" class="import-empty">
                暂无案件，请先在"我的案件"中创建
              </div>
              <div
                v-for="c in caseList"
                :key="c.id"
                class="import-case-item"
                @click="importCaseInfo(c)"
              >
                <div class="import-case-title">{{ c.title }}</div>
                <div class="import-case-meta">
                  <span v-if="c.entry_date">入职：{{ c.entry_date }}</span>
                  <span v-if="c.quit_date">离职：{{ c.quit_date }}</span>
                  <span v-if="c.average_salary">工资：{{ c.average_salary }}</span>
                  <span v-if="c.bonus_info">奖金：{{ c.bonus_info }}</span>
                  <span v-if="!c.entry_date && !c.quit_date && !c.average_salary && !c.bonus_info" class="no-info">无员工信息</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="input-wrapper">
        <textarea
          v-model="inputText"
          placeholder="请输入您的问题..."
          rows="1"
          @keydown.enter.exact.prevent="sendMessage"
          @input="autoResize"
          ref="inputArea"
        ></textarea>
        <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || sending || !selectedType">
          <span>发送</span>
          <span class="send-icon">↑</span>
        </button>
      </div>
      <div class="input-hint" v-if="!selectedType">
        请先选择劳动者类型
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted, onUnmounted } from "vue";
import { ElMessage } from "element-plus";
import http from "../api/http";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();

const inputText = ref("");
const selectedType = ref(auth.laborerType || "");
const sending = ref(false);
const messages = ref([]);
const messagesArea = ref(null);
const inputArea = ref(null);

// 导入案件信息相关
const showImportPanel = ref(false);
const caseList = ref([]);
const loadingCases = ref(false);

function toggleImportPanel() {
  showImportPanel.value = !showImportPanel.value;
  if (showImportPanel.value && caseList.value.length === 0) {
    fetchCases();
  }
}

async function fetchCases() {
  loadingCases.value = true;
  try {
    const { data } = await http.get("/cases");
    caseList.value = data.items || [];
  } catch (e) {
    ElMessage.error("获取案件列表失败");
  } finally {
    loadingCases.value = false;
  }
}

function importCaseInfo(c) {
  const parts = [];
  if (c.entry_date) parts.push(`入职日期：${c.entry_date}`);
  if (c.quit_date) parts.push(`离职日期：${c.quit_date}`);
  if (c.average_salary) parts.push(`月均工资：${c.average_salary}`);
  if (c.bonus_info) parts.push(`奖金情况：${c.bonus_info}`);
  if (parts.length === 0) {
    ElMessage.warning("该案件无员工信息");
    return;
  }
  inputText.value = parts.join("，") + "。";
  showImportPanel.value = false;
  ElMessage.success("已导入案件信息");
}

// 点击外部关闭导入面板
function handleClickOutside(e) {
  if (showImportPanel.value) {
    const panel = document.querySelector(".import-panel");
    const btn = document.querySelector(".import-btn");
    if (panel && !panel.contains(e.target) && btn && !btn.contains(e.target)) {
      showImportPanel.value = false;
    }
  }
}

// 监听类型变化，同步到 auth store
watch(selectedType, (val) => {
  if (val) {
    auth.laborerType = val;
    localStorage.setItem("laborerType", val);
  }
});

// 简单的Markdown解析函数
function parseMarkdown(text) {
  if (!text) return "";
  
  let html = text
    // 先处理AI返回的 <em> 标签 → 转为 markdown 斜体（必须在HTML转义之前）
    .replace(/<em>/g, '_')
    .replace(/<\/em>/g, '_')
    // 转义HTML特殊字符
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // 处理加粗 **文本** (先处理，避免嵌套问题)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // 处理斜体 _文本_（紧跟加粗之后）
    .replace(/_([^_]+)_/g, '<em class="md-em">$1</em>')
    // 处理行内代码 `code`
    .replace(/`(.+?)`/g, '<code class="md-inline-code">$1</code>')
    // 处理标题（从多到少，避免 #### 被 ### 误匹配）
    .replace(/^##### (.+)$/gm, '<h6 class="md-h6">$1</h6>')
    .replace(/^#### (.+)$/gm, '<h5 class="md-h5">$1</h5>')
    .replace(/^### (.+)$/gm, '<h4 class="md-h4">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="md-h3">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 class="md-h2">$1</h2>')
    // 处理分隔线
    .replace(/^---$/gm, '<hr class="md-hr">')
    // 处理列表项 - item (包括嵌套的**加粗**)
    .replace(/^- \*\*(.+?)\*\*：(.+)$/gm, '<li class="md-li"><strong>$1</strong>：$2</li>')
    .replace(/^- (.+)$/gm, '<li class="md-li">$1</li>')
    // 处理有序列表 1. item
    .replace(/^\d+\. (.+)$/gm, '<li class="md-li">$1</li>')
    // 处理引用块 > text
    .replace(/^> (.+)$/gm, '<blockquote class="md-blockquote">$1</blockquote>')
    // 处理单行换行
    .replace(/\n/g, '<br>')
    // 清理多余br
    .replace(/(<br>){3,}/g, '<br><br>');
  
  // 包装连续的列表项为ul
  html = html.replace(/(<li class="md-li">.*?<\/li>(?:<br>)?)+/gs, '<ul class="md-ul">$&</ul>');
  
  // 包装段落（非标题、非列表、非blockquote的内容）
  const lines = html.split(/(?=<h|<ul|<li|<blockquote|<hr)/g);
  html = lines.map(line => {
    const trimmed = line.trim();
    if (!trimmed) return '';
    if (trimmed.startsWith('<h') || trimmed.startsWith('<ul') || 
        trimmed.startsWith('<li') || trimmed.startsWith('<blockquote') || 
        trimmed.startsWith('<hr')) {
      return trimmed;
    }
    // 清理多余的br在开头和结尾
    return '<p class="md-p">' + trimmed.replace(/^<br>|<br>$/g, '') + '</p>';
  }).join('');
  
  // 清理空段落
  html = html.replace(/<p class="md-p"><\/p>/g, '');
  
  return html;
}

function autoResize(e) {
  const textarea = e.target;
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text) return;
  if (!selectedType.value) {
    ElMessage.warning("请先选择劳动者类型");
    return;
  }
  if (text.length < 1) {
    ElMessage.warning("请输入问题");
    return;
  }

  // 构建历史消息（发送给元器让它记住上下文）
  const history = messages.value.map(msg => ({
    role: msg.role,
    content: msg.reply?.interpretation || msg.text || msg.content
  }));

  console.log(`[前端] 历史消息数: ${history.length}`);

  // 添加用户消息到列表
  messages.value.push({ role: "user", text });
  inputText.value = "";
  sending.value = true;

  // 滚动到底部
  await nextTick();
  scrollToBottom();

  try {
    const { data } = await http.post("/agent/ask", {
      question: text,
      laborer_type: selectedType.value,
      history: history,
    });
    
    messages.value.push({
      role: "assistant",
      reply: data.reply,
    });
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || "咨询失败，请稍后重试");
    messages.value.pop();
  } finally {
    sending.value = false;
    await nextTick();
    scrollToBottom();
  }
}

function scrollToBottom() {
  if (messagesArea.value) {
    messagesArea.value.scrollTop = messagesArea.value.scrollHeight;
  }
}

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f7f8fa;
  width: 100%;
}

/* 顶部标题栏 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: #f5f5f5;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #eee;
}

.back-icon {
  font-size: 18px;
  color: #333;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 24px;
}

.title-text {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-right {
  display: flex;
  align-items: center;
}

.type-select {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 14px;
  color: #333;
  background: #fff;
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
}

.type-select:focus {
  border-color: #396af6;
}

/* 消息区域 */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

/* 欢迎消息 */
.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.welcome-message h2 {
  font-size: 20px;
  color: #333;
  margin-bottom: 8px;
}

.welcome-message p {
  font-size: 14px;
  color: #999;
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
  padding: 12px 16px;
  background: linear-gradient(135deg, #396af6, #2952d8);
  color: #fff;
  border-radius: 18px 18px 4px 18px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
}

/* 助手消息 */
.assistant-message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.avatar-img {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.message-body {
  flex: 1;
  max-width: calc(100% - 60px);
}

.reply-content {
  padding: 14px 18px;
  background: #fff;
  border-radius: 4px 18px 18px 18px;
  font-size: 15px;
  line-height: 1.8;
  color: #333;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 12px;
}

/* 法律依据 */
.law-refs {
  margin-bottom: 12px;
}

.refs-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 6px;
}

.refs-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ref-tag {
  padding: 4px 10px;
  background: #f0f9ff;
  color: #0284c7;
  border-radius: 12px;
  font-size: 12px;
}

/* 建议操作 */
.suggestions {
  padding: 14px 18px;
  background: #f0fdf4;
  border-radius: 12px;
  border: 1px solid #bbf7d0;
}

.suggestions-label {
  font-size: 13px;
  font-weight: 500;
  color: #166534;
  margin-bottom: 8px;
}

.suggestion-item {
  padding: 8px 12px;
  background: #fff;
  border-radius: 8px;
  font-size: 13px;
  color: #333;
  margin-bottom: 6px;
  border-left: 3px solid #22c55e;
}

.suggestion-item:last-child {
  margin-bottom: 0;
}

/* 加载动画 */
.typing {
  display: flex;
  gap: 4px;
  padding: 14px 18px;
  background: #fff;
  border-radius: 4px 18px 18px 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.dot {
  width: 8px;
  height: 8px;
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
  padding: 12px 20px 20px;
  background: #fff;
  border-top: 1px solid #eee;
}

/* 导入案件按钮行 */
.import-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.import-btn-wrapper {
  position: relative;
}

.import-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.import-btn:hover:not(:disabled) {
  background: #dcfce7;
  border-color: #86efac;
}

.import-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 导入案件下拉面板 */
.import-panel {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  width: 340px;
  max-height: 320px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  z-index: 100;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.import-panel-header {
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  border-bottom: 1px solid #f3f4f6;
  background: #fafafa;
}

.import-panel-body {
  overflow-y: auto;
  max-height: 270px;
}

.import-loading,
.import-empty {
  padding: 24px 16px;
  text-align: center;
  font-size: 13px;
  color: #9ca3af;
}

.import-case-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f3f4f6;
}

.import-case-item:last-child {
  border-bottom: none;
}

.import-case-item:hover {
  background: #f0fdf4;
}

.import-case-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.import-case-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: #6b7280;
}

.import-case-meta span {
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
}

.import-case-meta .no-info {
  color: #d1d5db;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 15px;
  line-height: 1.5;
  resize: none;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  max-height: 120px;
  font-family: inherit;
}

.input-wrapper textarea:focus {
  border-color: #396af6;
  box-shadow: 0 0 0 3px rgba(57, 106, 246, 0.1);
}

.send-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #396af6, #2952d8);
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
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
  font-size: 16px;
}

.input-hint {
  text-align: center;
  font-size: 12px;
  color: #f97316;
  margin-top: 8px;
}

/* Markdown 样式 */
.markdown-body {
  padding: 16px 18px;
  background: #fff;
  border-radius: 4px 18px 18px 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 12px;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}

.markdown-body .md-h2 {
  font-size: 16px;
  font-weight: 600;
  color: #1e40af;
  margin: 16px 0 10px;
  padding-bottom: 6px;
  border-bottom: 2px solid #dbeafe;
}

.markdown-body .md-h3 {
  font-size: 15px;
  font-weight: 600;
  color: #7c3aed;
  margin: 14px 0 8px;
}

.markdown-body .md-h4 {
  font-size: 14px;
  font-weight: 600;
  color: #0891b2;
  margin: 12px 0 6px;
}

.markdown-body .md-h5 {
  font-size: 14px;
  font-weight: 500;
  color: #6366f1;
  margin: 10px 0 4px;
}

.markdown-body .md-h6 {
  font-size: 13px;
  font-weight: 500;
  color: #8b5cf6;
  margin: 8px 0 4px;
}

.markdown-body .md-em {
  color: #6b7280;
  font-style: italic;
}

.markdown-body .md-p {
  margin: 8px 0;
  line-height: 1.8;
}

.markdown-body .md-ul {
  list-style: none;
  padding: 0;
  margin: 10px 0;
}

.markdown-body .md-li {
  position: relative;
  padding: 6px 0 6px 20px;
  margin: 4px 0;
  border-left: 3px solid #3b82f6;
  background: #f8fafc;
  padding-left: 12px;
  border-radius: 0 6px 6px 0;
}

.markdown-body .md-inline-code {
  background: #f1f5f9;
  color: #dc2626;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
}

.markdown-body .md-blockquote {
  border-left: 4px solid #f59e0b;
  background: #fffbeb;
  padding: 10px 14px;
  margin: 10px 0;
  border-radius: 0 8px 8px 0;
  font-style: italic;
  color: #92400e;
}

.markdown-body .md-info-box {
  background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%);
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 12px 16px;
  margin: 10px 0;
  color: #1e40af;
}

.markdown-body .md-disclaimer {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 10px 14px;
  margin-top: 12px;
  font-size: 12px;
  color: #92400e;
}

.markdown-body strong {
  color: #1e40af;
  font-weight: 600;
}

.markdown-body .md-hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 16px 0;
}

/* 特殊内容块样式 */
.markdown-body:deep(.md-calc-box) {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border: 1px solid #86efac;
  border-radius: 12px;
  padding: 14px;
  margin: 10px 0;
}

.markdown-body:deep(.md-case-box) {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fca5a5;
  border-radius: 12px;
  padding: 14px;
  margin: 10px 0;
}

.markdown-body:deep(.md-evidence-box) {
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border: 1px solid #fdba74;
  border-radius: 12px;
  padding: 14px;
  margin: 10px 0;
}

/* 修复列表样式 */
.markdown-body .md-ul {
  list-style: none;
  padding: 0;
  margin: 12px 0;
}

.markdown-body .md-ul .md-li {
  position: relative;
  padding: 8px 12px 8px 28px;
  margin: 6px 0;
  background: #f8fafc;
  border-left: 3px solid #3b82f6;
  border-radius: 0 8px 8px 0;
  line-height: 1.6;
}

.markdown-body .md-ul .md-li::before {
  content: "•";
  position: absolute;
  left: 10px;
  color: #3b82f6;
  font-weight: bold;
}

/* 段落间距优化 */
.markdown-body .md-p {
  margin: 10px 0;
  line-height: 1.8;
}

/* 标题间距优化 */
.markdown-body .md-h2,
.markdown-body .md-h3,
.markdown-body .md-h4 {
  margin-top: 18px;
  margin-bottom: 10px;
}

.markdown-body .md-h2:first-child,
.markdown-body .md-h3:first-child {
  margin-top: 0;
}
</style>
