import frappe
import requests
import json
from frappe.utils import now

def custom_before_submit(doc, method):
    settings = frappe.get_single("Taxify Settings")
    if doc.doctype != settings.target_doctype:
        return
    
    try:
        tax_rate = frappe.get_value('POS Profile', doc.pos_profile, 'tax_on_cash')

        payload = {
            "posId": int(settings.pos_id),
            "name": settings.business_name,
            "ntn": settings.ntn,
            "invoiceDateTime": now(),
            "invoiceType": int(settings.invoice_type),
            "invoiceID": doc.name,
            "rateValue": tax_rate,
            "saleValue": doc.total,
            "taxAmount": doc.total_taxes_and_charges,
            "consumerName": settings.default_consumer_name or "N/A",
            "consumerNTN": "N/A",
            "address": settings.default_address or "N/A",
            "tariffCode": settings.tariff_code or "N/A",
            "extraInf": settings.extra_info or "N/A",
            "pos_user": settings.pos_user,
            "pos_pass": settings.pos_pass
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(settings.api_url, json=payload, headers=headers, timeout=30)
        data = json.loads(response.text)

        res_code = data.get("resCode")
        srb_invoice_id = data.get("srbInvoceId")

        if res_code == "00":
            target_fieldname = settings.target_fieldname
            if target_fieldname:
                setattr(doc, target_fieldname, srb_invoice_id)
        else:
            frappe.throw(f"Taxify Error: {res_code or 'Unknown error'}")

    except requests.exceptions.RequestException as err:
        frappe.throw(f"Request error: {str(err)}")
    except Exception as e:
        frappe.throw(f"Unexpected error: {str(e)}")
