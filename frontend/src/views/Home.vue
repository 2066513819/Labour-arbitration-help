<template>
  <div class="home-page">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <span class="logo-icon">⚖️</span>
          <span class="logo-text">仲裁辅助</span>
          <span class="logo-tag">智能法律服务</span>
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" round @click="$router.push('/agent')">
          <span class="flex items-center gap-1">
            <span>💬</span>
            <span>AI 咨询</span>
          </span>
        </el-button>
        <el-button text @click="$router.push('/guide')">流程指引</el-button>
        <el-button text @click="logout">退出</el-button>
      </div>
    </header>

    <main v-loading="loading" class="main-content">
      <!-- 身份选择提示区 - 只在首次且未确认时显示 -->
      <div v-if="showIdentityPrompt" class="identity-prompt">
        <div class="prompt-icon">👤</div>
        <h2>尚未选择劳动者类型</h2>
        <p>选择后将为您匹配专属仲裁场景、证据清单与文书结构</p>
        <el-button type="primary" round size="large" @click="showType = true">
          去选择
        </el-button>
      </div>

      <!-- 已选择身份时显示的内容 -->
      <template v-else>
        <!-- 欢迎标题区 -->
        <div class="welcome-section">
          <h1>您好，欢迎使用仲裁辅助系统</h1>
          <p>高频功能快速入口</p>
          <div class="welcome-line"></div>
        </div>

        <!-- 功能卡片网格 -->
        <div class="tiles-grid">
          <button
            v-for="tile in tiles"
            :key="tile.to"
            type="button"
            class="tile-card"
            @click="$router.push(tile.to)"
          >
            <div class="tile-icon" :class="tile.colorClass">
              {{ tile.icon }}
            </div>
            <div class="tile-info">
              <div class="tile-title">{{ tile.title }}</div>
              <div class="tile-sub">{{ tile.sub }}</div>
            </div>
            <span class="tile-arrow">→</span>
          </button>
        </div>

        <!-- 仲裁知识区 -->
        <div class="faq-section">
          <h2 class="section-title">仲裁高频问题</h2>
          
          <div class="faq-grid">
            <div
              v-for="(f, i) in faqItems"
              :key="i"
              class="faq-card"
            >
              <div class="faq-number">{{ i + 1 }}</div>
              <div class="faq-content">
                <div class="faq-q">{{ f.q }}</div>
                <p class="faq-a">{{ f.a }}</p>
              </div>
            </div>
          </div>

          <!-- 空状态提示 -->
          <div v-if="faqItems.length === 0" class="empty-state">
            <div class="empty-icon">📋</div>
            <p>暂无相关问题</p>
          </div>
        </div>
      </template>
    </main>

    <LaborTypeModal v-model="showType" @confirm="onLaborType" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useAuthStore } from "../stores/auth";
import http from "../api/http";
import LaborTypeModal from "../components/LaborTypeModal.vue";

const auth = useAuthStore();
const loading = ref(true);
const faqItems = ref([]);
const showType = ref(false);
const identityConfirmed = ref(false); // 是否已确认身份选择

// 是否显示身份选择提示
const showIdentityPrompt = computed(() => {
  return !identityConfirmed.value;
});

const typeLabel = computed(() => {
  const m = {
    dispatch: "劳务派遣员工",
    intern: "在校实习生",
    platform: "外卖/快递/网约车",
    other_uncertain: "其他/不确定",
    courier: "外卖骑手",
  };
  return m[auth.laborerType] || "";
});

const tiles = computed(() => {
  const base = [
    { title: "我的案件", sub: "案件管理", to: "/mycases", icon: "📁", colorClass: "icon-rose" },
    { title: "类型判定", sub: "判定劳动关系", to: "/classify", icon: "🧭", colorClass: "icon-sky" },
    { title: "智能对话", sub: "AI 咨询", to: "/agent", icon: "💬", colorClass: "icon-emerald" },
    { title: "证据上传", sub: "OCR 识别", to: "/evidence", icon: "📄", colorClass: "icon-indigo" },
    { title: "文书生成", sub: "得理支撑", to: "/document", icon: "📝", colorClass: "icon-violet" },
    { title: "金额估算", sub: "辅助计算", to: "/calc", icon: "🧮", colorClass: "icon-amber" },
    { title: "法条检索", sub: "法规查询", to: "/law-search", icon: "📖", colorClass: "icon-sky" },
  ];
  return base;
});

onMounted(async () => {
  try {
    await auth.fetchMe();
    if (auth.laborerType) {
      identityConfirmed.value = true;
      await loadFaq();
    }
  } finally {
    loading.value = false;
  }
});

watch(
  () => auth.laborerType,
  (v) => {
    if (v) loadFaq();
  }
);

async function loadFaq() {
  if (!auth.laborerType) return;
  const { data } = await http.get("/labor/faq", { params: { laborer_type: auth.laborerType } });
  faqItems.value = data.items || [];
}

async function onLaborType(t) {
  await auth.setLaborerType(t, false);
  identityConfirmed.value = true;
  await loadFaq();
}

function logout() {
  auth.logout();
  window.location.hash = "#/login";
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background-color: #f2f3f5;
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
}

/* 顶部导航栏 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 24px;
  background-color: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 30;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.logo-tag {
  font-size: 12px;
  color: #396af6;
  background-color: #ecf5ff;
  padding: 2px 8px;
  border-radius: 10px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 主内容区 */
.main-content {
  padding: 24px 16px;
  max-width: 1600px;
  margin: 0 auto;
}

/* 功能卡片网格 - 更紧凑 */
.tiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 32px;
}

/* FAQ 区 - 更紧凑 */
.faq-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
}

/* 身份选择提示 */
.identity-prompt {
  text-align: center;
  padding: 60px 40px;
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: 0px 12px 32px 4px rgba(0, 0, 0, 0.04), 0px 8px 20px rgba(0, 0, 0, 0.08);
}

.prompt-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.identity-prompt h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.identity-prompt p {
  font-size: 14px;
  color: #909399;
  margin-bottom: 24px;
}

/* 欢迎区 */
.welcome-section {
  margin-bottom: 32px;
}

.welcome-section h1 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.welcome-section p {
  font-size: 14px;
  color: #909399;
}

.welcome-line {
  width: 120px;
  height: 4px;
  background: linear-gradient(90deg, #396af6, #5c85ff);
  border-radius: 2px;
  margin-top: 16px;
}

/* 功能卡片网格 */
.tiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 40px;
}

.tile-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  background-color: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.tile-card:hover {
  border-color: #396af6;
  box-shadow: 0 4px 16px rgba(57, 106, 246, 0.15);
  transform: translateY(-2px);
}

.tile-icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #ffffff;
  flex-shrink: 0;
}

.icon-sky { background: linear-gradient(135deg, #2bb1e8, #42b8dd); }
.icon-emerald { background: linear-gradient(135deg, #13c38e, #21ba45); }
.icon-indigo { background: linear-gradient(135deg, #5c4fcf, #6574d9); }
.icon-violet { background: linear-gradient(135deg, #8b5cf6, #a855f7); }
.icon-amber { background: linear-gradient(135deg, #f59e0b, #f2711c); }
.icon-slate { background: linear-gradient(135deg, #64748b, #475569); }

.tile-info {
  flex: 1;
  min-width: 0;
}

.tile-title {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 2px;
}

.tile-sub {
  font-size: 12px;
  color: #909399;
}

.tile-arrow {
  font-size: 16px;
  color: #c0c4cc;
  transition: color 0.2s;
}

.tile-card:hover .tile-arrow {
  color: #396af6;
}

/* FAQ 区 */
.faq-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title::before {
  content: "";
  width: 4px;
  height: 20px;
  background-color: #396af6;
  border-radius: 2px;
}

.faq-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.faq-card {
  display: flex;
  gap: 14px;
  padding: 18px;
  background-color: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  transition: all 0.2s;
}

.faq-card:hover {
  border-color: #396af6;
  box-shadow: 0 4px 12px rgba(57, 106, 246, 0.1);
}

.faq-number {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background-color: #ecf5ff;
  color: #396af6;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.faq-q {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
}

.faq-a {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px;
  color: #909399;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
</style>
