<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";

const route = useRoute();
const form = reactive({ title: "", body: "" });
const aiBody = ref("");
const uploaded = ref(false);
const reportType = route.meta.reportType || "analysis";

onMounted(async () => {
  const data = await api(`/reports/api/${reportType}/${route.params.id}/`);
  const source = data.report || data.initial;
  form.title = source.title;
  form.body = source.body || "";
  aiBody.value = source.aiBody || "";
});

async function upload() {
  const data = await api(`/reports/api/${reportType}/${route.params.id}/`, { method: "POST", body: JSON.stringify(form) });
  await api(`/reports/api/${data.report.id}/share/`, { method: "POST" });
  uploaded.value = true;
}
</script>

<template>
  <div class="page">
    <div class="page-head"><h1>보고서 작성</h1></div>
    <form class="panel form" @submit.prevent="upload">
      <div class="field"><label>제목</label><input v-model="form.title" class="input" required></div>
      <div class="field"><label>AI 분석 결과</label><pre class="ai-report-box">{{ aiBody }}</pre></div>
      <div class="field"><label>작성자 코멘트</label><textarea v-model="form.body" placeholder="분석 결과에 대한 추가 의견, 조치 계획, 현장 확인 내용을 작성하세요."></textarea></div>
      <div class="actions"><button class="btn primary">업로드</button></div>
    </form>
    <div v-if="uploaded" class="modal-backdrop"><section class="modal"><h2>업로드 완료</h2><p>보고서가 커뮤니티에 업로드되었습니다.</p><router-link class="btn primary" to="/community/">커뮤니티로 이동</router-link></section></div>
  </div>
</template>
