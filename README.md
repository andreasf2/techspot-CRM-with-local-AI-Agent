# Techspot Katerini CRM and Local AI Assistant

A bespoke, fully offline Customer Relationship Management (CRM) system designed specifically for the fast-paced workflow of hardware repair labs. Built from scratch with Python and CustomTkinter, it features a dynamically scaling UI and integrates a 100% Local AI Assistant that processes natural language into strict database actions.

## Key Features

* Local AI Co-Worker: Integrated with a local LLM (e.g., Qwen via LM Studio). Dictate or type repair issues in natural language, and the AI instantly maps the data to JSON payloads, automatically filling UI fields and creating tickets in real-time.
* 100% Data Privacy: Because the AI model runs locally, zero customer data (names, phone numbers, IMEIs) is ever sent to the cloud or third-party APIs.
* Instant Communication: Deep-linked WhatsApp and Viber URIs built directly into customer profiles for one-click updates.
* Dynamic Printouts: Automatically generates and prints formatted HTML diagnostic reports, repair tickets, and legal waivers by injecting database variables.
* Advanced UI/UX Architecture: 
    * Mastered Z-Order hierarchy (-topmost) to keep floating tools accessible.
    * DPI-aware, dynamic resolution scaling (zoomed states) to fit perfectly on 1080p laptops or 4K lab monitors.
    * Custom dynamic color mapping to eliminate Tkinter rendering artifacts in both Light and Dark modes.
* Standalone Deployment Ready: Designed to be easily packaged into a standalone executable using PyInstaller.

## Technology Stack

* Backend and Logic: Python
* GUI Framework: CustomTkinter
* Database: SQLite (Lightweight, serverless relational DB)
* AI Engine: LM Studio Local Server (OpenAI-compatible API format)

## Repository Structure

* tech_crm.py: The main application, window management, and UI loop.
* ai_engine.py: Handles the connection and logic for the local LLM.
* voice.py: Manages voice command recognition.
* vasi dedomenwn.py: Database initialization, table creation, and queries.
* logo.ico / logo.png: Application branding and assets.
* requirements.txt: Python package dependencies.

## Installation and Setup

### 1. Prerequisites
* Python 3.10 or higher installed.
* LM Studio (https://lmstudio.ai/) installed (for the AI features).

### 2. Clone the Repository
    git clone https://github.com/YourUsername/YourRepositoryName.git
    cd YourRepositoryName

### 3. Install Dependencies
    pip install -r requirements.txt

### 4. Setup the Local AI (LM Studio)
1. Open LM Studio and download an instruction-following model (e.g., Qwen-1.5 or similar).
2. Go to the Local Server tab in LM Studio.
3. Start the server on http://localhost:1234 (default).

### 5. Run the Application
    python tech_crm.py
        
(Note: A fresh SQLite database will be automatically generated upon first launch if it does not exist).

## Screenshots

<img width="1908" height="988" alt="Image" src="https://github.com/user-attachments/assets/044fd484-5f7c-4a1a-947e-a70a9f92ac8c" />

<img width="1271" height="699" alt="Image" src="https://github.com/user-attachments/assets/73063873-6929-407f-a7b5-e1db27e797e8" />

<img width="1898" height="869" alt="Image" src="https://github.com/user-attachments/assets/c3c7aadf-44ac-4f86-a52d-0d18fed00fa5" />

## Disclaimer
This repository contains the source code for the CRM. The pre-compiled executable installers, customer database, and virtual environments are explicitly excluded from this repository for security and privacy reasons.

## Author
Developed by [Your Name/Handle] for everyday use in a real-world tech repair lab.
