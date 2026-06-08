<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";

const route = useRoute();
const analysis = ref(null);

onMounted(async () => {
  analysis.value = (await api(`/analyses/api/${route.params.id}/`)).analysis;
});
</script>

<template>
  <div v-if="analysis" class="page">
    <div class="page-head">
      <h1>{{ analysis.analysisCode }}</h1>
      <div class="actions">
        <router-link class="btn ghost" :to="`/reports/analysis/${analysis.id}/new/`">보고서</router-link>
        <router-link class="btn ghost" to="/analyses/history/">목록</router-link>
      </div>
    </div>
    <div class="grid cols-2">
      <section class="panel">
        <h2>분석 결과</h2>
        <p><span :class="['badge', analysis.isLowConfidence ? 'warn' : 'ok']">{{ analysis.predictedLabel || "-" }} · {{ analysis.confidencePercent }}%</span></p>
        <dl class="grid cols-2">
          <div><dt class="muted">LOT</dt><dd>{{ analysis.lot?.lotId || "-" }}</dd></div>
          <div><dt class="muted">공정</dt><dd>{{ analysis.process || "-" }}</dd></div>
          <div><dt class="muted">장비</dt><dd>{{ analysis.equipmentId || "-" }}</dd></div>
          <div><dt class="muted">수율</dt><dd>{{ analysis.yieldRate ?? "-" }}</dd></div>
        </dl>
        <pre class="summary">{{ analysis.summary }}</pre>
      </section>
      <section class="panel">
        <h2>Wafer Map</h2>
        <img v-if="analysis.waferImage" class="wafer-img" :src="analysis.waferImage" alt="wafer map">
        <div v-else class="empty">이미지가 없습니다.</div>
      </section>
    </div>
    <section class="panel" style="margin-top:16px">
      <h2>추천 공정</h2>
      <div class="grid">
        <div v-for="item in analysis.recommendations" :key="item.rank" class="card">
          <strong>{{ item.rank }}. {{ item.process }}</strong>
          <span class="badge" style="margin-left:8px">{{ item.score }}</span>
          <p>{{ item.reason }}</p>
        </div>
      </div>
    </section>
  </div>
</template>
