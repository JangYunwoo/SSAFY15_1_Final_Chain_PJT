<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../services/api";
import { store } from "../services/store";

const saved = ref(false);
const editing = ref(false);
const form = reactive({ name: "", email: "", department: "", title: "", phone: "" });
const original = reactive({ name: "", email: "", department: "", title: "", phone: "" });

onMounted(async () => {
  const data = await api("/accounts/api/profile/");
  Object.assign(form, data.user);
  Object.assign(original, data.user);
});

async function submit() {
  const data = await api("/accounts/api/profile/", {
    method: "POST",
    body: JSON.stringify(form)
  });
  store.user = data.user;
  Object.assign(form, data.user);
  Object.assign(original, data.user);
  saved.value = true;
  editing.value = false;
}

function startEdit() {
  saved.value = false;
  editing.value = true;
}

function cancelEdit() {
  Object.assign(form, original);
  saved.value = false;
  editing.value = false;
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>프로필</h1>
      <button v-if="!editing" class="btn primary" type="button" @click="startEdit">수정</button>
    </div>
    <section v-if="!editing" class="panel profile-view">
      <div v-if="saved" class="notice">저장되었습니다.</div>
      <div class="profile-row"><span>이름</span><strong>{{ form.name || "-" }}</strong></div>
      <div class="profile-row"><span>이메일</span><strong>{{ form.email || "-" }}</strong></div>
      <div class="profile-row"><span>부서</span><strong>{{ form.department || "-" }}</strong></div>
      <div class="profile-row"><span>직책</span><strong>{{ form.title || "-" }}</strong></div>
      <div class="profile-row"><span>연락처</span><strong>{{ form.phone || "-" }}</strong></div>
    </section>
    <form v-else class="panel form" @submit.prevent="submit">
      <div class="field"><label>이름</label><input v-model="form.name" class="input"></div>
      <div class="field"><label>이메일</label><input v-model="form.email" class="input" type="email" required></div>
      <div class="field"><label>부서</label><input v-model="form.department" class="input"></div>
      <div class="field"><label>직책</label><input v-model="form.title" class="input"></div>
      <div class="field"><label>연락처</label><input v-model="form.phone" class="input"></div>
      <div class="actions">
        <button class="btn primary">저장</button>
        <button class="btn ghost" type="button" @click="cancelEdit">취소</button>
      </div>
    </form>
  </div>
</template>
