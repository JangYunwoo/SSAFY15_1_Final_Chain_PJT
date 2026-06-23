<script setup>
import { onMounted, reactive, ref } from "vue";
import { api } from "../services/api";
import { store } from "../services/store";
const saved = ref(false); const imagePreview = ref(""); const imageFile = ref(null);
const form = reactive({ name: "", email: "", department: "", title: "", phone: "" });
onMounted(async () => { const user = (await api("/accounts/api/profile/")).user; Object.assign(form, user); imagePreview.value = user.profileImage; });
function chooseImage(event) { imageFile.value = event.target.files[0]; if (imageFile.value) imagePreview.value = URL.createObjectURL(imageFile.value); }
async function submit() { const data = new FormData(); Object.entries(form).forEach(([key, value]) => data.append(key, value)); if (imageFile.value) data.append("profile_image", imageFile.value); const result = await api("/accounts/api/profile/", { method: "POST", body: data }); store.user = result.user; saved.value = true; }
</script>
<template><div class="page"><div class="page-head"><h1>프로필</h1></div><form class="panel profile-form" @submit.prevent="submit"><div class="profile-photo"><img v-if="imagePreview" :src="imagePreview" alt="프로필 사진"><span v-else>사진</span><label class="btn ghost">사진 선택<input type="file" accept="image/*" hidden @change="chooseImage"></label></div><div class="form"><div v-if="saved" class="notice">저장되었습니다.</div><div class="field"><label>이름</label><input v-model="form.name" class="input"></div><div class="field"><label>이메일</label><input v-model="form.email" class="input" type="email" required></div><div class="field"><label>부서</label><input v-model="form.department" class="input"></div><div class="field"><label>직책</label><input v-model="form.title" class="input"></div><div class="field"><label>연락처</label><input v-model="form.phone" class="input"></div><button class="btn primary">저장</button></div></form></div></template>
