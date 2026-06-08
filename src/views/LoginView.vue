<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api";
import { store } from "../services/store";

const router = useRouter();
const form = reactive({ username: "", password: "" });
const error = ref("");
const loading = ref(false);

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    const data = await api("/accounts/api/login/", { method: "POST", body: JSON.stringify(form) });
    store.user = data.user;
    router.push("/");
  } catch (err) {
    error.value = err.message || "로그인에 실패했습니다.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="auth-page">
    <form class="auth-panel form" @submit.prevent="submit">
      <div>
        <h1>Wafer Insight</h1>
        <p>Vue 프론트와 Django API로 동작하는 분석 대시보드</p>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="field"><label>아이디</label><input v-model="form.username" class="input" autocomplete="username" required></div>
      <div class="field"><label>비밀번호</label><input v-model="form.password" class="input" type="password" autocomplete="current-password" required></div>
      <button class="btn primary" :disabled="loading">{{ loading ? "로그인 중" : "로그인" }}</button>
      <router-link to="/accounts/register/" class="muted">계정이 없으면 회원가입</router-link>
    </form>
  </section>
</template>
