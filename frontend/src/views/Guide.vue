<template>
  <div class="max-w-3xl mx-auto px-4 py-8 min-h-screen">
    <el-page-header @back="$router.push('/')">
      <template #content>
        <span class="text-lg font-semibold">流程指引</span>
      </template>
    </el-page-header>

    <div v-loading="loading" class="mt-6 space-y-6">
      <div class="arb-paper p-6">
        <h3 class="font-semibold text-slate-800 mb-2">仲裁委与管辖</h3>
        <p class="text-sm text-slate-600">{{ guide.commission_hint }}</p>
        <el-button class="mt-3" round type="primary" @click="openMap">尝试地图检索附近仲裁委</el-button>
      </div>
      <div class="arb-paper p-6">
        <h3 class="font-semibold text-slate-800 mb-3">步骤</h3>
        <ol class="space-y-3">
          <li
            v-for="(s, i) in guide.steps"
            :key="i"
            class="flex gap-3 text-sm text-slate-700"
          >
            <span
              class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-indigo-500 text-white text-xs font-bold"
            >
              {{ i + 1 }}
            </span>
            <span>{{ s }}</span>
          </li>
        </ol>
      </div>
      <div class="arb-paper p-6">
        <h3 class="font-semibold text-slate-800 mb-2">材料清单</h3>
        <ul class="list-disc pl-5 text-sm text-slate-600 space-y-1">
          <li v-for="(m, i) in guide.materials" :key="i">{{ m }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import http from "../api/http";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const loading = ref(true);
const guide = reactive({
  steps: [],
  materials: [],
  commission_hint: "",
});

onMounted(async () => {
  const lt = auth.laborerType || "other_uncertain";
  try {
    const { data } = await http.get("/labor/guide", { params: { laborer_type: lt } });
    guide.steps = data.steps || [];
    guide.materials = data.materials || [];
    guide.commission_hint = data.commission_hint || "";
  } finally {
    loading.value = false;
  }
});

function openMap() {
  // 跳转到百度地图，搜索"劳动仲裁委员会"
  window.open("https://map.baidu.com/search/%E5%8A%B3%E5%8A%A8%E4%BB%B2%E8%A3%81%E5%A7%94%E5%91%98%E4%BC%9A/@13238314.071981376,3928672.275059101,11.08z?querytype=s&c=162&wd=%E5%8A%B3%E5%8A%A8%E4%BB%B2%E8%A3%81%E5%A7%94%E5%91%98%E4%BC%9A&da_src=shareurl&on_gel=1&l=11&gr=1&b=(13102529.311528385,3864292.563944687;13306506.373071324,3959619.136055313)&pn=0&device_ratio=2", "_blank");
  ElMessage.info("已打开地图检索，请以当地官方信息为准");
}
</script>
