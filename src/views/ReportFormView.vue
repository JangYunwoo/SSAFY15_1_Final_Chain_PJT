<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../services/api";

const route = useRoute();
const router = useRouter();
const report = ref(null);
const form = reactive({ title: "", body: "" });

onMounted(async () => {
  const data = await api(`/reports/api/analysis/${route.params.id}/`);
  report.value = data.report;
  Object.assign(form, data.report || data.initial);
});

async function submit() {
  const data = await api(`/reports/api/analysis/${route.params.id}/`, {
    method: "POST",
    body: JSON.stringify(form)
  });
  report.value = data.report;
}

async function share() {
  const data = await api(`/reports/api/${report.value.id}/share/`, { method: "POST" });
  router.push(`/community/${data.postId}/`);
}
</script>

<template>
  <div class="page">
    <div class="page-head"><h1>보고서</h1></div>
    <form class="panel form" @submit.prevent="submit">
      <div class="field"><label>제목</label><input v-model="form.title" class="input" required></div>
      <div class="field"><label>본문</label><textarea v-model="form.body" style="min-height:360px" required></textarea></div>
      <div class="actions">
        <button class="btn primary">저장</button>
        <button v-if="report" class="btn ghost" type="button" @click="share">커뮤니티 공유</button>
      </div>
    </form>
  </div>
</template>
