/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#396af6",
          light: "#5c85ff",
          dark: "#2952d8",
        },
        law: {
          primary: "#396af6",
          success: "#21ba45",
          warning: "#f2711c",
          danger: "#db2828",
          info: "#42b8dd",
          bg: "#f2f3f5",
          text: "#303133",
          "text-secondary": "#606266",
          "text-muted": "#909399",
          border: "#dcdfe6",
          "border-light": "#e4e7ed",
        },
      },
      fontFamily: {
        sans: [
          '"Helvetica Neue"',
          "Helvetica",
          '"PingFang SC"',
          '"Hiragino Sans GB"',
          '"Microsoft YaHei"',
          "微软雅黑",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        card: "0px 12px 32px 4px rgba(0, 0, 0, 0.04), 0px 8px 20px rgba(0, 0, 0, 0.08)",
        "card-light": "0px 0px 12px rgba(0, 0, 0, 0.12)",
      },
      borderRadius: {
        card: "10px",
      },
    },
  },
  plugins: [],
};
