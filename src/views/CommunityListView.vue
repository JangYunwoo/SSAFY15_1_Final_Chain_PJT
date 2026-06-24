<script setup>
import { onMounted, ref } from "vue";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const posts = ref([]);

async function toggleFavorite(event, post) {
  event.preventDefault();
  const data = await api(`/community/api/${post.id}/favorite/`, { method: "POST" });
  post.isFavorite = data.isFavorite;
}

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
    <p class="notice">배정된 LOT과 관련된 게시글만 표시됩니다.</p>
    <div class="grid">
      <router-link v-for="post in posts" :key="post.id" class="card" :to="`/community/${post.id}/`">
        <div class="post-title">
          <strong>{{ post.title }}</strong>
          <button class="star-button" :class="{ active: post.isFavorite }" @click="toggleFavorite($event, post)">
            {{ post.isFavorite ? "★" : "☆" }}
          </button>
        </div>
        <p class="muted">{{ post.author }} · {{ post.department || "-" }} · {{ dateText(post.createdAt) }}</p>
      </router-link>
    </div>
    <div v-if="posts.length === 0" class="empty panel">확인할 수 있는 게시글이 없습니다.</div>
  </div>
</template>
