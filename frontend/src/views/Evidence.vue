<template>
  <div class="min-h-screen bg-slate-50">
    <!-- 顶部导航 -->
    <div class="bg-white border-b sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex items-center justify-between h-14">
          <div class="flex items-center gap-4">
            <el-button text @click="$router.push('/mycases')">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <h1 class="text-lg font-semibold">证据管理</h1>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="flow.scenarioTitle" class="text-sm text-slate-500">
              {{ flow.scenarioTitle }}
            </span>
            <el-tag v-if="flow.caseId" type="success" size="small">
              案件 #{{ flow.caseId }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 py-6">
      <!-- 无案件提示 -->
      <div v-if="!flow.caseId" class="arb-paper p-8 text-center">
        <div class="text-5xl mb-4">📋</div>
        <h2 class="text-lg font-medium text-slate-700 mb-2">请先发起案件</h2>
        <p class="text-slate-500 mb-4">在「我的案件」中创建案件后，才能上传和管理证据</p>
        <el-button type="primary" @click="$router.push('/mycases')">
          前往我的案件
        </el-button>
      </div>

      <template v-else>
        <!-- 统计卡片 -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          <div class="arb-paper p-4 text-center">
            <div class="text-2xl font-bold text-slate-700">{{ stats.total }}</div>
            <div class="text-xs text-slate-400 mt-1">总证据数</div>
          </div>
          <div class="arb-paper p-4 text-center">
            <div class="text-2xl font-bold text-green-600">{{ stats.image_count }}</div>
            <div class="text-xs text-slate-400 mt-1">📷 图片</div>
          </div>
          <div class="arb-paper p-4 text-center">
            <div class="text-2xl font-bold text-blue-600">{{ stats.doc_count }}</div>
            <div class="text-xs text-slate-400 mt-1">📄 文档</div>
          </div>
          <div class="arb-paper p-4 text-center">
            <div class="text-2xl font-bold text-orange-500">{{ stats.audio_count }}</div>
            <div class="text-xs text-slate-400 mt-1">🎵 录音</div>
          </div>
          <div class="arb-paper p-4 text-center">
            <div class="text-2xl font-bold text-red-500">{{ stats.video_count }}</div>
            <div class="text-xs text-slate-400 mt-1">🎬 视频</div>
          </div>
        </div>

        <!-- 操作栏 -->
        <div class="arb-paper p-4 mb-4">
          <div class="flex flex-wrap items-center gap-3">
            <el-button type="primary" @click="showUploadDialog = true">
              <el-icon><Plus /></el-icon>
              添加证据
            </el-button>
            <el-button @click="loadEvidences" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <div class="flex-1"></div>
            <span class="text-sm text-slate-400">
              共 {{ evidences.length }} 条记录
            </span>
          </div>
        </div>

        <!-- Excel风格表格 -->
        <div class="arb-paper overflow-hidden">
          <!-- 表头 -->
          <div class="bg-slate-100 px-4 py-3 border-b grid grid-cols-12 gap-2 text-sm font-medium text-slate-600">
            <div class="col-span-1 text-center">序号</div>
            <div class="col-span-2">证据名称</div>
            <div class="col-span-1 text-center">类型</div>
            <div class="col-span-2">文件名</div>
            <div class="col-span-2">大小</div>
            <div class="col-span-2">URL</div>
            <div class="col-span-2 text-center">操作</div>
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="p-8 text-center text-slate-400">
            <el-icon class="is-loading text-2xl"><Loading /></el-icon>
            <div class="mt-2">加载中...</div>
          </div>

          <!-- 空状态 -->
          <div v-else-if="evidences.length === 0" class="p-12 text-center">
            <div class="text-5xl mb-3 opacity-30">📂</div>
            <div class="text-slate-500">暂无证据</div>
            <div class="text-slate-400 text-sm mt-1">点击「添加证据」上传您的第一份证据</div>
          </div>

          <!-- 数据行 -->
          <div
            v-else
            v-for="(item, index) in evidences"
            :key="item.id"
            class="px-4 py-3 border-b last:border-b-0 hover:bg-slate-50 grid grid-cols-12 gap-2 text-sm items-center"
          >
            <!-- 序号 -->
            <div class="col-span-1 text-center text-slate-400">
              {{ index + 1 }}
            </div>

            <!-- 证据名称 -->
            <div class="col-span-2 font-medium text-slate-700 truncate" :title="item.evidence_name">
              {{ item.evidence_name }}
            </div>

            <!-- 类型标签 -->
            <div class="col-span-1 text-center">
              <el-tag :type="getTypeTagType(item.evidence_type)" size="small">
                {{ item.type_icon }} {{ item.type_label }}
              </el-tag>
            </div>

            <!-- 文件名 -->
            <div class="col-span-2 text-slate-500 truncate" :title="item.filename">
              {{ item.filename || '-' }}
            </div>

            <!-- 大小 -->
            <div class="col-span-2 text-slate-500">
              {{ formatSize(item.file_size) }}
            </div>

            <!-- URL -->
            <div class="col-span-2">
              <el-tooltip v-if="item.file_url" :content="item.file_url" placement="top">
                <el-button link type="primary" class="truncate max-w-[150px]">
                  {{ getShortUrl(item.file_url) }}
                </el-button>
              </el-tooltip>
              <span v-else class="text-slate-400">-</span>
            </div>

            <!-- 操作按钮 -->
            <div class="col-span-2 flex justify-center gap-1 flex-wrap">
              <el-button 
                v-if="['image', 'doc'].includes(item.evidence_type)" 
                size="small" 
                type="primary"
                plain
                @click="sendToDocument(item)"
              >
                📝 起草
              </el-button>
              <el-button size="small" @click="previewEvidence(item)">
                查看
              </el-button>
              <el-button size="small" @click="editEvidence(item)">
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteEvidence(item)">
                删除
              </el-button>
            </div>
          </div>
        </div>

        <!-- 描述/备注 -->
        <div v-if="evidences.length > 0" class="mt-4 p-4 bg-slate-100 rounded-lg text-sm text-slate-500 flex justify-between">
          <span>证据总大小：{{ formatSize(stats.total_size) }}</span>
          <span>最后更新：{{ evidences[0]?.created_at ? formatDate(evidences[0].created_at) : '-' }}</span>
        </div>
      </template>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="添加证据" width="500px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="证据名称" required>
          <el-input v-model="uploadForm.evidence_name" placeholder="如：劳动合同、工资条、录音证据" />
        </el-form-item>
        <el-form-item label="证据类型" required>
          <el-select v-model="uploadForm.evidence_type" class="w-full">
            <el-option label="📷 图片" value="image" />
            <el-option label="📄 文档" value="doc" />
            <el-option label="🎵 录音" value="audio" />
            <el-option label="🎬 视频" value="video" />
          </el-select>
        </el-form-item>
        <el-form-item label="上传文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :accept="getAccept(uploadForm.evidence_type)"
            :on-change="handleFileChange"
            :limit="1"
            class="w-full"
          >
            <el-button type="primary" plain>
              <el-icon><Upload /></el-icon>
              选择{{ getTypeLabel(uploadForm.evidence_type) }}
            </el-button>
            <template #tip>
              <div class="text-xs text-slate-400 mt-1">
                支持：{{ getAcceptDesc(uploadForm.evidence_type) }}
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="2" placeholder="可选：证据描述或备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑证据" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="证据名称">
          <el-input v-model="editForm.evidence_name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-tag :type="getTypeTagType(editForm.evidence_type)" size="large">
            {{ editForm.type_icon }} {{ editForm.type_label }}
          </el-tag>
        </el-form-item>
        <el-form-item label="文件名">
          <span class="text-slate-600">{{ editForm.filename }}</span>
        </el-form-item>
        <el-form-item label="URL">
          <el-input :model-value="editForm.file_url" readonly />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="showPreviewDialog" :title="previewItem?.evidence_name" width="800px">
      <!-- 图片预览 -->
      <div v-if="previewItem?.evidence_type === 'image'" class="text-center">
        <el-image
          v-if="previewItem?.file_url"
          :src="previewItem.file_url"
          fit="contain"
          class="w-full max-h-[60vh]"
          :preview-src-list="[previewItem.file_url]"
        />
        <div v-else class="text-slate-400 py-8">暂无文件</div>
      </div>

      <!-- 音频预览 -->
      <div v-else-if="previewItem?.evidence_type === 'audio'" class="text-center py-8">
        <div class="text-5xl mb-4">🎵</div>
        <audio v-if="previewItem?.file_url" controls class="w-full">
          <source :src="previewItem.file_url">
          您的浏览器不支持音频播放
        </audio>
        <div v-else class="text-slate-400">暂无文件</div>
      </div>

      <!-- 视频预览 -->
      <div v-else-if="previewItem?.evidence_type === 'video'" class="text-center">
        <video v-if="previewItem?.file_url" controls class="w-full max-h-[60vh]" :src="previewItem.file_url">
          您的浏览器不支持视频播放
        </video>
        <div v-else class="text-slate-400 py-8">暂无文件</div>
      </div>

      <!-- 文档预览 -->
      <div v-else class="text-center py-8">
        <div class="text-5xl mb-4">📄</div>
        <div class="text-slate-600 mb-4">{{ previewItem?.filename }}</div>
        <el-button v-if="previewItem?.file_url" type="primary" @click="openUrl(previewItem.file_url)">
          在新窗口打开
        </el-button>
        <div v-else class="text-slate-400">暂无文件</div>
      </div>

      <!-- 证据信息 -->
      <el-divider />
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="text-slate-400">类型：</span>
          <span>{{ previewItem?.type_label }}</span>
        </div>
        <div>
          <span class="text-slate-400">大小：</span>
          <span>{{ formatSize(previewItem?.file_size) }}</span>
        </div>
        <div class="col-span-2">
          <span class="text-slate-400">描述：</span>
          <span>{{ previewItem?.description || '无' }}</span>
        </div>
        <div class="col-span-2">
          <span class="text-slate-400">上传时间：</span>
          <span>{{ previewItem?.created_at ? formatDate(previewItem.created_at) : '-' }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Plus, Refresh, Loading, Upload, ArrowLeft } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import http from "../api/http";
import { useFlowStore } from "../stores/flow";

const router = useRouter();

const flow = useFlowStore();

const loading = ref(false);
const uploading = ref(false);
const saving = ref(false);
const evidences = ref([]);
const stats = ref({ total: 0, image_count: 0, doc_count: 0, audio_count: 0, video_count: 0, total_size: 0 });

// 上传对话框
const showUploadDialog = ref(false);
const uploadForm = reactive({
  evidence_name: "",
  evidence_type: "image",
  description: "",
  file: null,
});
const uploadRef = ref(null);

// 编辑对话框
const showEditDialog = ref(false);
const editForm = reactive({
  id: null,
  evidence_name: "",
  evidence_type: "",
  type_label: "",
  type_icon: "",
  filename: "",
  file_url: "",
  description: "",
});

// 预览对话框
const showPreviewDialog = ref(false);
const previewItem = ref(null);

const TYPE_LABELS = { image: "图片", doc: "文档", audio: "录音", video: "视频" };

onMounted(() => loadEvidences());

async function loadEvidences() {
  if (!flow.caseId) return;
  loading.value = true;
  try {
    const { data } = await http.get(`/evidence/list/${flow.caseId}`);
    if (data.success) {
      evidences.value = data.data.evidences || [];
      stats.value = {
        total: data.data.total || 0,
        image_count: data.data.image_count || 0,
        doc_count: data.data.doc_count || 0,
        audio_count: data.data.audio_count || 0,
        video_count: data.data.video_count || 0,
        total_size: data.data.total_size || 0,
      };
    }
  } catch (e) {
    console.error("加载证据失败:", e);
    ElMessage.error("加载证据列表失败");
  } finally {
    loading.value = false;
  }
}

function getAccept(type) {
  const map = {
    image: "image/*",
    doc: ".pdf,.doc,.docx,.txt",
    audio: "audio/*",
    video: "video/*",
  };
  return map[type] || "*";
}

function getAcceptDesc(type) {
  const map = {
    image: "jpg, png, webp, gif",
    doc: "pdf, doc, docx, txt",
    audio: "mp3, wav, ogg, m4a",
    video: "mp4, webm, ogg",
  };
  return map[type] || "";
}

function getTypeLabel(type) {
  return TYPE_LABELS[type] || "文件";
}

function getTypeTagType(type) {
  const map = { image: "success", doc: "primary", audio: "warning", video: "danger" };
  return map[type] || "info";
}

function handleFileChange(file) {
  uploadForm.file = file.raw;
  if (!uploadForm.evidence_name) {
    uploadForm.evidence_name = file.name.replace(/\.[^.]+$/, "");
  }
}

// 发送到文书起草
function sendToDocument(item) {
  if (!item.file_url) {
    ElMessage.warning("该证据暂无文件URL，无法发送到文书起草");
    return;
  }
  // 设置预置文件并跳转到文书起草页面
  flow.setPresetFile({
    url: item.file_url,
    type: item.evidence_type,
    name: item.filename || item.evidence_name,
  });
  ElMessage.success("已发送到文书起草");
  router.push("/document");
}

async function submitUpload() {
  if (!uploadForm.evidence_name) {
    ElMessage.warning("请输入证据名称");
    return;
  }
  if (!uploadForm.file) {
    ElMessage.warning("请选择要上传的文件");
    return;
  }

  uploading.value = true;
  try {
    const fd = new FormData();
    fd.append("case_id", String(flow.caseId));
    fd.append("evidence_name", uploadForm.evidence_name);
    fd.append("file", uploadForm.file);
    if (uploadForm.description) {
      fd.append("description", uploadForm.description);
    }

    const { data } = await http.post("/evidence/upload", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    if (data.success) {
      ElMessage.success("上传成功");
      showUploadDialog.value = false;
      uploadForm.evidence_name = "";
      uploadForm.description = "";
      uploadForm.file = null;
      if (uploadRef.value) uploadRef.value.clearFiles();
      loadEvidences();
    } else {
      ElMessage.error(data.detail || "上传失败");
    }
  } catch (e) {
    console.error("上传失败:", e);
    ElMessage.error(e.response?.data?.detail || "上传失败");
  } finally {
    uploading.value = false;
  }
}

function editEvidence(item) {
  Object.assign(editForm, {
    id: item.id,
    evidence_name: item.evidence_name,
    evidence_type: item.evidence_type,
    type_label: item.type_label,
    type_icon: item.type_icon,
    filename: item.filename,
    file_url: item.file_url,
    description: item.description || "",
  });
  showEditDialog.value = true;
}

async function submitEdit() {
  saving.value = true;
  try {
    const { data } = await http.patch(`/evidence/${editForm.id}`, {
      evidence_name: editForm.evidence_name,
      description: editForm.description,
    });
    if (data.success) {
      ElMessage.success("保存成功");
      showEditDialog.value = false;
      loadEvidences();
    }
  } catch (e) {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
}

function previewEvidence(item) {
  previewItem.value = item;
  showPreviewDialog.value = true;
}

async function deleteEvidence(item) {
  try {
    await ElMessageBox.confirm(
      `确定要删除证据「${item.evidence_name}」吗？`,
      "删除确认",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" }
    );
    await http.delete(`/evidence/${item.id}`);
    ElMessage.success("删除成功");
    loadEvidences();
  } catch (e) {
    if (e !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
}

function openUrl(url) {
  window.open(url, "_blank");
}

function getShortUrl(url) {
  if (!url) return "-";
  try {
    const u = new URL(url);
    return u.pathname.split("/").pop() || url.slice(0, 20);
  } catch {
    return url.slice(0, 20) + "...";
  }
}

function formatSize(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  return `${bytes.toFixed(1)} ${units[i]}`;
}

function formatDate(dateStr) {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}
</script>

<style scoped>
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
