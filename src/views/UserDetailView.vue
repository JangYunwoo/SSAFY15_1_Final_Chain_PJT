<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../services/api";
import { store } from "../services/store";

const route = useRoute();
const user = ref(null);
const reports = ref([]);
const loading = ref(true);
const sending = ref(false);
const message = ref("");
const error = ref("");
const mail = reactive({ subject: "", body: "", reportId: "" });

const isMe = computed(() => user.value?.id === store.user?.id);
const profileInitial = computed(() => (user.value?.displayName || user.value?.email || "?").trim().charAt(0).toUpperCase());

async function load() {
  loading.value = true;
  error.value = "";
  try {
    user.value = (await api(`/accounts/api/users/${route.params.id}/`)).user;
    reports.value = (await api("/notifications/api/")).reports || [];
  } catch (requestError) {
    error.value = requestError.message || "사용자 정보를 불러오지 못했습니다.";
  } finally {
    loading.value = false;
  }
}

async function sendMail() {
  sending.value = true;
  message.value = "";
  error.value = "";
  try {
    await api("/notifications/api/send/", {
      method: "POST",
      body: JSON.stringify({
        receiverId: user.value.id,
        subject: mail.subject,
        body: mail.body,
        reportId: mail.reportId || null
      })
    });
    mail.subject = "";
    mail.body = "";
    mail.reportId = "";
    message.value = "메일을 보냈습니다.";
    window.dispatchEvent(new Event("inbox-counts-updated"));
  } catch (requestError) {
    error.value = requestError.message || "메일 전송에 실패했습니다.";
  } finally {
    sending.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>사용자 프로필</h1>
      <router-link class="btn ghost" to="/accounts/users/">목록으로</router-link>
    </div>

    <p v-if="message" class="notice">{{ message }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="loading" class="empty panel">불러오는 중</div>
    <template v-else-if="user">
      <section class="panel profile-view">
        <div class="profile-photo-section">
          <div class="profile-photo" aria-label="프로필 사진 영역">
            <img v-if="user.profileImageUrl" :src="user.profileImageUrl" :alt="user.displayName">
            <span v-else>{{ profileInitial }}</span>
          </div>
          <div class="profile-photo-meta">
            <strong>{{ user.displayName }}</strong>
            <span :class="['role-badge', user.lotRoleKey || (user.isStaff ? 'admin' : 'unassigned')]">
              {{ user.lotRole || (user.isStaff ? "관리자" : "미정") }}
            </span>
            <p>{{ user.department || "부서 미입력" }}</p>
          </div>
        </div>
        <div class="profile-row"><span>이름</span><strong>{{ user.displayName || "-" }}</strong></div>
        <div class="profile-row"><span>이메일</span><strong>{{ user.email || "-" }}</strong></div>
        <div class="profile-row"><span>부서</span><strong>{{ user.department || "-" }}</strong></div>
        <div class="profile-row"><span>직책</span><strong>{{ user.title || "-" }}</strong></div>
        <div class="profile-row"><span>연락처</span><strong>{{ user.phone || "-" }}</strong></div>
      </section>

      <form v-if="!isMe" class="panel form user-mail-form" @submit.prevent="sendMail">
        <h2>메일 보내기</h2>
        <div class="field">
          <label>제목</label>
          <input v-model="mail.subject" class="input" required>
        </div>
        <div class="field">
          <label>보고서 첨부</label>
          <select v-model="mail.reportId">
            <option value="">첨부하지 않음</option>
            <option v-for="report in reports" :key="report.id" :value="report.id">
              [{{ report.sourceType }}] {{ report.title }}
            </option>
          </select>
        </div>
        <div v-if="reports.length === 0" class="muted">첨부할 수 있는 내 보고서가 없습니다.</div>
        <div class="field">
          <label>내용</label>
          <textarea v-model="mail.body" required></textarea>
        </div>
        <button class="btn primary" :disabled="sending">
          {{ sending ? "전송 중" : "메일 보내기" }}
        </button>
      </form>
    </template>
  </div>
</template>
