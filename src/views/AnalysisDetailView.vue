<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";
const route = useRoute();
const analysis = ref(null);
onMounted(async () => { analysis.value = (await api(`/analyses/api/${route.params.id}/`)).analysis; });
</script>

<template>
  <div v-if="analysis" class="page">
    <div class="page-head"><h1>{{ analysis.analysisCode }}</h1><router-link class="btn ghost" to="/analyses/history/">목록</router-link></div>
    <div class="grid cols-2">
      <section class="panel">
        <h2>분석 결과</h2>
        <div v-if="analysis.isNormal" class="prediction-strip"><div class="prediction-card ok"><span>수율 기준</span><strong>정상</strong><em>{{ analysis.yieldRate }}%</em></div></div>
        <div v-else class="prediction-strip"><div v-for="candidate in analysis.topPredictions" :key="candidate.rank" class="prediction-card"><span>{{ candidate.rank }}순위</span><strong>{{ candidate.label }}</strong><em>{{ candidate.percent }}%</em></div></div>
        <dl class="grid cols-2"><div><dt class="muted">LOT</dt><dd>{{ analysis.lot?.lotId || '-' }}</dd></div><div><dt class="muted">공정</dt><dd>{{ analysis.process || '-' }}</dd></div><div><dt class="muted">장비</dt><dd>{{ analysis.equipmentId || '-' }}</dd></div><div><dt class="muted">수율</dt><dd>{{ analysis.yieldRate ?? '-' }}</dd></div></dl>
        <p class="muted">공정 추천과 AI 해석은 분석 이력에서 CSV 배치 단위로 제공합니다.</p>
      </section>
      <section class="panel"><h2>Wafer Map</h2><img v-if="analysis.waferImage" class="wafer-img" :src="analysis.waferImage" alt="wafer map"><div v-else class="empty">이미지가 없습니다.</div></section>
    </div>
  </div>
</template>
