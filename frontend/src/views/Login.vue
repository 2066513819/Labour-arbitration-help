<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
    </div>
    
    <div class="login-container">
      <!-- Logo 区域 -->
      <div class="logo-section">
        <div class="logo-icon">⚖️</div>
        <h1>劳动仲裁帮</h1>
        <p>多类劳动者细分场景 · 务实可落地</p>
      </div>
      
      <!-- 登录表单卡片 -->
      <div class="login-card">
        <!-- 登录方式切换 -->
        <div class="login-tabs">
          <button
            :class="['tab-btn', { active: loginMode === 'phone' }]"
            @click="loginMode = 'phone'"
          >📱 手机号登录</button>
          <button
            :class="['tab-btn', { active: loginMode === 'email' }]"
            @click="loginMode = 'email'"
          >📧 邮箱登录</button>
        </div>

        <el-form label-position="top" @submit.prevent>
          <!-- 手机号输入 -->
          <el-form-item v-if="loginMode === 'phone'" label="手机号">
            <el-input
              v-model="phone"
              maxlength="11"
              placeholder="请输入11位手机号"
              size="large"
            >
              <template #prefix>
                <span class="input-icon">📱</span>
              </template>
            </el-input>
          </el-form-item>

          <!-- 邮箱输入 -->
          <el-form-item v-if="loginMode === 'email'" label="邮箱">
            <el-input
              v-model="email"
              placeholder="请输入邮箱地址"
              size="large"
            >
              <template #prefix>
                <span class="input-icon">📧</span>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="验证码">
            <div class="code-input-wrapper">
              <el-input
                v-model="code"
                maxlength="6"
                placeholder="验证码"
                size="large"
              >
                <template #prefix>
                  <span class="input-icon">🔐</span>
                </template>
              </el-input>
              <el-button
                size="large"
                :disabled="sending"
                class="code-btn"
                @click="onSendCode"
              >
                {{ sending ? "发送中" : "获取验证码" }}
              </el-button>
            </div>
          </el-form-item>
          
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            size="large"
            @click="onLogin"
          >
            登录 / 注册
          </el-button>
        </el-form>
      </div>
      
      <!-- 底部提示 -->
      <p class="agreement">
        登录即表示同意《用户协议》和《隐私政策》
      </p>
      <p v-if="loginMode === 'email'" class="email-hint">
        💡 邮箱验证码通过 SMTP 真实发送，零资质门槛
      </p>
    </div>

    <LaborTypeModal v-model="showType" allow-skip @confirm="onLaborType" />
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import LaborTypeModal from "../components/LaborTypeModal.vue";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const loginMode = ref("phone"); // "phone" | "email"
const phone = ref("");
const email = ref("");
const code = ref("");
const loading = ref(false);
const sending = ref(false);
const showType = ref(false);

async function onSendCode() {
  if (loginMode.value === "phone") {
    if (!/^1\d{10}$/.test(phone.value)) {
      ElMessage.warning("请输入正确手机号");
      return;
    }
  } else {
    if (!email.value || !email.value.includes("@")) {
      ElMessage.warning("请输入正确的邮箱地址");
      return;
    }
  }

  sending.value = true;
  try {
    if (loginMode.value === "phone") {
      await auth.sendCode(phone.value);
    } else {
      await auth.sendEmailCode(email.value);
    }
    ElMessage.success("验证码已发送");
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || "发送失败，请确认后端已启动（127.0.0.1:8000）");
  } finally {
    sending.value = false;
  }
}

async function onLogin() {
  if (loginMode.value === "phone") {
    if (!/^1\d{10}$/.test(phone.value) || !code.value) {
      ElMessage.warning("请填写手机号与验证码");
      return;
    }
  } else {
    if (!email.value || !email.value.includes("@") || !code.value) {
      ElMessage.warning("请填写邮箱与验证码");
      return;
    }
  }

  loading.value = true;
  try {
    if (loginMode.value === "phone") {
      await auth.smsLogin(phone.value, code.value);
    } else {
      await auth.emailLogin(email.value, code.value);
    }
    showType.value = true;
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || "登录失败，请确认后端已启动（127.0.0.1:8000）");
  } finally {
    loading.value = false;
  }
}

async function onLaborType(type) {
  await auth.setLaborerType(type, false);
  ElMessage.success("已保存劳动者类型");
  const redirect = route.query.redirect || "/";
  router.push(redirect);
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f2f3f5;
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.5;
}

.circle-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #ecf5ff, #d9ecff);
  top: -100px;
  right: -100px;
}

.circle-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #f0f9eb, #e1f3d8);
  bottom: -50px;
  left: -50px;
}

/* 登录容器 */
.login-container {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  position: relative;
  z-index: 1;
}

/* Logo 区域 */
.logo-section {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, #396af6, #2952d8);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  box-shadow: 0 8px 24px rgba(57, 106, 246, 0.3);
}

.logo-section h1 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.logo-section p {
  font-size: 14px;
  color: #909399;
}

/* 登录卡片 */
.login-card {
  background-color: #ffffff;
  border-radius: 10px;
  padding: 32px;
  box-shadow: 0px 12px 32px 4px rgba(0, 0, 0, 0.04), 0px 8px 20px rgba(0, 0, 0, 0.08);
}

/* 登录方式切换标签 */
.login-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #e4e7ed;
}

.tab-btn {
  flex: 1;
  padding: 10px 0;
  border: none;
  background: #f5f7fa;
  color: #909399;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn.active {
  background: #396af6;
  color: #fff;
  font-weight: 500;
}

.tab-btn:not(.active):hover {
  background: #ecf5ff;
  color: #396af6;
}

.login-card :deep(.el-form-item__label) {
  font-size: 14px;
  color: #606266;
  padding-bottom: 8px;
}

.login-card :deep(.el-input__wrapper) {
  border-radius: 4px;
}

.input-icon {
  font-size: 16px;
}

.code-input-wrapper {
  display: flex;
  gap: 12px;
}

.code-input-wrapper :deep(.el-input) {
  flex: 1;
}

.code-btn {
  border-radius: 4px;
  white-space: nowrap;
}

.code-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.highlight {
  color: #396af6;
  font-weight: 500;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 4px;
  font-size: 16px;
  margin-top: 8px;
  background: linear-gradient(135deg, #396af6, #2952d8);
  border: none;
}

.login-btn:hover {
  background: linear-gradient(135deg, #2952d8, #1e40af);
}

/* 协议 */
.agreement {
  text-align: center;
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 24px;
}

.email-hint {
  text-align: center;
  font-size: 12px;
  color: #67c23a;
  margin-top: 8px;
}
</style>
