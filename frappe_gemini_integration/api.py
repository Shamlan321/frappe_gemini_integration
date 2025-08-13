import google.generativeai as genai
import frappe
from frappe import _
from frappe.utils import now


def get_gemini_settings():
    """
    Fetch Gemini settings.
    """
    return frappe.get_single("Gemini Integration Settings")


def get_gemini_response(prompt):
    try:
        settings = get_gemini_settings()
        genai.configure(api_key=settings.api_key)
        
        # Initialize the model
        model = genai.GenerativeModel(settings.model)
        
        # Generate response
        response = model.generate_content(prompt)
        answer = response.text
        return answer
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Gemini API Error"))
        return _("Sorry, I could not process your request at this time.")


@frappe.whitelist()
def ask_gemini(prompt):
    answer = get_gemini_response(prompt)
    return answer


@frappe.whitelist()
def save_chat_message(prompt, response):
    # Save the conversation linked with the logged in user
    doc = frappe.get_doc(
        {
            "doctype": "Gemini Prompt Log",
            "user": frappe.session.user,
            "timestamp": now(),
            "prompt_message": prompt,
            "response_message": response,
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return True


@frappe.whitelist()
def get_chat_history():
    # Fetch saved chat messages for current user
    chats = frappe.get_all(
        "Gemini Prompt Log",
        filters={"user": frappe.session.user},
        fields=["name", "prompt_message", "response_message", "timestamp"],
        order_by="creation asc",
        limit_page_length=10,
    )
    return chats


@frappe.whitelist()
def clear_chat_history():
    chats = frappe.get_all(
        "Gemini Prompt Log", filters={"user": frappe.session.user}, fields=["name"]
    )
    for chat in chats:
        frappe.delete_doc("Gemini Prompt Log", chat.name, force=True)
    return "success"
