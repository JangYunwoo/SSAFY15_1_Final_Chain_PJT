import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const djangoTarget = process.env.VITE_DJANGO_API_URL || "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/api": djangoTarget,
      "/accounts/api": djangoTarget,
      "/analyses/api": djangoTarget,
      "/community/api": djangoTarget,
      "/reports/api": djangoTarget,
      "/notifications/api": djangoTarget,
      "/media": djangoTarget,
      "/static": djangoTarget
    }
  }
});
