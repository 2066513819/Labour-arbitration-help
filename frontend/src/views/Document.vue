<template>
  <div class="min-h-screen bg-slate-100">
    <el-page-header @back="$router.push('/evidence')">
      <template #content>
        <span class="text-lg font-semibold">文书起草</span>
      </template>
    </el-page-header>

    <!-- 初始上传提示 -->
    <div class="mt-5 rounded-2xl arb-paper p-5 shadow-card mx-4">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div class="text-base font-semibold text-slate-800">你好，我是文书起草助手</div>
          <div class="text-sm text-slate-600 mt-1">
            请上传文档或图片，我将从您的材料中识别并提取信息，生成劳动仲裁申请书
          </div>
        </div>
      </div>
    </div>

    <!-- 上传区域 -->
    <div class="mt-5 mx-4">
      <div class="arb-paper rounded-2xl shadow-card overflow-hidden">
        <!-- 上传方式选择 -->
        <div class="p-4 border-b border-slate-200">
          <div class="flex gap-3 mb-4">
            <el-button 
              :type="uploadMode === 'image' ? 'primary' : 'default'"
              @click="uploadMode = 'image'"
            >
              📷 上传图片
            </el-button>
            <el-button 
              :type="uploadMode === 'doc' ? 'primary' : 'default'"
              @click="uploadMode = 'doc'"
            >
              📄 上传文档
            </el-button>
          </div>

          <!-- 图片上传 -->
          <div v-if="uploadMode === 'image'">
            <div 
              class="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center cursor-pointer hover:border-blue-400 transition-colors"
              :class="{ 'border-blue-500 bg-blue-50': isDragging }"
              @click="triggerImageUpload"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="handleImageDrop"
            >
              <input 
                ref="imageInput" 
                type="file" 
                accept="image/*" 
                class="hidden"
                @change="handleImageChange"
              />
              <div v-if="!imageUrl">
                <div class="text-4xl mb-3">📷</div>
                <div class="text-slate-600">点击或拖拽上传图片</div>
                <div class="text-xs text-slate-400 mt-1">支持 JPG、PNG 格式，大小不超过 10MB</div>
              </div>
              <div v-else class="relative inline-block">
                <img :src="imageUrl" class="max-h-40 rounded-lg" />
                <el-button 
                  type="danger" 
                  size="small" 
                  circle
                  class="absolute -top-2 -right-2"
                  @click.stop="removeImage"
                >
                  ✕
                </el-button>
              </div>
            </div>
          </div>

          <!-- 文档上传 -->
          <div v-else>
            <div 
              class="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center cursor-pointer hover:border-blue-400 transition-colors"
              :class="{ 'border-blue-500 bg-blue-50': isDragging }"
              @click="triggerDocUpload"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="handleDocDrop"
            >
              <input 
                ref="docInput" 
                type="file" 
                accept=".pdf,.doc,.docx,.txt" 
                class="hidden"
                @change="handleDocChange"
              />
              <div v-if="!docFile">
                <div class="text-4xl mb-3">📄</div>
                <div class="text-slate-600">点击或拖拽上传文档</div>
                <div class="text-xs text-slate-400 mt-1">支持 PDF、DOC、DOCX、TXT 格式，大小不超过 20MB</div>
              </div>
              <div v-else class="relative inline-block">
                <div class="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                  <span class="text-2xl">📄</span>
                  <div class="text-left">
                    <div class="font-medium text-slate-700">{{ docFile.name }}</div>
                    <div class="text-xs text-slate-400">{{ formatFileSize(docFile.size) }}</div>
                  </div>
                </div>
                <el-button 
                  type="danger" 
                  size="small" 
                  circle
                  class="absolute -top-2 -right-2"
                  @click.stop="removeDoc"
                >
                  ✕
                </el-button>
              </div>
            </div>
          </div>

          <!-- 开始对话按钮 -->
          <div class="mt-4 flex justify-center">
            <el-button 
              type="primary" 
              size="large" 
              round 
              :loading="uploading"
              :disabled="!canStart"
              @click="startWorkflow"
            >
              {{ uploading ? '正在启动...' : '🚀 开始对话' }}
            </el-button>
          </div>
          <p v-if="!canStart" class="text-xs text-slate-400 text-center mt-2">
            请先上传文档或图片才能开始对话
          </p>
        </div>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div v-if="conversationStarted" class="mt-5 mx-4">
      <div class="arb-paper rounded-2xl shadow-card overflow-hidden">
        <!-- 消息列表 -->
        <div class="messages-area" ref="messagesArea" :style="{ height: chatAreaHeight }">
          <!-- 消息列表 -->
          <div v-for="(msg, idx) in messages" :key="idx" class="message-wrapper">
            <!-- 用户消息 -->
            <div v-if="msg.role === 'user'" class="message user-message">
              <div class="message-content">
                <div v-if="msg.image" class="mb-2">
                  <img :src="msg.image" class="max-w-full rounded-lg max-h-48" />
                </div>
                <div v-if="msg.fileName" class="mb-2 flex items-center gap-2 p-2 bg-white/10 rounded">
                  <span>📄</span>
                  <span class="text-sm">{{ msg.fileName }}</span>
                </div>
                <div>{{ msg.text }}</div>
              </div>
            </div>

            <!-- 助手消息 -->
            <div v-else class="message assistant-message">
              <img src="/src/assets/lawyer.png" class="avatar-img" alt="律师助手" />
              <div class="message-body">
                <div class="reply-content" v-html="formatContent(msg.text)">
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

        <!-- 输入区域 -->
        <div class="input-area">
          <div class="flex items-end gap-3">
            <div class="flex-1">
              <div class="input-wrapper">
                <textarea
                  v-model="inputText"
                  placeholder="请输入您的问题或补充信息..."
                  rows="1"
                  @keydown.enter.exact.prevent="sendMessage"
                  @input="autoResize"
                  ref="inputArea"
                ></textarea>
                <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || sending">
                  <span class="send-icon">↑</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 生成文书按钮 -->
      <div class="mt-4 flex justify-center gap-4">
        <el-button type="primary" size="large" round :loading="generating" @click="generateDocument">
          📄 生成完整仲裁申请书
        </el-button>
        <el-button type="success" size="large" round @click="exportPDF" :disabled="!generatedDocument">
          📥 导出 PDF
        </el-button>
      </div>

      <!-- 生成的文书预览 -->
      <div v-if="generatedDocument" class="mt-5 mb-4 rounded-2xl arb-paper p-5 shadow-card">
        <div class="flex items-center justify-between mb-4">
          <div class="text-base font-semibold">生成的仲裁申请书</div>
          <div class="flex gap-2">
            <el-button @click="copyDocument">复制</el-button>
            <el-button type="primary" @click="exportPDF">导出 PDF</el-button>
            <el-button type="success" @click="saveDocument">保存到案件</el-button>
          </div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-[#fafaf8] p-6 max-h-[600px] overflow-auto document-preview" id="documentPrintArea">
          <div class="whitespace-pre-wrap text-slate-900 leading-8 text-sm" v-html="formatDocument(generatedDocument)"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import http from "../api/http";
import { useAuthStore } from "../stores/auth";
import { useFlowStore } from "../stores/flow";

const auth = useAuthStore();
const flow = useFlowStore();

// 上传相关
const uploadMode = ref("image"); // image 或 doc
const imageInput = ref(null);
const docInput = ref(null);
const imageUrl = ref("");
const imageFile = ref(null);
const docFile = ref(null);
const isDragging = ref(false);
const uploading = ref(false);
const conversationStarted = ref(false);
const presetLoaded = ref(false); // 标记预置文件是否已加载
const presetInfo = ref(null); // 临时保存预置文件信息（用于上传时获取URL）

// 处理预置文件
onMounted(() => {
  if (flow.presetFile && !presetLoaded.value) {
    const file = flow.presetFile;
    presetInfo.value = file; // 保存预置文件信息
    if (file.type === "image") {
      uploadMode.value = "image";
      imageUrl.value = file.url;
      imageFile.value = { name: file.name }; // 模拟文件对象
      ElMessage.success(`已加载预置图片：${file.name}`);
    } else if (file.type === "doc") {
      uploadMode.value = "doc";
      docFile.value = { name: file.name }; // 模拟文件对象
      ElMessage.success(`已加载预置文档：${file.name}`);
    }
    // 清除预置文件，避免刷新后重复加载
    flow.clearPresetFile();
    presetLoaded.value = true;
  }
});

// 聊天相关
const inputText = ref("");
const messages = ref([]);
const sending = ref(false);
const generating = ref(false);
const generatedDocument = ref("");
const messagesArea = ref(null);
const inputArea = ref(null);

// 是否可以开始对话（支持预置文件和手动上传）
const canStart = computed(() => {
  if (uploadMode.value === "image") {
    return !!(imageFile.value || imageUrl.value);
  }
  return !!(docFile.value || flow.presetFile?.type === "doc");
});

// 聊天区域高度
const chatAreaHeight = computed(() => {
  if (messages.value.length > 0) return "400px";
  return "300px";
});

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// 图片上传
function triggerImageUpload() {
  imageInput.value?.click();
}

function handleImageChange(e) {
  const file = e.target.files[0];
  if (file) processImageFile(file);
}

function handleImageDrop(e) {
  isDragging.value = false;
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) {
    processImageFile(file);
  } else {
    ElMessage.warning("请上传图片文件");
  }
}

function processImageFile(file) {
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning("图片大小不能超过 10MB");
    return;
  }
  
  imageFile.value = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    imageUrl.value = e.target.result;
  };
  reader.readAsDataURL(file);
}

function removeImage() {
  imageUrl.value = "";
  imageFile.value = null;
  if (imageInput.value) imageInput.value.value = "";
}

// 文档上传
function triggerDocUpload() {
  docInput.value?.click();
}

function handleDocChange(e) {
  const file = e.target.files[0];
  if (file) processDocFile(file);
}

function handleDocDrop(e) {
  isDragging.value = false;
  const file = e.dataTransfer.files[0];
  const allowedTypes = ["application/pdf", "application/msword", 
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"];
  if (file && (allowedTypes.includes(file.type) || file.name.endsWith('.pdf') || 
      file.name.endsWith('.doc') || file.name.endsWith('.docx') || file.name.endsWith('.txt'))) {
    processDocFile(file);
  } else {
    ElMessage.warning("请上传 PDF、DOC、DOCX 或 TXT 文件");
  }
}

function processDocFile(file) {
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.warning("文档大小不能超过 20MB");
    return;
  }
  
  docFile.value = file;
}

function removeDoc() {
  docFile.value = null;
  if (docInput.value) docInput.value.value = "";
}

// 开始工作流
async function startWorkflow() {
  if (!canStart.value) {
    ElMessage.warning("请先上传文档或图片");
    return;
  }

  uploading.value = true;

  try {
    if (uploadMode.value === "image") {
      // 图片模式
      // 如果是 URL（没有 base64 前缀），使用 URL 接口让后端下载
      if (imageUrl.value.startsWith('http')) {
        // 使用后端 URL 接口下载并分析
        const { data } = await http.post("/document/analyze-image-url", {
          image_url: imageUrl.value,
          context: "请分析这张图片内容，提取关键信息，帮助我生成劳动仲裁申请书。",
        });

        // 添加用户消息和助手回复
        messages.value.push({
          role: "user",
          text: "请帮我分析这份材料，提取关键信息",
          image: imageUrl.value,
        });

        messages.value.push({
          role: "assistant",
          text: data.result,
        });
      } else {
        // 手动上传的 base64 图片
        const base64Data = imageUrl.value.split(',')[1];
        const { data } = await http.post("/document/analyze-image", {
          image_base64: base64Data,
          context: "请分析这张图片内容，提取关键信息，帮助我生成劳动仲裁申请书。",
        });

        // 添加用户消息和助手回复
        messages.value.push({
          role: "user",
          text: "请帮我分析这份材料，提取关键信息",
          image: imageUrl.value,
        });

        messages.value.push({
          role: "assistant",
          text: data.result,
        });
      }
    } else {
      // 文档模式
      let uploadFile = docFile.value;
      let fileName = uploadFile?.name || "document";
      
      // 如果是预置 URL，需要先下载
      if (!uploadFile?.size && presetInfo.value?.url) {
        try {
          const response = await fetch(presetInfo.value.url);
          const blob = await response.blob();
          uploadFile = new File([blob], presetInfo.value.name, { type: blob.type });
          fileName = presetInfo.value.name;
        } catch (err) {
          ElMessage.error("文档加载失败，请手动上传");
          uploading.value = false;
          return;
        }
      }
      
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("context", "请分析这份文档内容，提取关键信息，帮助我生成劳动仲裁申请书。");

      const { data } = await http.post("/document/upload-document", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // 添加用户消息和助手回复
      messages.value.push({
        role: "user",
        text: "请帮我分析这份材料，提取关键信息",
        fileName: fileName,
      });

      messages.value.push({
        role: "assistant",
        text: data.result,
      });
    }

    conversationStarted.value = true;
    ElMessage.success("材料分析完成，请继续补充信息");
    
    await nextTick();
    scrollToBottom();
  } catch (e) {
    console.error("启动失败:", e);
    ElMessage.error(e.response?.data?.detail || "启动失败，请重试");
  } finally {
    uploading.value = false;
  }
}

function autoResize(e) {
  const textarea = e.target;
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text) {
    ElMessage.warning("请输入内容");
    return;
  }

  // 构建历史消息
  const history = messages.value.map(msg => ({
    role: msg.role,
    content: (msg.image ? "[图片] " : msg.fileName ? `[文件: ${msg.fileName}] ` : "") + msg.text
  }));

  // 添加用户消息
  messages.value.push({
    role: "user",
    text: text,
    image: null,
    fileName: null,
  });
  
  inputText.value = "";
  sending.value = true;

  await nextTick();
  scrollToBottom();

  try {
    // 构建请求
    let fileContent = null;
    let fileType = "image";
    let fileName = null;

    if (uploadMode.value === "image" && imageFile.value) {
      fileContent = imageUrl.value.split(',')[1];
      fileType = "image";
    } else if (uploadMode.value === "doc" && docFile.value) {
      // 将文件转为 base64
      fileContent = await fileToBase64(docFile.value);
      fileType = "doc";
      fileName = docFile.value.name;
    }

    console.log("[前端] 发送请求到 /document/chat");
    const { data } = await http.post("/document/chat", {
      message: text,
      history: history,
      file_type: fileType,
      file_content: fileContent,
      file_name: fileName,
    });
    console.log("[前端] 收到响应:", data);

    messages.value.push({
      role: "assistant",
      text: data.result,
    });

  } catch (e) {
    console.error("发送失败:", e);
    console.error("错误详情:", e.response?.data);
    ElMessage.error(e.response?.data?.detail || e.message || "发送失败，请重试");
    messages.value.pop();
  } finally {
    sending.value = false;
    await nextTick();
    scrollToBottom();
  }
}

// 文件转 base64
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function scrollToBottom() {
  if (messagesArea.value) {
    messagesArea.value.scrollTop = messagesArea.value.scrollHeight;
  }
}

function formatContent(text) {
  if (!text) return '';
  
  // 清理AI返回的混杂内容，提取纯文本
  let formatted = text
    // 移除所有HTML标签
    .replace(/<[^>]+>/g, '')
    // 移除无序列表符号
    .replace(/[•●○◆▪▸]\s*/g, '')
    // 清理多余的星号（但保留内容）
    .replace(/\*\*/g, '')
    // 清理特殊占位符如 **年**月**日
    .replace(/\*+/g, '')
    // 移除多余空格
    .replace(/\s{2,}/g, ' ')
    // 处理换行
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  
  // 关键信息高亮处理
  // 金额高亮：匹配 "XX元"、"XXXX.XX元" 等
  formatted = formatted.replace(/(\d+(?:\.\d{1,2})?\s*元)/g, '<span class="highlight-amount">$1</span>');
  // 日期高亮：匹配 "XXXX年XX月XX日" 格式
  formatted = formatted.replace(/(\d{4}年\d{1,2}月\d{1,2}日)/g, '<span class="highlight-date">$1</span>');
  // 百分比/倍数高亮：匹配 "X倍" 等
  formatted = formatted.replace(/(\d+(?:\.\d+)?\s*倍)/g, '<span class="highlight-factor">$1</span>');
  // 人名高亮：申请人、被申请人
  formatted = formatted.replace(/(申请人|被申请人)[：:]/g, '<strong>$1</strong>：');
  // 关键法律条款高亮
  formatted = formatted.replace(/(《[^》]+》)/g, '<span class="highlight-law">$1</span>');
  // 重要提示高亮（如"合计"、"共计"等）
  formatted = formatted.replace(/(合计|共计|总计)[：:]?\s*[\d元]+/g, '<strong>$&</strong>');
  
  // 将换行转换为br用于显示
  formatted = formatted.replace(/\n/g, '<br>');
  return formatted;
}

function formatDocument(text) {
  if (!text) return '';
  
  let formatted = text
    .replace(/<\/?ul>/gi, '')
    .replace(/<\/?li>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  
  const lines = formatted.split('\n');
  const result = lines.map(line => {
    const trimmed = line.trim();
    if (!trimmed) return '';
    if (trimmed.startsWith('#') || /^[\u4e00-\u9fa5]{2,4}(：|:)/.test(trimmed)) {
      return `<p class="doc-title">${trimmed}</p>`;
    }
    if (trimmed.startsWith('•') || trimmed.startsWith('-') || /^\d+[.、]/.test(trimmed)) {
      return `<p class="doc-list-item">${trimmed}</p>`;
    }
    return `<p>${line || '&nbsp;'}</p>`;
  }).join('');
  
  return result;
}

async function generateDocument() {
  if (messages.value.length === 0) {
    ElMessage.warning("请先进行对话");
    return;
  }

  generating.value = true;
  const info = extractInfoFromChat();
  const doc = generateArbitrationApplication(info);
  generatedDocument.value = doc;
  ElMessage.success("文书生成成功");
  generating.value = false;
}

function extractInfoFromChat() {
  const info = {
    applicantName: '',
    applicantGender: '',
    applicantBirth: '',
    applicantPhone: '',
    respondentName: '',
    respondentAddress: '',
    respondentCode: '',
    entryDate: '',
    quitDate: '',
    quitReason: '',
    monthlySalary: '',
    laborType: '正式工',
    claims: [],
  };
  
  const fullText = messages.value.map(m => m.text).join('\n');
  
  const nameMatch = fullText.match(/姓名[：:]\s*([^\n，,。]+)/) || fullText.match(/原告[：:]\s*([^\n，,。]+)/);
  if (nameMatch) info.applicantName = nameMatch[1].trim();
  
  if (fullText.includes('男')) info.applicantGender = '男';
  else if (fullText.includes('女')) info.applicantGender = '女';
  
  const birthMatch = fullText.match(/(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})日/) || fullText.match(/出生[：:]\s*(\d{4})/);
  if (birthMatch) info.applicantBirth = birthMatch.slice(1).join('-');
  
  const phoneMatch = fullText.match(/1[3-9]\d{9}/);
  if (phoneMatch) info.applicantPhone = phoneMatch[0];
  
  const companyMatch = fullText.match(/公司[名称]?[：:]\s*([^\n，,。]+)/) || fullText.match(/被告[：:]\s*([^\n，,。]+)/);
  if (companyMatch) info.respondentName = companyMatch[1].trim();
  
  const entryMatch = fullText.match(/入职[：:日期]*\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})[日]?/) || fullText.match(/(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})[日]?入职/);
  if (entryMatch) info.entryDate = entryMatch[1].replace(/\//g, '-');
  
  const quitMatch = fullText.match(/离职[：:日期]*\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})[日]?/) || fullText.match(/最后.*?(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})[日]?/);
  if (quitMatch) info.quitDate = quitMatch[1].replace(/\//g, '-');
  
  if (fullText.includes('开除') || fullText.includes('辞退')) {
    info.quitReason = '被公司违法辞退';
  } else if (fullText.includes('个人辞职') || fullText.includes('主动离职')) {
    info.quitReason = '个人原因主动辞职';
  } else if (fullText.includes('协商')) {
    info.quitReason = '双方协商一致解除';
  }
  
  const salaryMatch = fullText.match(/月薪[：:]*\s*(\d+)[元]?/) || fullText.match(/(\d+)\s*元.*?月/);
  if (salaryMatch) info.monthlySalary = salaryMatch[1];
  
  return info;
}

function generateArbitrationApplication(info) {
  const today = new Date().toLocaleDateString('zh-CN');
  const birthText = info.applicantBirth ? `出生于 ${info.applicantBirth},` : '';
  const salary = info.monthlySalary ? Math.round(parseInt(info.monthlySalary) * 2) : '【需计算】';
  
  return `# 劳动仲裁申请书

申请人：${info.applicantName || '【请填写】'}，${info.applicantGender || '男'}，${birthText}联系电话：${info.applicantPhone || '【请填写】'}

被申请人：${info.respondentName || '【请填写公司名称】'}，住所地：${info.respondentAddress || '【请填写】'}

## 仲裁请求

1. 请求依法判令被申请人支付违法解除劳动合同赔偿金人民币 ${salary} 元；
2. 请求依法判令被申请人支付 ${info.entryDate || '入职日期'} 至 ${info.quitDate || '离职日期'} 期间的工资差额（如有）人民币 【需计算】 元；
3. 请求依法判令被申请人承担本案全部仲裁费用。

## 事实与理由

申请人于 ${info.entryDate || '【请填写】'} 入职被申请人处，岗位为${info.laborType || '正式工'}。入职后，申请人严格遵守被申请人的各项规章制度，勤勉尽责地履行岗位职责。

然而，${info.quitDate || '近期'}，被申请人在未与申请人进行任何协商的情况下，单方面解除了劳动合同。申请人的离职原因为：${info.quitReason || '【请说明】'}。

申请人认为，被申请人的上述行为严重违反了《中华人民共和国劳动合同法》的相关规定，构成违法解除劳动合同。具体理由如下：

1. 缺乏事实依据：被申请人未能提供充分证据证明申请人存在严重违反规章制度、严重失职、营私舞弊等法定解除情形。
2. 程序严重违法：被申请人单方解除劳动合同，未事先将理由通知工会，也未依法向申请人出具《解除劳动合同证明书》。
3. 违法性明显：被申请人的解除行为缺乏事实与法律依据，依法应当支付违法解除劳动合同的赔偿金。

综上所述，为维护自身合法权益，申请人特依据《中华人民共和国劳动争议调解仲裁法》等相关法律法规之规定，向贵委提起仲裁申请，恳请贵委依法查明事实，支持申请人的全部仲裁请求。

此致

【】市/区劳动人事争议仲裁委员会

申请人（签名）：${info.applicantName || '【签名】'}

${today}`;
}

function exportPDF() {
  if (!generatedDocument.value) {
    ElMessage.warning("请先生成文书");
    return;
  }
  
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    ElMessage.error("请允许弹出窗口以导出 PDF");
    return;
  }
  
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>劳动仲裁申请书</title>
      <style>
        body {
          font-family: 'SimSun', '宋体', serif;
          font-size: 14px;
          line-height: 2;
          padding: 40px;
          max-width: 800px;
          margin: 0 auto;
        }
        h1 { text-align: center; font-size: 22px; margin-bottom: 30px; }
        h2 { font-size: 16px; margin-top: 20px; }
        p { text-indent: 2em; margin: 8px 0; }
        .signature { text-align: right; margin-top: 40px; }
        @media print { body { padding: 20px; } }
      </style>
    </head>
    <body>
      ${formatDocument(generatedDocument.value).replace(/<p class="doc-title">/g, '<h2>').replace(/<\/p>/g, '</h2>')}
    </body>
    </html>
  `);
  
  printWindow.document.close();
  printWindow.onload = function() {
    printWindow.print();
  };
}

function copyDocument() {
  if (!generatedDocument.value) return;
  navigator.clipboard.writeText(generatedDocument.value);
  ElMessage.success("已复制到剪贴板");
}

async function saveDocument() {
  if (!generatedDocument.value) return;
  if (!flow.caseId) {
    ElMessage.warning("请先创建案件");
    return;
  }

  try {
    await http.put(`/cases/${flow.caseId}`, {
      document_draft: generatedDocument.value,
    });
    ElMessage.success("文书已保存到案件");
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || "保存失败");
  }
}
</script>

<style scoped>
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
  max-height: 400px;
  min-height: 300px;
}

.message-wrapper {
  margin-bottom: 20px;
}

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
}

.assistant-message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
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
}

.input-area {
  padding: 12px 20px 20px;
  border-top: 1px solid #eee;
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
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #396af6, #2952d8);
  color: #fff;
  border: none;
  border-radius: 50%;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(57, 106, 246, 0.3);
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

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

.document-preview {
  font-family: 'Songti SC', 'SimSun', 'Noto Serif SC', serif;
}

.document-preview :deep(.doc-title) {
  font-weight: bold;
  font-size: 18px;
  text-align: center;
  margin: 20px 0 10px;
  color: #333;
}

.document-preview :deep(.doc-list-item) {
  margin-left: 2em;
  text-indent: -1.5em;
  margin-bottom: 8px;
}

.document-preview :deep(p) {
  margin: 4px 0;
}

/* 关键信息高亮样式 */
.reply-content .highlight-amount {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #b45309;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 14px;
}

.reply-content .highlight-date {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #1d4ed8;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.reply-content .highlight-factor {
  background: linear-gradient(135deg, #fce7f3, #fbcfe8);
  color: #be185d;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.reply-content .highlight-law {
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  color: #047857;
  padding: 1px 4px;
  border-radius: 4px;
  font-weight: 500;
}

.reply-content strong {
  color: #1e40af;
  font-weight: 600;
}
</style>
