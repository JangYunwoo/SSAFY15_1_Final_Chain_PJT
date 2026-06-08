<script setup>
import { statusBadge } from "../utils/format";

defineProps({
  items: {
    type: Array,
    default: () => []
  }
});
</script>

<template>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>분석 코드</th>
          <th>LOT</th>
          <th>웨이퍼</th>
          <th>결함</th>
          <th>신뢰도</th>
          <th>상태</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!items.length">
          <td colspan="7" class="empty">분석 데이터가 없습니다.</td>
        </tr>
        <tr v-for="item in items" :key="item.id">
          <td>{{ item.analysisCode }}</td>
          <td>{{ item.lot?.lotId || "-" }}</td>
          <td>{{ item.waferId || item.waferIndex || "-" }}</td>
          <td>{{ item.predictedLabel || "-" }}</td>
          <td>
            <span :class="['badge', item.isLowConfidence ? 'warn' : 'ok']">
              {{ item.confidencePercent }}%
            </span>
          </td>
          <td>
            <span :class="['badge', statusBadge(item.status)]">{{ item.status }}</span>
          </td>
          <td>
            <router-link class="btn ghost" :to="`/analyses/${item.id}/`">상세</router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
