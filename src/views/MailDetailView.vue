<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../services/api";
import { store } from "../services/store";
import { dateText } from "../utils/format";

const route = useRoute();
const router = useRouter();
const mail = ref(null);
const error = ref("");
const deleting = ref(false);
const replyBody = ref("");
const replyError = ref("");
const replyNotice = ref("");
const sendingReply = ref(false);
const isReceivedMail = computed(() => mail.value?.receiverId === store.user?.id);

onMounted(async () => {
  try {
    const data = await api(`/notifications/api/mails/${route.params.id}/`);
    mail.value = data.mail;
    window.dispatchEvent(new Event("inbox-counts-updated"));
  } catch (err) {
    error.value = err.message || "메일을 불러오지 못했습니다.";
  }
});

async function deleteMail() {
  if (!window.confirm("이 메일을 삭제할까요?")) return;

  deleting.value = true;
  error.value = "";
  try {
    await api(`/notifications/api/mails/${route.params.id}/`, { method: "DELETE" });
    window.dispatchEvent(new Event("inbox-counts-updated"));
    router.push("/mails/");
  } catch (err) {
    error.value = err.message || "메일을 삭제하지 못했습니다.";
  } finally {
    deleting.value = false;
  }
}

async function sendReply() {
  if (!mail.value) return;

  sendingReply.value = true;
  replyError.value = "";
  replyNotice.value = "";
  try {
    const subject = mail.value.subject.startsWith("Re: ")
      ? mail.value.subject
      : `Re: ${mail.value.subject}`;

    await api("/notifications/api/send/", {
      method: "POST",
      body: JSON.stringify({
        receiverId: mail.value.senderId,
        subject,
        body: replyBody.value
      })
    });
    replyBody.value = "";
    replyNotice.value = "답장을 보냈습니다.";
    window.dispatchEvent(new Event("inbox-counts-updated"));
  } catch (err) {
    replyError.value = err.message || "답장을 보내지 못했습니다.";
  } finally {
    sendingReply.value = false;
  }
}

async function toggleFavorite() {
  if (!mail.value) return;

  const data = await api(`/notifications/api/mails/${mail.value.id}/favorite/`, { method: "POST" });
  mail.value = data.mail;
  window.dispatchEvent(new Event("inbox-counts-updated"));
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>메일 상세</h1>
      <div class="actions">
        <button class="btn ghost" type="button" @click="router.push('/mails/')">목록</button>
        <button v-if="isReceivedMail" class="btn danger" type="button" :disabled="deleting" @click="deleteMail">
          {{ deleting ? "삭제 중" : "삭제" }}
        </button>
      </div>
    </div>

    <section v-if="mail" class="panel mail-detail">
      <div class="mail-detail-head">
        <button
          v-if="isReceivedMail"
          type="button"
          :class="['favorite-button', { active: mail.isFavorite }]"
          :aria-label="mail.isFavorite ? '즐겨찾기 해제' : '즐겨찾기'"
          @click="toggleFavorite"
        >
          ★
        </button>
        <h2>{{ mail.subject }}</h2>
      </div>
      <p class="muted">보낸 사람: {{ mail.sender }} · 받는 사람: {{ mail.receiver }} · {{ dateText(mail.createdAt) }}</p>
      <div class="mail-body">{{ mail.body }}</div>

      <article v-if="mail.attachedReport" class="attached-report">
        <div class="attached-report-head">
          <span class="attachment-badge">보고서 첨부</span>
          <router-link class="attached-report-title" :to="`/reports/${mail.attachedReport.id}/`">
            {{ mail.attachedReport.title }}
          </router-link>
        </div>
        <p class="muted">
          작성자: {{ mail.attachedReport.author }} · {{ dateText(mail.attachedReport.createdAt) }}
        </p>
        <details open>
          <summary>AI 분석 결과</summary>
          <pre class="summary">{{ mail.attachedReport.aiBody || "AI 분석 결과가 없습니다." }}</pre>
        </details>
        <details>
          <summary>작성 내용</summary>
          <pre class="summary">{{ mail.attachedReport.body || "작성 내용이 없습니다." }}</pre>
        </details>
      </article>

      <form v-if="isReceivedMail" class="reply-form" @submit.prevent="sendReply">
        <h3>답장</h3>
        <div v-if="replyNotice" class="success">{{ replyNotice }}</div>
        <div class="field">
          <label>내용</label>
          <textarea v-model="replyBody" required placeholder="답장 내용을 입력하세요"></textarea>
        </div>
        <div v-if="replyError" class="error">{{ replyError }}</div>
        <div class="actions">
          <button class="btn primary" type="submit" :disabled="sendingReply">
            {{ sendingReply ? "보내는 중" : "답장 보내기" }}
          </button>
        </div>
      </form>
    </section>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="empty">메일을 불러오는 중입니다.</div>
  </div>
</template>
