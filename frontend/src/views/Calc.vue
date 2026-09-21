<template>
  <div class="min-h-screen bg-slate-100 p-4 md:p-6">
    <el-page-header @back="$router.push('/')">
      <template #content>
        <span class="text-lg font-semibold">仲裁金额估算</span>
      </template>
    </el-page-header>
    <p class="text-xs text-slate-500 mt-2 mb-4">演示计算，不构成法律意见</p>

    <div class="arb-paper p-4 md:p-6 space-y-5 max-w-2xl mx-auto">
      <!-- 计算模式选择 -->
      <el-select v-model="mode" placeholder="计算模式" class="w-full">
        <el-option label="经济补偿金（精确日期）" value="severance" />
        <el-option label="经济补偿金（简易计算）" value="severance_simple" />
        <el-option label="延时加班费" value="overtime" />
        <el-option label="欠发工资" value="unpaid_wage" />
        <el-option label="罚款争议核对" value="fine_dispute" />
      </el-select>

      <!-- 经济补偿金-精确模式 -->
      <template v-if="mode === 'severance'">
        <el-form label-position="top" class="space-y-4">
          <el-form-item label="入职日期" required>
            <el-date-picker
              v-model="entryDate"
              type="date"
              placeholder="选择入职日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              class="!w-full"
            />
          </el-form-item>
          
          <el-form-item label="离职日期" required>
            <el-date-picker
              v-model="lastWorkingDay"
              type="date"
              placeholder="选择离职日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              class="!w-full"
            />
          </el-form-item>
          
          <el-form-item label="离职前12个月税前平均月薪（元）" required>
            <el-input-number
              v-model="salary"
              :min="0"
              :precision="2"
              :step="100"
              placeholder="输入月薪"
              class="!w-full"
            />
          </el-form-item>
          
          <el-form-item label="离职原因">
            <el-select v-model="terminationReason" placeholder="选择或填写离职原因" clearable class="!w-full">
              <el-option label="协商一致解除" value="协商一致解除" />
              <el-option label="合同到期不续签" value="合同到期不续签" />
              <el-option label="员工主动辞职" value="员工主动辞职" />
              <el-option label="用人单位裁员" value="用人单位裁员" />
              <el-option label="违法解除/辞退" value="违法解除" />
              <el-option label="其他" value="其他" />
            </el-select>
          </el-form-item>
        </el-form>
      </template>

      <!-- 经济补偿金-简易模式 -->
      <template v-if="mode === 'severance_simple'">
        <el-input-number v-model="baseAmount" :min="0" :precision="2" placeholder="月工资" class="!w-full" />
        <el-input-number v-model="months" :min="0" :step="0.5" placeholder="工作年限" class="!w-full" />
        <p class="text-xs text-slate-500 mt-1">不满半年按0.5年计算</p>
      </template>

      <!-- 加班费 -->
      <template v-if="mode === 'overtime'">
        <el-input-number v-model="hours" :min="0" placeholder="加班小时数" class="!w-full" />
        <el-input-number v-model="hourlyRate" :min="0" :precision="2" placeholder="小时工资" class="!w-full" />
      </template>

      <!-- 欠发工资 -->
      <template v-if="mode === 'unpaid_wage'">
        <el-input-number v-model="baseAmount" :min="0" :precision="2" placeholder="应发工资金额" class="!w-full" />
      </template>

      <!-- 罚款争议 -->
      <template v-if="mode === 'fine_dispute'">
        <el-input-number v-model="fineAmount" :min="0" :precision="2" placeholder="罚款金额" class="!w-full" />
      </template>

      <!-- 计算按钮 -->
      <el-button type="primary" class="w-full !rounded-xl" round :loading="loading" @click="run">
        计算赔偿金额
      </el-button>

      <!-- 计算结果 -->
      <transition name="fade">
        <div v-if="result !== null" class="space-y-3">
          <!-- 主结果卡片 -->
          <div class="rounded-xl bg-gradient-to-br from-brand-50 to-brand-100 border border-brand-200 p-5 text-center">
            <div class="text-4xl font-bold text-brand-700 tabular-nums">¥ {{ result }}</div>
            <p class="text-sm text-brand-600 mt-2">{{ resultNote }}</p>
          </div>

          <!-- 详细结果 -->
          <div v-if="detailResult" class="bg-slate-50 rounded-xl p-4 space-y-2">
            <h4 class="font-semibold text-slate-700 text-sm mb-3">计算详情</h4>
            
            <div class="flex justify-between text-sm">
              <span class="text-slate-500">赔偿类型</span>
              <span class="text-slate-800 font-medium">{{ detailResult.legal_type }}</span>
            </div>
            
            <div class="flex justify-between text-sm">
              <span class="text-slate-500">工龄</span>
              <span class="text-slate-800 font-medium">{{ detailResult.work_period }}</span>
            </div>
            
            <div class="flex justify-between text-sm">
              <span class="text-slate-500">N 值</span>
              <span class="text-brand-600 font-bold">{{ detailResult.n_value }}</span>
            </div>
            
            <div class="flex justify-between text-sm">
              <span class="text-slate-500">月薪</span>
              <span class="text-slate-800 font-medium">¥ {{ salary?.toLocaleString() }}</span>
            </div>
            
            <div v-if="detailResult.multiplier" class="flex justify-between text-sm">
              <span class="text-slate-500">赔偿倍数</span>
              <span :class="detailResult.multiplier === 2 ? 'text-red-600' : 'text-slate-800'" class="font-bold">
                {{ detailResult.multiplier }}N
              </span>
            </div>
            
            <el-divider class="!my-2" />
            
            <div class="flex justify-between text-sm font-semibold">
              <span class="text-slate-600">合计</span>
              <span class="text-brand-700">¥ {{ detailResult.total_money }}</span>
            </div>
          </div>

          <!-- 法律提示 -->
          <div class="bg-amber-50 border border-amber-200 rounded-xl p-3">
            <p class="text-xs text-amber-700">
              <span class="font-semibold">⚠️ 提示：</span>
              本计算结果仅供参考，实际赔偿金额可能因具体情况而有所不同。
              违法解除劳动合同应支付 2N 赔偿金；正常解除支付 N 经济补偿。
              建议保留相关证据材料，必要时咨询专业律师。
            </p>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import http from "../api/http";
import { useAuthStore } from "../stores/auth";
import { ElMessage } from "element-plus";

const auth = useAuthStore();

// 计算模式
const mode = ref("severance");

// 精确模式参数
const entryDate = ref("");
const lastWorkingDay = ref("");
const salary = ref(5000);
const terminationReason = ref("");

// 简易模式参数
const baseAmount = ref(5000);
const months = ref(2);

// 加班模式参数
const hours = ref(20);
const hourlyRate = ref(30);

// 罚款模式参数
const fineAmount = ref(500);

// 状态
const loading = ref(false);
const result = ref(null);
const resultNote = ref("");
const detailResult = ref(null);

// 监听模式切换，重置结果
watch(mode, () => {
  result.value = null;
  resultNote.value = "";
  detailResult.value = null;
});

async function run() {
  loading.value = true;
  result.value = null;
  resultNote.value = "";
  detailResult.value = null;

  try {
    // 构建请求参数
    const requestData = {
      laborer_type: auth.laborerType || "other_uncertain",
      mode: mode.value === "severance_simple" ? "severance" : mode.value,
    };

    // 根据模式添加参数
    if (mode.value === "severance") {
      if (!entryDate.value || !lastWorkingDay.value) {
        ElMessage.warning("请填写完整的入职日期、离职日期和月薪");
        return;
      }
      requestData.entry_date = entryDate.value;
      requestData.last_working_day = lastWorkingDay.value;
      requestData.salary = salary.value;
      requestData.termination_reason = terminationReason.value;
    } else if (mode.value === "severance_simple") {
      requestData.base_amount = baseAmount.value;
      requestData.months = months.value;
    } else if (mode.value === "overtime") {
      requestData.hours = hours.value;
      requestData.hourly_rate = hourlyRate.value;
    } else if (mode.value === "unpaid_wage") {
      requestData.base_amount = baseAmount.value;
    } else if (mode.value === "fine_dispute") {
      requestData.fine_amount = fineAmount.value;
    }

    const { data } = await http.post("/calc/estimate", requestData);
    result.value = data.estimated_amount;
    resultNote.value = data.note;
    
    // 解析详细结果
    if (data.detail) {
      detailResult.value = data.detail;
    }
  } catch (error) {
    ElMessage.error("计算失败，请检查输入");
    console.error(error);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
