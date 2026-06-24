<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { api } from "../services/api";
import { store } from "../services/store";

const saved = ref(false);
const editing = ref(false);
const selectedImage = ref(null);
const imagePreview = ref("");
const form = reactive({ name: "", email: "", department: "", title: "", phone: "", profileImageUrl: "" });
const original = reactive({ name: "", email: "", department: "", title: "", phone: "", profileImageUrl: "" });
const profileInitial = computed(() => (form.name || form.email || "?").trim().charAt(0).toUpperCase());
const photoUrl = computed(() => imagePreview.value || form.profileImageUrl);

function applyUser(user) {
  Object.assign(form, user);
  Object.assign(original, user);
  selectedImage.value = null;
  imagePreview.value = "";
}

onMounted(async () => {
  const data = await api("/accounts/api/profile/");
  applyUser(data.user);
});

function handleImageChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  selectedImage.value = file;
  imagePreview.value = URL.createObjectURL(file);
  saved.value = false;
}

async function submit() {
  const body = new FormData();
  body.append("name", form.name || "");
  body.append("email", form.email || "");
  body.append("department", form.department || "");
  body.append("title", form.title || "");
  body.append("phone", form.phone || "");
  if (selectedImage.value) {
    body.append("profile_image", selectedImage.value);
  }

  const data = await api("/accounts/api/profile/", {
    method: "POST",
    body
  });
  store.user = data.user;
  applyUser(data.user);
  saved.value = true;
  editing.value = false;
}

function startEdit() {
  saved.value = false;
  editing.value = true;
}

function cancelEdit() {
  Object.assign(form, original);
  selectedImage.value = null;
  imagePreview.value = "";
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
      <div class="profile-photo-section">
        <div class="profile-photo" aria-label="프로필 사진 영역">
          <img v-if="photoUrl" :src="photoUrl" alt="프로필 사진">
          <span v-else>{{ profileInitial }}</span>
        </div>
        <div class="profile-photo-meta">
          <strong>{{ form.name || "사용자" }}</strong>
          <p>{{ form.department || "부서 미입력" }}</p>
        </div>
      </div>
      <div v-if="saved" class="notice">저장되었습니다.</div>
      <div class="profile-row"><span>이름</span><strong>{{ form.name || "-" }}</strong></div>
      <div class="profile-row"><span>이메일</span><strong>{{ form.email || "-" }}</strong></div>
      <div class="profile-row"><span>부서</span><strong>{{ form.department || "-" }}</strong></div>
      <div class="profile-row"><span>직책</span><strong>{{ form.title || "-" }}</strong></div>
      <div class="profile-row"><span>연락처</span><strong>{{ form.phone || "-" }}</strong></div>
    </section>

    <form v-else class="panel form" @submit.prevent="submit">
      <div class="profile-photo-section">
        <div class="profile-photo" aria-label="프로필 사진 영역">
          <img v-if="photoUrl" :src="photoUrl" alt="프로필 사진 미리보기">
          <span v-else>{{ profileInitial }}</span>
        </div>
        <div class="profile-photo-meta">
          <strong>{{ form.name || "사용자" }}</strong>
          <p>프로필 사진</p>
          <label class="btn ghost profile-upload-button">
            사진 선택
            <input type="file" accept="image/*" @change="handleImageChange">
          </label>
        </div>
      </div>

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
