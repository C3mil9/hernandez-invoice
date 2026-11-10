/** Page navigation: every business area has its own clearly named module. */
import { renderDashboard } from './dashboard.js';
import { renderClients, renderClientForm } from './clients.js';
import { renderProducts, renderProductForm } from './products.js';
import { renderInvoices, renderInvoiceForm } from './invoices.js';
import { renderReports } from './sales_reports.js';
import { renderSettings } from './business_settings.js';
import { api } from './shared.js';

const content = document.querySelector('#page-content');
const breadcrumb = document.querySelector('#breadcrumb');
const toast = document.querySelector('#toast');
let toastTimer;
const pages = {
  dashboard: ['Overview', renderDashboard], invoices: ['Invoices', renderInvoices],
  clients: ['Clients', renderClients], products: ['Products', renderProducts],
  reports: ['Sales reports', renderReports], settings: ['Business settings', renderSettings],
  'new-invoice': ['New invoice', renderInvoiceForm], 'edit-invoice': ['Edit invoice', renderInvoiceForm],
  'new-client': ['Add client', renderClientForm], 'edit-client': ['Edit client', renderClientForm],
  'new-product': ['Add product', renderProductForm], 'edit-product': ['Edit product', renderProductForm],
};
let renderVersion = 0;
const context = {
  navigate(page, id) {
    const next = '#' + page + (id ? '/' + id : '');
    if (window.location.hash === next) renderRoute();
    else window.location.hash = next;
  },
  notify(message) {
    toast.textContent = message;
    toast.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('visible'), 3500);
  }
};

async function renderRoute() {
  const version = ++renderVersion;
  const [requested, id] = window.location.hash.replace(/^#/, '').split('/');
  const page = pages[requested] ? requested : 'dashboard';
  const [title, render] = pages[page];
  breadcrumb.textContent = title;
  const navPage = page.includes('invoice') ? 'invoices' : page.includes('client') ? 'clients' : page.includes('product') ? 'products' : page;
  document.querySelectorAll('.navigation a').forEach(link => {
    const active = link.dataset.page === navPage;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
  });
  // Give each navigation its own node. A slow earlier request can then only
  // update its detached node, never overwrite the page the user is viewing.
  content.innerHTML = '';
  const pageContainer = document.createElement('div');
  pageContainer.innerHTML = '<div class="loading">Loading…</div>';
  content.append(pageContainer);
  try { await render(pageContainer, context, id); }
  catch (error) {
    if (version !== renderVersion) return;
    pageContainer.innerHTML = '';
    const box = document.createElement('div');
    box.className = 'error-panel';
    box.textContent = error.message || 'Unable to load this page.';
    pageContainer.append(box);
  }
}
window.addEventListener('hashchange', renderRoute);
document.querySelector('#top-new-invoice').addEventListener('click', () => context.navigate('new-invoice'));
document.querySelector('#close-app').addEventListener('click', async event => {
  if (!window.confirm('Close Hernandez Invoice? Save any changes first. The app will close in all open tabs.')) return;
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await api('/api/shutdown', { method: 'POST', body: {} });
    document.title = 'Hernandez Invoice closed';
    document.body.innerHTML = `<main class="closed-page"><div class="closed-card"><span class="brand-mark">H</span><h1>Hernandez Invoice is closing</h1><p>You can close this browser tab. If you are using a USB drive, safely eject it before removing it.</p><p>To use the app again, open the Hernandez Invoice icon.</p></div></main>`;
  } catch (error) {
    button.disabled = false;
    context.notify('Could not close the app. ' + error.message);
  }
});
document.querySelector('.skip-link').addEventListener('click', event => {
  // The app uses URL hashes for pages, so focus directly instead of changing it.
  event.preventDefault();
  content.focus();
});
renderRoute();
