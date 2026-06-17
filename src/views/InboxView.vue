<script setup>
import { onMounted, ref } from "vue";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const notifications = ref([]);
const mails = ref([]);

onMounted(async () => {
  const data = await api("/notifications/api/");
  notifications.value = data.notifications;
  mails.value = data.mails;
});
</script>

<template>
  <div class="page">
    <div class="page-head"><h1>알림/메일</h1></div>
    <div class="grid cols-2">
      <section class="panel">
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
      <section class="panel">
        <h2>메일</h2>
        <div
          v-for="mail in mails"
          :key="mail.id"
          :class="['message-item', mail.isRead ? 'read' : 'unread']"
        >
          <hr class="message-divider">
          <strong>{{ mail.subject }}</strong>
          <p class="muted">{{ mail.sender }} · {{ dateText(mail.createdAt) }}</p>
          <p>{{ mail.body }}</p>
        </div>
        <div v-if="mails.length === 0" class="empty">메일이 없습니다.</div>
      </section>
    </div>
  </div>
</template>
