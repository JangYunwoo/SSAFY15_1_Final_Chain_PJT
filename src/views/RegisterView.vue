<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../services/api";
import { store } from "../services/store";

const router = useRouter();
const error = ref("");
const form = reactive({
  username: "",
  name: "",
  email: "",
  department: "",
  title: "",
  phone: "",
  password1: "",
  password2: ""
});

async function submit() {
  error.value = "";
  try {
    const data = await api("/accounts/api/register/", { method: "POST", body: JSON.stringify(form) });
    store.user = data.user;
    router.push("/");
  } catch (err) {
    error.value = err.message || "회원가입에 실패했습니다.";
  }
}
</script>

<template>
  <section class="auth-page">
    <form class="auth-panel form" @submit.prevent="submit">
      <div>
        <h1>회원가입</h1>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="field"><label>아이디</label><input v-model="form.username" class="input" required></div>
      <div class="field"><label>이름</label><input v-model="form.name" class="input"></div>
      <div class="field"><label>이메일</label><input v-model="form.email" class="input" type="email" required></div>
      <div class="field"><label>부서</label><input v-model="form.department" class="input"></div>
      <div class="field"><label>직책</label><input v-model="form.title" class="input"></div>
      <div class="field"><label>연락처</label><input v-model="form.phone" class="input"></div>
      <div class="field"><label>비밀번호</label><input v-model="form.password1" class="input" type="password" required></div>
      <div class="field"><label>비밀번호 확인</label><input v-model="form.password2" class="input" type="password" required></div>
      <button class="btn primary">가입하기</button>
      <router-link to="/accounts/login/" class="muted">이미 계정이 있으면 로그인</router-link>
    </form>
  </section>
</template>
