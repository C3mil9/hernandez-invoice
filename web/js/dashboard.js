/** Home screen: current sales and quick links. */
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
import { invoiceCount, locale, t } from "./language.js";

export async function renderDashboard(container, context) {
  const [year, month] = localDate().split("-");
  const [report, invoices, customers, products] = await Promise.all([
    api(`/api/reports?year=${year}&month=${month}`),
    api("/api/invoices"),
    api("/api/customers"),
    api("/api/products"),
  ]);
  const monthName = new Date(
    Number(year),
    Number(month) - 1,
    1,
  ).toLocaleDateString(locale(), { month: "long" });
  container.innerHTML = `
    <div class="page-heading"><div><p class="eyebrow">${t("WELCOME TO HERNANDEZ INVOICE")}</p><h1>${t("Your business, at a glance.")}</h1><p class="subheading">${t("Keep track of your invoices and see how business is doing.")}</p></div><button class="button button-primary" data-go="new-invoice">+&nbsp; ${t("Create invoice")}</button></div>
    <section class="stats-grid" aria-label="${t("Sales overview")}">
      <article class="stat-card"><div class="stat-top"><span>${t("Sales this month")}</span><span class="stat-icon mint">↗</span></div><strong>${money(report.selected_month.total_cents)}</strong><small>${e(monthName)} ${year} · ${invoiceCount(report.selected_month.invoice_count)}</small></article>
      <article class="stat-card"><div class="stat-top"><span>${t("Sales this year")}</span><span class="stat-icon lavender">▥</span></div><strong>${money(report.yearly.total_cents)}</strong><small>${t("From January to December {year}", { year })}</small></article>
      <article class="stat-card"><div class="stat-top"><span>${t("Paid invoices")}</span><span class="stat-icon peach">✓</span></div><strong>${money(report.yearly.paid_cents)}</strong><small>${t("Invoice date in {year}", { year })}</small></article>
      <article class="stat-card"><div class="stat-top"><span>${t("Unpaid invoices")}</span><span class="stat-icon yellow">◷</span></div><strong>${money(report.yearly.unpaid_cents)}</strong><small>${t("Invoice date in {year}", { year })}</small></article>
    </section>
    <div class="dashboard-grid"><section class="panel"><div class="panel-heading"><div><h2>${t("Recent invoices")}</h2><p>${t("Your latest activity in one place.")}</p></div><button class="text-button" data-go="invoices">${t("View all")} <span>→</span></button></div>
      <div class="table-scroll"><table><thead><tr><th>${t("Invoice")}</th><th>${t("Client")}</th><th>${t("Date")}</th><th>${t("Status")}</th><th class="align-right">${t("Total")}</th></tr></thead><tbody>${
        invoices
          .slice(0, 6)
          .map(
            (row) =>
              `<tr><td><a class="table-link" href="/print?id=${row.id}" target="_blank" rel="noopener">${invoiceNumber(row.id)}</a></td><td>${e(row.customer_name)}</td><td>${displayDate(row.invoice_date)}</td><td>${statusBadge(row.status)}</td><td class="align-right strong">${money(row.total_cents)}</td></tr>`,
          )
          .join("") ||
        emptyRow(
          5,
          t("No invoices yet. Create your first invoice to get started."),
        )
      }</tbody></table></div>
    </section><aside class="panel quick-panel"><div class="panel-heading"><div><h2>${t("Quick actions")}</h2><p>${t("A few ways to get started.")}</p></div></div><button class="quick-action" data-go="new-client"><span class="quick-icon">♙</span><span><strong>${t("Add a client")}</strong><small>${t("{count} active clients", { count: customers.filter((x) => !x.archived).length })}</small></span><b>→</b></button><button class="quick-action" data-go="new-product"><span class="quick-icon">◇</span><span><strong>${t("Add a product")}</strong><small>${t("{count} active products", { count: products.filter((x) => !x.archived).length })}</small></span><b>→</b></button><button class="quick-action" data-go="reports"><span class="quick-icon">▥</span><span><strong>${t("View sales reports")}</strong><small>${t("Explore your monthly sales")}</small></span><b>→</b></button></aside></div>
    <p class="report-note">${t("Sales totals include paid and unpaid invoices, including tax and shipping. Void invoices are excluded.")}</p>`;
  container.onclick = (event) => {
    const button = event.target.closest("[data-go]");
    if (button) context.navigate(button.dataset.go);
  };
}
