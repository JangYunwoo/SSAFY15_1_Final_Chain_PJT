<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api";

const router = useRouter();
const lots = ref([]);
const lot = ref("");
const file = ref(null);
const loading = ref(false);
const loadingLots = ref(true);
const message = ref("");

onMounted(async () => {
  try {
    lots.value = (await api("/analyses/api/lots/")).lots;
  } finally {
    loadingLots.value = false;
  }
});

async function submit() {
  const body = new FormData();
  body.append("lot", lot.value);
  body.append("uploaded_file", file.value);
  loading.value = true;
  message.value = "";
  try {
    const data = await api("/analyses/api/upload/", { method: "POST", body });
    message.value = data.message || "분석이 시작되었습니다.";
    window.setTimeout(() => {
      router.push("/analyses/history/");
    }, 700);
  } catch (err) {
    message.value = err.message || "업로드에 실패했습니다.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <div class="page-head"><h1>분석 업로드</h1></div>
    <form class="panel form" @submit.prevent="submit">
      <div v-if="message" class="notice">{{ message }}</div>
      <div class="field">
        <label>LOT</label>
        <select v-model="lot" :disabled="loadingLots || lots.length === 0" required>
          <option value="">{{ loadingLots ? "불러오는 중" : "선택" }}</option>
          <option v-for="item in lots" :key="item.id" :value="item.id">
            {{ item.lotId }} - {{ item.process || "공정 미입력" }}
          </option>
        </select>
        <p v-if="!loadingLots && lots.length === 0" class="muted">
          배정된 Line이 없습니다. 관리자에게 Line 배정을 요청해주세요.
        </p>
      </div>
      <div class="field">
        <label>CSV 파일</label>
        <input class="input" type="file" accept=".csv" required @change="file = $event.target.files[0]">
      </div>
      <button class="btn primary" :disabled="loading || loadingLots || lots.length === 0">
        {{ loading ? "분석 중" : "업로드 및 분석" }}
      </button>
    </form>
  </div>
</template>
