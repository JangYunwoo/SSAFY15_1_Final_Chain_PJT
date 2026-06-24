<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const route = useRoute();
const notifications = ref([]);
const mails = ref([]);
const sentMails = ref([]);
const users = ref([]);
const reports = ref([]);
const showComposer = ref(false);
const sending = ref(false);
const error = ref("");
const sentNotice = ref("");
const usersError = ref("");
const usersLoaded = ref(false);
const activeMailboxTab = ref("received");
const form = reactive({
  receiverId: "",
  subject: "",
  body: "",
  reportId: ""
});

const isMailView = computed(() => route.path.startsWith("/mails"));
const favoriteMails = computed(() => mails.value.filter((mail) => mail.isFavorite));
const visibleMails = computed(() => {
  if (activeMailboxTab.value === "sent") return sentMails.value;
  if (activeMailboxTab.value === "favorite") return favoriteMails.value;
  return mails.value;
});
const pageTitle = computed(() => (isMailView.value ? "메일" : "알림"));

async function loadInbox() {
  const data = await api("/notifications/api/");
  notifications.value = data.notifications;
  mails.value = data.mails;
  sentMails.value = data.sentMails || [];
  reports.value = data.reports || [];
  if (data.users) {
    users.value = data.users;
    usersLoaded.value = true;
  }
}

async function loadUsers() {
  usersError.value = "";
  try {
    const data = await api("/accounts/api/users/");
    users.value = data.users;
    usersLoaded.value = true;
  } catch {
    usersError.value = "받는 사람 목록을 불러오지 못했습니다.";
  }
}

function resetForm() {
  form.receiverId = "";
  form.subject = "";
  form.body = "";
  form.reportId = "";
  error.value = "";
}

async function toggleComposer() {
  showComposer.value = !showComposer.value;
  if (!showComposer.value) resetForm();
  if (showComposer.value) {
    await loadInbox();
    if (!usersLoaded.value) await loadUsers();
  }
}

async function sendMail() {
  sending.value = true;
  error.value = "";
  sentNotice.value = "";
  try {
    await api("/notifications/api/send/", {
      method: "POST",
      body: JSON.stringify({
        receiverId: form.receiverId,
        subject: form.subject,
        body: form.body,
        reportId: form.reportId || null
      })
    });
    await loadInbox();
    window.dispatchEvent(new Event("inbox-counts-updated"));
    resetForm();
    showComposer.value = false;
    sentNotice.value = "메일을 보냈습니다.";
  } catch (err) {
    error.value = err.message || "메일을 보내지 못했습니다.";
  } finally {
    sending.value = false;
  }
}

async function toggleFavorite(mail) {
  const data = await api(`/notifications/api/mails/${mail.id}/favorite/`, { method: "POST" });
  Object.assign(mail, data.mail);
  window.dispatchEvent(new Event("inbox-counts-updated"));
}

onMounted(async () => {
  await loadInbox();
  if (!usersLoaded.value) await loadUsers();
});
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>{{ pageTitle }}</h1>
      <button v-if="isMailView" class="btn primary" type="button" @click="toggleComposer">
        {{ showComposer ? "닫기" : "메일 보내기" }}
      </button>
    </div>
    <div class="grid">
      <section v-if="!isMailView" class="panel">
        <h2>알림</h2>
        <div
          v-for="item in notifications"
          :key="item.id"
          :class="['message-item', item.isRead ? 'read' : 'unread']"
        >
          <hr class="message-divider">
          <strong>{{ item.title }}</strong>
          <p>{{ item.body }}</p>
          <span>{{ dateText(item.createdAt) }}</span>
        </div>
        <div v-if="notifications.length === 0" class="empty">알림이 없습니다.</div>
      </section>

      <section v-else class="panel">
        <h2>메일</h2>
        <div class="mail-tabs">
          <button type="button" :class="{ active: activeMailboxTab === 'favorite' }" @click="activeMailboxTab = 'favorite'">
            즐겨찾기
          </button>
          <button type="button" :class="{ active: activeMailboxTab === 'received' }" @click="activeMailboxTab = 'received'">
            받은 메일
          </button>
          <button type="button" :class="{ active: activeMailboxTab === 'sent' }" @click="activeMailboxTab = 'sent'">
            보낸 메일
          </button>
        </div>

        <div v-if="sentNotice" class="success">{{ sentNotice }}</div>

        <form v-if="showComposer" class="mail-form" @submit.prevent="sendMail">
          <div class="field">
            <label>받는 사람</label>
            <select v-model="form.receiverId" required>
              <option value="">받는 사람 선택</option>
              <option v-for="user in users" :key="user.id" :value="user.id">
                {{ user.displayName }} · {{ user.email }}
              </option>
            </select>
          </div>
          <div v-if="usersError" class="error">{{ usersError }}</div>
          <div v-else-if="usersLoaded && users.length === 0" class="empty compact">
            메일을 보낼 수 있는 다른 사용자가 없습니다.
          </div>
          <div class="field">
            <label>보고서 첨부</label>
            <select v-model="form.reportId">
              <option value="">첨부하지 않음</option>
              <option v-for="report in reports" :key="report.id" :value="report.id">
                [{{ report.sourceType }}] {{ report.title }}
              </option>
            </select>
          </div>
          <div v-if="reports.length === 0" class="muted">첨부할 수 있는 내 보고서가 없습니다.</div>
          <div class="field">
            <label>제목</label>
            <input v-model="form.subject" class="input" type="text" required>
          </div>
          <div class="field">
            <label>내용</label>
            <textarea v-model="form.body" required></textarea>
          </div>
          <div v-if="error" class="error">{{ error }}</div>
          <div class="actions">
            <button class="btn primary" type="submit" :disabled="sending || users.length === 0">
              {{ sending ? "보내는 중" : "보내기" }}
            </button>
            <button class="btn ghost" type="button" @click="toggleComposer">취소</button>
          </div>
        </form>

        <div
          v-for="mail in visibleMails"
          :key="mail.id"
          :class="['message-item', 'mail-list-item', mail.isRead ? 'read' : 'unread']"
        >
          <hr class="message-divider">
          <div class="mail-list-head">
            <button
              v-if="activeMailboxTab !== 'sent'"
              type="button"
              :class="['favorite-button', { active: mail.isFavorite }]"
              :aria-label="mail.isFavorite ? '즐겨찾기 해제' : '즐겨찾기'"
              @click="toggleFavorite(mail)"
            >
              ★
            </button>
            <router-link class="mail-subject" :to="`/mails/${mail.id}/`">{{ mail.subject }}</router-link>
            <span v-if="mail.attachedReport" class="attachment-badge">보고서</span>
          </div>
          <p class="muted">
            {{ activeMailboxTab === "sent" ? `받는 사람: ${mail.receiver}` : `보낸 사람: ${mail.sender}` }} · {{ dateText(mail.createdAt) }}
          </p>
        </div>
        <div v-if="visibleMails.length === 0" class="empty">
          {{
            activeMailboxTab === "sent"
              ? "보낸 메일이 없습니다."
              : activeMailboxTab === "favorite"
                ? "즐겨찾기한 메일이 없습니다."
                : "받은 메일이 없습니다."
          }}
        </div>
      </section>
    </div>
  </div>
</template>
