<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api";

const router = useRouter();
const lots = ref([]);
const lot = ref("");
const file = ref(null);
const loading = ref(false);
const message = ref("");

onMounted(async () => {
  lots.value = (await api("/analyses/api/lots/")).lots;
});

async function submit() {
  const body = new FormData();
  body.append("lot", lot.value);
  body.append("uploaded_file", file.value);
  loading.value = true;
  message.value = "";
  try {
    const data = await api("/analyses/api/upload/", { method: "POST", body });
    router.push(`/analyses/batches/${data.batch.id}/`);
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
      <div v-if="message" class="error">{{ message }}</div>
      <div class="field">
        <label>LOT</label>
        <select v-model="lot" required>
          <option value="">선택</option>
          <option v-for="item in lots" :key="item.id" :value="item.id">{{ item.lotId }} - {{ item.process || "공정 미지정" }}</option>
        </select>
      </div>
      <div class="field"><label>CSV 파일</label><input class="input" type="file" accept=".csv" required @change="file = $event.target.files[0]"></div>
      <button class="btn primary" :disabled="loading">{{ loading ? "분석 중" : "업로드 및 분석" }}</button>
    </form>
  </div>
</template>
