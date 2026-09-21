import { defineStore } from "pinia";
import { ref, computed } from "vue";
import http from "../api/http";

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("token") || "");
  const phoneMasked = ref("");
  const laborerType = ref(localStorage.getItem("laborerType") || "");

  const isLoggedIn = computed(() => !!token.value);

  async function sendCode(phone) {
    const { data } = await http.post("/auth/send-code", { phone });
    return data;
  }

  async function smsLogin(phone, code) {
    const { data } = await http.post("/auth/sms-login", { phone, code });
    token.value = data.access_token;
    localStorage.setItem("token", data.access_token);
    await fetchMe();
    return data;
  }

  // ── 邮箱登录 ──
  async function sendEmailCode(email) {
    const { data } = await http.post("/auth/send-email-code", { email });
    return data;
  }

  async function emailLogin(email, code) {
    const { data } = await http.post("/auth/email-login", { email, code });
    token.value = data.access_token;
    localStorage.setItem("token", data.access_token);
    await fetchMe();
    return data;
  }

  async function fetchMe() {
    const { data } = await http.get("/auth/me");
    phoneMasked.value = data.phone;
    if (data.laborer_type) {
      laborerType.value = data.laborer_type;
      localStorage.setItem("laborerType", data.laborer_type);
    }
    return data;
  }

  async function setLaborerType(type, inferred = false) {
    await http.put("/auth/me/laborer-type", {
      laborer_type: type,
      inferred_from_flow: inferred,
    });
    laborerType.value = type;
    localStorage.setItem("laborerType", type);
  }

  function logout() {
    token.value = "";
    laborerType.value = "";
    localStorage.removeItem("token");
    localStorage.removeItem("laborerType");
  }

  return {
    token,
    phoneMasked,
    laborerType,
    isLoggedIn,
    sendCode,
    smsLogin,
    sendEmailCode,
    emailLogin,
    fetchMe,
    setLaborerType,
    logout,
  };
});
