import axios from "axios";

const http = axios.create({
  baseURL: "/api",
  timeout: 360000, // 6分钟
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/#/login";
    }
    return Promise.reject(err);
  }
);

export default http;
