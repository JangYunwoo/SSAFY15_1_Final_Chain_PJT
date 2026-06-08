export function statusBadge(status) {
  if (status === "done") return "ok";
  if (status === "failed") return "danger";
  return "warn";
}

export function dateText(value) {
  return value ? new Date(value).toLocaleString("ko-KR") : "-";
}
