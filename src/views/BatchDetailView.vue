<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";
import AnalysisTable from "../components/AnalysisTable.vue";

const route = useRoute();
const batch = ref(null);

onMounted(async () => {
  batch.value = (await api(`/analyses/api/batches/${route.params.id}/`)).batch;
});
</script>

<template>
  <div class="page">
    <div class="page-head"><h1>{{ batch?.batchCode || "배치" }}</h1></div>
    <div v-if="batch" class="grid">
      <div class="panel">
        <div class="grid cols-4">
          <div class="metric"><span>LOT</span><strong>{{ batch.lot.lotId }}</strong></div>
          <div class="metric"><span>상태</span><strong>{{ batch.status }}</strong></div>
          <div class="metric"><span>웨이퍼</span><strong>{{ batch.totalWafers }}</strong></div>
          <div class="metric"><span>저신뢰</span><strong>{{ batch.lowConfidenceCount }}</strong></div>
        </div>
      </div>
      <AnalysisTable :items="batch.analyses" />
    </div>
  </div>
</template>
