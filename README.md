# 🧠 AutoPCB – AI-Assisted Schematic to PCB Generator

AutoPCB is our proof-of-concept tool that automatically converts circuit schematics into PCB layouts using AI-assisted net inference and the KiCad API.  
This demo was built as part of a hackathon project to explore how design automation can make hardware prototyping faster, smarter, and more accessible.

---

## 🚀 Overview
AutoPCB takes a schematic (in text or structured form) and infers electrical connections between components using a lightweight AI model.  
It then uses the **KiCad Python API** to generate a preliminary PCB layout — automating a process that typically takes hours of manual work.

This repository contains the core Python backend that powers the proof-of-concept demo.

---

## 🧩 Features
- 🧠 **AI Net Inference:** Uses the Gemini API to intelligently predict circuit connections.
- ⚡ **Schematic Parsing:** Reads schematic data and extracts components and pins.
- 🪄 **PCB Generation:** Creates a KiCad PCB layout (.kicad_pcb) using inferred nets.
- 🗂️ **Output Management:** Stores generated files in an organized `outputs/` directory.
- 🔄 **FastAPI Integration (optional):** Easily deploy the tool as a web service for demos.

---

## 📁 Repository Structure
autoPCB/
│
├── ai_net.py # Handles AI-based netlist inference using Gemini API
├── parse_sch.py # Parses schematic files and extracts components
├── pcb_generator.py # Generates PCB layout using KiCad Python API
├── outputs/ # Stores generated PCB files and logs
└── main.py # Entry point for the FastAPI demo server


---

## ⚙️ Requirements
Make sure you have:

- **Python 3.9+**
- **KiCad 9.0+** with Python scripting enabled

Install required packages:
```bash
pip install fastapi uvicorn google-generativeai

Set your KiCad environment paths (Windows example):

set KICAD9_FOOTPRINT_DIR="C:\Program Files\KiCad\9.0\share\kicad\footprints"
set KICAD_SYMBOL_DIR="C:\Program Files\KiCad\9.0\share\kicad\symbols"

set KICAD9_FOOTPRINT_DIR="C:\Program Files\KiCad\9.0\share\kicad\footprints"
set KICAD_SYMBOL_DIR="C:\Program Files\KiCad\9.0\share\kicad\symbols"

🧪 Running the Demo

Start the backend server:

uvicorn main:app --reload


Upload or provide schematic input.

The AI infers nets, and AutoPCB generates a PCB layout under outputs/.

💡 Motivation

As ECE majors, this was our first time building a full software pipeline — integrating AI, backend logic, and EDA automation.
AutoPCB represents our attempt to bridge the gap between hardware design and intelligent automation — all in one tool.

🧰 Tech Stack

Python 3.10
FastAPI + Uvicorn
Google Gemini API
KiCad Python API
GitHub for version control

⚠️ Disclaimer

This is a proof of concept, not a production tool.
Some footprints and net assignments may require manual correction.
The goal was to showcase feasibility and integration, not perfection.
