/** Monthly and yearly sales views and Excel-friendly downloads. */
import {
  api,
  displayDate,
  escapeHtml as e,
  invoiceNumber,
  localDate,
  money,
  statusBadge,
  emptyRow,
} from "./shared.js";
import { currentLanguage, invoiceCount, locale, t } from "./language.js";

export async function renderReports(container, context) {
  const [initialYear, initialMonth] = localDate().split("-");
  async function draw(year, month) {
    const report = await api(
      `/api/reports?year=${encodeURIComponent(year)}&month=${encodeURIComponent(month)}`,
    );
    const names = Array.from({ length: 12 }, (_, index) =>
      new Date(2020, index, 1).toLocaleString(locale(), { month: "long" }),
    );
    const lang = currentLanguage();
    container.innerHTML = `<div class="page-heading"><div><p class="eyebrow">${t("UNDERSTAND YOUR BUSINESS")}</p><h1>${t("Sales reports")}</h1><p class="subheading">${t("See monthly and yearly invoice totals at a glance.")}</p></div></div>
      <form class="panel report-filters" id="report-filter"><label>${t("Year")}<input type="number" name="year" min="1900" max="9999" step="1" value="${report.year}" required></label><label>${t("Month")}<select name="month">${names.map((name, index) => `<option value="${index + 1}" ${index + 1 === report.month ? "selected" : ""}>${e(name)}</option>`).join("")}</select></label><button class="button button-primary" type="submit">${t("View report")}</button></form>
      <section class="stats-grid report-stats" aria-label="${t("Report totals")}"><article class="stat-card"><div class="stat-top"><span>${t("{month} sales", { month: names[report.month - 1] })}</span><span class="stat-icon mint">↗</span></div><strong>${money(report.selected_month.total_cents)}</strong><small>${invoiceCount(report.selected_month.invoice_count)}</small></article><article class="stat-card"><div class="stat-top"><span>${t("{year} sales", { year: report.year })}</span><span class="stat-icon lavender">▥</span></div><strong>${money(report.yearly.total_cents)}</strong><small>${invoiceCount(report.yearly.invoice_count)}</small></article><article class="stat-card"><div class="stat-top"><span>${t("Paid invoices")}</span><span class="stat-icon peach">✓</span></div><strong>${money(report.yearly.paid_cents)}</strong><small>${t("Invoice date in {year}", { year: report.year })}</small></article><article class="stat-card"><div class="stat-top"><span>${t("Unpaid invoices")}</span><span class="stat-icon yellow">◷</span></div><strong>${money(report.yearly.unpaid_cents)}</strong><small>${t("Invoice date in {year}", { year: report.year })}</small></article></section>
      <section class="panel report-panel"><div class="panel-heading wrap-heading"><div><h2>${t("Yearly breakdown")}</h2><p>${t("Monthly invoice totals for {year}.", { year: report.year })}</p></div><div class="heading-actions"><a class="button button-secondary button-small" href="/api/exports/sales.csv?year=${report.year}&amp;lang=${lang}">↓&nbsp; ${t("Export year CSV")}</a><a class="button button-secondary button-small" href="/api/exports/invoice-items.csv?year=${report.year}&amp;lang=${lang}">↓&nbsp; ${t("Export items CSV")}</a></div></div><div class="table-scroll"><table><thead><tr><th>${t("Month")}</th><th>${t("Invoices")}</th><th>${t("Paid")}</th><th>${t("Unpaid")}</th><th class="align-right">${t("Total sales")}</th></tr></thead><tbody>${report.months.map((row) => `<tr class="${row.month === report.month ? "selected-report-row" : ""}"><td><strong>${e(names[row.month - 1])}</strong></td><td>${row.invoice_count}</td><td>${money(row.paid_cents)}</td><td>${money(row.unpaid_cents)}</td><td class="align-right strong">${money(row.total_cents)}</td></tr>`).join("")}</tbody><tfoot><tr><td><strong>${t("Year total")}</strong></td><td>${report.yearly.invoice_count}</td><td>${money(report.yearly.paid_cents)}</td><td>${money(report.yearly.unpaid_cents)}</td><td class="align-right strong">${money(report.yearly.total_cents)}</td></tr></tfoot></table></div></section>
      <section class="panel report-panel"><div class="panel-heading wrap-heading"><div><h2>${t("{month} invoices", { month: names[report.month - 1] })}</h2><p>${t("Invoices included in this month's total.")}</p></div><a class="button button-secondary button-small" href="/api/exports/sales.csv?year=${report.year}&amp;month=${report.month}&amp;lang=${lang}">↓&nbsp; ${t("Export month CSV")}</a></div><div class="table-scroll"><table><thead><tr><th>${t("Invoice")}</th><th>${t("Client")}</th><th>${t("Date")}</th><th>${t("Status")}</th><th class="align-right">${t("Total")}</th></tr></thead><tbody>${report.invoices.map((row) => `<tr><td><a class="table-link" href="/print?id=${row.id}" target="_blank" rel="noopener">${invoiceNumber(row.id)}</a></td><td>${e(row.customer_name)}</td><td>${displayDate(row.invoice_date)}</td><td>${statusBadge(row.status)}</td><td class="align-right strong">${money(row.total_cents)}</td></tr>`).join("") || emptyRow(5, t("No sales invoices for this month."))}</tbody></table></div></section>
      <p class="report-note">${t("Sales are grouped by invoice date and include paid and unpaid invoices, tax, and shipping. Void invoices are excluded. CSV files open in Excel; amounts shown as unpaid are based on invoice status, not partial payments.")}</p>`;
    container.onsubmit = (event) => {
      event.preventDefault();
      const data = new FormData(event.target);
      draw(data.get("year"), data.get("month")).catch((error) =>
        context.notify(error.message),
      );
    };
  }
  await draw(initialYear, initialMonth);
}
