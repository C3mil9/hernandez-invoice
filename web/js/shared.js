/** Shared API, formatting and small interface helpers. */
import { locale, t, translateError, invoiceStatus } from "./language.js";

export async function api(path, options = {}) {
  const settings = { ...options, headers: { ...(options.headers || {}) } };
  if (settings.body && typeof settings.body !== "string") {
    settings.headers["Content-Type"] = "application/json";
    settings.body = JSON.stringify(settings.body);
  }
  let response;
  try {
    response = await fetch(path, settings);
  } catch {
    throw new Error(t("Could not connect to the app."));
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(t("The app could not read the server response."));
  }
  if (!response.ok)
    throw new Error(
      data.error ? translateError(data.error) : t("Something went wrong."),
    );
  return data;
}

export function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );
}

export function money(cents) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format((Number(cents) || 0) / 100);
}

export function displayDate(value) {
  if (!value) return "—";
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(locale(), {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function localDate() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function statusBadge(status) {
  const className =
    status === "Paid" ? "paid" : status === "Void" ? "void" : "unpaid";
  return `<span class="badge ${className}"><span></span>${escapeHtml(invoiceStatus(status))}</span>`;
}

export function invoiceNumber(id) {
  return `INV-${String(id).padStart(6, "0")}`;
}
export function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}
export function emptyRow(columns, message) {
  return `<tr><td class="empty-cell" colspan="${columns}">${escapeHtml(message)}</td></tr>`;
}
export function formError(form, message) {
  const box = form.querySelector(".form-error");
  if (box) {
    box.textContent = message;
    box.hidden = false;
    box.focus();
  }
}
export function confirmArchive(thing) {
  return window.confirm(
    t(
      thing === "client"
        ? "Archive this client? It will be hidden from new invoices and can be restored later."
        : "Archive this product? It will be hidden from new invoices and can be restored later.",
    ),
  );
}

export const icon = {
  arrow: "↗",
  plus: "+",
};
