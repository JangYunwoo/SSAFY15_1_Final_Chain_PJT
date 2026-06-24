<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../services/api";
import { store } from "../services/store";

const users = ref([]);
const keyword = ref("");
const loading = ref(true);

const roleColumns = [
  { key: "admin", label: "관리자" },
  { key: "responsible", label: "책임자" },
  { key: "owner", label: "담당자" },
  { key: "unassigned", label: "미정" }
];

const filteredUsers = computed(() => {
  const text = keyword.value.trim().toLowerCase();
  if (!text) return users.value;
  return users.value.filter((user) =>
    [user.displayName, user.email, user.department, user.title, user.lotRole]
      .filter(Boolean)
      .some((value) => value.toLowerCase().includes(text))
  );
});

const usersByRole = computed(() => {
  const grouped = Object.fromEntries(roleColumns.map((column) => [column.key, []]));
  for (const user of filteredUsers.value) {
    const key = user.lotRoleKey || (user.isStaff ? "admin" : "unassigned");
    if (!grouped[key]) grouped.unassigned.push(user);
    else grouped[key].push(user);
  }
  return grouped;
});

function initial(user) {
  return (user.displayName || user.email || "?").trim().charAt(0).toUpperCase();
}

onMounted(async () => {
  try {
    users.value = (await api("/accounts/api/users/")).users;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>사용자</h1>
    </div>

    <section class="panel user-directory-filter">
      <div class="field">
        <label>사용자 검색</label>
        <input v-model="keyword" class="input" placeholder="이름, 이메일, 부서, 직책, 역할로 검색">
      </div>
    </section>

    <section class="user-role-board row-layout">
      <article v-for="column in roleColumns" :key="column.key" class="user-role-row">
        <div class="user-role-row-head">
          <strong>{{ column.label }}</strong>
          <span>{{ usersByRole[column.key].length }}명</span>
        </div>
        <div class="user-role-row-list">
          <router-link
            v-for="user in usersByRole[column.key]"
            :key="user.id"
            class="user-card"
            :to="`/accounts/users/${user.id}/`"
          >
            <span class="user-avatar">
              <img v-if="user.profileImageUrl" :src="user.profileImageUrl" :alt="user.displayName">
              <span v-else>{{ initial(user) }}</span>
            </span>
            <span class="user-card-body">
              <span class="user-card-title">
                <strong>{{ user.displayName }}</strong>
                <span :class="['role-badge', user.lotRoleKey || (user.isStaff ? 'admin' : 'unassigned')]">
                  {{ user.lotRole || (user.isStaff ? "관리자" : "미정") }}
                </span>
                <span v-if="user.id === store.user?.id" class="self-badge">나</span>
              </span>
              <span class="muted">{{ user.department || "부서 미입력" }} · {{ user.title || "직책 미입력" }}</span>
              <span class="muted">{{ user.email }}</span>
            </span>
          </router-link>
          <div v-if="!loading && usersByRole[column.key].length === 0" class="empty compact">
            해당 사용자가 없습니다.
          </div>
        </div>
      </article>
    </section>

    <div v-if="loading" class="empty panel">불러오는 중</div>
    <div v-else-if="filteredUsers.length === 0" class="empty panel">표시할 사용자가 없습니다.</div>
  </div>
</template>
