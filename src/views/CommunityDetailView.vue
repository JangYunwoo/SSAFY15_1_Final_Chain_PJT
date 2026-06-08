<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const route = useRoute();
const post = ref(null);
const content = ref("");

async function loadPost() {
  post.value = (await api(`/community/api/${route.params.id}/`)).post;
}

async function comment() {
  await api(`/community/api/${post.value.id}/comments/`, {
    method: "POST",
    body: JSON.stringify({ content: content.value })
  });
  content.value = "";
  await loadPost();
}

onMounted(loadPost);
</script>

<template>
  <div v-if="post" class="page">
    <div class="page-head"><h1>{{ post.title }}</h1></div>
    <article class="panel">
      <p class="muted">{{ post.author }} · {{ dateText(post.createdAt) }}</p>
      <pre class="summary">{{ post.content }}</pre>
    </article>
    <section class="panel" style="margin-top:16px">
      <h2>댓글</h2>
      <div v-for="item in post.comments" :key="item.id" class="comment">
        <strong>{{ item.user }}</strong>
        <p>{{ item.content }}</p>
      </div>
      <form class="form" @submit.prevent="comment">
        <textarea v-model="content" required></textarea>
        <button class="btn primary">댓글 등록</button>
      </form>
    </section>
  </div>
</template>
