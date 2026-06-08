<script setup>
import { onMounted, ref } from "vue";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const posts = ref([]);

onMounted(async () => {
  posts.value = (await api("/community/api/")).posts;
});
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>커뮤니티</h1>
      <router-link class="btn primary" to="/community/new/">글쓰기</router-link>
    </div>
    <div class="grid">
      <router-link v-for="post in posts" :key="post.id" class="card" :to="`/community/${post.id}/`">
        <strong>{{ post.title }}</strong>
        <p class="muted">{{ post.author }} · {{ dateText(post.createdAt) }}</p>
      </router-link>
    </div>
  </div>
</template>
