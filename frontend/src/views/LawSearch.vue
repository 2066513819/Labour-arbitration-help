<template>
  <div class="law-search-page">
    <!-- 顶部导航 -->
    <div class="bg-white border-b sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex items-center justify-between h-14">
          <div class="flex items-center gap-4">
            <el-button text @click="$router.push('/')">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <h1 class="text-lg font-semibold">法律条文检索</h1>
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
          请简要描述您遇到的问题或情况，系统将为您匹配相关的法律条文
        </p>
        
        <el-input
          v-model="situation"
          type="textarea"
          :rows="4"
          placeholder="例如：公司没有和我签订劳动合同，已经工作了3个月..."
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
            <span v-if="!searching">检索法律条文</span>
            <span v-else>检索中...</span>
          </el-button>
          <el-button size="large" @click="situation = ''">清空</el-button>
        </div>
      </div>

      <!-- 快速分类入口 -->
      <div class="arb-paper p-6 mb-6" v-if="!searching && results.length === 0">
        <h3 class="text-base font-medium mb-4 flex items-center gap-2">
          <span class="text-xl">⚡</span>
          快速分类检索
        </h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            v-for="cat in quickCategories"
            :key="cat.id"
            class="category-card"
            @click="useCategory(cat)"
          >
            <span class="category-icon">{{ cat.icon }}</span>
            <span class="category-name">{{ cat.name }}</span>
          </button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="searching" class="arb-paper p-8 text-center">
        <el-icon class="is-loading text-4xl text-blue-500 mb-4"><Loading /></el-icon>
        <p class="text-slate-500">正在为您检索相关法律条文...</p>
        <p class="text-sm text-slate-400 mt-2">请稍候</p>
      </div>

      <!-- 搜索结果 -->
      <div v-else-if="results.length > 0">
        <!-- 匹配的法条列表 -->
        <div class="mb-6">
          <h3 class="text-base font-medium mb-4 flex items-center gap-2">
            <span class="text-xl">📜</span>
            匹配的法律条文
            <el-tag type="primary" size="small">{{ results.length }} 条</el-tag>
          </h3>

          <div class="space-y-4">
            <div
              v-for="(clause, index) in results"
              :key="index"
              class="law-card"
              :class="{ 'is-expanded': expandedIndex === index }"
            >
              <!-- 头部（可点击展开） -->
              <div class="law-card-header" @click="toggleExpand(index)">
                <!-- 标签行 -->
                <div class="law-tags-row">
                  <span class="law-tag law-tag--name">{{ clause.law_name }}</span>
                  <span v-if="clause.article_number" class="law-tag law-tag--article">
                    {{ clause.article_number }}
                  </span>
                  <span class="law-tag law-tag--rel">
                    相关度 {{ Math.round(clause.relevance * 100) }}%
                  </span>
                </div>

                <!-- 法条标题（文号/状态信息） -->
                <h4 v-if="clause.doc_number" class="law-title">
                  文号：{{ clause.doc_number }}
                  <span v-if="clause.status" class="law-status-tag">{{ clause.status }}</span>
                </h4>

                <!-- 正文摘要（默认截断3行） -->
                <p class="law-summary" :class="{ 'line-clamp-3': expandedIndex !== index }">
                  {{ clause.content }}
                </p>

                <div class="law-expand-hint">
                  <el-icon class="law-expand-icon" :class="{ 'rotate-180': expandedIndex === index }">
                    <ArrowDown />
                  </el-icon>
                  <span>{{ expandedIndex === index ? '收起' : '展开全文' }}</span>
                </div>
              </div>

              <!-- 展开详情 -->
              <div v-if="expandedIndex === index" class="law-detail">
                <div class="law-detail-section">
                  <p class="law-detail-text">{{ clause.content }}</p>
                </div>

                <!-- 操作按钮 -->
                <div class="law-actions">
                  <el-button type="primary" size="small" @click.stop="$router.push('/agent')">
                    <span>💬</span> AI进一步咨询
                  </el-button>
                  <el-button size="small" @click.stop="$router.push('/evidence')">
                    <span>📄</span> 准备证据
                  </el-button>
                  <el-button size="small" @click.stop="$router.push('/case-search')">
                    <span>📋</span> 查看相似案例
                  </el-button>
                </div>
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
          
          <div class="mt-6 flex gap-3">
            <el-button type="primary" @click="$router.push('/agent')">
              <span>💬</span> AI进一步咨询
            </el-button>
            <el-button @click="$router.push('/evidence')">
              <span>📄</span> 上传证据材料
            </el-button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!searching && hasSearched" class="arb-paper p-8 text-center">
        <div class="text-5xl mb-4 opacity-30">📭</div>
        <h3 class="text-lg font-medium text-slate-700 mb-2">未找到相关法条</h3>
        <p class="text-slate-500 mb-4">请尝试修改描述或使用更通用的关键词</p>
        <el-button @click="situation = ''; hasSearched = false">重新检索</el-button>
      </div>

      <!-- 法律知识小贴士 -->
      <div class="mt-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl">
        <h3 class="text-base font-medium mb-3 flex items-center gap-2">
          <span class="text-xl">📚</span>
          法律小贴士
        </h3>
        <div class="grid md:grid-cols-2 gap-4 text-sm">
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="font-medium text-slate-700 mb-2">📝 保留证据</div>
            <p class="text-slate-500">劳动争议中，谁主张谁举证。务必保留好劳动合同、工资条、考勤记录等证据材料。</p>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="font-medium text-slate-700 mb-2">⏰ 注意时效</div>
            <p class="text-slate-500">劳动仲裁申请时效为一年，从知道或应当知道权利被侵害之日起计算。</p>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="font-medium text-slate-700 mb-2">🤝 优先调解</div>
            <p class="text-slate-500">劳动争议可先通过企业调解委员会或街道调解中心进行调解，效率更高。</p>
          </div>
          <div class="bg-white rounded-lg p-4 shadow-sm">
            <div class="font-medium text-slate-700 mb-2">💼 免费援助</div>
            <p class="text-slate-500">符合条件的劳动者可申请法律援助，获得免费的法律咨询和代理服务。</p>
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
const results = ref([]);
const summary = ref("");
const suggestions = ref([]);
const quickCategories = ref([]);
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
  await loadCategories();
});

async function loadCategories() {
  try {
    const { data } = await http.get("/law/quick-categories");
    if (data.categories) {
      quickCategories.value = data.categories;
    }
  } catch (e) {
    console.error("加载分类失败:", e);
  }
}

function useCategory(cat) {
  // 使用分类的示例填充搜索框
  situation.value = cat.examples[0];
}

async function handleSearch() {
  if (!situation.value.trim()) {
    ElMessage.warning("请输入您的情况描述");
    return;
  }

  searching.value = true;
  hasSearched.value = true;
  results.value = [];
  expandedIndex.value = -1;

  try {
    const { data } = await http.post("/law/search", {
      situation: situation.value,
      laborer_type: laborType.value,
    });

    if (data.success) {
      results.value = data.matched_clauses || [];
      summary.value = data.summary || "已为您检索到相关法律条文";
      suggestions.value = data.suggestions || [];
      
      if (results.value.length === 0) {
        ElMessage.info("未找到精确匹配的法条，但已提供一般性建议");
      } else {
        ElMessage.success(`已为您匹配到 ${results.value.length} 条相关法律条文`);
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
.law-search-page {
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

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ========== 法条卡片 ========== */
.law-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.25s ease;
}

.law-card:hover {
  border-color: #94a3b8;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.law-card.is-expanded {
  border-color: #396af6;
  box-shadow: 0 4px 20px rgba(57, 106, 246, 0.1);
}

/* 头部 */
.law-card-header {
  padding: 16px 20px;
  cursor: pointer;
}

/* 标签行 */
.law-tags-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.law-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
}

.law-tag--name {
  background: #dbeafe;
  color: #1e40af;
}

.law-tag--article {
  background: #f1f5f9;
  color: #475569;
}

.law-tag--rel {
  background: #f1f5f9;
  color: #64748b;
  font-weight: 400;
}

/* 标题 */
.law-title {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  margin: 0 0 6px 0;
  line-height: 1.5;
}

.law-status-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  background: #fef3c7;
  color: #92400e;
}

/* 摘要 */
.law-summary {
  font-size: 14px;
  color: #334155;
  line-height: 1.75;
  margin: 0;
  white-space: pre-line;
}

/* 展开提示 */
.law-expand-hint {
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

.law-expand-icon {
  transition: transform 0.25s ease;
}

/* 详情区 */
.law-detail {
  padding: 0 20px 20px;
  border-top: 1px solid #f1f5f9;
}

.law-detail-section {
  padding-top: 12px;
}

.law-detail-text {
  font-size: 14px;
  color: #334155;
  line-height: 1.85;
  margin: 0;
  white-space: pre-line;
}

/* 操作按钮 */
.law-actions {
  display: flex;
  gap: 10px;
  padding-top: 16px;
  margin-top: 16px;
  border-top: 1px solid #f1f5f9;
}
</style>
