<template>
  <div class="max-w-xl mx-auto px-4 py-10 min-h-screen">
    <el-page-header @back="$router.push('/')">
      <template #content>
        <span class="text-lg font-semibold">劳动者类型判定</span>
      </template>
    </el-page-header>

    <div class="mt-8 rounded-2xl arb-paper p-6 shadow-card">
      <el-progress
        :percentage="Math.round(((step + 1) / steps.length) * 100)"
        :stroke-width="10"
        class="mb-8"
      />
      <transition name="slide-up" mode="out-in">
        <div v-if="cur" :key="cur.id">
          <h3 class="text-base font-medium text-slate-800 mb-4">{{ cur.question }}</h3>
          <el-radio-group v-model="answers[cur.id]" class="flex flex-col gap-2 w-full">
            <el-radio
              v-for="o in cur.options"
              :key="o.value"
              :label="o.value"
              border
              class="!mr-0 !w-full !rounded-xl !px-3 !py-2 !h-auto"
            >
              {{ o.label }}
            </el-radio>
          </el-radio-group>
        </div>
      </transition>
      <div class="flex justify-between mt-8">
        <el-button round :disabled="step === 0" @click="step--">上一步</el-button>
        <el-button type="primary" round :disabled="!canNext" @click="next">
          {{ step === steps.length - 1 ? "完成判定" : "下一步" }}
        </el-button>
      </div>
    </div>

    <el-result v-if="result" class="mt-6 rounded-2xl bg-emerald-50/50 border border-emerald-100" icon="success">
      <template #title>
        <span class="text-slate-800">判定结果：{{ labelOf(result.laborer_type) }}</span>
      </template>
      <template #sub-title>
        <p class="text-slate-600 text-sm">{{ result.reason }}</p>
      </template>
      <template #extra>
        <el-button type="primary" round @click="apply">采用此类型并返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import http from "../api/http";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const steps = ref([]);
const step = ref(0);
const answers = ref({});
const result = ref(null);

const cur = computed(() => steps.value[step.value]);
const canNext = computed(() => cur.value && answers.value[cur.value.id]);

onMounted(async () => {
  const { data } = await http.get("/labor/classification-flow");
  steps.value = data.steps || [];
});

function next() {
  if (step.value < steps.value.length - 1) {
    step.value++;
  } else {
    submit();
  }
}

async function submit() {
  const { data } = await http.post("/labor/classification-result", answers.value);
  result.value = data;
}

function labelOf(t) {
  const m = {
    dispatch: "劳务派遣员工",
    intern: "在校实习生",
    platform: "外卖/快递/网约车",
    courier: "外卖骑手",
    other_uncertain: "其他/不确定",
  };
  return m[t] || t;
}

async function apply() {
  if (!result.value) return;
  await auth.setLaborerType(result.value.laborer_type, true);
  router.push("/");
}
</script>
