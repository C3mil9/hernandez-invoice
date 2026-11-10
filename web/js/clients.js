/** Client directory and editor. Archived records can be restored at any time. */
import { api, confirmArchive, escapeHtml as e, formData, formError, emptyRow } from './shared.js';

export async function renderClients(container, context) {
  const clients = await api('/api/customers');
  container.innerHTML = `<div class="page-heading"><div><p class="eyebrow">YOUR RELATIONSHIPS</p><h1>Clients</h1><p class="subheading">Keep your clients and their contact information in one place.</p></div><div class="heading-actions"><a class="button button-secondary" href="/api/exports/clients.csv">↓&nbsp; Export CSV</a><button class="button button-primary" data-action="new">+&nbsp; Add client</button></div></div>
  <section class="panel"><div class="table-toolbar"><div class="search-wrap"><span aria-hidden="true">⌕</span><input id="client-search" type="search" placeholder="Search clients or stores" aria-label="Search clients or stores"></div><label class="checkbox-label"><input id="show-archived-clients" type="checkbox"> Show archived</label></div><div class="table-scroll"><table><thead><tr><th>Client</th><th>Contact</th><th>Phone</th><th>Status</th><th class="align-right">Actions</th></tr></thead><tbody id="client-rows"></tbody></table></div></section><p class="report-note">Archiving a client removes them from new invoices while keeping past invoices intact.</p>`;
  const draw = () => {
    const search = container.querySelector('#client-search').value.trim().toLowerCase();
    const showArchived = container.querySelector('#show-archived-clients').checked;
    const matches = clients.filter(c => (showArchived || !c.archived) && [c.name, c.store, c.email, c.phone].some(x => x.toLowerCase().includes(search)));
    const emptyMessage = search ? 'No clients match your search. Try a different name or store.' : 'No active clients yet. Add a client to get started, or show archived clients.';
    container.querySelector('#client-rows').innerHTML = matches.map(c => `<tr><td><strong>${e(c.name)}</strong>${c.store ? `<small class="cell-subtitle">${e(c.store)}</small>` : ''}</td><td>${e(c.email || '—')}</td><td>${e(c.phone || '—')}</td><td><span class="badge ${c.archived ? 'void' : 'paid'}"><span></span>${c.archived ? 'Archived' : 'Active'}</span></td><td class="align-right"><div class="row-actions"><button class="action-button" data-action="edit" data-id="${c.id}">Edit</button><button class="action-button ${c.archived ? '' : 'muted-action'}" data-action="${c.archived ? 'restore' : 'archive'}" data-id="${c.id}">${c.archived ? 'Restore' : 'Archive'}</button></div></td></tr>`).join('') || emptyRow(5, emptyMessage);
  };
  draw();
  container.oninput = draw;
  container.onchange = draw;
  container.onclick = async event => {
    const button = event.target.closest('[data-action]'); if (!button) return;
    const { action, id } = button.dataset;
    if (action === 'new') return context.navigate('new-client');
    if (action === 'edit') return context.navigate('edit-client', id);
    if (action === 'archive' && !confirmArchive('client')) return;
    try {
      await api(`/api/customers/${id}${action === 'restore' ? '/restore' : ''}`, { method: action === 'restore' ? 'POST' : 'DELETE' });
      context.notify(action === 'restore' ? 'Client restored.' : 'Client archived.');
      await renderClients(container, context);
    } catch (error) { context.notify(error.message); }
  };
}

export async function renderClientForm(container, context, id) {
  const client = id ? (await api('/api/customers')).find(row => row.id === Number(id)) : {};
  if (!client) throw new Error('Client not found.');
  container.innerHTML = `<div class="page-heading"><div><a class="back-link" href="#clients">←&nbsp; Back to clients</a><h1>${id ? 'Edit client' : 'Add a client'}</h1><p class="subheading">Save the details you need for invoices and deliveries.</p></div></div>
  <form class="panel form-panel narrow-form" id="client-form"><div class="form-section-title"><h2>Client details</h2><p>Only the client name is required.</p></div><div class="form-error" role="alert" tabindex="-1" hidden></div><div class="form-grid"><label>Client name <em>*</em><input name="name" value="${e(client.name || '')}" maxlength="200" required placeholder="e.g. Maria Garcia"></label><label>Store / company<input name="store" value="${e(client.store || '')}" maxlength="200" placeholder="e.g. Garcia Market"></label><label>Email<input type="email" name="email" value="${e(client.email || '')}" maxlength="200" placeholder="name@example.com"></label><label>Phone number<input name="phone" type="tel" value="${e(client.phone || '')}" maxlength="200" placeholder="(555) 123-4567"></label><label class="full-width">Billing / shipping address<textarea name="address" rows="3" maxlength="2000" placeholder="Street, city, state, ZIP">${e(client.address || '')}</textarea></label><label class="full-width">Notes <span class="optional">Optional</span><textarea name="notes" rows="3" maxlength="2000" placeholder="Any helpful details about this client">${e(client.notes || '')}</textarea></label></div><div class="form-actions"><a class="button button-secondary" href="#clients">Cancel</a><button class="button button-primary" type="submit">${id ? 'Save changes' : 'Add client'}</button></div></form>`;
  container.onsubmit = async event => {
    event.preventDefault(); const form = event.target; const submit = form.querySelector('[type=submit]'); submit.disabled = true;
    try { await api('/api/customers' + (id ? '/' + id : ''), { method: id ? 'PUT' : 'POST', body: formData(form) }); context.notify(id ? 'Client updated.' : 'Client added.'); context.navigate('clients'); }
    catch (error) { formError(form, error.message); submit.disabled = false; }
  };
}
