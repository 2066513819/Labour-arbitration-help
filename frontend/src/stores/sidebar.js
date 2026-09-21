import { defineStore } from "pinia";
import { ref, computed } from "vue";

export const useSidebarStore = defineStore("sidebar", () => {
  // 边栏是否可见
  const visible = ref(false);
  // 边栏宽度（px），默认 450，范围 360~800
  const width = ref(450);
  // 是否正在拖动调整宽度
  const resizing = ref(false);

  // 对话消息列表
  const messages = ref([]);
  // 是否正在发送
  const sending = ref(false);

  // 最小/最大宽度
  const MIN_WIDTH = 360;
  const MAX_WIDTH = 800;

  // 是否已登录（用于判断是否能发送消息）
  const isLoggedIn = computed(() => !!localStorage.getItem("token"));

  // 打开边栏
  function open() {
    visible.value = true;
    // 如果消息为空，添加欢迎消息
    if (messages.value.length === 0) {
      messages.value.push({
        role: "assistant",
        text: "你好！我是你的智能法律助手，有任何劳动仲裁相关问题，欢迎随时咨询我。",
      });
    }
  }

  // 关闭边栏
  function close() {
    visible.value = false;
  }

  // 切换显示状态
  function toggle() {
    if (visible.value) {
      close();
    } else {
      open();
    }
  }

  // 清空对话
  function clearMessages() {
    messages.value = [];
    // 重新添加欢迎消息
    messages.value.push({
      role: "assistant",
      text: "你好！我是你的智能法律助手，有任何劳动仲裁相关问题，欢迎随时咨询我。",
    });
  }

  // 添加用户消息
  function addUserMessage(text) {
    messages.value.push({ role: "user", text });
  }

  // 添加助手消息
  function addAssistantMessage(text) {
    messages.value.push({ role: "assistant", text });
  }

  // 设置发送状态
  function setSending(val) {
    sending.value = val;
  }

  // 开始拖动调整宽度
  function startResize(e) {
    resizing.value = true;
    const startX = e.clientX;
    const startWidth = width.value;

    // 防止拖动时选中页面文字
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    function onMove(e) {
      // 向右拖动（clientX 增大）→ 宽度减小（从右侧推入）
      const delta = startX - e.clientX;
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, startWidth + delta));
      width.value = newWidth;
    }

    function onUp() {
      resizing.value = false;
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    }

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }

  return {
    visible,
    width,
    resizing,
    messages,
    sending,
    isLoggedIn,
    MIN_WIDTH,
    MAX_WIDTH,
    open,
    close,
    toggle,
    clearMessages,
    addUserMessage,
    addAssistantMessage,
    setSending,
    startResize,
  };
});
