/** Invoice list and editor. The server recalculates all totals when saving. */
import { api, displayDate, escapeHtml as e, formData, formError, invoiceNumber, localDate, money, statusBadge, emptyRow } from './shared.js';
import { t } from './language.js';

export async function renderInvoices(container, context) {
  const invoices = await api('/api/invoices');
  container.innerHTML = `<div class="page-heading"><div><p class="eyebrow">${t('GET PAID WITH CONFIDENCE')}</p><h1>${t('Invoices')}</h1><p class="subheading">${t('Create, print, and keep track of your invoices.')}</p></div><button class="button button-primary" data-action="new">+&nbsp; ${t('New invoice')}</button></div><section class="panel"><div class="table-toolbar"><div class="search-wrap"><span aria-hidden="true">⌕</span><input id="invoice-search" type="search" placeholder="${t('Search invoice number or client')}" aria-label="${t('Search invoices')}"></div><label class="filter-label">${t('Status')} <select id="invoice-filter" aria-label="${t('Filter invoice status')}"><option value="">${t('All statuses')}</option><option value="Unpaid">${t('Unpaid')}</option><option value="Paid">${t('Paid')}</option><option value="Void">${t('Void')}</option></select></label></div><div class="table-scroll"><table class="invoice-list-table"><thead><tr><th>${t('Invoice')}</th><th>${t('Client')}</th><th>${t('Date')}</th><th>${t('Status')}</th><th>${t('Total')}</th><th class="align-right">${t('Actions')}</th></tr></thead><tbody id="invoice-rows"></tbody></table></div></section><p class="report-note">${t('Void invoices stay in your history and are excluded from sales reports.')}</p>`;
  const draw = () => {
    const search = container.querySelector('#invoice-search').value.trim().toLowerCase();
    const filter = container.querySelector('#invoice-filter').value;
    const matches = invoices.filter(row => (!filter || row.status === filter) && [invoiceNumber(row.id), row.customer_name, row.customer_store].some(value => value.toLowerCase().includes(search)));
    const emptyMessage = search || filter ? t('No invoices match these filters. Try another search or status.') : t('No invoices yet. Create your first invoice to get started.');
    container.querySelector('#invoice-rows').innerHTML = matches.map(row => `<tr><td><strong>${invoiceNumber(row.id)}</strong></td><td>${e(row.customer_name)}${row.customer_store ? `<small class="cell-subtitle">${e(row.customer_store)}</small>` : ''}</td><td>${displayDate(row.invoice_date)}</td><td>${statusBadge(row.status)}</td><td class="strong">${money(row.total_cents)}</td><td class="align-right"><div class="row-actions"><a class="action-button" href="/print?id=${row.id}" target="_blank" rel="noopener">${t('View / print')}</a><button class="action-button" data-action="edit" data-id="${row.id}">${t('Edit')}</button>${row.status === 'Unpaid' ? `<button class="action-button" data-action="status" data-status="Paid" data-id="${row.id}">${t('Mark paid')}</button>` : row.status === 'Paid' ? `<button class="action-button" data-action="status" data-status="Unpaid" data-id="${row.id}">${t('Mark unpaid')}</button>` : `<button class="action-button" data-action="status" data-status="Unpaid" data-id="${row.id}">${t('Reopen')}</button>`}${row.status !== 'Void' ? `<button class="action-button muted-action" data-action="status" data-status="Void" data-id="${row.id}">${t('Void invoice')}</button>` : ''}</div></td></tr>`).join('') || emptyRow(6, emptyMessage);
  };
  draw(); container.oninput = draw; container.onchange = draw;
  container.onclick = async event => {
    const button = event.target.closest('[data-action]'); if (!button) return;
    const { action, id, status } = button.dataset;
    if (action === 'new') return context.navigate('new-invoice');
    if (action === 'edit') return context.navigate('edit-invoice', id);
    if (action === 'status') {
      if (status === 'Void' && !window.confirm(t('Void this invoice? It will stay in your records but will be excluded from sales reports.'))) return;
      try { await api(`/api/invoices/${id}/status`, { method: 'POST', body: { status } }); context.notify(t(`Invoice marked ${status.toLowerCase()}.`)); await renderInvoices(container, context); }
      catch (error) { context.notify(error.message); }
    }
  };
}

// Convert decimal input to a scaled integer so the preview follows the same
// rounding as the Python server. Invalid inputs display as zero until fixed.
function scaled(value, places) {
  if (!/^\d+(\.\d+)?$/.test(value || '')) return 0n;
  const [whole, fraction = ''] = value.split('.');
  if (fraction.length > places) return 0n;
  return BigInt(whole) * (10n ** BigInt(places)) + BigInt((fraction + '0'.repeat(places)).slice(0, places));
}

export async function renderInvoiceForm(container, context, id) {
  const [clients, products, settings, invoice] = await Promise.all([
    api('/api/customers'), api('/api/products'), api('/api/settings'), id ? api('/api/invoices/' + id) : Promise.resolve(null)
  ]);
  const activeClients = clients.filter(client => !client.archived || (invoice && client.id === invoice.customer_id));
  const clientOptions = activeClients.map(client => `<option value="${client.id}" ${invoice && client.id === invoice.customer_id ? 'selected' : ''}>${e(client.name)}${client.store ? ` — ${e(client.store)}` : ''}${client.archived ? ` (${t('archived')})` : ''}</option>`).join('');
  container.innerHTML = `<div class="page-heading"><div><a class="back-link" href="#invoices">←&nbsp; ${t('Back to invoices')}</a><h1>${invoice ? t('Edit {number}', { number: invoiceNumber(invoice.id) }) : t('Create an invoice')}</h1><p class="subheading">${t('Add the details below, then save and print your invoice.')}</p></div></div>
  ${!activeClients.length ? `<div class="notice">${t('You need a client before creating an invoice.')} <a href="#new-client">${t('Add your first client')} →</a></div>` : ''}
  <form class="invoice-form" id="invoice-form"><div class="form-error" role="alert" tabindex="-1" hidden></div><section class="panel form-panel"><div class="form-section-title"><h2>${t('Invoice details')}</h2><p>${t('Choose who this invoice is for and when it is due.')}</p></div><div class="form-grid four-columns"><label class="span-two">${t('Client')} <em>*</em><select name="customer_id" required><option value="">${t('Select a client')}</option>${clientOptions}</select></label><label>${t('Invoice date')} <em>*</em><input name="invoice_date" type="date" value="${e(invoice?.invoice_date || localDate())}" required></label><label>${t('Due date')} <span class="optional">${t('Optional')}</span><input name="due_date" type="date" value="${e(invoice?.due_date || '')}"></label><label>${t('Status')}<select name="status"><option value="Unpaid" ${!invoice || invoice.status === 'Unpaid' ? 'selected' : ''}>${t('Unpaid')}</option><option value="Paid" ${invoice?.status === 'Paid' ? 'selected' : ''}>${t('Paid')}</option><option value="Void" ${invoice?.status === 'Void' ? 'selected' : ''}>${t('Void')}</option></select></label></div></section>
  <section class="panel form-panel"><div class="form-section-title split-title"><div><h2>${t('Invoice items')}</h2><p>${t('Select a product or add a custom item. Prices can be adjusted here.')}</p></div><button class="button button-secondary" type="button" data-action="add-item">+&nbsp; ${t('Add item')}</button></div><div class="items-list" id="items-list"></div></section>
  <section class="panel form-panel"><div class="form-section-title"><h2>${t('Totals & notes')}</h2><p>${t('Tax applies to items before shipping.')}</p></div><div class="totals-layout"><label>${t('Notes')} <span class="optional">${t('Optional')}</span><textarea name="notes" rows="5" maxlength="2000" placeholder="${t('Add a note for this invoice')}">${e(invoice?.notes || '')}</textarea></label><div class="totals-box"><div class="total-row"><span>${t('Subtotal')}</span><strong id="preview-subtotal">$0.00</strong></div><label class="total-row input-row"><span>${t('Tax rate (%)')}</span><input name="tax_rate" type="number" min="0" max="100" step="0.01" value="${e(invoice?.tax_rate || settings.default_tax_rate || '0.00')}" required></label><div class="total-row"><span>${t('Tax')}</span><strong id="preview-tax">$0.00</strong></div><label class="total-row input-row"><span>${t('Shipping ($)')}</span><input name="shipping" type="number" min="0" max="99999999" step="0.01" value="${e(invoice?.shipping || '0.00')}" required></label><div class="total-row grand-total"><span>${t('Total')}</span><strong id="preview-total">$0.00</strong></div></div></div></section><div class="form-actions invoice-form-actions"><a class="button button-secondary" href="#invoices">${t('Cancel')}</a><button class="button button-primary" type="submit" ${!activeClients.length ? 'disabled' : ''}>${t(invoice ? 'Save changes' : 'Save invoice')}</button></div></form>`;

  const list = container.querySelector('#items-list');
  const addItem = (item = {}) => {
    const productOptions = products.filter(product => !product.archived || product.id === item.product_id).map(product => `<option value="${product.id}" ${product.id === item.product_id ? 'selected' : ''}>${e(product.name)}${product.archived ? ` (${t('archived')})` : ''}</option>`).join('');
    const row = document.createElement('div'); row.className = 'invoice-item';
    row.innerHTML = `<div class="item-main"><label>${t('Product')}<select data-field="product_id"><option value="">${t('Custom item')}</option>${productOptions}</select></label><label>${t('Item name')} <em>*</em><input data-field="name" value="${e(item.name || '')}" maxlength="200" required placeholder="${t('Item name')}"></label><label>SKU <span class="optional">${t('Optional')}</span><input data-field="sku" value="${e(item.sku || '')}" maxlength="100" placeholder="SKU"></label></div><div class="item-details"><label>${t('Quantity')} <em>*</em><input data-field="quantity" type="number" min="0.001" max="100000" step="0.001" value="${e(item.quantity || '1')}" required></label><label>${t('Unit price ($)')} <em>*</em><input data-field="unit_price" type="number" min="0" max="99999999" step="0.01" value="${e(item.unit_price || '0.00')}" required></label><div class="item-amount"><span>${t('Amount')}</span><strong data-item-total>$0.00</strong></div><button class="remove-item" type="button" data-action="remove-item" aria-label="${t('Remove item')}">×</button></div>`;
    list.append(row);
  };
  (invoice?.items?.length ? invoice.items : [{}]).forEach(addItem);
  const recalculate = () => {
    let subtotal = 0n;
    list.querySelectorAll('.invoice-item').forEach(row => {
      const qty = scaled(row.querySelector('[data-field=quantity]').value, 3);
      const price = scaled(row.querySelector('[data-field=unit_price]').value, 2);
      const line = (qty * price + 500n) / 1000n;
      subtotal += line; row.querySelector('[data-item-total]').textContent = money(Number(line));
    });
    const taxRate = scaled(container.querySelector('[name=tax_rate]').value, 2);
    const shipping = scaled(container.querySelector('[name=shipping]').value, 2);
    const tax = (subtotal * taxRate + 5000n) / 10000n;
    container.querySelector('#preview-subtotal').textContent = money(Number(subtotal));
    container.querySelector('#preview-tax').textContent = money(Number(tax));
    container.querySelector('#preview-total').textContent = money(Number(subtotal + tax + shipping));
  };
  recalculate();
  container.oninput = recalculate;
  container.onchange = event => {
    if (event.target.matches('[data-field=product_id]')) {
      const row = event.target.closest('.invoice-item');
      const product = products.find(p => p.id === Number(event.target.value));
      if (product) { row.querySelector('[data-field=name]').value = product.name; row.querySelector('[data-field=sku]').value = product.sku; row.querySelector('[data-field=unit_price]').value = product.price; }
    }
    recalculate();
  };
  container.onclick = event => {
    const button = event.target.closest('[data-action]'); if (!button) return;
    if (button.dataset.action === 'add-item') { addItem(); recalculate(); }
    if (button.dataset.action === 'remove-item') { if (list.children.length === 1) { context.notify(t('An invoice needs at least one item.')); return; } button.closest('.invoice-item').remove(); recalculate(); }
  };
  container.onsubmit = async event => {
    event.preventDefault(); const form = event.target; const submit = form.querySelector('[type=submit]'); submit.disabled = true;
    const data = formData(form);
    data.items = [...list.querySelectorAll('.invoice-item')].map(row => Object.fromEntries([...row.querySelectorAll('[data-field]')].map(field => [field.dataset.field, field.value])));
    try {
      const saved = await api('/api/invoices' + (id ? '/' + id : ''), { method: id ? 'PUT' : 'POST', body: data });
      context.notify(invoice ? t('Invoice updated.') : t('Invoice {number} created.', { number: invoiceNumber(saved.id) }));
      context.navigate('invoices');
    } catch (error) { formError(form, error.message); submit.disabled = false; }
  };
}
