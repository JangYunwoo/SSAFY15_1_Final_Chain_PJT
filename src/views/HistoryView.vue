<script setup>
import { onMounted, ref } from "vue";
import { api } from "../services/api";
import AnalysisTable from "../components/AnalysisTable.vue";

const items = ref([]);
onMounted(async () => {
  items.value = (await api("/analyses/api/history/")).analyses;
});
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>분석 이력</h1>
      <router-link class="btn primary" to="/analyses/upload/">업로드</router-link>
    </div>
    <AnalysisTable :items="items" />
  </div>
</template>
