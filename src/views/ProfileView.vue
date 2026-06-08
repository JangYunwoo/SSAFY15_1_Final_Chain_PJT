<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../services/api";
import { store } from "../services/store";

const saved = ref(false);
const form = reactive({ name: "", email: "", department: "", title: "", phone: "" });

onMounted(async () => {
  Object.assign(form, (await api("/accounts/api/profile/")).user);
});

async function submit() {
  const data = await api("/accounts/api/profile/", {
    method: "POST",
    body: JSON.stringify(form)
  });
  store.user = data.user;
  saved.value = true;
}
</script>

<template>
  <div class="page">
    <div class="page-head"><h1>프로필</h1></div>
    <form class="panel form" @submit.prevent="submit">
      <div v-if="saved" class="notice">저장되었습니다.</div>
      <div class="field"><label>이름</label><input v-model="form.name" class="input"></div>
      <div class="field"><label>이메일</label><input v-model="form.email" class="input" type="email" required></div>
      <div class="field"><label>부서</label><input v-model="form.department" class="input"></div>
      <div class="field"><label>직책</label><input v-model="form.title" class="input"></div>
      <div class="field"><label>연락처</label><input v-model="form.phone" class="input"></div>
      <button class="btn primary">저장</button>
    </form>
  </div>
</template>
