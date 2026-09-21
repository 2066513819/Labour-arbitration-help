<template>
  <el-dialog
    v-model="innerVisible"
    title=""
    width="560px"
    class="labor-modal"
    :show-close="false"
    align-center
    append-to-body
    destroy-on-close
  >
    <div class="modal-content">
      <!-- 头部 -->
      <div class="modal-header">
        <div class="header-icon">👤</div>
        <h2>请选择您的劳动者类型</h2>
        <p>系统将匹配专属仲裁场景、证据清单与文书结构</p>
      </div>

      <!-- 选项列表 -->
      <div class="options-grid">
        <button
          v-for="item in items"
          :key="item.value"
          type="button"
          class="option-card"
          :class="{ selected: selected === item.value }"
          @click="selected = item.value"
        >
          <span class="option-badge" :class="item.accent">
            {{ item.short }}
          </span>
          <span class="option-info">
            <span class="option-label">{{ item.label }}</span>
            <span class="option-hint">{{ item.hint }}</span>
          </span>
        </button>
      </div>

      <!-- 底部按钮 -->
      <div class="modal-footer">
        <el-button
          type="primary"
          round
          size="large"
          :disabled="!selected"
          class="confirm-btn"
          @click="confirm"
        >
          确定
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue", "confirm"]);

const innerVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

const selected = ref("");

const items = [
  { value: "regular", label: "正式员工", short: "正", accent: "accent-blue", hint: "合同、社保、工资、辞退等" },
  { value: "dispatch", label: "劳务派遣员工", short: "派", accent: "accent-sky", hint: "同工同酬、社保责任等" },
  { value: "intern", label: "在校实习生", short: "习", accent: "accent-emerald", hint: "实习报酬、协议、证明" },
  { value: "platform", label: "外卖/快递/网约车", short: "平", accent: "accent-amber", hint: "接单、罚款、关系判定" },
  { value: "other_uncertain", label: "其他/不确定", short: "?", accent: "accent-slate", hint: "帮我做判断 / 引导判定类型" },
];

function confirm() {
  if (!selected.value) return;
  emit("confirm", selected.value);
  innerVisible.value = false;
}

watch(
  () => props.modelValue,
  (v) => {
    if (v) selected.value = "";
  }
);
</script>

<style scoped>
.modal-content {
  padding: 8px;
}

.modal-header {
  text-align: center;
  margin-bottom: 28px;
}

.header-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #396af6, #2952d8);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  box-shadow: 0 4px 16px rgba(57, 106, 246, 0.3);
}

.modal-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.modal-header p {
  font-size: 14px;
  color: #909399;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.option-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background-color: #ffffff;
  border: 2px solid #e4e7ed;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.option-card:hover {
  border-color: #396af6;
  background-color: #f8faff;
}

.option-card.selected {
  border-color: #396af6;
  background-color: #ecf5ff;
}

.option-badge {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  flex-shrink: 0;
}

.accent-blue { background: linear-gradient(135deg, #396af6, #2952d8); }
.accent-sky { background: linear-gradient(135deg, #2bb1e8, #42b8dd); }
.accent-emerald { background: linear-gradient(135deg, #13c38e, #21ba45); }
.accent-amber { background: linear-gradient(135deg, #f59e0b, #f2711c); }
.accent-slate { background: linear-gradient(135deg, #64748b, #475569); }
.accent-orange { background: linear-gradient(135deg, #f97316, #ea580c); }

.option-info {
  flex: 1;
  min-width: 0;
}

.option-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.option-hint {
  display: block;
  font-size: 12px;
  color: #909399;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
}

.skip-btn {
  color: #909399;
}

.skip-btn:hover {
  color: #606266;
}

.confirm-btn {
  padding: 0 32px;
  background: linear-gradient(135deg, #396af6, #2952d8);
  border: none;
}

.confirm-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #2952d8, #1e40af);
}
</style>

<style>
/* 全局样式覆盖 Element Plus 弹窗 */
.labor-modal .el-dialog {
  border-radius: 16px;
  overflow: hidden;
}

.labor-modal .el-dialog__body {
  padding: 32px;
}
</style>
