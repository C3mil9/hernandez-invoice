/** Render an invoice using its saved historical details, ready for printing. */
import { api, displayDate, escapeHtml as e, money } from './shared.js';

const content = document.querySelector('#print-content');
document.querySelector('#print-button').addEventListener('click', () => window.print());
const id = new URLSearchParams(window.location.search).get('id');
try {
  if (!/^\d+$/.test(id || '')) throw new Error('Invoice not found.');
  const invoice = await api('/api/invoices/' + id);
  document.title = `${invoice.invoice_number} · Hernandez Invoice`;
  const block = (...values) => values.filter(Boolean).map(value => `<div>${e(value)}</div>`).join('');
  content.innerHTML = `<article class="invoice-sheet"><header class="invoice-header"><div><div class="business-name">${e(invoice.business_name || 'Your business')}</div><div class="contact-block">${block(invoice.business_address, invoice.business_email, invoice.business_phone)}</div></div><div class="invoice-heading"><p>INVOICE</p><h1>${e(invoice.invoice_number)}</h1><span class="invoice-status ${invoice.status.toLowerCase()}">${e(invoice.status)}</span></div></header><div class="invoice-divider"></div><section class="invoice-meta"><div><h2>BILL TO</h2><strong>${e(invoice.customer_name)}</strong><div class="contact-block">${block(invoice.customer_store, invoice.customer_address, invoice.customer_email, invoice.customer_phone)}</div></div><div class="date-list"><div><span>Invoice date</span><strong>${displayDate(invoice.invoice_date)}</strong></div><div><span>Due date</span><strong>${displayDate(invoice.due_date)}</strong></div></div></section><div class="items-wrapper"><table><thead><tr><th>DESCRIPTION</th><th>QTY</th><th>UNIT PRICE</th><th>AMOUNT</th></tr></thead><tbody>${invoice.items.map(item => `<tr><td><strong>${e(item.name)}</strong>${item.sku ? `<small>SKU: ${e(item.sku)}</small>` : ''}</td><td>${e(item.quantity)}</td><td>${money(item.unit_price_cents)}</td><td>${money(item.line_total_cents)}</td></tr>`).join('')}</tbody></table></div><div class="invoice-bottom"><div class="invoice-notes">${invoice.notes ? `<div><h2>NOTES</h2><p>${e(invoice.notes)}</p></div>` : ''}${invoice.invoice_message ? `<div><h2>MESSAGE</h2><p>${e(invoice.invoice_message)}</p></div>` : ''}</div><div class="invoice-totals"><div><span>Subtotal</span><strong>${money(invoice.subtotal_cents)}</strong></div><div><span>Tax (${e(invoice.tax_rate)}%)</span><strong>${money(invoice.tax_cents)}</strong></div><div><span>Shipping</span><strong>${money(invoice.shipping_cents)}</strong></div><div class="invoice-grand-total"><span>Total</span><strong>${money(invoice.total_cents)}</strong></div></div></div><footer>Thank you for your business.</footer></article>`;
} catch (error) {
  content.innerHTML = '';
  const p = document.createElement('p'); p.textContent = error.message; content.append(p);
}
