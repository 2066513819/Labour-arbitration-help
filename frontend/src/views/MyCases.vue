<template>
  <div class="min-h-screen bg-slate-50">
    <!-- 顶部导航 -->
    <div class="bg-white border-b sticky top-0 z-10">
      <div class="max-w-5xl mx-auto px-4">
        <div class="flex items-center justify-between h-14">
          <div class="flex items-center gap-4">
            <el-button text @click="$router.push('/')">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <h1 class="text-lg font-semibold">我的案件</h1>
          </div>
          <div>
            <el-button type="primary" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon>
              新建案件
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-5xl mx-auto px-4 py-6">
      <!-- 统计卡片 -->
      <div class="grid grid-cols-3 gap-3 mb-6">
        <div class="arb-paper p-4 text-center">
          <div class="text-2xl font-bold text-slate-700">{{ stats.total }}</div>
          <div class="text-xs text-slate-400 mt-1">总案件数</div>
        </div>
        <div class="arb-paper p-4 text-center">
          <div class="text-2xl font-bold text-blue-600">{{ stats.ongoing }}</div>
          <div class="text-xs text-slate-400 mt-1">进行中</div>
        </div>
        <div class="arb-paper p-4 text-center">
          <div class="text-2xl font-bold text-green-600">{{ stats.completed }}</div>
          <div class="text-xs text-slate-400 mt-1">已完成</div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-12 text-slate-400">
        <el-icon class="is-loading text-3xl"><Loading /></el-icon>
        <div class="mt-3">加载中...</div>
      </div>

      <!-- 空状态 -->
      <div v-else-if="cases.length === 0" class="arb-paper p-12 text-center">
        <div class="text-6xl mb-4 opacity-30">📋</div>
        <h2 class="text-lg font-medium text-slate-700 mb-2">暂无案件</h2>
        <p class="text-slate-500 mb-6">点击「新建案件」开始创建您的第一个案件</p>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建案件
        </el-button>
      </div>

      <!-- 案件列表 -->
      <div v-else class="space-y-4">
        <div
          v-for="item in cases"
          :key="item.id"
          class="arb-paper p-5 hover:shadow-md transition-shadow cursor-pointer"
          @click="openCase(item)"
        >
          <!-- 案件头部 -->
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <h3 class="font-semibold text-slate-800 truncate">{{ item.title }}</h3>
                <el-tag
                  :type="getStatusType(item.case_status)"
                  size="small"
                >
                  {{ item.case_status }}
                </el-tag>
              </div>
              <div class="text-sm text-slate-500">
                场景：{{ item.scenario_id }} · 证据：{{ item.evidence_count }} 个
              </div>
            </div>
            <div class="flex items-center gap-2">
              <el-button size="small" @click.stop="editCase(item)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button size="small" type="danger" @click.stop="deleteCase(item)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>

          <!-- 案件备注 -->
          <div v-if="item.case_notes" class="mt-3 p-3 bg-slate-50 rounded-lg">
            <div class="text-xs text-slate-400 mb-1">备注</div>
            <div class="text-sm text-slate-600 line-clamp-2">{{ item.case_notes }}</div>
          </div>

          <!-- 员工信息 -->
          <div v-if="item.entry_date || item.quit_date || item.average_salary || item.bonus_info" class="mt-3 p-3 bg-blue-50 rounded-lg">
            <div class="text-xs text-blue-400 mb-1">员工信息</div>
            <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-slate-600">
              <div v-if="item.entry_date">入职：{{ item.entry_date }}</div>
              <div v-if="item.quit_date">离职：{{ item.quit_date }}</div>
              <div v-if="item.average_salary">月均工资：{{ item.average_salary }}</div>
              <div v-if="item.bonus_info">奖金：{{ item.bonus_info }}</div>
            </div>
          </div>

          <!-- 时间信息 -->
          <div class="mt-3 flex items-center justify-between text-xs text-slate-400">
            <span>创建于 {{ formatDate(item.created_at) }}</span>
            <span>更新于 {{ formatDate(item.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建案件对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建案件" width="560px">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="案件名称" required>
          <el-input v-model="createForm.title" placeholder="如：张三诉XX公司劳动纠纷" />
        </el-form-item>
        <el-form-item label="场景ID" required>
          <el-input v-model="createForm.scenario_id" placeholder="场景编号" />
        </el-form-item>
        <el-divider content-position="left">员工信息（选填）</el-divider>
        <el-form-item label="入职日期">
          <el-input v-model="createForm.entry_date" placeholder="如：2023-03-01 或 2023年3月" />
        </el-form-item>
        <el-form-item label="离职日期">
          <el-input v-model="createForm.quit_date" placeholder="如：2025-01-15" />
        </el-form-item>
        <el-form-item label="月均工资">
          <el-input v-model="createForm.average_salary" placeholder="如：8000元 或 8000" />
        </el-form-item>
        <el-form-item label="奖金信息">
          <el-input v-model="createForm.bonus_info" type="textarea" :rows="2" placeholder="如：年终奖2个月，被辞退前尚未发放" />
        </el-form-item>
        <el-divider content-position="left">其他</el-divider>
        <el-form-item label="备注">
          <el-input v-model="createForm.case_notes" type="textarea" :rows="2" placeholder="可选：案件相关备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑案件对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑案件" width="560px">
      <el-form :model="editForm" label-width="90px">
        <el-form-item label="案件名称">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="案件状态">
          <el-select v-model="editForm.case_status" class="w-full">
            <el-option label="🟡 进行中" value="进行中" />
            <el-option label="🟢 已完成" value="已完成" />
            <el-option label="⚪ 已搁置" value="已搁置" />
          </el-select>
        </el-form-item>
        <el-divider content-position="left">员工信息</el-divider>
        <el-form-item label="入职日期">
          <el-input v-model="editForm.entry_date" placeholder="如：2023-03-01 或 2023年3月" />
        </el-form-item>
        <el-form-item label="离职日期">
          <el-input v-model="editForm.quit_date" placeholder="如：2025-01-15" />
        </el-form-item>
        <el-form-item label="月均工资">
          <el-input v-model="editForm.average_salary" placeholder="如：8000元 或 8000" />
        </el-form-item>
        <el-form-item label="奖金信息">
          <el-input v-model="editForm.bonus_info" type="textarea" :rows="2" placeholder="如：年终奖2个月，被辞退前尚未发放" />
        </el-form-item>
        <el-divider content-position="left">其他</el-divider>
        <el-form-item label="备注">
          <el-input v-model="editForm.case_notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Plus, Edit, Delete, ArrowLeft, Loading } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import http from "../api/http";
import { useFlowStore } from "../stores/flow";

const router = useRouter();
const flow = useFlowStore();

const loading = ref(false);
const creating = ref(false);
const saving = ref(false);
const cases = ref([]);

// 统计
const stats = computed(() => ({
  total: cases.value.length,
  ongoing: cases.value.filter(c => c.case_status === "进行中").length,
  completed: cases.value.filter(c => c.case_status === "已完成").length,
}));

// 新建表单
const showCreateDialog = ref(false);
const createForm = reactive({
  title: "",
  scenario_id: "",
  case_notes: "",
  entry_date: "",
  quit_date: "",
  average_salary: "",
  bonus_info: "",
});

// 编辑表单
const showEditDialog = ref(false);
const editForm = reactive({
  id: null,
  title: "",
  case_status: "进行中",
  case_notes: "",
  entry_date: "",
  quit_date: "",
  average_salary: "",
  bonus_info: "",
});

onMounted(() => loadCases());

async function loadCases() {
  loading.value = true;
  try {
    const { data } = await http.get("/cases");
    cases.value = data.items || [];
  } catch (e) {
    console.error("加载案件失败:", e);
    ElMessage.error("加载案件列表失败");
  } finally {
    loading.value = false;
  }
}

async function submitCreate() {
  if (!createForm.title || !createForm.scenario_id) {
    ElMessage.warning("请填写案件名称和场景ID");
    return;
  }

  creating.value = true;
  try {
    const scenarioId = createForm.scenario_id;
    const { data } = await http.post("/cases", {
      title: createForm.title,
      scenario_id: scenarioId,
      case_notes: createForm.case_notes,
      entry_date: createForm.entry_date,
      quit_date: createForm.quit_date,
      average_salary: createForm.average_salary,
      bonus_info: createForm.bonus_info,
    });
    ElMessage.success("案件创建成功");
    showCreateDialog.value = false;
    createForm.title = "";
    createForm.scenario_id = "";
    createForm.case_notes = "";
    createForm.entry_date = "";
    createForm.quit_date = "";
    createForm.average_salary = "";
    createForm.bonus_info = "";
    loadCases();

    // 跳转到证据管理
    if (data.id) {
      flow.setCase({ caseId: data.id, scenarioId: scenarioId });
      router.push("/evidence");
    }
  } catch (e) {
    ElMessage.error("创建失败");
  } finally {
    creating.value = false;
  }
}

function editCase(item) {
  editForm.id = item.id;
  editForm.title = item.title;
  editForm.case_status = item.case_status || "进行中";
  editForm.case_notes = item.case_notes || "";
  editForm.entry_date = item.entry_date || "";
  editForm.quit_date = item.quit_date || "";
  editForm.average_salary = item.average_salary || "";
  editForm.bonus_info = item.bonus_info || "";
  showEditDialog.value = true;
}

async function submitEdit() {
  saving.value = true;
  try {
    await http.patch(`/cases/${editForm.id}`, {
      title: editForm.title,
      case_status: editForm.case_status,
      case_notes: editForm.case_notes,
      entry_date: editForm.entry_date,
      quit_date: editForm.quit_date,
      average_salary: editForm.average_salary,
      bonus_info: editForm.bonus_info,
    });
    ElMessage.success("保存成功");
    showEditDialog.value = false;
    loadCases();
  } catch (e) {
    ElMessage.error("保存失败");
  } finally {
    saving.value = false;
  }
}

async function deleteCase(item) {
  try {
    await ElMessageBox.confirm(
      `确定要删除案件「${item.title}」吗？\n注意：同时会删除该案件下的所有证据！`,
      "删除确认",
      { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" }
    );
    await http.delete(`/cases/${item.id}`);
    ElMessage.success("删除成功");
    loadCases();
  } catch (e) {
    if (e !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
}

function openCase(item) {
  // 设置当前案件并跳转到证据管理
  flow.setCase({
    caseId: item.id,
    scenarioId: item.scenario_id,
    scenarioTitle: item.title,
  });
  router.push("/evidence");
}

function getStatusType(status) {
  const map = { "进行中": "warning", "已完成": "success", "已搁置": "info" };
  return map[status] || "info";
}

function formatDate(dateStr) {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
