import { api, displayDate, escapeHtml as e, invoiceNumber, localDate, money, statusBadge, emptyRow } from './shared.js';

export async function renderDashboard(container, context) {
  const [year, month] = localDate().split('-');
  const [report, invoices, customers, products] = await Promise.all([
    api(`/api/reports?year=${year}&month=${month}`), api('/api/invoices'), api('/api/customers'), api('/api/products')
  ]);
  const monthName = new Date(Number(year), Number(month) - 1, 1).toLocaleDateString('en-US', { month: 'long' });
  container.innerHTML = `
    <div class="page-heading"><div><p class="eyebrow">WELCOME TO HERNANDEZ INVOICE</p><h1>Your business, at a glance.</h1><p class="subheading">Keep track of your invoices and see how business is doing.</p></div><button class="button button-primary" data-go="new-invoice">+&nbsp; Create invoice</button></div>
    <section class="stats-grid" aria-label="Sales overview">
      <article class="stat-card"><div class="stat-top"><span>Sales this month</span><span class="stat-icon mint">↗</span></div><strong>${money(report.selected_month.total_cents)}</strong><small>${e(monthName)} ${year} · ${report.selected_month.invoice_count} invoice(s)</small></article>
      <article class="stat-card"><div class="stat-top"><span>Sales this year</span><span class="stat-icon lavender">▥</span></div><strong>${money(report.yearly.total_cents)}</strong><small>From January to December ${year}</small></article>
      <article class="stat-card"><div class="stat-top"><span>Paid invoices</span><span class="stat-icon peach">✓</span></div><strong>${money(report.yearly.paid_cents)}</strong><small>Invoice date in ${year}</small></article>
      <article class="stat-card"><div class="stat-top"><span>Unpaid invoices</span><span class="stat-icon yellow">◷</span></div><strong>${money(report.yearly.unpaid_cents)}</strong><small>Invoice date in ${year}</small></article>
    </section>
    <div class="dashboard-grid"><section class="panel"><div class="panel-heading"><div><h2>Recent invoices</h2><p>Your latest activity in one place.</p></div><button class="text-button" data-go="invoices">View all <span>→</span></button></div>
      <div class="table-scroll"><table><thead><tr><th>Invoice</th><th>Client</th><th>Date</th><th>Status</th><th class="align-right">Total</th></tr></thead><tbody>${invoices.slice(0, 6).map(row => `<tr><td><a class="table-link" href="/print?id=${row.id}" target="_blank" rel="noopener">${invoiceNumber(row.id)}</a></td><td>${e(row.customer_name)}</td><td>${displayDate(row.invoice_date)}</td><td>${statusBadge(row.status)}</td><td class="align-right strong">${money(row.total_cents)}</td></tr>`).join('') || emptyRow(5, 'No invoices yet. Create your first invoice to get started.')}</tbody></table></div>
    </section><aside class="panel quick-panel"><div class="panel-heading"><div><h2>Quick actions</h2><p>A few ways to get started.</p></div></div><button class="quick-action" data-go="new-client"><span class="quick-icon">♙</span><span><strong>Add a client</strong><small>${customers.filter(x => !x.archived).length} active clients</small></span><b>→</b></button><button class="quick-action" data-go="new-product"><span class="quick-icon">◇</span><span><strong>Add a product</strong><small>${products.filter(x => !x.archived).length} active products</small></span><b>→</b></button><button class="quick-action" data-go="reports"><span class="quick-icon">▥</span><span><strong>View sales reports</strong><small>Explore your monthly sales</small></span><b>→</b></button></aside></div>
    <p class="report-note">Sales totals include paid and unpaid invoices, including tax and shipping. Void invoices are excluded.</p>`;
  container.onclick = event => { const button = event.target.closest('[data-go]'); if (button) context.navigate(button.dataset.go); };
}
