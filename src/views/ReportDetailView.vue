<script setup>
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const route = useRoute();
const router = useRouter();
const report = ref(null);
const error = ref("");

onMounted(async () => {
  try {
    report.value = (await api(`/reports/api/${route.params.id}/`)).report;
  } catch (requestError) {
    error.value = requestError.message || "보고서를 불러오지 못했습니다.";
  }
});
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>보고서 상세</h1>
      <button class="btn ghost" type="button" @click="router.back()">이전으로</button>
    </div>

    <section v-if="report" class="panel report-detail">
      <div class="report-detail-head">
        <span class="attachment-badge">보고서</span>
        <h2>{{ report.title }}</h2>
      </div>
      <p class="muted">
        작성자: {{ report.author }} · {{ dateText(report.createdAt) }}
      </p>
      <details open>
        <summary>AI 분석 결과</summary>
        <pre class="summary">{{ report.aiBody || "AI 분석 결과가 없습니다." }}</pre>
      </details>
      <details open>
        <summary>작성 내용</summary>
        <pre class="summary">{{ report.body || "작성 내용이 없습니다." }}</pre>
      </details>
    </section>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="empty panel">보고서를 불러오는 중입니다.</div>
  </div>
</template>
