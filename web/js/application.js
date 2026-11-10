/** Page navigation and the shared English/Spanish language switch. */
import { renderDashboard } from './dashboard.js';
import { renderClients, renderClientForm } from './clients.js';
import { renderProducts, renderProductForm } from './products.js';
import { renderInvoices, renderInvoiceForm } from './invoices.js';
import { renderReports } from './sales_reports.js';
import { renderSettings } from './business_settings.js';
import { api } from './shared.js';
import { currentLanguage, enableLocalizedValidation, setLanguage, t } from './language.js';

const content = document.querySelector('#page-content');
const breadcrumb = document.querySelector('#breadcrumb');
const toast = document.querySelector('#toast');
const languageSelect = document.querySelector('#language-select');
let toastTimer;
let formDirty = false;
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
  },
  markSaved() { formDirty = false; }
};

function translateShell() {
  document.querySelectorAll('[data-i18n]').forEach(element => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelector('.navigation').setAttribute('aria-label', t('Main navigation'));
  languageSelect.setAttribute('aria-label', t('Language'));
  languageSelect.value = currentLanguage();
}

async function renderRoute() {
  const version = ++renderVersion;
  formDirty = false;
  const [requested, id] = window.location.hash.replace(/^#/, '').split('/');
  const page = pages[requested] ? requested : 'dashboard';
  const [title, render] = pages[page];
  breadcrumb.textContent = t(title);
  const navPage = page.includes('invoice') ? 'invoices' : page.includes('client') ? 'clients' : page.includes('product') ? 'products' : page;
  document.querySelectorAll('.navigation a').forEach(link => {
    const active = link.dataset.page === navPage;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
  });
  // Earlier slow requests only update their detached node, not the current page.
  content.innerHTML = '';
  const pageContainer = document.createElement('div');
  pageContainer.className = 'route-content';
  pageContainer.innerHTML = `<div class="loading">${t('Loading…')}</div>`;
  content.append(pageContainer);
  try {
    await render(pageContainer, context, id);
    if (version === renderVersion) pageContainer.classList.add('route-ready');
  }
  catch (error) {
    if (version !== renderVersion) return;
    pageContainer.innerHTML = '';
    const box = document.createElement('div');
    box.className = 'error-panel';
    box.textContent = error.message || t('Unable to load this page.');
    pageContainer.append(box);
  }
}

// Switching languages rerenders the screen, so warn before discarding a form.
for (const eventName of ['input', 'change']) content.addEventListener(eventName, event => {
  const form = event.target.closest('form');
  if (form && form.id !== 'report-filter') formDirty = true;
});
content.addEventListener('click', event => {
  if (event.target.closest('[data-action="add-item"], [data-action="remove-item"]')) formDirty = true;
});
languageSelect.addEventListener('change', () => {
  if (formDirty && !window.confirm(t('You have unsaved changes. Change language and discard them?'))) {
    languageSelect.value = currentLanguage();
    return;
  }
  setLanguage(languageSelect.value);
  translateShell();
  renderRoute();
});
window.addEventListener('hashchange', renderRoute);
document.querySelector('#top-new-invoice').addEventListener('click', () => context.navigate('new-invoice'));
document.querySelector('#close-app').addEventListener('click', async event => {
  if (!window.confirm(t('Close Hernandez Invoice? Save any changes first. The app will close in all open tabs.'))) return;
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await api('/api/shutdown', { method: 'POST', body: {} });
    document.title = t('Hernandez Invoice closed');
    document.body.innerHTML = `<main class="closed-page"><div class="closed-card"><span class="brand-mark">H</span><h1>${t('Hernandez Invoice is closing')}</h1><p>${t('You can close this browser tab. If you are using a USB drive, safely eject it before removing it.')}</p><p>${t('To use the app again, open the Hernandez Invoice icon.')}</p></div></main>`;
  } catch (error) {
    button.disabled = false;
    context.notify(t('Could not close the app.') + ' ' + error.message);
  }
});
document.querySelector('.skip-link').addEventListener('click', event => {
  event.preventDefault();
  content.focus();
});
setLanguage(currentLanguage());
translateShell();
enableLocalizedValidation();
renderRoute();
