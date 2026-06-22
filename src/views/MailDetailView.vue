<script setup>
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const route = useRoute();
const router = useRouter();
const mail = ref(null);
const error = ref("");
const deleting = ref(false);

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
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>메일 상세</h1>
      <div class="actions">
        <button class="btn ghost" type="button" @click="router.push('/mails/')">목록</button>
        <button class="btn danger" type="button" :disabled="deleting" @click="deleteMail">
          {{ deleting ? "삭제 중" : "삭제" }}
        </button>
      </div>
    </div>

    <section v-if="mail" class="panel mail-detail">
      <h2>{{ mail.subject }}</h2>
      <p class="muted">{{ mail.sender }} · {{ dateText(mail.createdAt) }}</p>
      <div class="mail-body">{{ mail.body }}</div>
    </section>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="empty">메일을 불러오는 중입니다.</div>
  </div>
</template>
