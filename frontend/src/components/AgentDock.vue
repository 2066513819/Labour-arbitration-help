<template>
  <div>
    <!-- 浮动按钮：点击打开/关闭侧边栏，支持拖拽 -->
    <button
      ref="dockBtn"
      type="button"
      class="dock-btn"
      :class="{ 'btn-active': sidebar.visible, 'dragging': isDragging }"
      :style="buttonStyle"
      aria-label="智能法律咨询"
      @mousedown="startDrag"
      @click="handleClick"
    >
      <span class="dock-icon">💬</span>
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useSidebarStore } from "../stores/sidebar";

const sidebar = useSidebarStore();
const dockBtn = ref(null);

// 按钮位置状态（使用像素定位）
const pos = ref({ x: 0, y: 0 });
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });
const buttonOffset = ref({ x: 0, y: 0 });
const hasDragged = ref(false);

// 计算按钮样式
const buttonStyle = computed(() => {
  // 如果 pos 有值，使用 left/top 定位；否则使用默认的 fixed bottom-right
  if (pos.value.x !== 0 || pos.value.y !== 0) {
    return {
      left: pos.value.x + 'px',
      top: pos.value.y + 'px',
      right: 'auto',
      bottom: 'auto',
    };
  }
  return {};
});

// 初始化位置到右下角
function initPosition() {
  if (dockBtn.value) {
    const rect = dockBtn.value.getBoundingClientRect();
    pos.value = {
      x: window.innerWidth - rect.width - 24,
      y: window.innerHeight - rect.height - 24,
    };
  }
}

function startDrag(e) {
  // 只有左键可以拖拽
  if (e.button !== 0) return;

  hasDragged.value = false;
  isDragging.value = true;

  // 记录鼠标按下时的位置
  dragStart.value = { x: e.clientX, y: e.clientY };

  // 记录按钮当前的偏移
  buttonOffset.value = { x: e.clientX - pos.value.x, y: e.clientY - pos.value.y };

  // 添加全局事件监听
  document.addEventListener('mousemove', onDrag);
  document.addEventListener('mouseup', stopDrag);
}

function onDrag(e) {
  if (!isDragging.value) return;

  const dx = Math.abs(e.clientX - dragStart.value.x);
  const dy = Math.abs(e.clientY - dragStart.value.y);

  // 移动超过 3px 视为拖拽
  if (dx > 3 || dy > 3) {
    hasDragged.value = true;
  }

  // 计算新位置
  let newX = e.clientX - buttonOffset.value.x;
  let newY = e.clientY - buttonOffset.value.y;

  // 限制在视口范围内
  const btnWidth = dockBtn.value?.offsetWidth || 56;
  const btnHeight = dockBtn.value?.offsetHeight || 56;

  newX = Math.max(0, Math.min(newX, window.innerWidth - btnWidth));
  newY = Math.max(0, Math.min(newY, window.innerHeight - btnHeight));

  pos.value = { x: newX, y: newY };
}

function stopDrag() {
  isDragging.value = false;
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', stopDrag);
}

function handleClick(e) {
  // 如果发生了拖拽，不触发点击
  if (hasDragged.value) {
    e.preventDefault();
    e.stopPropagation();
    return;
  }
  sidebar.toggle();
}

// 窗口大小改变时，确保按钮仍在可视区域内
function handleResize() {
  if (dockBtn.value) {
    const btnWidth = dockBtn.value.offsetWidth || 56;
    const btnHeight = dockBtn.value.offsetHeight || 56;
    pos.value.x = Math.min(pos.value.x, window.innerWidth - btnWidth);
    pos.value.y = Math.min(pos.value.y, window.innerHeight - btnHeight);
  }
}

onMounted(() => {
  initPosition();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  document.removeEventListener('mousemove', onDrag);
  document.removeEventListener('mouseup', stopDrag);
});
</script>

<style scoped>
.dock-btn {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #396af6, #2952d8);
  color: #ffffff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(57, 106, 246, 0.4);
  transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
  user-select: none;
  touch-action: none;
}
.dock-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 24px rgba(57, 106, 246, 0.5);
}
.dock-btn:active {
  transform: scale(0.95);
}
.dock-btn.dragging {
  transform: scale(1.05);
  box-shadow: 0 8px 32px rgba(57, 106, 246, 0.6);
  cursor: grabbing;
}
.dock-btn.btn-active {
  background: linear-gradient(135deg, #f56c6c, #e23c3c);
  box-shadow: 0 4px 16px rgba(245, 108, 108, 0.4);
}
.dock-icon {
  font-size: 24px;
  pointer-events: none;
}
</style>
