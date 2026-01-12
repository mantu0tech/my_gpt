---

# 🤖 MyGPT – AI Assistant for Text, PDF & Image Q&A

MyGPT is an AI-powered chatbot inspired by ChatGPT that allows users to **ask questions**, **upload PDFs**, and **upload images** to get intelligent answers.
It can understand documents, analyze images, extract text, and answer questions contextually using powerful LLMs.

---

## 🚀 Features

* 💬 Ask questions just like ChatGPT
* 📄 Upload **PDF documents** and ask questions from them
* 🖼️ Upload **images** and get:

  * Object detection
  * Color identification
  * Text extraction (OCR)
  * Image-based Q&A
* 🧠 Context-aware responses
* ⚡ Fast responses using modern LLM APIs
* 🌐 Simple and interactive UI (Streamlit)

---

## 🛠️ Tech Stack

* **Python**
* **Streamlit** – UI framework
* **LLM APIs** (Groq / LLaMA models)
* **PDF Processing** – PyPDF / similar
* **Image Processing** – Vision-enabled LLMs
* **Base64 Encoding** – Image handling

---

## 📂 Project Structure

```
mygpt/
│── app.py
│── requirements.txt
│── README.md
│── utils/
│   ├── pdf_handler.py
│   ├── image_handler.py
│── assets/
│   ├── screenshots/
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/mygpt.git
cd mygpt
```

### 2️⃣ Create virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 API Key Setup

Create a `.env` file or set environment variable:

```bash
export GROQ_API_KEY="your_api_key_here"
```

(Windows)

```powershell
setx GROQ_API_KEY "your_api_key_here"
```

---

## ▶️ Run the Application

```bash
streamlit run app.py
```

App will be available at:

```
http://localhost:8501
```

---

## 🧪 How It Works

### 💬 Text Chat

* Ask any general question
* AI responds instantly

### 📄 PDF Q&A

* Upload a PDF
* Ask questions related to the document
* AI extracts content and answers contextually

### 🖼️ Image Analysis

* Upload an image
* Ask questions like:

  * *What objects are in this image?*
  * *What text is written here?*
  * *What color is the object?*

---

## 📸 Screenshots

*Add your app screenshots here*

```
assets/screenshots/
```

---

## 🔮 Future Enhancements

* 🔐 User authentication
* 🗂️ Chat history
* ☁️ Cloud deployment (AWS / GCP)
* 🧠 Model auto-selection (text vs vision)
* 📊 Analytics dashboard

---

## 🙌 Acknowledgements

* Inspired by **ChatGPT**
* Powered by **LLaMA models**
* Built with ❤️ using **Python & Streamlit**

---

## 👤 Author

**Ansari Mantasha**
Cloud & DevOps Trainer | AI Enthusiast

📌 *If you like this project, don’t forget to ⭐ the repo!*

---
