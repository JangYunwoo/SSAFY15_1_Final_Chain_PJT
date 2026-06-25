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
const sentMails = ref([]);
const activePopover = ref("");
const activeMailTab = ref("new");
const navOpen = ref(false);
const SUMMARY_REFRESH_MS = 5000;
let summaryTimer = null;

const unreadNotifications = computed(() => notifications.value.filter((item) => !item.isRead));
const unreadMails = computed(() => mails.value.filter((mail) => !mail.isRead));
const favoriteMails = computed(() => mails.value.filter((mail) => mail.isFavorite));
const visiblePopupMails = computed(() => (activeMailTab.value === "new" ? unreadMails.value : favoriteMails.value));

async function loadNotificationSummary() {
  if (!store.user) {
    notifications.value = [];
    mails.value = [];
    sentMails.value = [];
    return;
  }

  try {
    const data = await api("/notifications/api/");
    notifications.value = data.notifications;
    mails.value = data.mails;
    sentMails.value = data.sentMails || [];
  } catch {
    notifications.value = [];
    mails.value = [];
    sentMails.value = [];
  }
}

function stopSummaryPolling() {
  if (summaryTimer) {
    window.clearInterval(summaryTimer);
    summaryTimer = null;
  }
}

function startSummaryPolling() {
  stopSummaryPolling();
  if (!store.user) return;
  summaryTimer = window.setInterval(() => {
    if (!document.hidden) loadNotificationSummary();
  }, SUMMARY_REFRESH_MS);
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
  try {
    await api(`/notifications/api/notifications/${item.id}/read/`, { method: "POST" });
    item.isRead = true;
    notifications.value = notifications.value.map((notification) =>
      notification.id === item.id ? { ...notification, isRead: true } : notification
    );
  } catch {
    return;
  }

  closePopover();
  router.push(item.targetUrl || "/notifications/");
}

async function markAllNotificationsRead() {
  await api("/notifications/api/notifications/read-all/", { method: "POST" });
  notifications.value = notifications.value.map((item) => ({ ...item, isRead: true }));
  window.dispatchEvent(new Event("inbox-counts-updated"));
}

async function markAllMailsRead() {
  await api("/notifications/api/mails/read-all/", { method: "POST" });
  mails.value = mails.value.map((mail) => ({ ...mail, isRead: true }));
  window.dispatchEvent(new Event("inbox-counts-updated"));
}

function closeNav() {
  navOpen.value = false;
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
  sentMails.value = [];
  router.push("/accounts/login/");
}

watch(() => store.user?.id, () => {
  loadNotificationSummary();
  startSummaryPolling();
}, { immediate: true });
watch(() => route.fullPath, () => {
  closePopover();
  closeNav();
});
onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
  window.addEventListener("inbox-counts-updated", loadNotificationSummary);
  startSummaryPolling();
});
onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
  window.removeEventListener("inbox-counts-updated", loadNotificationSummary);
  stopSummaryPolling();
});
</script>

<template>
  <router-view v-if="isPublic" />
  <div v-else class="app-shell">
    <aside class="sidebar no-print" :class="{ open: navOpen }">
      <router-link class="brand" to="/">Wafer Insight</router-link>
      <nav class="nav">
        <router-link to="/">대시보드</router-link>
        <router-link to="/analyses/upload/">분석 업로드</router-link>
        <router-link to="/analyses/history/">분석 이력</router-link>
        <router-link to="/community/">커뮤니티</router-link>
        <router-link to="/accounts/users/">사용자</router-link>
        <router-link to="/accounts/profile/">프로필</router-link>
        <router-link v-if="store.user?.isStaff" to="/management/lot-assignments/">Line 배정</router-link>
        <a v-if="store.user?.isStaff" href="http://127.0.0.1:8000/admin/">관리자</a>
      </nav>
    </aside>
    <main class="content">
      <header class="topbar no-print">
        <button class="menu-toggle" type="button" :aria-expanded="navOpen" aria-label="메뉴" @click="navOpen = !navOpen">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 6h16"></path>
            <path d="M4 12h16"></path>
            <path d="M4 18h16"></path>
          </svg>
        </button>
        <div class="topbar-user">
          <span class="user-name">{{ store.user?.displayName }}</span>
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
                  <article v-for="item in unreadNotifications" :key="item.id" class="notification-preview">
                    <button class="notification-preview-title" type="button" @click="openNotification(item)">
                      {{ item.title }}
                    </button>
                    <p>{{ dateText(item.createdAt) }}</p>
                  </article>
                  <p v-if="unreadNotifications.length === 0" class="notification-empty">
                    새로운 알림이 없습니다.
                  </p>
                </div>
                <div class="notification-popover-footer">
                  <button class="mark-all-link" type="button" @click="markAllNotificationsRead">
                    모두 읽음으로 표시
                  </button>
                  <router-link class="mail-link" to="/notifications/">알림으로 이동</router-link>
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
                    즐겨찾기
                  </button>
                </div>
                <div class="notification-preview-list">
                  <article v-for="mail in visiblePopupMails" :key="mail.id" class="notification-preview">
                    <router-link class="notification-preview-title" :to="`/mails/${mail.id}/`">
                      {{ mail.subject }}
                    </router-link>
                    <p>보낸 사람: {{ mail.sender }} · {{ dateText(mail.createdAt) }}</p>
                  </article>
                  <p v-if="visiblePopupMails.length === 0" class="notification-empty">
                    표시할 메일이 없습니다.
                  </p>
                </div>
                <div class="notification-popover-footer">
                  <button class="mark-all-link" type="button" @click="markAllMailsRead">
                    모두 읽음으로 표시
                  </button>
                  <router-link class="mail-link" to="/mails/">메일로 이동</router-link>
                </div>
              </section>
            </div>
          </div>
        </div>
        <button class="btn ghost" type="button" @click="logout">로그아웃</button>
      </header>
      <router-view />
    </main>
  </div>
</template>
