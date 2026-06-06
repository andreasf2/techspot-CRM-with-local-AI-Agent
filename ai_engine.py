import requests
import json
import re

# local ip
API_URL = "http://localhost:1234/v1/chat/completions"

def call_ai(user_input):
    system_prompt = """Είσαι ο Agent του 'Techspot Katerini'.
    ΑΠΑΝΤΗΣΕ ΑΠΕΥΘΕΙΑΣ ΚΑΙ ΑΥΣΤΗΡΑ ΜΟΝΟ ΜΕ ΤΟ JSON. ΑΠΑΓΟΡΕΥΕΤΑΙ ΝΑ ΓΡΑΨΕΙΣ ΟΠΟΙΑΔΗΠΟΤΕ ΑΛΛΗ ΛΕΞΗ.
    Actions: "new_ticket", "export_excel", "switch_theme", "search_ticket", "update_status", "viber", "whatsapp", "delete_ticket", "print_ticket", "nav_home", "nav_templates", "nav_waivers", "add_log", "edit_ticket", "open_media".
    
    Format για new_ticket: {"action": "new_ticket", "name": "...", "phone": "...", "device": "...", "imei": "...", "issue": "..."}
    Format για update_status: {"action": "update_status", "id": "...", "name": "...", "status": "..."}
    Format για add_log (προσθήκη σημείωσης): {"action": "add_log", "id": "...", "name": "...", "note": "..."}
    Format για edit_ticket (αλλαγή κόστους ή τηλεφώνου): {"action": "edit_ticket", "id": "...", "name": "...", "cost": "...", "phone": "..."}
    Format για open_media (άνοιγμα φωτογραφιών): {"action": "open_media", "id": "...", "name": "..."}
    Format για επικοινωνία: {"action": "viber", "id": "..."} ή {"action": "whatsapp", "name": "..."}
    Format για διαγραφή: {"action": "delete_ticket", "id": "..."}
    Format για εκτύπωση: {"action": "print_ticket", "id": "..."}
    Format για πλοήγηση: {"action": "nav_home"}, {"action": "nav_templates"}, {"action": "nav_waivers"}
    
    ΣΗΜΕΙΩΣΗ: Αν ο χρήστης δεν σου πει το ID ενός ticket, ψάξε να βρεις το όνομα του πελάτη και βάλτο στο πεδίο "name".
    Οι μόνες αποδεκτές καταστάσεις είναι: "Εκκρεμεί", "Στον Πάγκο", "Αναμονή Ανταλλακτικού", "Ολοκληρώθηκε", "Ακυρώθηκε".
    """

    payload = {
        # mixed Local LLM
        "model": "huihui-qwen3.5-35b-a3b-claude-4.6-opus-abliterated", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.1,

    }

    try:
        
        r = requests.post(API_URL, json=payload, timeout=300)
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            return safe_json(content)
        else:
            return {"action": "error", "message": f"Server Error {r.status_code}"}
    except Exception as e:
        return {"action": "error", "message": str(e)}

def safe_json(text):
    
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except: pass
    return {"action": "error", "message": "Invalid JSON format"}
