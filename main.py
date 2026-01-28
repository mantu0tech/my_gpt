import streamlit as st
from groq import Groq
import os
from PyPDF2 import PdfReader
from PIL import Image
import base64
from io import BytesIO
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import hashlib
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Assistant by Mantasha",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database Configuration
def get_database_connection():
    """Create and return database connection (fresh connection each time)"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "ai_assistant"),
            autocommit=False
        )
        return connection
    except Error as e:
        st.error(f"❌ Database connection error: {e}")
        st.info("💡 Check your .env file and ensure MySQL is running")
        return None

def init_database():
    """Initialize database tables"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "")
        )
        cursor = connection.cursor()
        
        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_NAME', 'ai_assistant')}")
        cursor.execute(f"USE {os.getenv('DB_NAME', 'ai_assistant')}")
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Chat history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                chat_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                chat_type VARCHAR(20) NOT NULL,
                role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_user_chat (user_id, chat_type, created_at)
            )
        """)
        
        # PDF documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_documents (
                doc_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255) NOT NULL,
                content TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Error as e:
        st.error(f"❌ Database initialization error: {e}")
        return False

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    """Register a new user"""
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        if not connection:
            return False, "Database connection failed. Please check MySQL is running."
        
        if not connection.is_connected():
            return False, "Database connection is not active"
        
        cursor = connection.cursor()
        password_hash = hash_password(password)
        
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        connection.commit()
        return True, "Registration successful!"
        
    except Error as e:
        if connection:
            connection.rollback()
        error_msg = str(e)
        if "Duplicate entry" in error_msg:
            if "username" in error_msg:
                return False, "Username already exists"
            else:
                return False, "Email already registered"
        return False, f"Registration failed: {error_msg}"
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def login_user(username, password):
    """Authenticate user login"""
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        if not connection:
            st.error("Database connection failed")
            return None
        
        if not connection.is_connected():
            st.error("Database connection is not active")
            return None
        
        cursor = connection.cursor(dictionary=True)
        password_hash = hash_password(password)
        
        cursor.execute(
            "SELECT user_id, username, email FROM users WHERE username = %s AND password_hash = %s",
            (username, password_hash)
        )
        user = cursor.fetchone()
        return user
        
    except Error as e:
        st.error(f"Login error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def save_chat_message(user_id, chat_type, role, content):
    """Save a chat message to database"""
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        if not connection or not connection.is_connected():
            return False
        
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO chat_history (user_id, chat_type, role, content) VALUES (%s, %s, %s, %s)",
            (user_id, chat_type, role, content)
        )
        connection.commit()
        return True
    except Error as e:
        if connection:
            connection.rollback()
        st.error(f"Error saving chat: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def load_chat_history(user_id, chat_type):
    """Load chat history for a user"""
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        if not connection or not connection.is_connected():
            return []
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT role, content, created_at 
               FROM chat_history 
               WHERE user_id = %s AND chat_type = %s 
               ORDER BY created_at ASC""",
            (user_id, chat_type)
        )
        messages = cursor.fetchall()
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    except Error as e:
        st.error(f"Error loading chat history: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def clear_chat_history(user_id, chat_type):
    """Clear chat history for a specific chat type"""
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        if not connection or not connection.is_connected():
            return False
        
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM chat_history WHERE user_id = %s AND chat_type = %s",
            (user_id, chat_type)
        )
        connection.commit()
        return True
    except Error as e:
        if connection:
            connection.rollback()
        st.error(f"Error clearing chat history: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

# Initialize Groq client
@st.cache_resource
def get_groq_client():
    try:
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            st.error("⚠️ GROQ_API_KEY not found in .env file.")
            st.info("""
            **Setup Instructions:**
            1. Create a file named `.env` in your project folder
            2. Add this line (no quotes): `GROQ_API_KEY=gsk_your_actual_key`
            3. Get your key from: https://console.groq.com/keys
            4. Restart the app
            """)
            st.stop()
        
        # Clean the API key
        api_key = api_key.strip().strip('"').strip("'")
        
        if not api_key.startswith("gsk_"):
            st.error("⚠️ Invalid API key format. Groq API keys should start with 'gsk_'")
            st.info("Get a valid key from: https://console.groq.com/keys")
            st.stop()
        
        # Initialize client with just the API key
        try:
            client = Groq(api_key=api_key)
            # Test the connection with a simple call
            return client
        except TypeError as te:
            # If there's a TypeError, try alternative initialization
            import groq
            client = groq.Client(api_key=api_key)
            return client
        
    except Exception as e:
        st.error(f"❌ Error initializing Groq client: {str(e)}")
        st.info("💡 Try: pip install --upgrade groq")
        st.stop()

# Initialize database and client
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = init_database()

try:
    client = get_groq_client()
except Exception as e:
    st.error(f"Failed to initialize: {e}")
    st.stop()

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        font-weight: 800 !important;
    }
    .qa-container {
        background: #f0f2f6;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .qa-question {
        color: #1f1f1f;
        font-weight: 600;
        font-size: 1.05rem;
        margin-bottom: 0.5rem;
    }
    .qa-answer {
        color: #333;
        line-height: 1.6;
        font-size: 1rem;
    }
    .login-container {
        max-width: 500px;
        margin: 2rem auto;
        padding: 2rem;
        background: #f8f9fa;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Authentication Logic
def show_login_page():
    """Display login/register page"""
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    
    st.title("🔐 Welcome")
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        st.markdown("### Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type="password")
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if submit:
                if username and password:
                    user = login_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.authenticated = True
                        st.success(f"✅ Welcome back, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please fill in all fields")
    
    with tab2:
        st.markdown("### Create New Account")
        with st.form("register_form"):
            new_username = st.text_input("👤 Username")
            new_email = st.text_input("📧 Email")
            new_password = st.text_input("🔒 Password", type="password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password")
            register = st.form_submit_button("📝 Register", use_container_width=True)
            
            if register:
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("❌ Passwords don't match")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        success, message = register_user(new_username, new_email, new_password)
                        if success:
                            st.success(f"✅ {message} Please login.")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ Please fill in all fields")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Check authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    show_login_page()
    st.stop()

# Main App (shown only when authenticated)
user = st.session_state.user

# Header
st.title("🤖 AI Assistant")
st.caption(f"Powered by Groq • Logged in as: **{user['username']}**")
st.markdown("---")

# Helper functions
def read_pdf(file):
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text if text.strip() else None
    except Exception as e:
        st.error(f"❌ Error reading PDF: {str(e)}")
        return None

def encode_image(image_file):
    try:
        img = Image.open(image_file)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        max_size = 2048
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_bytes = buffered.getvalue()
        encoded = base64.b64encode(img_bytes).decode('utf-8')
        return encoded, img
    except Exception as e:
        st.error(f"❌ Error encoding image: {str(e)}")
        return None, None

# Sidebar
with st.sidebar:
    st.markdown(f"### 👤 {user['username']}")
    st.caption(f"📧 {user['email']}")
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 🎯 Features")
    
    feature = st.radio(
        "Select Mode:",
        ["💬 Chat Assistant", "📄 PDF Analyzer", "🖼️ Image Q&A"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Model selector
    st.markdown("### ⚙️ Settings")
    if feature == "🖼️ Image Q&A":
        model = st.selectbox(
            "Vision Model:",
            ["meta-llama/llama-4-maverick-17b-128e-instruct", "meta-llama/llama-4-scout-17b-16e-instruct"],
            index=0,
            help="Vision models for image analysis"
        )
    else:
        model = st.selectbox(
            "AI Model:",
            ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
            index=0
        )
    
    temperature = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.1)
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.info("💬 **Chat**: Your conversations are saved!\n\n📄 **PDF**: Upload & analyze documents\n\n🖼️ **Image**: AI-powered vision analysis")

# Feature 1: Chat Assistant
if feature == "💬 Chat Assistant":
    st.markdown("### 💬 Chat with AI")
    
    # Load chat history from database
    if "messages_loaded" not in st.session_state:
        st.session_state.messages = load_chat_history(user['user_id'], 'chat')
        st.session_state.messages_loaded = True
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🗑️ Clear Chat"):
            if clear_chat_history(user['user_id'], 'chat'):
                st.session_state.messages = []
                st.success("✅ Chat cleared!")
                st.rerun()
    with col2:
        if st.session_state.messages:
            chat_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button(
                label="💾 Save",
                data=chat_text,
                file_name=f"chat_history_{user['username']}.txt",
                mime="text/plain"
            )
    
    st.markdown("")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("💭 Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_message(user['user_id'], 'chat', 'user', prompt)
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a helpful, friendly, and knowledgeable AI assistant."},
                            *st.session_state.messages
                        ],
                        temperature=temperature,
                        max_tokens=2048
                    )
                    ai_response = response.choices[0].message.content
                    st.markdown(ai_response)
                    
                    # Save assistant response
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    save_chat_message(user['user_id'], 'chat', 'assistant', ai_response)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Feature 2: PDF Analyzer
elif feature == "📄 PDF Analyzer":
    st.markdown("### 📄 PDF Question & Answer")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📤 Upload Document")
        uploaded_pdf = st.file_uploader(
            "Drop your PDF here",
            type="pdf",
            help="Upload a PDF document to analyze"
        )
    
    with col2:
        if uploaded_pdf:
            st.markdown("#### ✅ Document Loaded")
            st.success(f"**{uploaded_pdf.name}**")
            st.caption(f"Size: {uploaded_pdf.size / 1024:.2f} KB")
    
    if uploaded_pdf:
        with st.spinner("📖 Reading PDF..."):
            pdf_text = read_pdf(uploaded_pdf)
        
        if pdf_text:
            st.session_state.pdf_text = pdf_text
            
            with st.expander("📖 View Document Preview", expanded=False):
                preview_text = pdf_text[:2000] + "..." if len(pdf_text) > 2000 else pdf_text
                st.text_area(
                    "Content Preview:",
                    preview_text,
                    height=300,
                    disabled=True
                )
            
            st.markdown("---")
            st.markdown("#### 🔍 Ask Questions")
            
            # Load PDF chat history
            if "pdf_messages_loaded" not in st.session_state:
                st.session_state.pdf_messages = load_chat_history(user['user_id'], 'pdf')
                st.session_state.pdf_messages_loaded = True
            
            # Display previous Q&A
            for msg in st.session_state.pdf_messages:
                if msg['role'] == 'user':
                    st.markdown(f"""
                        <div class="qa-container">
                            <div class="qa-question">❓ Question: {msg['content']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="qa-container">
                            <div class="qa-answer">💡 Answer: {msg['content']}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            question = st.text_input("💭 What would you like to know about this document?", key="pdf_question")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                ask_button = st.button("🔍 Get Answer", use_container_width=True, type="primary")
            with col2:
                if st.button("🗑️ Clear History", use_container_width=True):
                    if clear_chat_history(user['user_id'], 'pdf'):
                        st.session_state.pdf_messages = []
                        st.success("✅ History cleared!")
                        st.rerun()
            
            if ask_button and question:
                with st.spinner("🤖 Analyzing document..."):
                    try:
                        text_limit = 15000
                        truncated_text = pdf_text[:text_limit]
                        
                        prompt = f"""Based on the document below, provide a clear and concise answer to the question.
If the answer is not in the document, say "I cannot find this information in the document."

DOCUMENT:
{truncated_text}

QUESTION: {question}

ANSWER:"""
                        
                        response = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.3,
                            max_tokens=1024
                        )
                        
                        answer = response.choices[0].message.content
                        
                        # Save to database
                        save_chat_message(user['user_id'], 'pdf', 'user', question)
                        save_chat_message(user['user_id'], 'pdf', 'assistant', answer)
                        
                        # Update session state
                        st.session_state.pdf_messages.append({"role": "user", "content": question})
                        st.session_state.pdf_messages.append({"role": "assistant", "content": answer})
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Could not extract text from PDF.")
    else:
        st.info("👆 Upload a PDF document to get started!")

# Feature 3: Image Q&A
elif feature == "🖼️ Image Q&A":
    st.markdown("### 🖼️ Image Analysis")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📤 Upload Image")
        uploaded_image = st.file_uploader(
            "Drop your image here",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload an image to analyze"
        )
    
    if uploaded_image:
        with col2:
            st.markdown("#### 🖼️ Preview")
            encoded_image, display_img = encode_image(uploaded_image)
            
            if display_img:
                st.image(display_img, use_container_width=True)
                st.caption(f"Size: {display_img.size[0]}x{display_img.size[1]} pixels")
                st.session_state.current_image = encoded_image
        
        if encoded_image:
            st.markdown("---")
            st.markdown("#### 💭 Ask About the Image")
            
            # Load image chat history
            if "image_messages_loaded" not in st.session_state:
                st.session_state.image_messages = load_chat_history(user['user_id'], 'image')
                st.session_state.image_messages_loaded = True
            
            # Display previous Q&A
            for msg in st.session_state.image_messages:
                if msg['role'] == 'user':
                    st.markdown(f"""
                        <div class="qa-container">
                            <div class="qa-question">❓ Question: {msg['content']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div class="qa-container">
                            <div class="qa-answer">💡 Response: {msg['content']}</div>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Quick actions
            st.markdown("**Quick Actions:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 Describe", use_container_width=True):
                    st.session_state.quick_question = "Describe this image in detail."
            with col2:
                if st.button("🏷️ Objects", use_container_width=True):
                    st.session_state.quick_question = "What objects can you see?"
            with col3:
                if st.button("📝 Text", use_container_width=True):
                    st.session_state.quick_question = "Extract any text from this image."
            
            default_question = st.session_state.get("quick_question", "")
            question = st.text_input(
                "💭 What would you like to know?",
                value=default_question,
                placeholder="e.g., What's in this image?",
                key="image_question"
            )
            
            if "quick_question" in st.session_state:
                del st.session_state.quick_question
            
            col1, col2 = st.columns([1, 4])
            with col1:
                analyze_button = st.button("🔍 Analyze", use_container_width=True, type="primary")
            with col2:
                if st.button("🗑️ Clear History", use_container_width=True):
                    if clear_chat_history(user['user_id'], 'image'):
                        st.session_state.image_messages = []
                        st.success("✅ History cleared!")
                        st.rerun()
            
            if analyze_button and question:
                with st.spinner("🤖 Analyzing image..."):
                    try:
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": question},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{st.session_state.current_image}"
                                            }
                                        }
                                    ]
                                }
                            ],
                            temperature=temperature,
                            max_tokens=1024
                        )
                        
                        answer = response.choices[0].message.content
                        
                        # Save to database
                        save_chat_message(user['user_id'], 'image', 'user', question)
                        save_chat_message(user['user_id'], 'image', 'assistant', answer)
                        
                        # Update session state
                        st.session_state.image_messages.append({"role": "user", "content": question})
                        st.session_state.image_messages.append({"role": "assistant", "content": answer})
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    else:
        st.info("👆 Upload an image to get started!")

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; padding: 2rem;'>
        <p style='font-size: 1.2rem; font-weight: 600;'>Built with ❤️ by Mantasha</p>
        <p style='color: #666;'>Powered by Groq AI • Streamlit • MySQL</p>
        <p style='color: #999; font-size: 0.9rem;'>User ID: {user['user_id']} • Session Active</p>
    </div>
    """,
    unsafe_allow_html=True
)
