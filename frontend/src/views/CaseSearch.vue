<template>
  <div class="case-search-page">
    <!-- 顶部导航 -->
    <div class="bg-white border-b sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex items-center justify-between h-14">
          <div class="flex items-center gap-4">
            <el-button text @click="$router.push('/')">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <h1 class="text-lg font-semibold">案例检索</h1>
          </div>
          <div class="flex items-center gap-2">
            <el-tag v-if="laborType" type="success" size="small">
              {{ laborTypeLabel }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-5xl mx-auto px-4 py-6">
      <!-- 搜索区域 -->
      <div class="arb-paper p-6 mb-6">
        <h2 class="text-lg font-medium mb-4 flex items-center gap-2">
          <span class="text-2xl">🔍</span>
          描述您的情况
        </h2>
        <p class="text-sm text-slate-500 mb-4">
          请简要描述您遇到的劳动纠纷，系统将为您匹配相似的真实仲裁案例
        </p>
        
        <el-input
          v-model="situation"
          type="textarea"
          :rows="4"
          placeholder="例如：公司没有和我签订劳动合同，已经工作了3个月，后被口头辞退..."
          maxlength="500"
          show-word-limit
          class="mb-4"
        />
        
        <div class="flex items-center gap-4">
          <el-button 
            type="primary" 
            size="large"
            :loading="searching"
            :disabled="!situation.trim()"
            @click="handleSearch"
          >
            <el-icon v-if="!searching"><Search /></el-icon>
            <span v-if="!searching">检索相似案例</span>
            <span v-else>检索中...</span>
          </el-button>
          <el-button size="large" @click="situation = ''">清空</el-button>
        </div>
      </div>

      <!-- 快速分类入口 -->
      <div class="arb-paper p-6 mb-6" v-if="!searching && cases.length === 0">
        <h3 class="text-base font-medium mb-4 flex items-center gap-2">
          <span class="text-xl">⚡</span>
          快速分类检索
        </h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            v-for="type in quickTypes"
            :key="type.id"
            class="category-card"
            @click="useType(type)"
          >
            <span class="category-icon">{{ type.icon }}</span>
            <span class="category-name">{{ type.name }}</span>
          </button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="searching" class="arb-paper p-8 text-center">
        <el-icon class="is-loading text-4xl text-blue-500 mb-4"><Loading /></el-icon>
        <p class="text-slate-500">正在为您检索相似案例...</p>
        <p class="text-sm text-slate-400 mt-2">请稍候</p>
      </div>

      <!-- 搜索结果 -->
      <div v-else-if="cases.length > 0">
        <!-- 匹配案例统计 -->
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-base font-medium flex items-center gap-2">
            <span class="text-xl">📋</span>
            相似案例
            <el-tag type="primary" size="small">{{ cases.length }} 个</el-tag>
          </h3>
          <el-button link type="primary" @click="situation = ''; cases = []">
            清除结果
          </el-button>
        </div>

        <!-- 案例卡片列表 -->
        <div class="space-y-4 mb-6">
          <div
            v-for="(c, index) in cases"
            :key="index"
            class="case-card"
            :class="{ 'is-expanded': expandedIndex === index }"
          >
            <!-- 案例头部（可点击展开） -->
            <div class="case-card-header" @click="toggleExpand(index)">
              <!-- 顶部标签行：类型 + 案号 + 相关度 -->
              <div class="case-tags-row">
                <span class="case-tag case-tag--type">{{ c.case_type }}</span>
                <span v-if="c.case_number" class="case-tag case-tag--number">
                  案号：{{ c.case_number }}
                </span>
                <span class="case-tag case-tag--rel">
                  相关度 {{ Math.round(c.relevance * 100) }}%
                </span>
              </div>

              <!-- 标题 -->
              <h4 class="case-title">📍 {{ c.case_title }}</h4>

              <!-- 审理法院 -->
              <div v-if="c.court_name" class="case-court">
                <span class="case-court-label">审理法院</span>
                <span class="case-court-name">{{ c.court_name }}</span>
              </div>

              <div class="case-expand-hint">
                <el-icon class="case-expand-icon" :class="{ 'rotate-180': expandedIndex === index }">
                  <ArrowDown />
                </el-icon>
                <span>{{ expandedIndex === index ? '收起详情' : '展开详情' }}</span>
              </div>
            </div>

            <!-- 展开详情 -->
            <div v-if="expandedIndex === index" class="case-detail">
              <!-- 案情摘要（展开后完整显示） -->
              <div v-if="c.case_summary" class="detail-section">
                <div class="detail-label">
                  <span class="detail-icon">📝</span>
                  <span>案情摘要</span>
                </div>
                <p class="detail-text">{{ c.case_summary }}</p>
              </div>

              <!-- 裁决结果 -->
              <div v-if="c.ruling_result" class="detail-section detail-section--ruling">
                <div class="detail-label">
                  <span class="detail-icon">⚖️</span>
                  <span>裁决结果</span>
                </div>
                <p class="detail-text">{{ c.ruling_result }}</p>
              </div>

              <!-- 关键证据 -->
              <div v-if="c.key_evidence && c.key_evidence.length" class="detail-section">
                <div class="detail-label">
                  <span class="detail-icon">📎</span>
                  <span>关键证据</span>
                </div>
                <div class="detail-tags">
                  <span
                    v-for="(evidence, i) in c.key_evidence"
                    :key="i"
                    class="detail-tag detail-tag--evidence"
                  >
                    {{ evidence }}
                  </span>
                </div>
              </div>

              <!-- 法律依据 -->
              <div v-if="c.law_basis && c.law_basis.length" class="detail-section">
                <div class="detail-label">
                  <span class="detail-icon">📜</span>
                  <span>法律依据</span>
                </div>
                <div class="detail-tags">
                  <span
                    v-for="(law, i) in c.law_basis"
                    :key="i"
                    class="detail-tag detail-tag--law"
                  >
                    {{ law }}
                  </span>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="case-actions">
                <el-button type="primary" size="small" @click="$router.push('/agent')">
                  <span>💬</span> AI进一步咨询
                </el-button>
                <el-button size="small" @click="$router.push('/evidence')">
                  <span>📄</span> 准备证据
                </el-button>
                <el-button size="small" @click="$router.push('/law-search')">
                  <span>📖</span> 查看法条
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 维权建议 -->
        <div class="arb-paper p-6">
          <h3 class="text-base font-medium mb-4 flex items-center gap-2">
            <span class="text-xl">💪</span>
            维权建议
          </h3>
          <div class="space-y-3">
            <div 
              v-for="(suggestion, index) in suggestions" 
              :key="index"
              class="flex items-start gap-3 p-3 bg-slate-50 rounded-lg"
            >
              <span class="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
                {{ index + 1 }}
              </span>
              <span class="text-slate-700">{{ suggestion }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!searching && hasSearched" class="arb-paper p-8 text-center">
        <div class="text-5xl mb-4 opacity-30">📭</div>
        <h3 class="text-lg font-medium text-slate-700 mb-2">未找到相似案例</h3>
        <p class="text-slate-500 mb-4">请尝试修改描述或使用更通用的关键词</p>
        <el-button @click="situation = ''; hasSearched = false">重新检索</el-button>
      </div>

      <!-- 使用提示 -->
      <div class="mt-8 p-6 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl">
        <h3 class="text-base font-medium mb-3 flex items-center gap-2">
          <span class="text-xl">💡</span>
          使用提示
        </h3>
        <div class="grid md:grid-cols-2 gap-4 text-sm">
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="font-medium text-slate-700 mb-2">📊 参考相似案例</div>
            <p class="text-slate-500">通过检索相似案例，了解仲裁委的裁决标准和赔偿区间，对自己的案件形成合理预期。</p>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="font-medium text-slate-700 mb-2">📋 准备关键证据</div>
            <p class="text-slate-500">案例中标注的关键证据是胜诉要点，务必提前准备并规范保存。</p>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="font-medium text-slate-700 mb-2">⚖️ 了解法律依据</div>
            <p class="text-slate-500">明确案件涉及的法律条款，可以在维权过程中更有针对性地主张权利。</p>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="font-medium text-slate-700 mb-2">🤝 必要时寻求帮助</div>
            <p class="text-slate-500">复杂案件建议咨询专业律师，符合条件可申请法律援助。</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { Search, Loading, ArrowLeft, ArrowDown } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import http from "../api/http";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();

const situation = ref("");
const searching = ref(false);
const hasSearched = ref(false);
const cases = ref([]);
const suggestions = ref([]);
const quickTypes = ref([]);
const expandedIndex = ref(-1);

const laborType = computed(() => auth.laborerType);

const laborTypeLabel = computed(() => {
  const labels = {
    dispatch: "劳务派遣",
    intern: "在校实习生",
    platform: "平台工作者",
    other_uncertain: "其他/不确定",
    courier: "外卖骑手",
    formal: "正式工",
  };
  return labels[laborType.value] || laborType.value;
});

onMounted(async () => {
  await loadTypes();
});

async function loadTypes() {
  try {
    const { data } = await http.get("/case-search/quick-types");
    if (data.types) {
      quickTypes.value = data.types;
    }
  } catch (e) {
    console.error("加载分类失败:", e);
  }
}

function useType(type) {
  situation.value = type.description;
}

async function handleSearch() {
  if (!situation.value.trim()) {
    ElMessage.warning("请输入您的情况描述");
    return;
  }

  searching.value = true;
  hasSearched.value = true;
  cases.value = [];
  expandedIndex.value = -1;

  try {
    const { data } = await http.post("/case-search/search", {
      situation: situation.value,
      laborer_type: laborType.value,
    });

    if (data.success) {
      cases.value = data.cases || [];
      suggestions.value = data.suggestions || [];
      
      if (cases.value.length === 0) {
        ElMessage.info("未找到相似案例，请尝试其他描述");
      } else {
        ElMessage.success(`已为您匹配 ${cases.value.length} 个相似案例`);
      }
    } else {
      ElMessage.error(data.detail || "检索失败");
    }
  } catch (e) {
    console.error("检索失败:", e);
    ElMessage.error(e.response?.data?.detail || "检索失败，请稍后重试");
  } finally {
    searching.value = false;
  }
}

function toggleExpand(index) {
  expandedIndex.value = expandedIndex.value === index ? -1 : index;
}
</script>

<style scoped>
.case-search-page {
  min-height: 100vh;
  background-color: #f2f3f5;
}

.category-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-card:hover {
  background: #fff;
  border-color: #396af6;
  box-shadow: 0 4px 12px rgba(57, 106, 246, 0.15);
  transform: translateY(-2px);
}

.category-icon {
  font-size: 24px;
}

.category-name {
  font-size: 13px;
  font-weight: 500;
  color: #475569;
}

.rotate-180 {
  transform: rotate(180deg);
}

/* ========== 案例卡片 ========== */
.case-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.25s ease;
}

.case-card:hover {
  border-color: #94a3b8;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.case-card.is-expanded {
  border-color: #396af6;
  box-shadow: 0 4px 20px rgba(57, 106, 246, 0.1);
}

/* 头部 */
.case-card-header {
  padding: 16px 20px;
  cursor: pointer;
}

/* 标签行 */
.case-tags-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.case-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
}

.case-tag--type {
  background: #fee2e2;
  color: #b91c1c;
}

.case-tag--number {
  background: #dbeafe;
  color: #1e40af;
}

.case-tag--rel {
  background: #f1f5f9;
  color: #64748b;
  font-weight: 400;
}

/* 标题 */
.case-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
  line-height: 1.5;
}

/* 审理法院 */
.case-court {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.case-court-label {
  font-size: 11px;
  color: #94a3b8;
  background: #f8fafc;
  padding: 2px 8px;
  border-radius: 4px;
}

.case-court-name {
  font-size: 12px;
  color: #475569;
}

/* 展开提示 */
.case-expand-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #e2e8f0;
  font-size: 12px;
  color: #94a3b8;
}

.case-expand-icon {
  transition: transform 0.25s ease;
}

/* 详情区 */
.case-detail {
  padding: 0 20px 20px;
  border-top: 1px solid #f1f5f9;
}

.detail-section {
  padding-top: 16px;
}

.detail-section--ruling {
  background: #f0fdf4;
  margin: 12px -20px 0;
  padding: 16px 20px;
  border-left: 3px solid #22c55e;
}

.detail-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
}

.detail-icon {
  font-size: 15px;
}

.detail-text {
  font-size: 14px;
  color: #475569;
  line-height: 1.7;
  margin: 0;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.detail-tag--evidence {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}

.detail-tag--law {
  background: #eff6ff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}

/* 操作按钮 */
.case-actions {
  display: flex;
  gap: 10px;
  padding-top: 16px;
  margin-top: 16px;
  border-top: 1px solid #f1f5f9;
}
</style>
