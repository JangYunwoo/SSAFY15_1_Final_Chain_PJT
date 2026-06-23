<script setup>
import { nextTick, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const batches = ref([]);
const route = useRoute();
const customAnalyses = ref([]);
const opened = ref({});
const batchRefs = ref({});
const customOpened = ref({});
const details = ref({});
const customMode = ref(false);
const selected = ref([]);
const loading = ref(false);
const error = ref("");

async function load() {
  const data = await api("/analyses/api/history/");
  batches.value = data.batches;
  customAnalyses.value = data.customAnalyses;
  await openRequestedBatch();
}

async function openRequestedBatch() {
  const batchId = Number(route.query.batch);
  const batch = batches.value.find((item) => item.id === batchId);
  if (!batch) return;
  opened.value = { [batch.id]: true };
  if (!details.value[batch.id]) {
    details.value[batch.id] = (await api(`/analyses/api/batches/${batch.id}/`)).batch;
  }
  await nextTick();
  batchRefs.value[batch.id]?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setBatchRef(id, element) {
  if (element) batchRefs.value[id] = element;
}

async function toggle(batch) {
  opened.value[batch.id] = !opened.value[batch.id];
  if (opened.value[batch.id] && !details.value[batch.id]) {
    details.value[batch.id] = (await api(`/analyses/api/batches/${batch.id}/`)).batch;
  }
}

function toggleCustom() {
  customMode.value = !customMode.value;
  if (!customMode.value) selected.value = [];
}

function batchCount(custom) {
  return new Set(custom.selectedWafers.map((item) => item.batchId)).size;
}

async function runCustomAnalysis() {
  loading.value = true;
  error.value = "";
  try {
    const data = await api("/analyses/api/custom-analyses/", {
      method: "POST",
      body: JSON.stringify({ analysisIds: selected.value })
    });
    customAnalyses.value.unshift(data.customAnalysis);
    selected.value = [];
    customMode.value = false;
  } catch (requestError) {
    error.value = requestError.message || "커스텀 분석을 완료하지 못했습니다.";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
watch(() => route.query.batch, openRequestedBatch);
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>분석 이력</h1>
      <div class="actions">
        <button v-if="!customMode" class="btn primary" @click="toggleCustom">커스텀</button>
        <template v-else>
          <button class="btn ghost" @click="toggleCustom">취소</button>
          <button class="btn primary" :disabled="!selected.length || loading" @click="runCustomAnalysis">{{ loading ? '분석 중…' : `분석 (${selected.length})` }}</button>
        </template>
      </div>
    </div>
    <p v-if="customMode" class="notice">CSV를 펼쳐 원하는 웨이퍼맵을 선택하세요. 서로 다른 CSV의 웨이퍼도 함께 분석할 수 있습니다.</p>
    <p v-if="error" class="error">{{ error }}</p>

    <section v-if="customAnalyses.length" class="batch-list custom-analysis-list">
      <article v-for="custom in customAnalyses" :key="custom.id" class="batch-card">
        <div class="batch-row">
          <div>
            <strong>{{ dateText(custom.createdAt) }} 커스텀 분석데이터</strong>
            <span class="muted">커스텀 선택 · {{ custom.selectedWafers.length }}장 · CSV {{ batchCount(custom) }}개</span>
          </div>
          <button :class="['fold-button', { expanded: customOpened[custom.id] }]" :aria-label="customOpened[custom.id] ? '접기' : '펼치기'" @click="customOpened[custom.id] = !customOpened[custom.id]"></button>
        </div>
        <div v-if="customOpened[custom.id]" class="batch-content">
          <section class="batch-summary"><div><span class="muted">라벨 분포</span><p>{{ Object.entries(custom.labelDistribution).map(([label, count]) => `${label} ${count}장`).join(' · ') }}</p></div></section>
          <article class="insight-card">
            <strong>{{ dateText(custom.createdAt) }} 커스텀 분석데이터</strong>
            <p v-if="custom.isFallback" class="error">GMS 응답을 끝까지 받지 못해 AI 분석 결과를 생성하지 못했습니다.</p>
              <template v-else>
                <p>{{ custom.summary }}</p>
                <div v-for="item in custom.recommendations" :key="`${custom.id}-${item.rank}`" class="recommendation"><b>{{ item.rank }}. {{ item.process }}</b> — {{ item.reason }}</div>
                <details><summary>AI 보고서 보기</summary><pre class="summary">{{ custom.report }}</pre><div class="report-action"><router-link class="btn ghost" :to="`/reports/custom/${custom.id}/new/`">보고서 작성</router-link></div></details>
            </template>
          </article>
          <div class="wafer-grid">
            <label v-for="item in custom.selectedWafers" :key="item.id" class="wafer-card">
              <img v-if="item.waferImage" :src="item.waferImage" :alt="item.waferId">
              <div><strong>{{ item.waferId || item.analysisCode }}</strong><span :class="['badge', item.isNormal ? 'ok' : 'warn']">{{ item.isNormal ? '정상' : (item.predictedLabel || '-') }}</span></div>
              <router-link :to="`/analyses/${item.id}/`">상세 보기</router-link>
            </label>
          </div>
        </div>
      </article>
    </section>

    <section class="batch-list">
      <article v-for="batch in batches" :key="batch.id" :ref="(element) => setBatchRef(batch.id, element)" class="batch-card">
        <div class="batch-row">
          <div>
            <strong>{{ dateText(batch.createdAt) }} 분석데이터</strong>
            <span class="muted">{{ batch.fileName }} · {{ batch.totalWafers }}장 · LOT {{ batch.lot.lotId }}</span>
          </div>
          <button :class="['fold-button', { expanded: opened[batch.id] }]" :aria-label="opened[batch.id] ? '접기' : '펼치기'" @click="toggle(batch)"></button>
        </div>
        <div v-if="opened[batch.id]" class="batch-content">
          <div v-if="!details[batch.id]" class="empty">불러오는 중…</div>
          <template v-else>
            <section class="batch-summary"><div><span class="muted">라벨 분포</span><p>{{ Object.entries(details[batch.id].analyses.reduce((map, item) => { map[item.isNormal ? '정상' : (item.predictedLabel || '미분류')] = (map[item.isNormal ? '정상' : (item.predictedLabel || '미분류')] || 0) + 1; return map; }, {})).map(([label, count]) => `${label} ${count}장`).join(' · ') }}</p></div></section>
            <article v-for="insight in details[batch.id].insights" :key="insight.id" class="insight-card">
              <strong>{{ insight.title }}</strong>
              <p v-if="insight.isFallback" class="error">GMS 응답을 끝까지 받지 못해 AI 분석 결과를 생성하지 못했습니다.</p>
              <template v-else><p>{{ insight.summary }}</p><div v-for="item in insight.recommendations" :key="`${insight.id}-${item.rank}`" class="recommendation"><b>{{ item.rank }}. {{ item.process }}</b> — {{ item.reason }}</div><details><summary>AI 보고서 보기</summary><pre class="summary">{{ insight.report }}</pre><div class="report-action"><router-link class="btn ghost" :to="`/reports/batch/${batch.id}/new/`">보고서 작성</router-link></div></details></template>
            </article>
            <div class="wafer-grid">
              <label v-for="item in details[batch.id].analyses" :key="item.id" class="wafer-card">
                <input v-if="customMode" v-model="selected" type="checkbox" :value="item.id">
                <img v-if="item.waferImage" :src="item.waferImage" :alt="item.waferId">
                <div><strong>{{ item.waferId || item.analysisCode }}</strong><span :class="['badge', item.isNormal ? 'ok' : 'warn']">{{ item.isNormal ? '정상' : (item.predictedLabel || '-') }}</span></div>
                <router-link :to="`/analyses/${item.id}/`">상세 보기</router-link>
              </label>
            </div>
          </template>
        </div>
      </article>
      <div v-if="!batches.length" class="empty panel">분석 이력이 없습니다.</div>
    </section>
  </div>
</template>
