<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../services/api";
import AnalysisTable from "../components/AnalysisTable.vue";

const loading = ref(true);
const data = reactive({ metrics: {}, recent: [] });

onMounted(async () => {
  Object.assign(data, await api("/api/dashboard/"));
  loading.value = false;
});
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>대시보드</h1>
      <router-link class="btn primary" to="/analyses/upload/">분석 업로드</router-link>
    </div>
    <div v-if="loading" class="panel">불러오는 중...</div>
    <template v-else>
      <div class="grid cols-4">
        <div class="card metric"><span>LOT</span><strong>{{ data.metrics.lotCount }}</strong></div>
        <div class="card metric"><span>배치</span><strong>{{ data.metrics.batchCount }}</strong></div>
        <div class="card metric"><span>분석</span><strong>{{ data.metrics.analysisCount }}</strong></div>
        <div class="card metric"><span>평균 신뢰도</span><strong>{{ data.metrics.avgConfidence }}%</strong></div>
      </div>
      <section class="panel" style="margin-top:16px">
        <h2>최근 분석</h2>
        <AnalysisTable :items="data.recent" />
      </section>
    </template>
  </div>
</template>
