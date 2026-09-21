import { createRouter, createWebHashHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const routes = [
  { path: "/login", name: "login", component: () => import("../views/Login.vue"), meta: { public: true } },
  { path: "/", name: "home", component: () => import("../views/Home.vue") },
  { path: "/mycases", name: "mycases", component: () => import("../views/MyCases.vue") },
  { path: "/agent", name: "agent", component: () => import("../views/AgentChat.vue") },
  { path: "/classify", name: "classify", component: () => import("../views/Classify.vue") },
  { path: "/evidence", name: "evidence", component: () => import("../views/Evidence.vue") },
  { path: "/document", name: "document", component: () => import("../views/Document.vue") },
  { path: "/guide", name: "guide", component: () => import("../views/Guide.vue") },
  { path: "/calc", name: "calc", component: () => import("../views/Calc.vue") },
  { path: "/law-search", name: "law-search", component: () => import("../views/LawSearch.vue") },
  { path: "/case-search", name: "case-search", component: () => import("../views/CaseSearch.vue") },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (to.meta.public) return true;
  if (!auth.token) return { name: "login", query: { redirect: to.fullPath } };
  return true;
});

export default router;
