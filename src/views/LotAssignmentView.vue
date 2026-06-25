<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { api } from "../services/api";
import { dateText } from "../utils/format";

const lines = ref([]);
const users = ref([]);
const assignments = ref([]);
const loading = ref(true);
const saving = ref(false);
const message = ref("");
const error = ref("");
const form = reactive({ lineId: "", userId: "", role: "owner" });

const selectedLineAssignments = computed(() => {
  if (!form.lineId) return assignments.value;
  return assignments.value.filter((item) => item.lineId === Number(form.lineId));
});

const assignedUserIds = computed(() => new Set(assignments.value.map((item) => item.userId)));

const availableUsers = computed(() => {
  if (!form.lineId) return users.value;
  return users.value.filter((user) => !assignedUserIds.value.has(user.id) || user.id === Number(form.userId));
});

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const data = await api("/analyses/api/lot-assignments/");
    lines.value = data.lines;
    users.value = data.users;
    assignments.value = data.assignments;
  } catch (requestError) {
    error.value = requestError.message || "Line 배정 정보를 불러오지 못했습니다.";
  } finally {
    loading.value = false;
  }
}

async function submit() {
  saving.value = true;
  message.value = "";
  error.value = "";
  try {
    const data = await api("/analyses/api/lot-assignments/", {
      method: "POST",
      body: JSON.stringify({
        lineId: form.lineId,
        userId: form.userId,
        role: form.role
      })
    });
    const index = assignments.value.findIndex((item) => item.id === data.assignment.id);
    if (index >= 0) {
      assignments.value[index] = data.assignment;
    } else {
      assignments.value.unshift(data.assignment);
    }
    form.userId = "";
    message.value = data.created ? "Line을 배정했습니다." : "기존 배정을 업데이트했습니다.";
  } catch (requestError) {
    error.value = requestError.message || "Line 배정에 실패했습니다.";
  } finally {
    saving.value = false;
  }
}

async function removeAssignment(assignment) {
  if (!window.confirm(`${assignment.userName}님의 ${assignment.lineName} Line 배정을 해제할까요?`)) return;
  message.value = "";
  error.value = "";
  try {
    await api(`/analyses/api/lot-assignments/${assignment.id}/`, { method: "DELETE" });
    assignments.value = assignments.value.filter((item) => item.id !== assignment.id);
    message.value = "Line 배정을 해제했습니다.";
  } catch (requestError) {
    error.value = requestError.message || "Line 배정 해제에 실패했습니다.";
  }
}

onMounted(load);
</script>

<template>
  <div class="page">
    <div class="page-head">
      <div>
        <h1>Line 배정</h1>
        <p class="muted">관리자가 사용자에게 Line을 배정하면 해당 Line에서 발생한 LOT 분석 결과만 확인할 수 있습니다.</p>
      </div>
    </div>

    <p v-if="message" class="notice">{{ message }}</p>
    <p v-if="error" class="error">{{ error }}</p>

    <section class="panel assignment-layout">
      <form class="assignment-form" @submit.prevent="submit">
        <div class="field">
          <label>Line</label>
          <select v-model="form.lineId" required>
            <option value="">선택</option>
            <option v-for="line in lines" :key="line.id" :value="line.id">
              {{ line.displayName }}
            </option>
          </select>
        </div>
        <div class="field">
          <label>사용자</label>
          <select v-model="form.userId" :disabled="!form.lineId" required>
            <option value="">선택</option>
            <option v-for="user in availableUsers" :key="user.id" :value="user.id">
              {{ user.displayName }} · {{ user.department || "부서 미입력" }}
            </option>
          </select>
        </div>
        <div class="field">
          <label>역할</label>
          <select v-model="form.role">
            <option value="owner">담당자</option>
            <option value="reviewer">책임자</option>
          </select>
        </div>
        <button class="btn primary" :disabled="saving || !form.lineId || !form.userId">
          {{ saving ? "배정 중" : "Line 배정" }}
        </button>
      </form>

      <div class="assignment-summary">
        <strong>{{ assignments.length }}</strong>
        <span>현재 배정</span>
        <p class="muted">배정 즉시 사용자에게 알림이 전송됩니다.</p>
      </div>
    </section>

    <section class="table-wrap assignment-table">
      <table>
        <thead>
          <tr>
            <th>Line</th>
            <th>사용자</th>
            <th>역할</th>
            <th>배정자</th>
            <th>배정일</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="assignment in selectedLineAssignments" :key="assignment.id">
            <td><strong>{{ assignment.lineName }}</strong></td>
            <td>
              <strong>{{ assignment.userName }}</strong>
              <p class="muted">{{ assignment.department || "부서 미입력" }} · {{ assignment.userEmail }}</p>
            </td>
            <td>
              <span class="badge">{{ assignment.role === "owner" ? "담당자" : "책임자" }}</span>
            </td>
            <td>{{ assignment.assignedBy }}</td>
            <td>{{ dateText(assignment.assignedAt) }}</td>
            <td>
              <button class="btn ghost" type="button" @click="removeAssignment(assignment)">해제</button>
            </td>
          </tr>
          <tr v-if="!loading && selectedLineAssignments.length === 0">
            <td colspan="6" class="empty">표시할 Line 배정이 없습니다.</td>
          </tr>
          <tr v-if="loading">
            <td colspan="6" class="empty">불러오는 중</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>
