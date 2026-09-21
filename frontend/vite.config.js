import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      // 元器 API 代理（避免跨域）
      "/yuanqi": {
        target: "https://yuanqi.tencent.com",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/yuanqi/, ""),
      },
    },
  },
});
