<script setup>
import { useRouter, useRoute } from "vue-router";
import { computed } from "vue";
import { api } from "./services/api";
import { store } from "./services/store";

const router = useRouter();
const route = useRoute();
const isPublic = computed(() => route.meta.public);

async function logout() {
  await api("/accounts/api/logout/", { method: "POST" });
  store.user = null;
  router.push("/accounts/login/");
}
</script>

<template>
  <router-view v-if="isPublic" />
  <div v-else class="app-shell">
    <aside class="sidebar no-print">
      <router-link class="brand" to="/">Wafer Insight</router-link>
      <nav class="nav">
        <router-link to="/">대시보드</router-link>
        <router-link to="/analyses/upload/">분석 업로드</router-link>
        <router-link to="/analyses/history/">분석 이력</router-link>
        <router-link to="/analyses/model/performance/">모델 성능</router-link>
        <router-link to="/community/">커뮤니티</router-link>
        <router-link to="/notifications/">알림/메일</router-link>
        <router-link to="/accounts/profile/">프로필</router-link>
        <a v-if="store.user?.isStaff" href="http://127.0.0.1:8000/admin/">관리자</a>
      </nav>
    </aside>
    <main class="content">
      <header class="topbar no-print">
        <span>{{ store.user?.displayName }}</span>
        <button class="btn ghost" type="button" @click="logout">로그아웃</button>
      </header>
      <router-view />
    </main>
  </div>
</template>
