import customtkinter as ctk
import sqlite3
import os
import csv
import webbrowser
import requests
import json
import threading
import re
from ai_engine import call_ai
from voice import listen_greek
from datetime import datetime
from tkinter import filedialog, messagebox


# ==========================================
# UI
# ==========================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green") 

COLOR_BG = ("#F0F2F5", "#0B0E14")          
COLOR_CARD = ("#FFFFFF", "#151A22")        
COLOR_BORDER = ("#D1D9E6", "#333333")     

# Electric Green 
COLOR_CYAN = ("#008A27", "#39FF14")       
COLOR_BTN_GREEN = ("#28A745", "#00FF41")   
COLOR_BTN_RED = ("#DC3545", "#CC0030")     

COLOR_TEXT = ("#111111", "#E0E6ED")        
COLOR_TEXT_MUTED = ("#666666", "#8A95A5")  
COLOR_HOVER = ("#E2E6EA", "#1E2532")       
# Σκούρο καφέ/χρυσό για Light Mode - Έντονο κίτρινο για Dark Mode
COLOR_STATUS_PENDING = ("#856404", "#FFD700")
# Χρώμα για τα γράμματα πάνω στα κουμπιά 
COLOR_BTN_TEXT = ("#FFFFFF", "#000000")    # Λευκά γράμματα στο Light, Μαύρα στο Dark

FONT_TITLE = ("Consolas", 22, "bold")
FONT_NORMAL = ("Consolas", 14)
FONT_BTN = ("Consolas", 15, "bold")

STATUS_OPTIONS = ["Εκκρεμεί", "Στον Πάγκο", "Αναμονή Ανταλλακτικού", "Ολοκληρώθηκε", "Ακυρώθηκε"]

# ==========================================
# ΣΤΟΙΧΕΙΑ ΕΠΙΧΕΙΡΗΣΗΣ ΓΙΑ ΕΚΤΥΠΩΣΕΙΣ
# ==========================================
MY_COMPANY_NAME = "company name"
MY_COMPANY_SUBTITLE = "company subtitle "
MY_ADDRESS = "your address"
MY_PHONE = "69******"
MY_EMAIL = "you email"
MY_VAT = "your  vat number"
MY_LOGO_FILE = "logo.png" 

# ==========================================
# ΠΑΡΑΘΥΡΟ ΝΕΟΥ ΠΡΟΤΥΠΟΥ
# ==========================================
class NewTemplateWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("✨ Προσθήκη Νέου Προτύπου")
        self.geometry("600x550")
        self.attributes("-topmost", True)
        #self.grab_set() # Κλειδώνει την οθόνη από πίσω
        self.configure(fg_color=COLOR_BG)

        ctk.CTkLabel(self, text="Τίτλος Νέου Προτύπου:", font=FONT_NORMAL, text_color=COLOR_TEXT).pack(anchor="w", pady=(20,5), padx=20)
        self.entry_title = ctk.CTkEntry(self, font=FONT_NORMAL, fg_color=COLOR_BG, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
        self.entry_title.pack(fill="x", padx=20)

        ctk.CTkLabel(self, text="Κείμενο:", font=FONT_NORMAL, text_color=COLOR_TEXT).pack(anchor="w", pady=(20,5), padx=20)
        self.textbox_content = ctk.CTkTextbox(self, font=("Consolas", 15), fg_color=COLOR_BG, border_width=1, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
        self.textbox_content.pack(fill="both", expand=True, padx=20, pady=5)

        # Κουμπί αποθήκευσης
        self.btn_save = ctk.CTkButton(self, text="💾  Αποθήκευση", height=45, fg_color=COLOR_BTN_GREEN, text_color=COLOR_BTN_TEXT, font=FONT_BTN, command=self.save_new)
        self.btn_save.pack(pady=20, padx=20, fill="x")
        
        self.entry_title.focus() # Σε βάζει κατευθείαν να γράψεις

    def save_new(self):
        title = self.entry_title.get()
        content = self.textbox_content.get("1.0", "end-1c")
        if not title.strip() or not content.strip():
            messagebox.showwarning("Προσοχή", "Συμπλήρωσε τίτλο και κείμενο!")
            return
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO templates (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
        conn.close()
        self.master.load_list() # Ανανεώνει τη λίστα στο από πίσω παράθυρο
        self.destroy() # Κλείνει το pop-up αυτόματα


# ==========================================
# ΠΑΡΑΘΥΡΟ ΔΙΑΧΕΙΡΙΣΗΣ TEMPLATES
# ==========================================
class TemplatesWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙️ Διαχείριση Προτύπων / Diagnostics")
        self.geometry("1100x700")  
        self.after(200, lambda: self.state('zoomed'))
        self.attributes("-topmost", True)
        #self.grab_set() 
        self.configure(fg_color=COLOR_BG)
        
        self.current_id = None
        
        self.left_frame = ctk.CTkFrame(self, width=380, fg_color=COLOR_CARD)
        self.left_frame.pack(side="left", fill="y", padx=20, pady=20)
        self.left_frame.pack_propagate(False) 
        
        # Το κουμπί τώρα ανοίγει το Pop-Up!
        self.btn_new = ctk.CTkButton(self.left_frame, text="➕  Νέο Πρότυπο", height=45, fg_color=COLOR_BTN_GREEN, text_color=COLOR_BTN_TEXT, font=FONT_BTN, command=self.open_new_window)
        self.btn_new.pack(pady=15, padx=15, fill="x")
        
        self.list_inner = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.list_inner.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        self.right_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(0,20), pady=20)
        
        ctk.CTkLabel(self.right_frame, text="Τίτλος Προτύπου:", font=FONT_NORMAL, text_color=COLOR_TEXT).pack(anchor="w", pady=(20,5), padx=20)
        self.entry_title = ctk.CTkEntry(self.right_frame, font=FONT_NORMAL, fg_color=COLOR_BG, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
        self.entry_title.pack(fill="x", padx=20)
        
        ctk.CTkLabel(self.right_frame, text="Κείμενο (Χρησιμοποίησε [ ___ ] στα κενά):", font=FONT_NORMAL, text_color=COLOR_TEXT).pack(anchor="w", pady=(20,5), padx=20)
        self.textbox_content = ctk.CTkTextbox(self.right_frame, font=("Consolas", 15), fg_color=COLOR_BG, border_width=1, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
        self.textbox_content.pack(fill="both", expand=True, padx=20, pady=5)
        self.textbox_content.bind("<Control-c>", lambda e: self.textbox_content.event_generate("<<Copy>>"))
        self.textbox_content.bind("<Control-v>", lambda e: self.textbox_content.event_generate("<<Paste>>"))
        self.textbox_content.bind("<Control-x>", lambda e: self.textbox_content.event_generate("<<Cut>>"))
        
        # --- ΚΑΤΩ ΚΟΥΜΠΙΑ  ---
        self.btn_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=20, padx=20)
        
        self.btn_save = ctk.CTkButton(self.btn_frame, text="💾  Αποθήκευση", height=45, fg_color=COLOR_BTN_GREEN, text_color=COLOR_BTN_TEXT, font=FONT_BTN, command=self.save_template)
        self.btn_save.pack(side="right", padx=5)

        self.btn_print = ctk.CTkButton(self.btn_frame, text="Εκτύπωση", height=45, fg_color="#17A2B8", text_color="white", font=FONT_BTN, command=self.print_template)
        self.btn_print.pack(side="right", padx=5)

        self.btn_viber = ctk.CTkButton(self.btn_frame, text="Viber", height=45, fg_color="#7360F2", text_color="white", font=FONT_BTN, command=self.send_to_viber)
        self.btn_viber.pack(side="right", padx=5)
        
        self.btn_delete = ctk.CTkButton(self.btn_frame, text="Διαγραφή", height=45, fg_color=COLOR_BTN_RED, text_color="white", font=FONT_BTN, command=self.delete_template)
        self.btn_delete.pack(side="left", padx=5)
        
        self.load_list()

    def open_new_window(self):
        NewTemplateWindow(self)

    def load_list(self):
        for w in self.list_inner.winfo_children(): w.destroy()
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM templates ORDER BY title")
        for row in cursor.fetchall():
            btn = ctk.CTkButton(self.list_inner, text=row[1], anchor="w", fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_HOVER, font=FONT_NORMAL, command=lambda r=row: self.load_template(r[0]))
            btn.pack(pady=2, fill="x")
        conn.close()
        
    def load_template(self, t_id):
        self.current_id = t_id
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("SELECT title, content FROM templates WHERE id=?", (t_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            self.entry_title.delete(0, 'end')
            self.entry_title.insert(0, row[0])
            self.textbox_content.delete("1.0", 'end')
            self.textbox_content.insert("1.0", row[1])
            
    def save_template(self):
        if not self.current_id: return 
        title = self.entry_title.get()
        content = self.textbox_content.get("1.0", "end-1c")
        if not title.strip() or not content.strip(): return
        
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE templates SET title=?, content=? WHERE id=?", (title, content, self.current_id))
        conn.commit()
        conn.close()
        self.load_list()
        messagebox.showinfo("Αποθηκεύτηκε!", f"Το πρότυπο ενημερώθηκε επιτυχώς.")
        
    def delete_template(self):
        if not self.current_id: return
        if messagebox.askyesno("Επιβεβαίωση", "Σίγουρα να διαγραφεί μόνιμα αυτό το πρότυπο;"):
            conn = sqlite3.connect('tech_lab.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM templates WHERE id=?", (self.current_id,))
            conn.commit()
            conn.close()
            self.current_id = None
            self.entry_title.delete(0, 'end')
            self.textbox_content.delete("1.0", 'end')
            self.load_list()

    def send_to_viber(self):
        text = self.textbox_content.get("1.0", "end-1c").strip()
        if not text: return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        webbrowser.open("viber://chat")

    def print_template(self):
        title = self.entry_title.get().strip()
        content = self.textbox_content.get("1.0", "end-1c").strip()
        if not content: return
        
        date_now = datetime.now().strftime("%d/%m/%Y - %H:%M")
        
        html = f"""
        <html><head><meta charset="utf-8"><title>{title}</title>
        <style>
            @page {{ size: auto; margin: 0mm; }} /* Κρύβει το path του browser */
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #222; line-height: 1.6; max-width: 850px; margin: 15mm auto; padding: 20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #00C853; padding-bottom: 15px; margin-bottom: 40px; }}
            .logo-section img {{ max-height: 70px; }}
            .company-info {{ text-align: right; font-size: 13px; color: #555; }}
            .company-info h3 {{ margin: 0; color: #111; font-size: 18px; }}
            h1 {{ text-align: center; font-size: 24px; text-transform: uppercase; margin-bottom: 10px; color: #111; }}
            .date-box {{ text-align: right; font-weight: bold; font-size: 14px; margin-bottom: 30px; color: #555; }}
            .content-box {{ font-size: 16px; background: #fdfdfd; border-left: 4px solid #00C853; padding: 20px; white-space: pre-wrap; font-family: 'Consolas', monospace; }}
            .footer {{ margin-top: 60px; font-size: 12px; text-align: center; color: #777; border-top: 1px solid #ddd; padding-top: 15px; }}
        </style></head><body>
            
            <div class="header">
                <div class="logo-section"><img src="{MY_LOGO_FILE}" alt="Logo" onerror="this.style.display='none'"></div>
                <div class="company-info">
                    <h3>{MY_COMPANY_NAME}</h3>
                    <div>{MY_ADDRESS} | T: {MY_PHONE}</div>
                    <div>{MY_EMAIL}</div>
                    <div>{MY_VAT}</div>
                </div>
            </div>

            <h1>{title if title else 'ΤΕΧΝΙΚΗ ΑΝΑΦΟΡΑ / ΔΙΑΓΝΩΣΗ'}</h1>
            <div class="date-box">Ημερομηνία: {date_now}</div>

            <div class="content-box">{content}</div>
            
            <div style="display: flex; justify-content: space-between; margin-top: 60px; font-weight: bold; text-align: center;">
                <div style="width: 40%;">Το Εργαστήριο / Ο Τεχνικός<div style="border-bottom: 1px solid #000; margin-top: 40px;"></div></div>
                <div style="width: 40%;">Ο/Η Πελάτης (Υπογραφή)<div style="border-bottom: 1px solid #000; margin-top: 40px;"></div></div>
            </div>
            <div class="footer">
                Επίσημη αναφορά συστήματος Techspot Katerini. Το παρόν έγγραφο αποτελεί τεχνική γνωμάτευση / καταγραφή του εργαστηρίου.
            </div>
            
            <script>window.print();</script>
        </body></html>
        """
        with open("template_print.html", "w", encoding="utf-8") as f: f.write(html)
        webbrowser.open('file://' + os.path.realpath("template_print.html"))

# ==========================================
# ΠΑΡΑΘΥΡΟ ΔΙΑΧΕΙΡΙΣΗΣ WAIVERS
# ==========================================
class WaiverManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙️ Διαχείριση Υπεύθυνων Δηλώσεων")
        self.geometry("900x600")
        self.after(200, lambda: self.state('zoomed'))
        self.attributes("-topmost", True)
        #self.grab_set()
        self.configure(fg_color=COLOR_BG)

        self.current_id = None
        self.left_frame = ctk.CTkFrame(self, width=250, fg_color=COLOR_CARD)
        self.left_frame.pack(side="left", fill="y", padx=20, pady=20)

        self.btn_new = ctk.CTkButton(self.left_frame, text="➕ Νέα Δήλωση", fg_color=COLOR_BTN_GREEN, text_color=COLOR_BTN_TEXT, command=self.clear_form)
        self.btn_new.pack(pady=15, padx=15, fill="x")

        self.list_inner = ctk.CTkScrollableFrame(self.left_frame, fg_color="transparent")
        self.list_inner.pack(fill="both", expand=True, padx=10, pady=(0,10))

        self.right_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(0,20), pady=20)

        ctk.CTkLabel(self.right_frame, text="Τίτλος Δήλωσης:", font=FONT_NORMAL, text_color=COLOR_TEXT).pack(anchor="w", pady=(20,5), padx=20)
        self.entry_title = ctk.CTkEntry(self.right_frame, font=FONT_NORMAL, fg_color=COLOR_BG, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
        self.entry_title.pack(fill="x", padx=20)

        ctk.CTkLabel(self.right_frame, text="Κείμενο (Χρησιμοποίησε [CUSTOMER_NAME] για το όνομα):", font=FONT_NORMAL, text_color=COLOR_TEXT).pack(anchor="w", pady=(20,5), padx=20)
        self.textbox_content = ctk.CTkTextbox(self.right_frame, font=("Consolas", 15), fg_color=COLOR_BG, border_width=1, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
        self.textbox_content.pack(fill="both", expand=True, padx=20, pady=5)

        self.btn_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", pady=20, padx=20)

        self.btn_save = ctk.CTkButton(self.btn_frame, text="💾 Αποθήκευση", fg_color=COLOR_BTN_GREEN, text_color=COLOR_BTN_TEXT, command=self.save_waiver)
        self.btn_save.pack(side="right", padx=5)

        self.btn_delete = ctk.CTkButton(self.btn_frame, text="Διαγραφή", fg_color=COLOR_BTN_RED, text_color="white", command=self.delete_waiver)
        self.btn_delete.pack(side="left", padx=5)

        self.load_list()

    def load_list(self):
        for w in self.list_inner.winfo_children(): w.destroy()
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM waiver_templates ORDER BY title")
        for row in cursor.fetchall():
            btn = ctk.CTkButton(self.list_inner, text=row[1], anchor="w", fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_HOVER, command=lambda r=row: self.load_waiver(r[0]))
            btn.pack(pady=2, fill="x")
        conn.close()

    def clear_form(self):
        self.current_id = None
        self.entry_title.delete(0, 'end')
        self.textbox_content.delete("1.0", 'end')
        self.entry_title.focus()  

    def load_waiver(self, t_id):
        self.current_id = t_id
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("SELECT title, content FROM waiver_templates WHERE id=?", (t_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            self.clear_form()
            self.entry_title.insert(0, row[0])
            self.textbox_content.insert("1.0", row[1])

    def save_waiver(self):
        title = self.entry_title.get()
        content = self.textbox_content.get("1.0", "end-1c")
        if not title.strip() or not content.strip(): return
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        if self.current_id: cursor.execute("UPDATE waiver_templates SET title=?, content=? WHERE id=?", (title, content, self.current_id))
        else: cursor.execute("INSERT INTO waiver_templates (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
        conn.close()
        self.load_list()
        if hasattr(self.master, 'refresh_dropdown'): self.master.refresh_dropdown()

    def delete_waiver(self):
        if not self.current_id: return
        if messagebox.askyesno("Επιβεβαίωση", "Διαγραφή δήλωσης;"):
            conn = sqlite3.connect('tech_lab.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM waiver_templates WHERE id=?", (self.current_id,))
            conn.commit()
            conn.close()
            self.clear_form()
            self.load_list()
            if hasattr(self.master, 'refresh_dropdown'): self.master.refresh_dropdown()

# ==========================================
# ΠΑΡΑΘΥΡΟ ΔΗΛΩΣΕΩΝ WAIVERS
# ==========================================
class WaiversWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📝 Υπεύθυνες Δηλώσεις / Συμφωνητικά")
        self.geometry("900x650")
        self.after(200, lambda: self.state('zoomed'))
        self.attributes("-topmost", True)
        #self.grab_set() 
        self.configure(fg_color=COLOR_BG)
        
        self.top_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        self.top_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(self.top_frame, text="Ονοματεπώνυμο Πελάτη:", font=FONT_NORMAL, text_color=COLOR_TEXT).pack(side="left", padx=15, pady=15)
        self.customer_entry = ctk.CTkEntry(self.top_frame, font=FONT_NORMAL, width=250, fg_color=COLOR_BG, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
        self.customer_entry.pack(side="left", padx=5, pady=15)
        self.customer_entry.bind("<KeyRelease>", self.update_preview)

        self.main_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.waivers = {"Επίλεξε Δήλωση...": ""}
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT title, content FROM waiver_templates ORDER BY id")
            for row in cursor.fetchall(): self.waivers[row[0]] = row[1]
        except: pass
        conn.close()

        self.waiver_var = ctk.StringVar(value="Επίλεξε Δήλωση...")
        dropdown_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        dropdown_frame.pack(fill="x", padx=20, pady=15)

        self.waiver_menu = ctk.CTkOptionMenu(dropdown_frame, values=list(self.waivers.keys()), variable=self.waiver_var, command=self.update_preview, fg_color=COLOR_BG, button_color=COLOR_HOVER, text_color=COLOR_TEXT, dropdown_text_color=COLOR_TEXT)
        self.waiver_menu.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_manage = ctk.CTkButton(dropdown_frame, text="⚙️ Επεξεργασία", width=120, font=FONT_NORMAL, fg_color=COLOR_HOVER, text_color=COLOR_TEXT, command=lambda: WaiverManagerWindow(self))
        self.btn_manage.pack(side="right")
        
        self.textbox_preview = ctk.CTkTextbox(self.main_frame, font=("Consolas", 15), fg_color=COLOR_BG, border_width=1, border_color=COLOR_BORDER, text_color=COLOR_TEXT)
        self.textbox_preview.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.btn_print = ctk.CTkButton(self.main_frame, text="🖨️ ΕΚΤΥΠΩΣΗ ΔΗΛΩΣΗΣ", font=FONT_BTN, fg_color=COLOR_BTN_GREEN, text_color=COLOR_BTN_TEXT, height=50, command=self.print_waiver)
        self.btn_print.pack(pady=15, padx=20, fill="x")

    def update_preview(self, choice=None):
        selected = self.waiver_var.get()
        if selected == "Επίλεξε Δήλωση...": return
        base_text = self.waivers.get(selected, "")
        customer_name = self.customer_entry.get().strip()
        if not customer_name: customer_name = "___________________"
        
        final_text = base_text.replace("[CUSTOMER_NAME]", customer_name)
        self.textbox_preview.delete("1.0", "end")
        self.textbox_preview.insert("1.0", final_text)

    def refresh_dropdown(self):
        self.waivers = {"Επίλεξε Δήλωση...": ""}
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT title, content FROM waiver_templates ORDER BY id")
            for row in cursor.fetchall(): self.waivers[row[0]] = row[1]
        except: pass
        conn.close()
        self.waiver_menu.configure(values=list(self.waivers.keys()))
        self.waiver_var.set("Επίλεξε Δήλωση...")
        self.textbox_preview.delete("1.0", "end")

    def print_waiver(self):
        content = self.textbox_preview.get("1.0", "end-1c").strip()
        if not content: return
        title = self.waiver_var.get()
        date_now = datetime.now().strftime("%d/%m/%Y")
        
        html = f"""
        <html><head><meta charset="utf-8"><title>Υπεύθυνη Δήλωση</title>
        <style>
            @page {{ margin: 15mm; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #222; line-height: 1.6; max-width: 850px; margin: auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ddd; padding-bottom: 15px; margin-bottom: 40px; }}
            .logo-section img {{ max-height: 70px; }}
            .company-info {{ text-align: right; font-size: 13px; color: #555; }}
            .company-info h3 {{ margin: 0; color: #111; font-size: 18px; }}
            h1 {{ text-align: center; font-size: 26px; text-decoration: underline; margin-bottom: 10px; }}
            h2 {{ text-align: center; font-size: 18px; color: #555; margin-top: 0; margin-bottom: 40px; }}
            .content {{ font-size: 16px; text-align: justify; padding: 20px; background: #fafafa; border: 1px solid #eee; border-radius: 8px; }}
            .signatures {{ margin-top: 80px; display: flex; justify-content: space-between; font-size: 16px; font-weight: bold; }}
            .sign-box {{ text-align: center; width: 35%; }}
            .line {{ border-bottom: 1px solid #000; margin-top: 60px; }}
        </style></head><body>
            
            <div class="header">
                <div class="logo-section"><img src="{MY_LOGO_FILE}" alt="Logo" onerror="this.style.display='none'"></div>
                <div class="company-info">
                    <h3>{MY_COMPANY_NAME}</h3>
                    <div>{MY_ADDRESS} | T: {MY_PHONE}</div>
                    <div>{MY_EMAIL}</div>
                    <div>{MY_VAT}</div>
                </div>
            </div>

            <h1>ΥΠΕΥΘΥΝΗ ΔΗΛΩΣΗ / ΣΥΜΦΩΝΗΤΙΚΟ</h1>
            <h2>ΘΕΜΑ: {title}</h2>
            
            <div style="text-align: right; margin-bottom: 20px; font-weight: bold;">Ημερομηνία: {date_now}</div>

            <div class="content">{content.replace(chr(10), '<br><br>')}</div>
            
            <div class="signatures">
                <div class="sign-box">Για την επιχείρηση<div class="line"></div></div>
                <div class="sign-box">Ο/Η Δηλών / Πελάτης<div class="line"></div></div>
            </div>

            <script>window.print();</script>
        </body></html>
        """
        with open("waiver_temp.html", "w", encoding="utf-8") as f: f.write(html)
        webbrowser.open('file://' + os.path.realpath("waiver_temp.html"))

# ==========================================
# ΠΑΡΑΘΥΡΟ ΚΑΡΤΕΛΑΣ ΕΠΙΣΚΕΥΗΣ
# ==========================================
class RepairWindow(ctk.CTkToplevel):
    def __init__(self, parent, repair_id=None):
        super().__init__(parent)
        self.title("🛠️ Ticket Επισκευής" if repair_id else "✨ Νέο Ticket")
        self.geometry("1100x750")
        self.minsize(1000, 700)
        self.after(200, lambda: self.state('zoomed'))
        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()
        #self.grab_set()
        
        self.repair_id = repair_id
        self.new_media_paths = []
        self.configure(fg_color=COLOR_BG)

        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True)

        self.info_frame = ctk.CTkFrame(self.main_scroll, fg_color=COLOR_CARD, corner_radius=15, border_width=1, border_color=COLOR_CYAN[0])
        self.info_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(self.info_frame, text="SYS_DATA // ΣΤΟΙΧΕΙΑ ΣΥΣΚΕΥΗΣ & ΠΕΛΑΤΗ", font=FONT_TITLE, text_color=COLOR_CYAN[0]).grid(row=0, column=0, columnspan=6, pady=(15, 15), sticky="w", padx=20)

        self.entries = {}
        fields_layout = [
            ("Πελάτης:", "customer_name", 1, 0), ("Τηλέφωνο:", "phone", 1, 2), ("Συμφωνηθέν Κόστος (€):", "cost", 1, 4),
            ("Μοντέλο Συσκευής:", "device_model", 2, 0), ("IMEI / Serial:", "imei_serial", 2, 2), ("Κωδικός (PIN/Pattern):", "device_passcode", 2, 4)
        ]

        for label_text, key, r, c in fields_layout:
            lbl = ctk.CTkLabel(self.info_frame, text=label_text, font=FONT_NORMAL, text_color=COLOR_TEXT, width=170, anchor="e")
            lbl.grid(row=r, column=c, padx=(5, 10), pady=10, sticky="e")
            entry = ctk.CTkEntry(self.info_frame, height=35, font=FONT_NORMAL, corner_radius=5, fg_color=COLOR_BG, border_color="#333")
            entry.grid(row=r, column=c+1, padx=(0, 15), pady=10, sticky="we")
            self.entries[key] = entry

        lbl_status = ctk.CTkLabel(self.info_frame, text="Κατάσταση Επισκευής:", font=FONT_NORMAL, text_color=COLOR_CYAN[0], width=170, anchor="e")
        lbl_status.grid(row=3, column=0, padx=(5, 10), pady=(10, 20), sticky="e")
        
        self.status_var = ctk.StringVar(value="Εκκρεμεί")
        self.status_menu = ctk.CTkOptionMenu(self.info_frame, values=STATUS_OPTIONS, variable=self.status_var, font=FONT_NORMAL, fg_color=COLOR_BG, button_color=COLOR_HOVER, text_color=("black", "white"), dropdown_text_color=("black", "white"), dropdown_fg_color=COLOR_CARD, dropdown_hover_color=COLOR_HOVER)
        self.status_menu.grid(row=3, column=1, padx=(0, 15), pady=(10, 20), sticky="we")

        lbl_damage = ctk.CTkLabel(self.info_frame, text="⚠️ Εξωτερική Ζημιά:", font=FONT_NORMAL, text_color=COLOR_BTN_RED[0], width=170, anchor="e")
        lbl_damage.grid(row=3, column=2, padx=(5, 10), pady=(10, 20), sticky="e")
        
        self.entries["visual_damage"] = ctk.CTkEntry(self.info_frame, height=35, font=FONT_NORMAL, corner_radius=5, fg_color=COLOR_BG, border_color=COLOR_BTN_RED[0])
        self.entries["visual_damage"].grid(row=3, column=3, columnspan=3, padx=(0, 15), pady=(10, 20), sticky="ew")

        self.info_frame.grid_columnconfigure((1, 3, 5), weight=1, uniform="group1")

        self.bottom_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.bottom_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.history_frame = ctk.CTkFrame(self.bottom_frame, fg_color=COLOR_CARD, corner_radius=15, border_width=1, border_color="#333")
        self.history_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        hist_top = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        hist_top.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(hist_top, text=">_ ΙΣΤΟΡΙΚΟ & ΔΙΑΓΝΩΣΗ", font=FONT_TITLE, text_color=COLOR_TEXT).pack(side="left")
        self.btn_new_log = ctk.CTkButton(hist_top, text="+ Προσθήκη Log", font=FONT_NORMAL, fg_color=COLOR_HOVER, text_color=COLOR_CYAN[0], command=self.add_timestamp)
        self.btn_new_log.pack(side="right")

        self.templates = {"Επίλεξε Πρότυπο...": ""}
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT title, content FROM templates ORDER BY title")
            for row in cursor.fetchall(): self.templates[row[0]] = row[1]
        except: pass
        conn.close()

        self.template_var = ctk.StringVar(value="Επίλεξε Πρότυπο...")
        self.template_menu = ctk.CTkOptionMenu(self.history_frame, values=list(self.templates.keys()), variable=self.template_var, command=self.insert_template, fg_color=COLOR_BG)
        self.template_menu.pack(fill="x", padx=15, pady=(0, 10))

        self.notes_textbox = ctk.CTkTextbox(self.history_frame, font=("Consolas", 15), fg_color=COLOR_BG, text_color=COLOR_BTN_GREEN[0], corner_radius=5)
        self.notes_textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.media_frame = ctk.CTkFrame(self.bottom_frame, width=320, fg_color=COLOR_CARD, corner_radius=15, border_width=1, border_color="#333")
        self.media_frame.pack(side="right", fill="y")
        self.media_frame.pack_propagate(False)

        ctk.CTkLabel(self.media_frame, text="📸 ΑΡΧΕΙΑ (Photos)", font=FONT_TITLE, text_color=COLOR_TEXT).pack(pady=(15, 10))
        self.btn_add_media = ctk.CTkButton(self.media_frame, text="Προσθήκη Αρχείου", font=FONT_BTN, fg_color=COLOR_HOVER, text_color=COLOR_CYAN[0], command=self.add_media)
        self.btn_add_media.pack(pady=(0, 10), padx=20, fill="x")

        self.media_list_frame = ctk.CTkScrollableFrame(self.media_frame, fg_color=COLOR_BG, corner_radius=5)
        self.media_list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.buttons_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.buttons_frame.pack(fill="x", pady=(10, 20), padx=20)

        self.btn_save = ctk.CTkButton(self.buttons_frame, text="💾 ΑΠΟΘΗΚΕΥΣΗ", font=FONT_BTN, fg_color=COLOR_BTN_GREEN[0], text_color="white", height=50, command=self.save_repair)
        self.btn_save.pack(side="right", padx=10)

        self.btn_print = ctk.CTkButton(self.buttons_frame, text="ΕΚΤΥΠΩΣΗ", font=FONT_BTN, fg_color="#17A2B8", text_color="white", height=50, command=self.print_current_ticket)
        self.btn_print.pack(side="right", padx=10)

        if self.repair_id:
            self.btn_delete = ctk.CTkButton(self.buttons_frame, text="ΔΙΑΓΡΑΦΗ", font=FONT_BTN, fg_color=COLOR_BTN_RED[0], text_color="white", height=50, command=self.delete_repair)
            self.btn_delete.pack(side="left", padx=10)
            self.load_repair_data()

    def print_current_ticket(self):
        vals = {key: entry.get() for key, entry in self.entries.items()}
        notes = self.notes_textbox.get("1.0", "end-1c")
        ticket_data = (self.repair_id if self.repair_id else "NEO", vals["customer_name"], vals["phone"], vals["device_model"], vals["imei_serial"], vals["device_passcode"], vals["visual_damage"], self.status_var.get(), vals["cost"], notes)
        self.master.print_ticket(ticket_data)

    def insert_template(self, choice):
        if choice == "Επίλεξε Πρότυπο...": return
        text = self.templates.get(choice, "")
        if text:
            self.notes_textbox.insert("end", f"{text}\n\n")
            self.template_menu.set("Επίλεξε Πρότυπο...")

    def add_timestamp(self):
        now = datetime.now().strftime("%d/%m/%y %H:%M")
        self.notes_textbox.insert("end", f"\n[{now}] LOG: \n")
        self.notes_textbox.focus()

    def add_media(self):
        file_path = filedialog.askopenfilename(title="Επίλεξε Αρχείο")
        if file_path:
            self.new_media_paths.append(file_path)
            self.add_media_button_to_list(file_path)

    def add_media_button_to_list(self, file_path):
        filename = os.path.basename(file_path)
        btn = ctk.CTkButton(self.media_list_frame, text=f"📄 {filename[:20]}...", fg_color="transparent", anchor="w", text_color=COLOR_TEXT, command=lambda p=file_path: os.startfile(p))
        btn.pack(pady=3, fill="x")

    def load_repair_data(self):
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("SELECT customer_name, phone, device_model, imei_serial, device_passcode, visual_damage, repair_status, cost, notes FROM repairs WHERE id=?", (self.repair_id,))
        data = cursor.fetchone()
        
        if data:
            keys = ["customer_name", "phone", "device_model", "imei_serial", "device_passcode", "visual_damage", "repair_status", "cost"]
            for i, key in enumerate(keys):
                if key == "repair_status":
                    self.status_var.set(data[i] if data[i] else "Εκκρεμεί")
                elif data[i]:
                    self.entries[key].insert(0, data[i])
            if data[8]: self.notes_textbox.insert("1.0", data[8])
            
        cursor.execute("SELECT file_path FROM media_files WHERE repair_id=?", (self.repair_id,))
        for media in cursor.fetchall(): self.add_media_button_to_list(media[0])
        conn.close()

    def save_repair(self):
        vals = {key: entry.get() for key, entry in self.entries.items()}
        vals["repair_status"] = self.status_var.get()
        notes = self.notes_textbox.get("1.0", "end-1c")
        
        if not vals["customer_name"] or not vals["device_model"]:
            messagebox.showerror("Σφάλμα", "Όνομα και Μοντέλο είναι υποχρεωτικά!")
            return
            
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        
        if self.repair_id:
            cursor.execute('''UPDATE repairs SET customer_name=?, phone=?, device_model=?, imei_serial=?, device_passcode=?, visual_damage=?, repair_status=?, cost=?, notes=? WHERE id=?''', 
                           (vals["customer_name"], vals["phone"], vals["device_model"], vals["imei_serial"], vals["device_passcode"], vals["visual_damage"], vals["repair_status"], vals["cost"], notes, self.repair_id))
            curr_id = self.repair_id
        else:
            cursor.execute('''INSERT INTO repairs (customer_name, phone, device_model, imei_serial, device_passcode, visual_damage, repair_status, cost, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (vals["customer_name"], vals["phone"], vals["device_model"], vals["imei_serial"], vals["device_passcode"], vals["visual_damage"], vals["repair_status"], vals["cost"], notes))
            curr_id = cursor.lastrowid
            
        for path in self.new_media_paths:
            cursor.execute("INSERT INTO media_files (repair_id, file_path) VALUES (?, ?)", (curr_id, path))
            
        conn.commit()
        conn.close()
        self.master.load_repairs()
        self.master.show_preview(curr_id)
        self.destroy()

    def delete_repair(self):
        if messagebox.askyesno("Επιβεβαίωση", "Διαγραφή του ticket;"):
            conn = sqlite3.connect('tech_lab.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM repairs WHERE id=?", (self.repair_id,))
            cursor.execute("DELETE FROM media_files WHERE repair_id=?", (self.repair_id,))
            conn.commit()
            conn.close()
            self.master.show_welcome_screen()
            self.master.load_repairs()
            self.destroy()




# ==========================================
# ΠΑΡΑΘΥΡΟ ΣΥΝΟΜΙΛΙΑΣ AI AGENT
# ==========================================
class AgentChatWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent 
        self.title("🤖 AI Assistant")
        self.geometry("350x400")
        self.attributes("-topmost", True)
        self.configure(fg_color=COLOR_BG)
        
        self.history_box = ctk.CTkTextbox(self, font=FONT_NORMAL, fg_color=COLOR_CARD, text_color=COLOR_TEXT, wrap="word", corner_radius=10)
        self.history_box.pack(fill="both", expand=True, padx=15, pady=(15, 10))
        self.history_box.insert("end", "🤖 Agent: Γεια! Πες μου ή γράψε μου τι θέλεις να κάνω;\n\n")
        self.history_box.configure(state="disabled")
        
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 🎤 ΝΕΟ: Το κουμπί του μικροφώνου στα αριστερά
        self.btn_mic = ctk.CTkButton(self.input_frame, text="🎤", width=45, height=45, font=("Arial", 20), fg_color="#2ecc71", hover_color="#27ae60", command=self.voice_input)
        self.btn_mic.pack(side="left", padx=(0, 10))

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Πες μου τι να κάνω...", font=FONT_NORMAL, height=45)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.send_command)
        
        self.btn_send = ctk.CTkButton(self.input_frame, text="➤", width=45, height=45, font=("Arial", 22), fg_color="#7360F2", hover_color="#5A4ABF", command=self.send_command)
        self.btn_send.pack(side="right")

    def voice_input(self):
        """Ξεκινάει την αναγνώριση φωνής χωρίς να παγώνει το UI"""
        self.entry.delete(0, 'end')
        self.entry.insert(0, "Ακούω... 🎤")
        self.btn_mic.configure(fg_color="#DC3545") # Γίνεται κόκκινο όσο ακούει
        self.update()
        
        def listen():
            from voice import listen_greek
            text = listen_greek()
            self.after(0, self.process_voice_result, text)
        
        threading.Thread(target=listen, daemon=True).start()

    def process_voice_result(self, text):
        """Διαχειρίζεται το αποτέλεσμα της φωνής"""
        self.btn_mic.configure(fg_color="#2ecc71") # Επιστρέφει στο πράσινο
        self.entry.delete(0, 'end')
        if text:
            self.entry.insert(0, text)
            self.send_command() # Στέλνει την εντολή αυτόματα!
        else:
            self.entry.insert(0, "") # Καθαρίζει το πεδίο αν δεν άκουσε κάτι

    def append_to_chat(self, text, is_user=False):
        try:
            if not self.winfo_exists(): return 
            self.history_box.configure(state="normal")
            if is_user:
                self.history_box.insert("end", f"👤 Εσύ:\n{text}\n\n")
            else:
                self.history_box.insert("end", f"🤖 Agent:\n{text}\n\n")
            self.history_box.see("end") 
            self.history_box.configure(state="disabled")
        except: pass

    def send_command(self, event=None):
        user_text = self.entry.get()
        if not user_text.strip() or user_text == "Ακούω... 🎤": return
        
        self.entry.delete(0, 'end')
        self.append_to_chat(user_text, is_user=True)
        
        threading.Thread(target=self.parent.process_ai_command, args=(user_text, self), daemon=True).start()

# ==========================================
# ΚΕΝΤΡΙΚΗ ΟΘΟΝΗ
# ==========================================
class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Techspot Katerini")
        self.after(200, lambda: self.state('zoomed'))
        self.configure(fg_color=COLOR_BG)

        self.top_frame = ctk.CTkFrame(self, height=80, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_CYAN[0])
        self.top_frame.pack(fill="x", padx=20, pady=20)

        self.search_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Αναζήτηση...", width=250, height=45, font=FONT_NORMAL, fg_color=COLOR_BG)
        self.search_entry.pack(side="left", padx=20, pady=15)
        self.search_entry.bind("<KeyRelease>", self.search_data)
        

        self.btn_home = ctk.CTkButton(self.top_frame, text="🏠 ΑΡΧΙΚΗ", font=FONT_BTN, fg_color=COLOR_HOVER, text_color=COLOR_TEXT, height=45, command=self.show_welcome_screen)
        self.btn_home.pack(side="left", padx=5, pady=15)

        # ΕΠΕΣΤΡΕΨΑΝ ΤΑ ΚΟΥΜΠΙΑ ΕΞΑΓΩΓΗΣ ΚΑΙ ΠΡΟΤΥΠΩΝ
        self.theme_switch = ctk.CTkSwitch(self.top_frame, text="🌙", font=("Consolas", 16), command=self.toggle_theme, width=40)
        self.theme_switch.pack(side="right", padx=20, pady=15)

        self.btn_new = ctk.CTkButton(self.top_frame, text="[+] ΝΕΟ TICKET", font=FONT_BTN, fg_color=COLOR_CYAN[0], text_color="black", height=45, command=self.open_new_repair)
        self.btn_new.pack(side="right", padx=10, pady=15)

        self.btn_export = ctk.CTkButton(self.top_frame, text="📊 EXCEL", font=FONT_BTN, fg_color=COLOR_HOVER, text_color=COLOR_TEXT, height=45, command=self.export_to_excel)
        self.btn_export.pack(side="right", padx=10, pady=15)

        self.btn_templates = ctk.CTkButton(self.top_frame, text="⚙️ ΠΡΟΤΥΠΑ", font=FONT_BTN, fg_color=COLOR_HOVER, text_color=COLOR_TEXT, height=45, command=self.open_templates)
        self.btn_templates.pack(side="right", padx=10, pady=15)

        self.list_frame = ctk.CTkScrollableFrame(self, width=350, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color="#333")
        self.list_frame.pack(side="left", fill="y", padx=20, pady=(0, 20))

        self.right_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color="#333")
        self.right_frame.pack(side="right", fill="both", expand=True, padx=(0, 20), pady=(0, 20))
        
        self.show_welcome_screen()
        self.load_repairs()
        # Το κουμπί του Agent
        self.agent_fab = ctk.CTkButton(
            self, 
            text="🤖", 
            font=("Segoe UI Emoji", 22),
            width=56,           
            height=56,          
            corner_radius=28,   
            
            # Χρώματα
            fg_color="#2ecc71",      
            hover_color="#27ae60",   
            
            # Floating Effect
          
            bg_color=COLOR_BG,
            
            border_width=0,       
            command=self.open_agent_chat
        )
        
        
        self.agent_fab.place(relx=0.98, rely=0.96, anchor="se")

    # ==========================================
    #  AI AGENT: ΛΟΓΙΚΗ & ΕΚΤΕΛΕΣΗ 
    # ==========================================
    def open_agent_chat(self):
        if not hasattr(self, "agent_chat_window") or not self.agent_chat_window.winfo_exists():
            self.agent_chat_window = AgentChatWindow(self)
            self.agent_chat_window.entry.focus()
            self.after(100, lambda: self.agent_chat_window.entry.focus())
        else:
           
            self.agent_chat_window.deiconify() 
            self.agent_chat_window.lift()      
            self.agent_chat_window.focus_force()
            self.agent_chat_window.entry.focus()
            self.after(100, lambda: self.agent_chat_window.entry.focus())

    def trigger_ai(self, event=None):
        user_text = self.ai_entry.get()
        if not user_text.strip(): return
        self.ai_entry.delete(0, 'end')
        
        self.open_agent_chat()
        self.agent_chat_window.entry.insert(0, user_text)
        self.agent_chat_window.send_command()

    def voice_command(self):
        text = listen_greek()
        if text:
            self.open_agent_chat()
            self.agent_chat_window.entry.insert(0, text)
            self.agent_chat_window.send_command()        

    def process_ai_command(self, user_input, chat_window):
        # 1. Ενημέρωση UI
        self.after(0, lambda: chat_window.append_to_chat("🤖 Επεξεργασία..."))

        # 2. Κλήση στον AI Engine 
        ai_data = call_ai(user_input)

        # 3. Εκτέλεση της ενέργειας στο κεντρικό UI
        self.after(0, self.execute_ai_action, ai_data, chat_window)

    def execute_ai_action(self, ai_data, chat_window):
        action = ai_data.get("action")

        if action == "error":
            error_msg = ai_data.get("message", "Άγνωστο σφάλμα JSON")
            chat_window.append_to_chat(f"❌ Σφάλμα AI: {error_msg}")
            return

        if action == "new_ticket":
            win = RepairWindow(self)

            if ai_data.get("name"):
                win.entries["customer_name"].insert(0, ai_data["name"])

            if ai_data.get("phone"):
                win.entries["phone"].insert(0, ai_data["phone"])

            if ai_data.get("device"):
                win.entries["device_model"].insert(0, ai_data["device"])
            
            if ai_data.get("imei"):
                win.entries["imei_serial"].insert(0, ai_data["imei"])

            if ai_data.get("issue"):
                win.entries["visual_damage"].insert(0, ai_data["issue"])

            chat_window.append_to_chat("✅ Ticket έτοιμο")

        elif action == "export_excel":
            self.export_to_excel()
            chat_window.append_to_chat("📊 Export OK")

        elif action == "switch_theme":
            self.toggle_theme()
            chat_window.append_to_chat("🌓 Theme άλλαξε")

        elif action == "search_ticket":
            name = ai_data.get("name", "")
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, name)
            self.load_repairs(name)
            chat_window.append_to_chat(f"🔍 Αναζήτηση για {name}")

        elif action == "update_status":
            t_id = ai_data.get("id")
            name = ai_data.get("name")
            new_status = ai_data.get("status")
            
            conn = sqlite3.connect('tech_lab.db')
            cursor = conn.cursor()
            
            try:
                if t_id:
                    cursor.execute("UPDATE repairs SET repair_status=? WHERE id=?", (new_status, t_id))
                    msg = f"Το Ticket #{t_id} ενημερώθηκε σε: {new_status}"
                elif name:
                    # Αν δεν ξέρει ID, ψάχνει με το όνομα του πελάτη
                    cursor.execute("UPDATE repairs SET repair_status=? WHERE customer_name LIKE ?", (new_status, f"%{name}%"))
                    msg = f"Η επισκευή του/της {name} ενημερώθηκε σε: {new_status}"
                else:
                    msg = "Πρέπει να μου πεις το ID του ticket ή το όνομα."
                
                conn.commit()
                self.load_repairs() # Ανανεώνει τη λίστα αριστερά!
                chat_window.append_to_chat(msg)
                
            except Exception as e:
                chat_window.append_to_chat(f"Σφάλμα βάσης: {e}")
            finally:
                conn.close()

        # ================= ΟΛΕΣ ΟΙ ΛΕΙΤΟΥΡΓΙΕΣ ΜΑΖΙ =================

        elif action in ["viber", "whatsapp", "delete_ticket", "print_ticket", "add_log", "edit_ticket", "open_media"]:
            t_id = ai_data.get("id")
            name = ai_data.get("name")
            
            conn = sqlite3.connect('tech_lab.db')
            cursor = conn.cursor()
            try:
                # Βρίσκουμε το Ticket από τη Βάση με ID ή Όνομα
                if t_id:
                    cursor.execute("SELECT * FROM repairs WHERE id=?", (t_id,))
                elif name:
                    cursor.execute("SELECT * FROM repairs WHERE customer_name LIKE ?", (f"%{name}%",))
                else:
                    chat_window.append_to_chat("Πρέπει να μου πεις το ID του ticket ή το όνομα.")
                    conn.close()
                    return
                
                data = cursor.fetchone()
                if not data:
                    chat_window.append_to_chat("Δεν βρέθηκε τέτοιο ticket στη βάση.")
                    conn.close()
                    return
                
                # Ανάκτηση στοιχείων
                real_id = data[0]
                customer_name = data[1]
                phone = data[2]
                old_notes = data[9] # Παίρνουμε το παλιό ιστορικό
                
                # --- ΕΠΙΚΟΙΝΩΝΙΑ & ΕΚΤΥΠΩΣΗ ---
                if action == "viber":
                    self.open_viber(phone)
                    chat_window.append_to_chat(f"🟣 Άνοιξα το Viber για: {customer_name}")
                
                elif action == "whatsapp":
                    self.open_whatsapp(phone)
                    chat_window.append_to_chat(f"💬 Άνοιξα το WhatsApp για: {customer_name}")
                
                elif action == "print_ticket":
                    self.print_ticket(data)
                    chat_window.append_to_chat(f"🖨️ Ετοιμάζω εκτύπωση για το Ticket #{real_id}")
                
                # --- ΔΙΑΓΡΑΦΗ ---
                elif action == "delete_ticket":
                    cursor.execute("DELETE FROM repairs WHERE id=?", (real_id,))
                    cursor.execute("DELETE FROM media_files WHERE repair_id=?", (real_id,))
                    conn.commit()
                    self.load_repairs()
                    self.show_welcome_screen()
                    chat_window.append_to_chat(f"🗑️ Το Ticket #{real_id} διαγράφηκε οριστικά.")
                
                # --- ΠΡΟΣΘΗΚΗ ΙΣΤΟΡΙΚΟΥ LOG ---
                elif action == "add_log":
                    note = ai_data.get("note", "")
                    now = datetime.now().strftime("%d/%m/%y %H:%M")
                    new_notes = f"{old_notes}\n[{now}] AI LOG: {note}" if old_notes else f"[{now}] AI LOG: {note}"
                    cursor.execute("UPDATE repairs SET notes=? WHERE id=?", (new_notes, real_id))
                    conn.commit()
                    self.load_repairs()
                    chat_window.append_to_chat(f"📝 Το ιστορικό του/της {customer_name} ενημερώθηκε!")

                # --- ΑΛΛΑΓΗ ΚΟΣΤΟΥΣ / ΣΤΟΙΧΕΙΩΝ ---
                elif action == "edit_ticket":
                    cost = ai_data.get("cost")
                    new_phone = ai_data.get("phone")
                    updates = []
                    params = []
                    if cost:
                        updates.append("cost=?")
                        params.append(cost)
                    if new_phone:
                        updates.append("phone=?")
                        params.append(new_phone)

                    if updates:
                        params.append(real_id)
                        cursor.execute(f"UPDATE repairs SET {', '.join(updates)} WHERE id=?", tuple(params))
                        conn.commit()
                        self.load_repairs()
                        chat_window.append_to_chat(f"Τα στοιχεία στο Ticket #{real_id} ενημερώθηκαν.")
                    else:
                        chat_window.append_to_chat("Πες μου τι νέο κόστος ή τηλέφωνο να βάλω.")

                # --- ΑΝΟΙΓΜΑ ΦΩΤΟΓΡΑΦΙΩΝ ---
                elif action == "open_media":
                    cursor.execute("SELECT file_path FROM media_files WHERE repair_id=?", (real_id,))
                    files = cursor.fetchall()
                    if files:
                        for f in files:
                            try: os.startfile(f[0])
                            except: pass
                        chat_window.append_to_chat(f"Άνοιξα {len(files)} αρχεία για τον/την {customer_name}.")
                    else:
                        chat_window.append_to_chat(f"Δεν υπάρχουν σωσμένα αρχεία για αυτό το ticket.")
                    
            except Exception as e:
                chat_window.append_to_chat(f"Σφάλμα κατά την εκτέλεση: {e}")
            finally:
                conn.close()

        # --- ΠΛΟΗΓΗΣΗ (NAVIGATION) ---
        elif action == "nav_home":
            self.show_welcome_screen()
            chat_window.append_to_chat("Σε πήγα στην Αρχική Οθόνη!")
            
        elif action == "nav_templates":
            self.open_templates()
            chat_window.append_to_chat("Άνοιξα τη διαχείριση Προτύπων!")
            
        elif action == "nav_waivers":
            WaiversWindow(self)
            chat_window.append_to_chat("Άνοιξα το μενού των Υπεύθυνων Δηλώσεων!")

        else:
            chat_window.append_to_chat("Δεν κατάλαβα")


    def toggle_theme(self):
        # Βλέπει ποιο είναι το τρέχον θέμα
        current_mode = ctk.get_appearance_mode()
        
        if current_mode == "Dark":
            ctk.set_appearance_mode("Light")
            self.theme_switch.select()  # Γυρνάει το διακοπτάκι στο ON
            self.theme_switch.configure(text="☀️")
        else:
            ctk.set_appearance_mode("Dark")
            self.theme_switch.deselect() # Γυρνάει το διακοπτάκι στο OFF
            self.theme_switch.configure(text="🌙")


    def export_to_excel(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Excel CSV Files", "*.csv")], title="Αποθήκευση Αντιγράφου")
        if not filename: return
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_name, phone, device_model, imei_serial, visual_damage, repair_status, cost, notes FROM repairs ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(["Ticket ID", "Πελάτης", "Τηλέφωνο", "Συσκευή", "IMEI/Serial", "Εξωτ. Ζημιά", "Κατάσταση", "Κόστος", "Ιστορικό"])
                writer.writerows(rows)
            messagebox.showinfo("Επιτυχία", "Η εξαγωγή ολοκληρώθηκε!")
        except Exception as e:
            messagebox.showerror("Σφάλμα", f"Σφάλμα: {str(e)}")

    def open_templates(self):
        TemplatesWindow(self)

    def open_new_repair(self):
        RepairWindow(self)

    def show_welcome_screen(self):
        for w in self.right_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.right_frame, text="SYSTEM ONLINE - Techspot", font=("Consolas", 32, "bold"), text_color=COLOR_CYAN[0]).pack(pady=(60, 20))
        
        dash_frame = ctk.CTkFrame(self.right_frame, fg_color=COLOR_BG, corner_radius=15)
        dash_frame.pack(fill="both", expand=True, padx=50, pady=(0, 50))
        
        ctk.CTkLabel(dash_frame, text="⚠️ Συσκευές σε Εκκρεμότητα / Στον Πάγκο:", font=FONT_TITLE, text_color=COLOR_BTN_RED[0]).pack(pady=20)

        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, device_model, customer_name FROM repairs WHERE repair_status IN ('Εκκρεμεί', 'Στον Πάγκο') ORDER BY id DESC")
        pending = cursor.fetchall()
        conn.close()

        if pending:
            for apt in pending:
                r_id, model, name = apt
                btn = ctk.CTkButton(dash_frame, text=f"Ticket #{r_id} | {model} ({name})", font=FONT_NORMAL, fg_color=COLOR_HOVER, text_color=COLOR_TEXT, height=40, anchor="w", command=lambda cid=r_id: self.show_preview(cid))
                btn.pack(pady=5, padx=40, fill="x")
        else:
            ctk.CTkLabel(dash_frame, text="Δεν υπάρχουν εκκρεμότητες! Όλα καθαρά.", font=FONT_NORMAL, text_color=COLOR_BTN_GREEN[0]).pack(pady=40)

    def load_repairs(self, search_query=""):
        for w in self.list_frame.winfo_children(): w.destroy()
        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        
        if search_query:
            q = "%" + search_query.replace("%", "") + "%"
            cursor.execute("SELECT id, device_model, customer_name, repair_status FROM repairs WHERE customer_name LIKE ? OR device_model LIKE ? OR imei_serial LIKE ? ORDER BY id DESC", (q, q, q))
        else:
            cursor.execute("SELECT id, device_model, customer_name, repair_status FROM repairs ORDER BY id DESC")
            
        for row in cursor.fetchall():
            r_id, model, name, status = row
            status_indicator = "🟢" if status == "Ολοκληρώθηκε" else "🔴" if status == "Ακυρώθηκε" else "🟡"
            display = f"#{r_id} | {model}\n👤 {name} {status_indicator}"
            
            btn = ctk.CTkButton(self.list_frame, text=display, anchor="w", font=FONT_NORMAL, fg_color=COLOR_HOVER, text_color=COLOR_TEXT, corner_radius=5, command=lambda cid=r_id: self.show_preview(cid))
            btn.pack(pady=4, fill="x")
        conn.close()

    def search_data(self, event):
        self.load_repairs(self.search_entry.get())

    # ΕΠΕΣΤΡΕΨΑΝ ΤΑ COPY, WHATSAPP, VIBER!
    def copy_to_clipboard(self, val, button):
        if not val or val == "-": return
        self.clipboard_clear()
        self.clipboard_append(val)
        self.update()
        original_text = button.cget("text")
        button.configure(text="COPIED!", text_color=COLOR_BTN_GREEN[0])
        self.after(1500, lambda: button.configure(text=original_text, text_color=COLOR_TEXT))

    def open_whatsapp(self, mobile):
        if mobile and mobile != "-":
            clean_num = mobile.replace(" ", "").replace("-", "")
            if clean_num.startswith("69"): clean_num = "30" + clean_num 
            webbrowser.open(f"https://wa.me/{clean_num}")

    def open_viber(self, mobile):
        if mobile and mobile != "-":
            clean_num = mobile.replace(" ", "").replace("-", "")
            if clean_num.startswith("69"): clean_num = "30" + clean_num 
            webbrowser.open(f"viber://chat?number=%2B{clean_num}")

    def print_ticket(self, data):
        r_id, name, phone, model, imei, passcode, damage, status, cost, notes = data
        date_now = datetime.now().strftime("%d/%m/%Y - %H:%M")
        
        html = f"""
        <html><head><meta charset="utf-8"><title>Ticket #{r_id}</title>
        <style>
            @page {{ margin: 15mm; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.5; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #00C853; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo-section img {{ max-height: 90px; max-width: 200px; }}
            .company-info {{ text-align: right; font-size: 14px; color: #555; }}
            .company-info h2 {{ margin: 0; color: #111; font-size: 24px; letter-spacing: 1px; }}
            .title {{ text-align: center; font-size: 22px; font-weight: bold; background: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 30px; }}
            .grid {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
            .column {{ width: 48%; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
            .column h4 {{ margin-top: 0; border-bottom: 1px solid #ddd; padding-bottom: 5px; color: #00C853; }}
            .row {{ margin-bottom: 8px; font-size: 15px; }}
            .label {{ font-weight: bold; color: #555; display: inline-block; width: 140px; }}
            .notes-box {{ background: #fdfdfd; border-left: 4px solid #00C853; padding: 15px; margin-bottom: 40px; font-family: 'Consolas', monospace; white-space: pre-wrap; }}
            .footer {{ text-align: center; font-size: 11px; color: #777; border-top: 1px solid #ddd; padding-top: 15px; }}
        </style></head><body>
            
            <div class="header">
                <div class="logo-section">
                    <img src="{MY_LOGO_FILE}" alt="Logo" onerror="this.style.display='none'">
                </div>
                <div class="company-info">
                    <h2>{MY_COMPANY_NAME}</h2>
                    <div><i>{MY_COMPANY_SUBTITLE}</i></div>
                    <div>{MY_ADDRESS} | {MY_PHONE}</div>
                    <div>{MY_EMAIL}</div>
                    <div>{MY_VAT}</div>
                </div>
            </div>

            <div class="title">ΔΕΛΤΙΟ ΠΑΡΑΛΑΒΗΣ / ΕΠΙΣΚΕΥΗΣ - TICKET #{r_id}</div>
            
            <div style="text-align: right; margin-top: -20px; margin-bottom: 20px; font-size: 14px; color: #666;">Ημερομηνία: {date_now}</div>

            <div class="grid">
                <div class="column">
                    <h4>Στοιχεία Πελάτη</h4>
                    <div class="row"><span class="label">Ονοματεπώνυμο:</span>{name}</div>
                    <div class="row"><span class="label">Τηλέφωνο:</span>{phone}</div>
                </div>
                <div class="column">
                    <h4>Στοιχεία Συσκευής</h4>
                    <div class="row"><span class="label">Μοντέλο:</span><b>{model}</b></div>
                    <div class="row"><span class="label">IMEI / S/N:</span>{imei if imei else '-'}</div>
                    <div class="row"><span class="label">Εξωτερική Ζημιά:</span>{damage if damage else 'ΟΧΙ'}</div>
                    <div class="row"><span class="label">Κόστος:</span><b style="font-size: 18px;">{cost} €</b></div>
                </div>
            </div>

            <h4>Διάγνωση / Παρατηρήσεις Εργαστηρίου:</h4>
            <div class="notes-box">{notes if notes else 'Καμία επιπλέον παρατήρηση.'}</div>

            <div style="display: flex; justify-content: space-between; text-align: center; margin-top: 50px; font-weight: bold;">
                <div style="width: 40%;">Το Εργαστήριο<div style="border-bottom: 1px solid #000; margin-top: 40px;"></div></div>
                <div style="width: 40%;">Ο/Η Πελάτης<div style="border-bottom: 1px solid #000; margin-top: 40px;"></div></div>
            </div>

            <div class="footer">
                Η συσκευή παραλαμβάνεται για έλεγχο. Το εργαστήριο δεν φέρει ευθύνη για περαιτέρω νέκρωση της συσκευής (βλάβες board level) ή απώλεια δεδομένων (φωτογραφίες, επαφές). Παρακαλούμε κρατήστε το παρόν δελτίο για την παραλαβή της συσκευής σας.
            </div>

            <script>window.print();</script>
        </body></html>
        """
        with open("ticket_temp.html", "w", encoding="utf-8") as f: f.write(html)
        webbrowser.open('file://' + os.path.realpath("ticket_temp.html"))

    def show_preview(self, r_id):
        for w in self.right_frame.winfo_children(): w.destroy()
        scroll = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        conn = sqlite3.connect('tech_lab.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_name, phone, device_model, imei_serial, device_passcode, visual_damage, repair_status, cost, notes FROM repairs WHERE id=?", (r_id,))
        data = cursor.fetchone()
        conn.close()

        if data:
            _, name, phone, model, imei, passcode, damage, status, cost, notes = data

            header = ctk.CTkFrame(scroll, fg_color="transparent")
            header.pack(fill="x", pady=10, padx=20)
            
            ctk.CTkLabel(header, text=f"📱 {model}", font=("Consolas", 28, "bold"), text_color=COLOR_CYAN[0]).pack(side="left")
            
            btn_print = ctk.CTkButton(header, text="ΕΚΤΥΠΩΣΗ", font=FONT_BTN, fg_color="#E6E6E6", text_color="black", hover_color="#CCCCCC", command=lambda: self.print_ticket(data))
            btn_print.pack(side="right", padx=5)
            
            btn_edit = ctk.CTkButton(header, text="✏️ ΕΠΕΞΕΡΓΑΣΙΑ", font=FONT_BTN, fg_color=COLOR_HOVER, text_color=COLOR_TEXT, command=lambda: RepairWindow(self, r_id))
            btn_edit.pack(side="right", padx=5)

            # Αφαιρούμε το [0] για να χρησιμοποιεί ολόκληρη την πλειάδα (tuple) χρωμάτων
            sc = COLOR_BTN_GREEN if status == "Ολοκληρώθηκε" else COLOR_BTN_RED if status == "Ακυρώθηκε" else COLOR_STATUS_PENDING
            ctk.CTkLabel(scroll, text=f"STATUS: [ {status} ]", font=("Consolas", 18, "bold"), text_color=sc).pack(anchor="w", padx=20)

            info_f = ctk.CTkFrame(scroll, fg_color=COLOR_BG, corner_radius=5, border_width=1, border_color="#333")
            info_f.pack(fill="x", pady=15, padx=20)

            details = [("👤 Πελάτης:", name), ("📞 Τηλέφωνο:", phone), ("🔑 Passcode:", passcode), ("🏷️ IMEI/SN:", imei), ("💰 Κόστος:", f"{cost} €"), ("⚠️ Ζημιά:", damage)]
            
            for i, (lbl, val) in enumerate(details):
                ctk.CTkLabel(info_f, text=lbl, font=("Consolas", 14, "bold"), text_color=COLOR_TEXT_MUTED).grid(row=i, column=0, sticky="w", pady=8, padx=20)
                
                action_frame = ctk.CTkFrame(info_f, fg_color="transparent")
                action_frame.grid(row=i, column=1, sticky="w")
                
                val_btn = ctk.CTkButton(action_frame, text=val if val else "-", font=("Consolas", 14), fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_HOVER, anchor="w", cursor="hand2")
                val_btn.configure(command=lambda v=val, b=val_btn: self.copy_to_clipboard(v, b))
                val_btn.pack(side="left")
                
                # Προσθήκη Viber & WhatsApp μόνο στη γραμμή του Τηλεφώνου
                if "Τηλέφωνο" in lbl and val:
                    wa_btn = ctk.CTkButton(action_frame, text="💬 WhatsApp", font=("Consolas", 12, "bold"), fg_color="#25D366", hover_color="#1DA851", text_color="white", width=80, height=24, corner_radius=5, command=lambda m=val: self.open_whatsapp(m))
                    wa_btn.pack(side="left", padx=(10, 5))

                    vi_btn = ctk.CTkButton(action_frame, text="🟣 Viber", font=("Consolas", 12, "bold"), fg_color="#7360F2", hover_color="#5A4ABF", text_color="white", width=80, height=24, corner_radius=5, command=lambda m=val: self.open_viber(m))
                    vi_btn.pack(side="left", padx=5)

            if notes:
                ctk.CTkLabel(scroll, text=">_ TERMINAL LOGS:", font=("Consolas", 16, "bold"), text_color=COLOR_CYAN[0]).pack(anchor="w", padx=20, pady=(10, 0))
                box = ctk.CTkTextbox(scroll, height=200, font=("Consolas", 14), fg_color=COLOR_BG, text_color=COLOR_BTN_GREEN[0])
                box.pack(fill="x", padx=20, pady=5)
                box.insert("1.0", notes)
                box.configure(state="disabled")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
