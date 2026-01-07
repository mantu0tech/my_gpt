import streamlit as st
from groq import Groq
import os
from PyPDF2 import PdfReader
from PIL import Image
import base64
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Assistant by Mantasha",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        
        client = Groq(api_key=api_key)
        return client
        
    except Exception as e:
        st.error(f"❌ Error initializing Groq client: {str(e)}")
        st.stop()

# Initialize client
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
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🤖 AI Assistant")
st.caption("Powered by Groq • Built by Mantasha")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Features")
    
    feature = st.radio(
        "Select Mode:",
        ["💬 Chat Assistant", "📄 PDF Analyzer", "🖼️ Image Q&A"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Model selector - Updated vision models
    st.markdown("### ⚙️ Settings")
    if feature == "🖼️ Image Q&A":
        model = st.selectbox(
            "Vision Model:",
            ["meta-llama/llama-4-maverick-17b-128e-instruct", "meta-llama/llama-4-scout-17b-16e-instruct" ],
            index=0,
            help="Vision models for image analysis (90b is more accurate)"
        )
    else:
        model = st.selectbox(
            "AI Model:",
            ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"],
            index=0
        )
    
    temperature = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.1)
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    message_count = 0
    if feature == "💬 Chat Assistant" and "messages" in st.session_state:
        message_count = len(st.session_state.messages)
    elif feature == "📄 PDF Analyzer" and "pdf_messages" in st.session_state:
        message_count = len(st.session_state.pdf_messages)
    elif feature == "🖼️ Image Q&A" and "image_messages" in st.session_state:
        message_count = len(st.session_state.image_messages)
    
    st.metric("Messages", message_count)
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.info("💬 **Chat**: Ask anything!\n\n📄 **PDF**: Upload & ask questions\n\n🖼️ **Image**: Analyze visuals with AI vision")

# Helper function to read PDF
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

# Helper function to encode image
def encode_image(image_file):
    try:
        img = Image.open(image_file)
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Resize if too large (max 2048px on longest side)
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

# Feature 1: Chat Assistant
if feature == "💬 Chat Assistant":
    st.markdown("### 💬 Chat with AI")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.session_state.messages:
            chat_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button(
                label="💾 Save",
                data=chat_text,
                file_name="chat_history.txt",
                mime="text/plain"
            )
    
    st.markdown("")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("💭 Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
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
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
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
            
            if "pdf_messages" not in st.session_state:
                st.session_state.pdf_messages = []
            
            # Display previous Q&A with better visibility
            for idx, qa in enumerate(st.session_state.pdf_messages):
                st.markdown(f"""
                    <div class="qa-container">
                        <div class="qa-question">❓ Question: {qa['question']}</div>
                        <div class="qa-answer">💡 Answer: {qa['answer']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            question = st.text_input("💭 What would you like to know about this document?", key="pdf_question")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                ask_button = st.button("🔍 Get Answer", use_container_width=True, type="primary")
            with col2:
                if st.button("🗑️ Clear History", use_container_width=True):
                    st.session_state.pdf_messages = []
                    st.rerun()
            
            if ask_button and question:
                # Create a placeholder for the answer
                answer_placeholder = st.empty()
                
                with answer_placeholder.container():
                    with st.spinner("🤖 Analyzing document..."):
                        try:
                            # Limit PDF text to avoid token limits
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
                            
                            # Store in session state
                            st.session_state.pdf_messages.append({
                                "question": question,
                                "answer": answer
                            })
                            
                            # Clear the placeholder and rerun to show the answer
                            answer_placeholder.empty()
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Could not extract text from PDF. The file might be empty or image-based.")
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
            help="Upload an image to analyze (max 2048px)"
        )
    
    if uploaded_image:
        with col2:
            st.markdown("#### 🖼️ Preview")
            encoded_image, display_img = encode_image(uploaded_image)
            
            if display_img:
                st.image(display_img, use_container_width=True)
                st.caption(f"Size: {display_img.size[0]}x{display_img.size[1]} pixels")
                st.session_state.current_image = encoded_image
            else:
                st.error("Failed to load image")
        
        if encoded_image:
            st.markdown("---")
            st.markdown("#### 💭 Ask About the Image")
            
            if "image_messages" not in st.session_state:
                st.session_state.image_messages = []
            
            # Display previous Q&A
            for qa in st.session_state.image_messages:
                st.markdown(f"""
                    <div class="qa-container">
                        <div class="qa-question">❓ Question: {qa['question']}</div>
                        <div class="qa-answer">💡 Response: {qa['answer']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Quick action buttons
            st.markdown("**Quick Actions:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 Describe Image", use_container_width=True):
                    st.session_state.quick_question = "Describe this image in detail."
            with col2:
                if st.button("🏷️ Identify Objects", use_container_width=True):
                    st.session_state.quick_question = "What objects can you see in this image?"
            with col3:
                if st.button("📝 Extract Text", use_container_width=True):
                    st.session_state.quick_question = "Is there any text in this image? If yes, what does it say?"
            
            default_question = st.session_state.get("quick_question", "")
            question = st.text_input(
                "💭 What would you like to know?",
                value=default_question,
                placeholder="e.g., What's in this image? Describe what you see.",
                key="image_question"
            )
            
            # Clear quick question after displaying
            if "quick_question" in st.session_state:
                del st.session_state.quick_question
            
            col1, col2 = st.columns([1, 4])
            with col1:
                analyze_button = st.button("🔍 Analyze", use_container_width=True, type="primary")
            with col2:
                if st.button("🗑️ Clear History", use_container_width=True):
                    st.session_state.image_messages = []
                    st.rerun()
            
            if analyze_button and question:
                # Create placeholder for answer
                answer_placeholder = st.empty()
                
                with answer_placeholder.container():
                    with st.spinner("🤖 Analyzing image..."):
                        try:
                            response = client.chat.completions.create(
                                model=model,
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": question
                                            },
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
                            
                            st.session_state.image_messages.append({
                                "question": question,
                                "answer": answer
                            })
                            
                            # Clear placeholder and rerun
                            answer_placeholder.empty()
                            st.rerun()
                            
                        except Exception as e:
                            error_msg = str(e)
                            st.error(f"❌ Error: {error_msg}")
                            
                            if "decommissioned" in error_msg.lower():
                                st.info("⚠️ This vision model is no longer available. Switching to llama-3.2-90b-vision-preview...")
                            elif "vision" in error_msg.lower():
                                st.info("💡 Make sure you're using a vision-capable model.")
                            else:
                                st.info("Try uploading a different image or check your connection.")
    else:
        st.info("👆 Upload an image to get started!")
        
        with st.expander("💡 Example Questions", expanded=True):
            st.markdown("""
            - Describe what you see in this image
            - What objects are present?
            - Is there any text in the image? What does it say?
            - What's the setting or location?
            - What colors are dominant?
            - Are there any people? What are they doing?
            - What's the mood or atmosphere?
            - Can you identify any brands or logos?
            """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 2rem;'>
        <p style='font-size: 1.2rem; font-weight: 600;'>Built with ❤️ by Mantasha</p>
        <p style='color: #666;'>Powered by Groq AI • Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)