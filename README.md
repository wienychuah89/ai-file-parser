# 📄 AI Multi-Purpose Document & Smart Receipt Assistant
### 🚀 AI 多功能文件解读与智能发票汇总系统 (Batch Receipt to Excel & Health Report Assistant)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Gemini](https://img.shields.io/badge/AI-Gemini%20Flash-orange?logo=google)
![License](https://img.shields.io/badge/License-MIT-green)

A powerful, mobile-friendly **AI Document Analysis & Receipt-to-Excel Web App** tailored for Southeast Asia (Malaysia). Built with **Streamlit**, **Google Gemini**, and **openpyxl**.

一款专为马来西亚及东南亚用户量身打造的**移动端自适应 AI 文件与商业发票智能助手**。支持批量发票提取、自动求和分类导出 Excel、肾移植复诊化验单智能解读、多语种语音播报及 WhatsApp 一键分享。

---

## 🌟 Key Features / 核心功能亮点

### 🧾 1. Smart Receipt & Invoice Batch Processor (发票批量整理转 Excel)
- **Batch Processing**: Upload multiple thermal receipts, fuel bills, or invoices (JPG / PNG / PDF) simultaneously.
- **Smart Extraction**: Automatically extracts `Date`, `Merchant Name`, `Category` (Petrol, Dining, Repair, Office, etc.), `Receipt No`, `SST (Tax)`, and `Total Amount`.
- **Live Interactive Data Editor**: Double-click any cell on the web table to modify figures before exporting.
- **Financial-Grade Excel (.xlsx) Export**:
  - **Sheet 1 (Details)**: Formatted table with dark blue headers, light grey borders, and automatic `TOTAL` sum with financial double-underline.
  - **Sheet 2 (Category Summary)**: Aggregates total expenditure per category automatically.

### 🏥 2. Health Lab Report (健康检测报告)
- Provide personalized, practical dietary advice and daily health monitoring reminders based on my current results.

### 🌐 3. Multilingual Support & Neural Voice Audio (三语界面与语音播报)
- Full UI and Prompt localization for **🇨🇳 中文 / 🇬🇧 English / 🇲🇾 Bahasa Melayu**.
- High-fidelity **Edge-TTS Neural Voice** generation for hands-free audio listening.

### 🔐 4. Built-in User Authentication & Quota Management (商业级用户鉴权与风控)
- Google Sheets cloud database backend for user registration and login.
- Daily free quota limit management with automatic daily reset.
- Direct WhatsApp VIP recharge & support channel integration.

---

## 🛠️ Tech Stack / 技术栈

- **Frontend / Framework**: [Streamlit](https://streamlit.io/) (Mobile-Responsive Layout)
- **AI Core**: Google Gemini Flash via `google-genai` SDK
- **Data & Excel Processing**: `pandas`, `openpyxl`
- **Database & Auth**: Google Sheets API via `gspread` & `oauth2client`
- **Text-to-Speech (TTS)**: `edge-tts` (Yunxi / Andrew / Osman Neural Voices)
- **Image Optimization**: `Pillow` (Auto-transpose & dynamic compression)

---

## 🚀 Live Demo / 在线体验

Try the live application here:  
👉 **[Launch AI Assistant on Streamlit Community Cloud](https://share.streamlit.io)** *(https://nexgen-ai-studio.streamlit.app/)*

---

## 📦 Local Setup & Deployment / 本地运行指南

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/wienychuah89/ai-file-parser.git](https://github.com/wienychuah89/ai-file-parser.git)
   cd ai-file-parser
