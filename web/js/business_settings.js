/** Business information snapshotted when a new invoice is created. */
import { api, escapeHtml as e, formData, formError } from "./shared.js";
import { t } from "./language.js";

export async function renderSettings(container, context) {
  const settings = await api("/api/settings");
  container.innerHTML = `<div class="page-heading"><div><p class="eyebrow">${t("MAKE IT YOURS")}</p><h1>${t("Business settings")}</h1><p class="subheading">${t("These details appear on newly created invoices.")}</p></div></div><form class="panel form-panel narrow-form" id="settings-form"><div class="form-section-title"><h2>${t("Your business information")}</h2><p>${t("Add the contact details you want customers to see.")}</p></div><div class="form-error" role="alert" tabindex="-1" hidden></div><div class="form-grid"><label>${t("Business name")}<input name="business_name" maxlength="200" value="${e(settings.business_name)}" placeholder="${t("Your business name")}"></label><label>${t("Email")}<input name="email" type="email" maxlength="200" value="${e(settings.email)}" placeholder="business@example.com"></label><label>${t("Phone")}<input name="phone" type="tel" maxlength="200" value="${e(settings.phone)}" placeholder="(555) 123-4567"></label><label>${t("Default tax rate (%)")}<input name="default_tax_rate" type="number" min="0" max="100" step="0.01" value="${e(settings.default_tax_rate)}" required></label><label class="full-width">${t("Business address")}<textarea name="address" rows="3" maxlength="2000" placeholder="${t("Street, city, state, ZIP")}">${e(settings.address)}</textarea></label><label class="full-width">${t("Message on invoices")} <span class="optional">${t("Optional")}</span><textarea name="invoice_message" rows="3" maxlength="2000" placeholder="${t("e.g. Thank you for your business!")}">${e(settings.invoice_message)}</textarea></label></div><div class="notice subtle-notice">${t("Changes apply to new invoices. Existing invoices keep their original business details.")}</div><div class="form-actions"><button class="button button-primary" type="submit">${t("Save business settings")}</button></div></form>`;
  container.onsubmit = async (event) => {
    event.preventDefault();
    const form = event.target;
    const submit = form.querySelector("[type=submit]");
    submit.disabled = true;
    try {
      await api("/api/settings", { method: "PUT", body: formData(form) });
      context.markSaved();
      context.notify(t("Business settings saved."));
      submit.disabled = false;
    } catch (error) {
      formError(form, error.message);
      submit.disabled = false;
    }
  };
}
