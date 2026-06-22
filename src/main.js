import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";

import App from "./App.vue";
import "./assets/main.css";
import { api } from "./services/api";
import { store } from "./services/store";
import DashboardView from "./views/DashboardView.vue";
import LoginView from "./views/LoginView.vue";
import RegisterView from "./views/RegisterView.vue";
import UploadView from "./views/UploadView.vue";
import HistoryView from "./views/HistoryView.vue";
import BatchDetailView from "./views/BatchDetailView.vue";
import AnalysisDetailView from "./views/AnalysisDetailView.vue";
import CommunityListView from "./views/CommunityListView.vue";
import CommunityFormView from "./views/CommunityFormView.vue";
import CommunityDetailView from "./views/CommunityDetailView.vue";
import ReportFormView from "./views/ReportFormView.vue";
import InboxView from "./views/InboxView.vue";
import MailDetailView from "./views/MailDetailView.vue";
import ProfileView from "./views/ProfileView.vue";

const routes = [
  { path: "/accounts/login/", component: LoginView, meta: { public: true } },
  { path: "/accounts/register/", component: RegisterView, meta: { public: true } },
  { path: "/", component: DashboardView },
  { path: "/analyses/upload/", component: UploadView },
  { path: "/analyses/history/", component: HistoryView },
  { path: "/analyses/batches/:id/", component: BatchDetailView },
  { path: "/analyses/:id/", component: AnalysisDetailView },
  { path: "/analyses/:id/recommendations/", component: AnalysisDetailView },
  { path: "/reports/analysis/:id/new/", component: ReportFormView },
  { path: "/community/", component: CommunityListView },
  { path: "/community/new/", component: CommunityFormView },
  { path: "/community/:id/", component: CommunityDetailView },
  { path: "/notifications/", component: InboxView },
  { path: "/mails/", component: InboxView },
  { path: "/mails/:id/", component: MailDetailView },
  { path: "/accounts/profile/", component: ProfileView }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to) => {
  if (!store.ready && !to.meta.public) {
    const data = await api("/accounts/api/me/");
    store.user = data.user;
    store.ready = true;
  }
  if (!to.meta.public && !store.user) return "/accounts/login/";
  if (to.meta.public && store.user) return "/";
});

createApp(App).use(router).mount("#app");
