import os
import sqlite3

# 1. Καθαρίζουμε την παλιά βάση αν υπάρχει
if os.path.exists('tech_lab.db'):
    os.remove('tech_lab.db')
    print("Η παλιά βάση διεγράφη.")

conn = sqlite3.connect('tech_lab.db')
cursor = conn.cursor()

# --- ΠΙΝΑΚΑΣ 1: ΠΕΛΑΤΕΣ & ΣΥΣΚΕΥΕΣ ---
cursor.execute('''CREATE TABLE repairs (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL, phone TEXT NOT NULL, device_model TEXT NOT NULL, imei_serial TEXT, device_passcode TEXT, visual_damage TEXT, repair_status TEXT, cost TEXT, notes TEXT)''')

# --- ΠΙΝΑΚΑΣ 2: ΑΡΧΕΙΑ ---
cursor.execute('''CREATE TABLE media_files (id INTEGER PRIMARY KEY AUTOINCREMENT, repair_id INTEGER, file_path TEXT NOT NULL, FOREIGN KEY(repair_id) REFERENCES repairs(id) ON DELETE CASCADE)''')

# --- ΠΙΝΑΚΑΣ 3: ΠΡΟΤΥΠΑ (Standard Διαγνώσεις) ---
cursor.execute('''CREATE TABLE templates (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT NOT NULL)''')

# --- ΠΙΝΑΚΑΣ 4: ΝΕΟΣ - ΥΠΕΥΘΥΝΕΣ ΔΗΛΩΣΕΙΣ / WAIVERS ---
cursor.execute('''CREATE TABLE waiver_templates (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT NOT NULL)''')

# Έτοιμα Tech Templates (Logs)
defaults = [
    ("📱 Διάγνωση: Νεκρό Κινητό (Board Level)", "ΚΑΤΑΣΤΑΣΗ ΣΥΣΚΕΥΗΣ:\nΗ συσκευή δεν ανάβει. Έγινε μέτρηση στο τροφοδοτικό.\nΚατανάλωση: [ ___ ] A.\nΣυμπέρασμα: Πιθανό βραχυκύκλωμα στη μητρική (VCC Main/BATT). Απαιτείται board level repair.\nΚόστος: [ ___ ]€"),
    ("💻 Διάγνωση: Format / Software PC", "ΕΡΓΑΣΙΕΣ ΛΟΓΙΣΜΙΚΟΥ:\n- Έγινε Backup αρχείων ( [ ___ ] GB )\n- Εγκατάσταση Windows\n- Εγκατάσταση βασικών προγραμμάτων\n- Ενημέρωση Drivers & BIOS\nΚατάσταση: Ολοκληρώθηκε επιτυχώς."),
    ("🔋 Αλλαγή Μπαταρίας / Οθόνης", "ΕΡΓΑΣΙΕΣ HARDWARE:\n- Αφαίρεση παλιάς οθόνης/μπαταρίας\n- Καθαρισμός πλαισίου\n- Εγκατάσταση νέου ανταλλακτικού\n- Έλεγχος σωστής λειτουργίας (Touch/Φόρτιση)\nΠαρατηρήσεις: [ ___ ]")
]
cursor.executemany("INSERT INTO templates (title, content) VALUES (?, ?)", defaults)

# Έτοιμα Κείμενα για Υπεύθυνες Δηλώσεις / Συμφωνητικά
waivers = [
    ("⚠️ Επισκευή Μητρικής (Board Level / Reflow)", "Ο/Η κάτωθι υπογεγραμμένος/η [CUSTOMER_NAME], δηλώνω ότι ενημερώθηκα πως η επισκευή στη μητρική πλακέτα της συσκευής μου (Reflow / Reballing / Micro-soldering) ενέχει υψηλό ρίσκο. Κατανοώ πλήρως ότι η συσκευή ενδέχεται να νεκρώσει οριστικά κατά τη διάρκεια της προσπάθειας επισκευής. Η συγκεκριμένη εργασία θεωρείται «προσπάθεια ανάκτησης» και ΔΕΝ συνοδεύεται από καμία εγγύηση καλής λειτουργίας."),
    
    ("💧 Συσκευή με Υγρασία (Water Damage)", "Ο/Η κάτωθι υπογεγραμμένος/η [CUSTOMER_NAME], παραδίδω τη συσκευή μου η οποία έχει υποστεί βλάβη από υγρά. Ενημερώθηκα από το εργαστήριο ότι η διάβρωση της μητρικής είναι απρόβλεπτη. Αυτό σημαίνει ότι μπορεί να προκύψουν νέες βλάβες στο μέλλον, ακόμα και μετά από επιτυχή αρχικό καθαρισμό. Το εργαστήριο ΔΕΝ παρέχει καμία εγγύηση για συσκευές που έχουν έρθει σε επαφή με υγρά."),
    
    ("📱 Αλλαγή Οθόνης / Μπαταρίας (Όροι Εγγύησης)", "Ο/Η κάτωθι υπογεγραμμένος/η [CUSTOMER_NAME], παρέλαβα τη συσκευή μου μετά από αντικατάσταση ανταλλακτικού. Το νέο ανταλλακτικό καλύπτεται από εγγύηση [ ___ ] μηνών. Η εγγύηση ΑΚΥΡΩΝΕΤΑΙ ΑΥΤΟΜΑΤΑ σε περίπτωση που η συσκευή φέρει νέο χτύπημα, ράγισμα, γρατζουνιές, ίχνη υγρασίας ή αν παραβιαστεί η ταινία ασφαλείας του εργαστηρίου στο εσωτερικό της."),
    
    ("🔓 Ξεκλείδωμα / Επαναφορά Λογισμικού (Format)", "Ο/Η κάτωθι υπογεγραμμένος/η [CUSTOMER_NAME], δηλώνω υπεύθυνα ότι είμαι ο νόμιμος κάτοχος της συσκευής. Συναινώ στην πλήρη διαγραφή των δεδομένων της (Format / Factory Reset / FRP / Passcode Bypass). Απαλλάσσω το εργαστήριο από κάθε ευθύνη για την απώλεια προσωπικών δεδομένων, φωτογραφιών ή αρχείων.")
]
cursor.executemany("INSERT INTO waiver_templates (title, content) VALUES (?, ?)", waivers)

conn.commit()
conn.close()
print("ΕΠΙΤΥΧΙΑ! Η βάση 'tech_lab.db' δημιουργήθηκε με τα έτοιμα συμφωνητικά.")
