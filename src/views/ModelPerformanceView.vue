<script setup>
import { onMounted, ref } from "vue";
import { api } from "../services/api";

const versions = ref([]);
const counts = ref([]);

onMounted(async () => {
  const data = await api("/analyses/api/model/performance/");
  versions.value = data.versions;
  counts.value = data.labelCounts;
});
</script>

<template>
  <div class="page">
    <div class="page-head"><h1>모델 성능</h1></div>
    <section class="panel">
      <h2>버전</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>모델</th><th>버전</th><th>F1</th><th>등록일</th><th>활성</th></tr></thead>
          <tbody>
            <tr v-for="version in versions" :key="version.id">
              <td>{{ version.modelName }}</td>
              <td>{{ version.version }}</td>
              <td>{{ version.f1Score }}</td>
              <td>{{ version.registeredAt }}</td>
              <td>{{ version.isActive ? "Y" : "N" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    <section class="panel" style="margin-top:16px">
      <h2>결함 분포</h2>
      <div v-for="count in counts" :key="count.predicted_label || 'empty'" class="card">
        {{ count.predicted_label || "미분류" }}: {{ count.total }}
      </div>
    </section>
  </div>
</template>
