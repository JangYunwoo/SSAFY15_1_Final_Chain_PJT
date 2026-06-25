<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const batches = ref([]);
const customAnalyses = ref([]);
const route = useRoute();
const opened = ref({});
const customOpened = ref({});
const batchRefs = ref({});
const details = ref({});
const customMode = ref(false);
const selected = ref([]);
const loading = ref(false);
const error = ref("");
const favoriteOnly = ref(false);
const HISTORY_REFRESH_MS = 5000;
let refreshTimer = null;
let refreshing = false;

const historyItems = computed(() => [
  ...batches.value.map((item) => ({ ...item, kind: "batch" })),
  ...customAnalyses.value.map((item) => ({ ...item, kind: "custom" })),
].sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt)));
const visibleHistoryItems = computed(() =>
  favoriteOnly.value ? historyItems.value.filter((item) => item.isFavorite) : historyItems.value
);

async function load({ scrollRequested = true } = {}) {
  if (refreshing) return;
  refreshing = true;
  try {
  const data = await api("/analyses/api/history/");
  batches.value = data.batches;
  customAnalyses.value = data.customAnalyses;
    if (scrollRequested) await openRequestedBatch();
    await refreshOpenBatchDetails();
  } finally {
    refreshing = false;
  }
}

async function openRequestedBatch() {
  const batchId = Number(route.query.batch);
  const batch = batches.value.find((item) => item.id === batchId);
  if (!batch) return;
  opened.value = { [batch.id]: true };
  if (!details.value[batch.id]) details.value[batch.id] = (await api(`/analyses/api/batches/${batch.id}/`)).batch;
  await nextTick();
  batchRefs.value[batch.id]?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setBatchRef(id, element) {
  if (element) batchRefs.value[id] = element;
}

async function toggle(batch) {
  opened.value[batch.id] = !opened.value[batch.id];
  if (opened.value[batch.id] && !details.value[batch.id]) details.value[batch.id] = (await api(`/analyses/api/batches/${batch.id}/`)).batch;
}

async function refreshOpenBatchDetails() {
  const openIds = Object.entries(opened.value)
    .filter(([, isOpen]) => isOpen)
    .map(([id]) => Number(id));
  await Promise.all(openIds.map(async (id) => {
    details.value[id] = (await api(`/analyses/api/batches/${id}/`)).batch;
  }));
}

function toggleCustom() {
  customMode.value = !customMode.value;
  if (!customMode.value) selected.value = [];
}

function batchCount(custom) {
  return new Set(custom.selectedWafers.map((item) => item.batchId)).size;
}

function labelDistribution(items) {
  return Object.entries(items.reduce((map, item) => {
    const label = item.isNormal ? "Normal" : (item.predictedLabel || "미분류");
    map[label] = (map[label] || 0) + 1;
    return map;
  }, {})).map(([label, count]) => `${label} ${count}장`).join(" · ");
}

async function runCustomAnalysis() {
  loading.value = true;
  error.value = "";
  try {
    const data = await api("/analyses/api/custom-analyses/", { method: "POST", body: JSON.stringify({ analysisIds: selected.value }) });
    customAnalyses.value.unshift(data.customAnalysis);
    selected.value = [];
    customMode.value = false;
  } catch (requestError) {
    error.value = requestError.message || "커스텀 분석을 완료하지 못했습니다.";
  } finally {
    loading.value = false;
  }
}

async function toggleHistoryFavorite(entry) {
  const endpoint = entry.kind === "custom"
    ? `/analyses/api/custom-analyses/${entry.id}/favorite/`
    : `/analyses/api/batches/${entry.id}/favorite/`;
  const data = await api(endpoint, { method: "POST" });
  if (entry.kind === "custom") {
    const target = customAnalyses.value.find((item) => item.id === entry.id);
    if (target) target.isFavorite = data.isFavorite;
  } else {
    const target = batches.value.find((item) => item.id === entry.id);
    if (target) target.isFavorite = data.isFavorite;
  }
}

onMounted(async () => {
  await load();
  refreshTimer = window.setInterval(() => {
    if (!document.hidden) load({ scrollRequested: false });
  }, HISTORY_REFRESH_MS);
});
onBeforeUnmount(() => {
  if (refreshTimer) window.clearInterval(refreshTimer);
});
watch(() => route.query.batch, openRequestedBatch);
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>분석 이력</h1>
      <div class="actions">
        <button type="button" :class="['btn', favoriteOnly ? 'primary' : 'ghost']" @click="favoriteOnly = !favoriteOnly">
          {{ favoriteOnly ? "전체 보기" : "즐겨찾기" }}
        </button>
        <button v-if="!customMode" class="btn primary" @click="toggleCustom">커스텀 분석</button>
        <template v-else>
          <button class="btn ghost" @click="toggleCustom">취소</button>
          <button class="btn primary" :disabled="!selected.length || loading" @click="runCustomAnalysis">{{ loading ? '분석 중…' : `분석 (${selected.length})` }}</button>
        </template>
      </div>
    </div>
    <p v-if="customMode" class="notice">CSV를 펼쳐 원하는 웨이퍼맵을 선택하세요. 서로 다른 CSV의 웨이퍼도 함께 분석할 수 있습니다.</p>
    <p v-if="error" class="error">{{ error }}</p>

    <section class="batch-list">
      <article v-for="entry in visibleHistoryItems" :key="`${entry.kind}-${entry.id}`" :ref="(element) => entry.kind === 'batch' && setBatchRef(entry.id, element)" class="batch-card">
        <template v-if="entry.kind === 'custom'">
          <div class="batch-row">
            <button
              type="button"
              :class="['star-button', 'history-star', { active: entry.isFavorite }]"
              :aria-label="entry.isFavorite ? '즐겨찾기 해제' : '즐겨찾기'"
              @click.stop="toggleHistoryFavorite(entry)"
            >
              {{ entry.isFavorite ? "★" : "☆" }}
            </button>
            <div class="batch-row-main">
              <strong>{{ dateText(entry.createdAt) }} 커스텀 분석데이터</strong>
              <span class="muted">커스텀 선택 · {{ entry.selectedWafers.length }}장 · CSV {{ batchCount(entry) }}개</span>
            </div>
            <button :class="['fold-button', { expanded: customOpened[entry.id] }]" :aria-label="customOpened[entry.id] ? '접기' : '펼치기'" @click="customOpened[entry.id] = !customOpened[entry.id]"></button>
          </div>
          <div v-if="customOpened[entry.id]" class="batch-content">
            <section class="batch-summary"><div><span class="muted">라벨 분포</span><p>{{ Object.entries(entry.labelDistribution).map(([label, count]) => `${label} ${count}장`).join(' · ') }}</p></div></section>
            <article class="insight-card">
              <strong>{{ dateText(entry.createdAt) }} 커스텀 분석데이터</strong>
              <p v-if="entry.isFallback" class="error">GMS 응답을 끝까지 받지 못해 AI 분석 결과를 생성하지 못했습니다.</p>
              <template v-else>
                <p>{{ entry.summary }}</p>
                <div v-for="item in entry.recommendations" :key="`${entry.id}-${item.rank}`" class="recommendation"><b>{{ item.rank }}. {{ item.process }}</b> — {{ item.reason }}</div>
                <details><summary>AI 보고서 보기</summary><pre class="summary">{{ entry.report }}</pre><div class="report-action"><router-link class="btn ghost" :to="`/reports/custom/${entry.id}/new/`">보고서 작성</router-link></div></details>
              </template>
            </article>
            <div class="wafer-grid">
              <label v-for="item in entry.selectedWafers" :key="item.id" class="wafer-card">
                <img v-if="item.waferImage" :src="item.waferImage" :alt="item.waferId">
                <div><strong>{{ item.waferId || item.analysisCode }}</strong><span :class="['badge', item.isNormal ? 'ok' : 'warn']">{{ item.isNormal ? 'Normal' : (item.predictedLabel || '-') }}</span></div>
                <router-link :to="`/analyses/${item.id}/`">상세 보기</router-link>
              </label>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="batch-row">
            <button
              type="button"
              :class="['star-button', 'history-star', { active: entry.isFavorite }]"
              :aria-label="entry.isFavorite ? '즐겨찾기 해제' : '즐겨찾기'"
              @click.stop="toggleHistoryFavorite(entry)"
            >
              {{ entry.isFavorite ? "★" : "☆" }}
            </button>
            <div class="batch-row-main">
              <strong>{{ dateText(entry.createdAt) }} 분석데이터</strong>
              <span class="muted">{{ entry.fileName }} · {{ entry.totalWafers }}장 · LOT {{ entry.lot.lotId }}</span>
            </div>
            <button :class="['fold-button', { expanded: opened[entry.id] }]" :aria-label="opened[entry.id] ? '접기' : '펼치기'" @click="toggle(entry)"></button>
          </div>
          <div v-if="opened[entry.id]" class="batch-content">
            <div v-if="!details[entry.id]" class="empty">불러오는 중…</div>
            <template v-else>
              <section class="batch-summary"><div><span class="muted">라벨 분포</span><p>{{ labelDistribution(details[entry.id].analyses) }}</p></div></section>
              <article v-for="insight in details[entry.id].insights" :key="insight.id" class="insight-card">
                <strong>{{ insight.title }}</strong>
                <p v-if="insight.isFallback" class="error">GMS 응답을 끝까지 받지 못해 AI 분석 결과를 생성하지 못했습니다.</p>
                <template v-else>
                  <p>{{ insight.summary }}</p>
                  <div v-for="item in insight.recommendations" :key="`${insight.id}-${item.rank}`" class="recommendation"><b>{{ item.rank }}. {{ item.process }}</b> — {{ item.reason }}</div>
                  <details><summary>AI 보고서 보기</summary><pre class="summary">{{ insight.report }}</pre><div class="report-action"><router-link class="btn ghost" :to="`/reports/batch/${entry.id}/new/`">보고서 작성</router-link></div></details>
                </template>
              </article>
              <div class="wafer-grid">
                <label v-for="item in details[entry.id].analyses" :key="item.id" class="wafer-card">
                  <input v-if="customMode" v-model="selected" type="checkbox" :value="item.id">
                  <img v-if="item.waferImage" :src="item.waferImage" :alt="item.waferId">
                  <div><strong>{{ item.waferId || item.analysisCode }}</strong><span :class="['badge', item.isNormal ? 'ok' : 'warn']">{{ item.isNormal ? 'Normal' : (item.predictedLabel || '-') }}</span></div>
                  <router-link :to="`/analyses/${item.id}/`">상세 보기</router-link>
                </label>
              </div>
            </template>
          </div>
        </template>
      </article>
      <div v-if="!visibleHistoryItems.length" class="empty panel">
        {{ favoriteOnly ? "즐겨찾기한 분석 이력이 없습니다." : "분석 이력이 없습니다." }}
      </div>
    </section>
  </div>
</template>
