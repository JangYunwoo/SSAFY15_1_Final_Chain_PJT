<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const route = useRoute();
const notifications = ref([]);
const mails = ref([]);
const users = ref([]);
const showComposer = ref(false);
const sending = ref(false);
const error = ref("");
const usersError = ref("");
const usersLoaded = ref(false);
const form = reactive({
  receiverId: "",
  subject: "",
  body: ""
});
const isMailView = computed(() => route.path.startsWith("/mails"));
const pageTitle = computed(() => (isMailView.value ? "메일" : "알림"));

async function loadInbox() {
  const data = await api("/notifications/api/");
  notifications.value = data.notifications;
  mails.value = data.mails;
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
  error.value = "";
}

function toggleComposer() {
  showComposer.value = !showComposer.value;
  if (!showComposer.value) resetForm();
  if (showComposer.value && !usersLoaded.value) loadUsers();
}

async function sendMail() {
  sending.value = true;
  error.value = "";
  try {
    await api("/notifications/api/send/", {
      method: "POST",
      body: JSON.stringify({
        receiverId: form.receiverId,
        subject: form.subject,
        body: form.body
      })
    });
    await loadInbox();
    window.dispatchEvent(new Event("inbox-counts-updated"));
    resetForm();
    showComposer.value = false;
  } catch (err) {
    error.value = err.message || "메일을 보내지 못했습니다.";
  } finally {
    sending.value = false;
  }
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
            메일을 보낼 수 있는 다른 활성 사용자가 없습니다.
          </div>
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
            <button class="btn primary" type="submit" :disabled="sending || users.length === 0">{{ sending ? "보내는 중" : "보내기" }}</button>
            <button class="btn ghost" type="button" @click="toggleComposer">취소</button>
          </div>
        </form>
        <div
          v-for="mail in mails"
          :key="mail.id"
          :class="['message-item', 'mail-list-item', mail.isRead ? 'read' : 'unread']"
        >
          <hr class="message-divider">
          <router-link class="mail-subject" :to="`/mails/${mail.id}/`">{{ mail.subject }}</router-link>
          <p class="muted">{{ mail.sender }} · {{ dateText(mail.createdAt) }}</p>
        </div>
        <div v-if="mails.length === 0" class="empty">메일이 없습니다.</div>
      </section>
    </div>
  </div>
</template>
