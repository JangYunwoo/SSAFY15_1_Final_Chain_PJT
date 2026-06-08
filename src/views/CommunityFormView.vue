<script setup>
import { reactive } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api";

const router = useRouter();
const form = reactive({ title: "", content: "" });

async function submit() {
  const data = await api("/community/api/new/", { method: "POST", body: JSON.stringify(form) });
  router.push(`/community/${data.post.id}/`);
}
</script>

<template>
  <div class="page">
    <div class="page-head"><h1>글쓰기</h1></div>
    <form class="panel form" @submit.prevent="submit">
      <div class="field"><label>제목</label><input v-model="form.title" class="input" required></div>
      <div class="field"><label>내용</label><textarea v-model="form.content" required></textarea></div>
      <button class="btn primary">등록</button>
    </form>
  </div>
</template>
