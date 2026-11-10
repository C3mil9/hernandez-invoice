/** Product catalog and pricing editor. */
import { api, confirmArchive, escapeHtml as e, formData, formError, emptyRow, money } from './shared.js';

export async function renderProducts(container, context) {
  const products = await api('/api/products');
  container.innerHTML = `<div class="page-heading"><div><p class="eyebrow">YOUR CATALOG</p><h1>Products</h1><p class="subheading">Organize your products and keep your prices up to date.</p></div><div class="heading-actions"><a class="button button-secondary" href="/api/exports/products.csv">↓&nbsp; Export CSV</a><button class="button button-primary" data-action="new">+&nbsp; Add product</button></div></div>
  <section class="panel"><div class="table-toolbar"><div class="search-wrap"><span aria-hidden="true">⌕</span><input id="product-search" type="search" placeholder="Search products or SKU" aria-label="Search products or SKU"></div><label class="checkbox-label"><input id="show-archived-products" type="checkbox"> Show archived</label></div><div class="table-scroll"><table><thead><tr><th>Product</th><th>SKU</th><th>Price</th><th>Status</th><th class="align-right">Actions</th></tr></thead><tbody id="product-rows"></tbody></table></div></section><p class="report-note">Changing or archiving a product won't change the details on existing invoices.</p>`;
  const draw = () => {
    const search = container.querySelector('#product-search').value.trim().toLowerCase();
    const showArchived = container.querySelector('#show-archived-products').checked;
    const matches = products.filter(p => (showArchived || !p.archived) && [p.name, p.sku, p.description].some(x => x.toLowerCase().includes(search)));
    const emptyMessage = search ? 'No products match your search. Try a different name or SKU.' : 'No active products yet. Add a product to get started, or show archived products.';
    container.querySelector('#product-rows').innerHTML = matches.map(p => `<tr><td><strong>${e(p.name)}</strong>${p.description ? `<small class="cell-subtitle">${e(p.description)}</small>` : ''}</td><td>${e(p.sku || '—')}</td><td class="strong">${money(p.price_cents)}</td><td><span class="badge ${p.archived ? 'void' : 'paid'}"><span></span>${p.archived ? 'Archived' : 'Active'}</span></td><td class="align-right"><div class="row-actions"><button class="action-button" data-action="edit" data-id="${p.id}">Edit</button><button class="action-button ${p.archived ? '' : 'muted-action'}" data-action="${p.archived ? 'restore' : 'archive'}" data-id="${p.id}">${p.archived ? 'Restore' : 'Archive'}</button></div></td></tr>`).join('') || emptyRow(5, emptyMessage);
  };
  draw();
  container.oninput = draw; container.onchange = draw;
  container.onclick = async event => {
    const button = event.target.closest('[data-action]'); if (!button) return;
    const { action, id } = button.dataset;
    if (action === 'new') return context.navigate('new-product');
    if (action === 'edit') return context.navigate('edit-product', id);
    if (action === 'archive' && !confirmArchive('product')) return;
    try { await api(`/api/products/${id}${action === 'restore' ? '/restore' : ''}`, { method: action === 'restore' ? 'POST' : 'DELETE' }); context.notify(action === 'restore' ? 'Product restored.' : 'Product archived.'); await renderProducts(container, context); }
    catch (error) { context.notify(error.message); }
  };
}

export async function renderProductForm(container, context, id) {
  const product = id ? (await api('/api/products')).find(row => row.id === Number(id)) : {};
  if (!product) throw new Error('Product not found.');
  container.innerHTML = `<div class="page-heading"><div><a class="back-link" href="#products">←&nbsp; Back to products</a><h1>${id ? 'Edit product' : 'Add a product'}</h1><p class="subheading">Keep commonly sold items ready for your next invoice.</p></div></div><form class="panel form-panel narrow-form" id="product-form"><div class="form-section-title"><h2>Product details</h2><p>Set a default price that you can adjust on each invoice.</p></div><div class="form-error" role="alert" tabindex="-1" hidden></div><div class="form-grid"><label>Product name <em>*</em><input name="name" value="${e(product.name || '')}" maxlength="200" required placeholder="e.g. Handmade candle"></label><label>SKU <span class="optional">Optional</span><input name="sku" value="${e(product.sku || '')}" maxlength="100" placeholder="e.g. CND-001"></label><label>Unit price ($) <em>*</em><input type="number" name="price" value="${e(product.price || '')}" min="0" max="99999999" step="0.01" required placeholder="0.00"></label><label class="full-width">Description <span class="optional">Optional</span><textarea name="description" rows="3" maxlength="2000" placeholder="Details about this product">${e(product.description || '')}</textarea></label></div><div class="form-actions"><a class="button button-secondary" href="#products">Cancel</a><button class="button button-primary" type="submit">${id ? 'Save changes' : 'Add product'}</button></div></form>`;
  container.onsubmit = async event => {
    event.preventDefault(); const form = event.target; const submit = form.querySelector('[type=submit]'); submit.disabled = true;
    try { await api('/api/products' + (id ? '/' + id : ''), { method: id ? 'PUT' : 'POST', body: formData(form) }); context.notify(id ? 'Product updated.' : 'Product added.'); context.navigate('products'); }
    catch (error) { formError(form, error.message); submit.disabled = false; }
  };
}
