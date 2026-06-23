function getCookie(name) {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`))
    ?.split("=")[1] || "";
}

const unsafeMethods = new Set(["POST", "PUT", "PATCH", "DELETE"]);
let csrfReady = false;

async function ensureCsrfCookie() {
  if (csrfReady || getCookie("csrftoken")) {
    csrfReady = true;
    return;
  }
  await fetch("/accounts/api/me/", {
    credentials: "same-origin"
  });
  csrfReady = true;
}

export async function api(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  if (unsafeMethods.has(method)) {
    await ensureCsrfCookie();
  }

  const headers = options.headers || {};
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      ...headers
    }
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok !== true) {
    throw {
      ...data,
      message: data.message || data.detail || `요청에 실패했습니다. (HTTP ${response.status})`
    };
  }
  return data;
}
