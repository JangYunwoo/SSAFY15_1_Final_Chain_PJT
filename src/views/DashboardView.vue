<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import Highcharts from "highcharts";
import Highcharts3d from "highcharts/highcharts-3d";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const loading = ref(true);
const trendChartEl = ref(null);
const trendChart = ref(null);
const data = reactive({ metrics: {}, recent: [], recentBatches: [], recentTrend: { total: 0, normalCount: 0, distribution: [] } });
const opened = ref({});
const details = ref({});
const trendColors = ["#2563eb", "#f59e0b", "#8b5cf6", "#ef4444", "#14b8a6", "#64748b", "#ec4899", "#84cc16"];
const DASHBOARD_REFRESH_MS = 5000;
let refreshTimer = null;
let refreshing = false;

Highcharts3d(Highcharts);

function renderTrendChart() {
  if (!trendChartEl.value || !data.recentTrend.distribution.length) return;
  const chartData = data.recentTrend.distribution.map((item, index) => ({
    name: item.label,
    y: item.count,
    color: trendColors[index % trendColors.length],
    sliced: index === 0,
    selected: index === 0,
  }));
  if (trendChart.value) {
    trendChart.value.series[0].setData(chartData, false, false, false);
    trendChart.value.redraw(false);
    return;
  }
  trendChart.value = Highcharts.chart(trendChartEl.value, {
    chart: {
      type: "pie",
      animation: false,
      backgroundColor: "transparent",
      height: 310,
      options3d: { enabled: true, alpha: 52, beta: 0 },
      spacing: [4, 4, 22, 4],
    },
    title: { text: null },
    credits: { enabled: false },
    tooltip: { pointFormat: "<b>{point.y}개</b> · {point.percentage:.1f}%" },
    plotOptions: {
      pie: {
        animation: false,
        depth: 38,
        size: "92%",
        innerSize: 0,
        center: ["50%", "45%"],
        allowPointSelect: true,
        cursor: "pointer",
        dataLabels: {
          enabled: true,
          distance: 15,
          crop: false,
          overflow: "allow",
          format: "{point.name}<br/><b>{point.percentage:.1f}%</b>",
          style: { color: "#172033", fontSize: "13px", fontWeight: "600", textOutline: "none" },
        },
      },
    },
    series: [{
      name: "웨이퍼",
      animation: false,
      colorByPoint: true,
      data: chartData,
    }],
  });
}

async function toggle(batch) {
  opened.value[batch.id] = !opened.value[batch.id];
  if (opened.value[batch.id] && !details.value[batch.id]) {
    details.value[batch.id] = (await api(`/analyses/api/batches/${batch.id}/`)).batch;
  }
}

async function loadDashboard() {
  if (refreshing) return;
  refreshing = true;
  try {
    Object.assign(data, await api("/api/dashboard/"));
    loading.value = false;
    const openIds = Object.entries(opened.value)
      .filter(([, isOpen]) => isOpen)
      .map(([id]) => Number(id));
    await Promise.all(openIds.map(async (id) => {
      details.value[id] = (await api(`/analyses/api/batches/${id}/`)).batch;
    }));
    await nextTick();
    renderTrendChart();
  } finally {
    refreshing = false;
  }
}

onMounted(async () => {
  await loadDashboard();
  refreshTimer = window.setInterval(() => {
    if (!document.hidden) loadDashboard();
  }, DASHBOARD_REFRESH_MS);
});

onBeforeUnmount(() => {
  if (refreshTimer) window.clearInterval(refreshTimer);
  trendChart.value?.destroy();
});
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>대시보드</h1>
      <router-link class="btn primary" to="/analyses/upload/">분석 업로드</router-link>
    </div>

    <div v-if="loading" class="panel">불러오는 중…</div>

    <template v-else>
      <div class="grid cols-4">
        <div class="card metric"><span>LINE</span><strong class="lot-metric">{{ data.metrics.lineIds?.join(' · ') || '-' }}</strong></div>
        <div class="card metric"><span>배치</span><strong>{{ data.metrics.batchCount }}</strong></div>
        <div class="card metric"><span>분석</span><strong>{{ data.metrics.analysisCount }}</strong></div>
        <div class="card metric"><span>최근 100개 정상 비율</span><strong>{{ data.metrics.recentNormalRate }}%</strong></div>
      </div>

      <section class="panel trend-panel">
        <div>
          <h2>최근 100개 웨이퍼 동향</h2>
          <p class="muted">완료된 최신 웨이퍼 {{ data.recentTrend.total }}개 기준</p>
        </div>
        <div class="trend-layout">
          <div v-if="data.recentTrend.total" ref="trendChartEl" class="highcharts-pie"></div>
          <div v-else class="empty">완료된 분석 데이터가 없습니다.</div>
          <div class="trend-legend">
            <div v-for="(item, index) in data.recentTrend.distribution" :key="item.label" class="trend-legend-item">
              <span class="trend-swatch" :style="{ background: trendColors[index % trendColors.length] }"></span>
              <span>{{ item.label }}</span>
              <strong>{{ item.count }}개</strong>
              <em>{{ item.percent }}%</em>
            </div>
          </div>
        </div>
      </section>

      <section style="margin-top:16px">
        <div class="page-head dashboard-section-head">
          <h2>최근 분석</h2>
          <router-link class="btn ghost" to="/analyses/history/">전체 이력</router-link>
        </div>
        <div class="batch-list">
          <article v-for="batch in data.recentBatches" :key="batch.id" class="batch-card">
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
                <section class="batch-summary">
                  <div>
                    <span class="muted">라벨 분포</span>
                    <p>{{ Object.entries(details[batch.id].analyses.reduce((map, item) => { map[item.isNormal ? 'Normal' : (item.predictedLabel || '미분류')] = (map[item.isNormal ? 'Normal' : (item.predictedLabel || '미분류')] || 0) + 1; return map; }, {})).map(([label, count]) => `${label} ${count}장`).join(' · ') }}</p>
                  </div>
                </section>
                <div class="wafer-grid">
                  <article v-for="item in details[batch.id].analyses" :key="item.id" class="wafer-card">
                    <img v-if="item.waferImage" :src="item.waferImage" :alt="item.waferId">
                    <div>
                      <strong>{{ item.waferId || item.analysisCode }}</strong>
                      <span :class="['badge', item.isNormal ? 'ok' : 'warn']">{{ item.isNormal ? 'Normal' : (item.predictedLabel || '-') }}</span>
                    </div>
                    <router-link :to="`/analyses/${item.id}/`">상세 보기</router-link>
                  </article>
                </div>
              </template>
            </div>
          </article>
          <div v-if="!data.recentBatches.length" class="empty panel">최근 분석이 없습니다.</div>
        </div>
      </section>
    </template>
  </div>
</template>
