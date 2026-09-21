<template>
  <div class="min-h-screen flex">
    <aside
      v-if="showSidebar"
      class="w-60 shrink-0 border-r border-slate-200/70 bg-white/80 backdrop-blur px-3 py-4 sticky top-0 h-screen"
    >
      <div class="flex items-center gap-2 px-2">
        <div class="h-9 w-9 rounded-xl bg-gradient-to-br from-brand-500 to-indigo-500 text-white flex items-center justify-center font-bold">
          ⚖️
        </div>
        <div class="leading-tight">
          <div class="text-sm font-semibold text-slate-900">劳动仲裁帮</div>
          <div class="text-xs text-slate-500">智能法律服务</div>
        </div>
      </div>

      <div class="mt-5 grid gap-1">
        <button
          v-for="it in nav"
          :key="it.to"
          type="button"
          class="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition-colors"
          :class="isActive(it.to) ? 'bg-brand-50 text-brand-700 border border-brand-100' : 'text-slate-700 hover:bg-slate-50'"
          @click="go(it.to)"
        >
          <span class="w-5 text-center">{{ it.icon }}</span>
          <span class="flex-1 text-left">{{ it.label }}</span>
        </button>
      </div>

      <div class="mt-auto pt-6">
        <div class="px-3 text-xs text-slate-400">如遇页面一直转圈，通常是后端接口未启动或接口超时</div>
      </div>
    </aside>

    <main class="flex-1 min-w-0">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 全局侧边栏智能助手 -->
    <SidebarAssistant v-if="showSidebar" />

    <!-- 右下角浮动按钮 -->
    <AgentDock v-if="showSidebar" />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import SidebarAssistant from "./components/SidebarAssistant.vue";
import AgentDock from "./components/AgentDock.vue";

const route = useRoute();
const router = useRouter();

const showSidebar = computed(() => !route.meta?.public);

const nav = [
  { to: "/", label: "首页", icon: "🏠" },
  { to: "/mycases", label: "我的案件", icon: "📁" },
  { to: "/classify", label: "类型判定", icon: "🧭" },
  { to: "/agent", label: "智能对话", icon: "💬" },
  { to: "/law-search", label: "法条检索", icon: "📖" },
  { to: "/case-search", label: "案例检索", icon: "📋" },
  { to: "/document", label: "文书起草", icon: "📝" },
  { to: "/evidence", label: "证据上传", icon: "📄" },
  { to: "/guide", label: "流程指引", icon: "📋" },
  { to: "/calc", label: "金额估算", icon: "🧮" },
];

function go(to) {
  router.push(to);
}

function isActive(to) {
  if (to === "/") return route.path === "/";
  return route.path === to;
}
</script>
