<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "./services/api";
import { dateText } from "./utils/format";
import { store } from "./services/store";

const router = useRouter();
const route = useRoute();
const isPublic = computed(() => route.meta.public);
const notifications = ref([]);
const mails = ref([]);
const activePopover = ref("");
const activeMailTab = ref("new");
let refreshTimer;

const unreadNotifications = computed(() => notifications.value.filter((item) => !item.isRead));
const unreadMails = computed(() => mails.value.filter((mail) => !mail.isRead));
const favoriteMails = computed(() => mails.value.filter((mail) => mail.isFavorite));
const visiblePopupMails = computed(() => (activeMailTab.value === "new" ? unreadMails.value : favoriteMails.value));

async function loadNotificationSummary() {
  if (!store.user) {
    notifications.value = [];
    mails.value = [];
    return;
  }

  try {
    const data = await api("/notifications/api/");
    notifications.value = data.notifications;
    mails.value = data.mails;
  } catch {
    notifications.value = [];
    mails.value = [];
  }
}

async function togglePopover(name) {
  activePopover.value = activePopover.value === name ? "" : name;
  if (activePopover.value) {
    await loadNotificationSummary();
  }
}

function closePopover() {
  activePopover.value = "";
}

async function openNotification(item) {
  await api(`/notifications/api/notifications/${item.id}/read/`, { method: "POST" });
  await loadNotificationSummary();
  router.push(item.targetUrl || "/notifications/");
}

async function openMail(mail) {
  await api(`/notifications/api/mails/${mail.id}/read/`, { method: "POST" });
  await loadNotificationSummary();
  router.push(`/notifications/?mail=${mail.id}`);
}

async function markAllNotificationsRead() {
  await api("/notifications/api/notifications/read-all/", { method: "POST" });
  await loadNotificationSummary();
}

function handleDocumentClick(event) {
  if (!activePopover.value) return;
  if (!event.target.closest(".notification-menu")) {
    closePopover();
  }
}

async function logout() {
  await api("/accounts/api/logout/", { method: "POST" });
  store.user = null;
  notifications.value = [];
  mails.value = [];
  router.push("/accounts/login/");
}

watch(() => store.user?.id, loadNotificationSummary, { immediate: true });
watch(() => route.fullPath, closePopover);
onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
  refreshTimer = window.setInterval(loadNotificationSummary, 15000);
});
onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
  window.clearInterval(refreshTimer);
});
</script>

<template>
  <router-view v-if="isPublic" />
  <div v-else class="app-shell">
    <aside class="sidebar no-print">
      <router-link class="brand" to="/">Wafer Insight</router-link>
      <nav class="nav">
        <router-link to="/">대시보드</router-link>
        <router-link to="/analyses/upload/">분석 업로드</router-link>
        <router-link to="/analyses/history/">분석 이력</router-link>
        <router-link to="/community/">커뮤니티</router-link>
        <router-link to="/notifications/">알림/메일</router-link>
        <router-link to="/accounts/profile/">프로필</router-link>
        <a v-if="store.user?.isStaff" href="http://127.0.0.1:8000/admin/">관리자</a>
      </nav>
    </aside>
    <main class="content">
      <header class="topbar no-print">
        <div class="topbar-user">
          <div class="topbar-actions">
            <div class="notification-menu">
              <button class="notification-link" type="button" aria-label="알림" @click="togglePopover('notification')">
                <span class="notification-icon bell-icon" aria-hidden="true"></span>
                <span v-if="unreadNotifications.length > 0" class="notification-count">
                  {{ unreadNotifications.length > 99 ? "99+" : unreadNotifications.length }}
                </span>
              </button>
              <section v-if="activePopover === 'notification'" class="notification-popover">
                <div class="notification-popover-title">알림</div>
                <div class="notification-preview-list">
                  <button v-for="item in unreadNotifications" :key="item.id" class="notification-preview notification-preview-button" @click="openNotification(item)">
                    <strong>{{ item.title }}</strong>
                    <p>{{ dateText(item.createdAt) }}</p>
                  </button>
                  <p v-if="unreadNotifications.length === 0" class="notification-empty">
                    새로운 알림이 없습니다.
                  </p>
                </div>
                <div class="notification-popover-footer">
                  <button class="mark-all-link" type="button" @click="markAllNotificationsRead">모두 읽음으로 표시</button>
                  <router-link class="mail-link" to="/notifications/">알림/메일로 이동</router-link>
                </div>
              </section>
            </div>

            <div class="notification-menu">
              <button class="notification-link" type="button" aria-label="메일" @click="togglePopover('mail')">
                <span class="notification-icon mail-icon" aria-hidden="true"></span>
                <span v-if="unreadMails.length > 0" class="notification-count">
                  {{ unreadMails.length > 99 ? "99+" : unreadMails.length }}
                </span>
              </button>
              <section v-if="activePopover === 'mail'" class="notification-popover">
                <div class="notification-tabs">
                  <button
                    type="button"
                    :class="{ active: activeMailTab === 'new' }"
                    @click="activeMailTab = 'new'"
                  >
                    새로운 메일
                  </button>
                  <button
                    type="button"
                    :class="{ active: activeMailTab === 'favorite' }"
                    @click="activeMailTab = 'favorite'"
                  >
                    즐겨찾기한 메일
                  </button>
                </div>
                <div class="notification-preview-list">
                  <button v-for="mail in visiblePopupMails" :key="mail.id" class="notification-preview notification-preview-button" @click="openMail(mail)">
                    <strong>{{ mail.subject }}</strong>
                    <p>{{ mail.sender }} · {{ dateText(mail.createdAt) }}</p>
                  </button>
                  <p v-if="visiblePopupMails.length === 0" class="notification-empty">
                    표시할 메일이 없습니다.
                  </p>
                </div>
                <div class="notification-popover-footer">
                  <router-link class="mail-link" to="/notifications/">알림/메일로 이동</router-link>
                </div>
              </section>
            </div>
          </div>
          <span>{{ store.user?.displayName }} · {{ store.user?.department || "-" }}</span>
        </div>
        <button class="btn ghost" type="button" @click="logout">로그아웃</button>
      </header>
      <router-view />
    </main>
  </div>
</template>
