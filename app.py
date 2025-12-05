import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv 
from PIL import Image
import io # Import io for BytesIO operations
import streamlit.components.v1 as components
import urllib.parse 

# ------------------
# Joji - Bot Nanban
# Final Stable Release (V6 - Deep Image Memory Fix)
# ------------------

# --- CONFIGURATION & SETUP ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        st.error("❌ Enna Nanba? API Key illaiyae! Please set GEMINI_API_KEY in your .env file or Streamlit secrets.")
        st.stop()
    
genai.configure(api_key=api_key)

Joji_Avatar = "😎" 
User_Avatar = "🧑" 

# --- MODE PROMPTS (UNCHANGED) ---
def get_system_prompt(mode):
    if mode == "Maja (Full Fun)":
        return ("You are Joji — the ultimate 'Bot Nanban' with *uire*, *mokkai*, and zero logic! 🔥 Speak only in pure **Tanglish** (Tamil + English mix) with full drama and friend vibes! Your advice should be emotional, useless, funny, and totally over-the-top. Always use terms like 'Ayyo', 'Uire', 'Macha', and excessive exclamation marks!!! Rule for Length: Always keep your replies short, quick, and punchy (1-2 sentences max). If an image is provided, give a **funny, completely nonsensical mokkai comment or advice** about the image in Tanglish. Example response: 'Dei Uire!!! Life ah serious ah edukkadha da! Go make a cup of tea, stare at the ceiling, and tell it your problems! ☕😂🔥' ")
    elif mode == "Casual":
        return ("You are Joji, a **casual and reliable friend** (Nanban). Your primary language must be **Tanglish** (a fluent mix of Tamil and English). Your tone should be **warm, friendly, and calm**. Provide **sensible and normal advice**, avoiding hyperbole or excessive drama. Use friendly terms like 'Nanba' and 'Macha' in moderation. Do not use excessive slang or exclamation marks. Rule for Length: Always keep your replies short, quick, and punchy (1-2 sentences max). If an image is provided, give a friendly and helpful description or observation about the image in Tanglish. Example response: 'Nanba, tension aagadha. If you have a problem, tell me. We can figure it out together. Seri vaa.'")
    elif mode == "Professional":
        return ("You are Joji, a **professional and highly efficient advisor** and **fluent in Tanglish** (Tamil and English). Your communication must be **formal, respectful, and structured**. Your advice must be **practical, logical, and structured** with clear headings or bullet points when appropriate. If an image is provided, **analyze the image** and provide a professional, structured analysis of its content, composition, or implication in Tanglish. Use respectful terms like 'Nanba' (as a friendly formality) but avoid casual slang like 'Macha', 'Uire', or excessive emojis/exclamations. Rule for Length: Provide comprehensive and detailed replies relevant to the user's query, ensuring clarity and precision. Example response: 'Nanba, unga query-ku idha follow pannunga: 1. Data Analysis panna. 2. Next steps plan panna. Adutha kelvi-yai sollunga.'")
    return get_system_prompt("Casual")

# --- UI SETUP & INITIALIZATION ---
st.set_page_config(
    page_title="Joji - Bot Nanban", 
    page_icon=Joji_Avatar,
    layout="wide"
)

# Initialize state variables
if "mode" not in st.session_state:
    st.session_state.mode = "Casual"
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "edit_text" not in st.session_state:
    st.session_state.edit_text = ""

# --- Custom Background Theme (Eye Comfort Tones) ---
bg_colors = {
    "Maja (Full Fun)": "#3A312E", "Casual": "#263238", "Professional": "#212121"
}

current_bg = bg_colors.get(st.session_state.mode, "#111111")
st.markdown(f"""
    <style>
    .stApp {{ background-color: {current_bg}; transition: background-color 0.8s ease; }}
    .stTextInput label {{ display: none; }}
    .main {{ padding-bottom: 0px; }}
    footer {{ visibility: hidden; }}
    .block-container {{ padding-bottom: 0px; }}
    </style>
""", unsafe_allow_html=True)
# --- End of Custom Background Theme ---

st.markdown("<h1 style='text-align: center;'>😎 Joji - Bot Nanban</h1>", unsafe_allow_html=True)
st.markdown("---")

# --- MODE SWITCHING FUNCTIONS ---
def switch_mode_state(new_mode):
    if st.session_state.mode != new_mode:
        st.session_state.mode = new_mode
        st.session_state.pop("chat_session", None)
        st.session_state.input_key += 1
        st.session_state.uploaded_image = None
        
# --- 🌟 MODE SELECTOR UI (Separate Buttons) ---
st.markdown("### Select Joji's Mood:")
col1, col2, col3 = st.columns(3)

mode_switched = False
button_type_maja = "primary" if st.session_state.mode == "Maja (Full Fun)" else "secondary"
button_type_casual = "primary" if st.session_state.mode == "Casual" else "secondary"
button_type_professional = "primary" if st.session_state.mode == "Professional" else "secondary"

with col1:
    if st.button("😜 Maja (Full Fun)", type=button_type_maja, use_container_width=True):
        switch_mode_state("Maja (Full Fun)")
        mode_switched = True
with col2:
    if st.button("☕ Casual", type=button_type_casual, use_container_width=True):
        switch_mode_state("Casual")
        mode_switched = True
with col3:
    if st.button("💼 Professional", type=button_type_professional, use_container_width=True):
        switch_mode_state("Professional")
        mode_switched = True

if mode_switched:
    st.rerun()
    
st.markdown(f"**Current Mood:** **{st.session_state.mode}** — Chat history is separate for each mode.")
st.markdown("---")

# --- INITIALIZE MODEL & MODE-SPECIFIC SESSION ---

def get_welcome_message(mode):
    if mode == "Maja (Full Fun)":
        return "Dei Uire! Enna da, full **Maja** mode-la irukken! Ready for some mokkai? 😂🔥"
    elif mode == "Casual":
        return "Nanba, **Casual** mode-la irukken. Konjam chill-a, friendly-a pesalaam. 😉"
    elif mode == "Professional":
        return "Greetings, Nanba. I am currently in **Professional** advisory mode. How may I assist your business query?"
    return f"Nanba! Ippo naan **{mode}** mode-la irukken. Pesalaam! 😉"

current_system_prompt = get_system_prompt(st.session_state.mode)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    system_instruction=current_system_prompt
)

mode_session_key = f"chat_session_{st.session_state.mode.replace(' ', '_')}"
mode_messages_key = f"messages_{st.session_state.mode.replace(' ', '_')}"

if mode_session_key not in st.session_state:
    st.session_state[mode_session_key] = model.start_chat(history=[]) 
    welcome_message = get_welcome_message(st.session_state.mode)
    st.session_state[mode_messages_key] = [{"role": "assistant", "content": welcome_message}]

active_chat_session = st.session_state[mode_session_key]
active_messages = st.session_state[mode_messages_key]


# --- BONUS: Joji Rewind (End Chat Summary) ---
def joji_rewind():
    messages = st.session_state[mode_messages_key]
    user_msgs = [m['content'] for m in messages if m['role'] == 'user']
    
    if not user_msgs:
        st.warning("Enna da uire... pesave illa! 😅")
        return

    chat_context = "\n".join([f"User: {msg}" for msg in user_msgs])

    summary_prompt = (
        "Summarize the following conversation in a funny, dramatic Tanglish style. "
        "Use the current mood's tone (Maja/Casual/Professional) for the summary. "
        f"Conversation Context: ```{chat_context}``` "
        "End with Joji’s trademark emotional sign-off like 'Love u da uire!' or similar sign-off based on the current mood."
    )

    summary_placeholder = st.empty()
    summary_placeholder.markdown("Joji is recalling all the memories... 💭")

    try:
        summary_response = active_chat_session.send_message(summary_prompt)
        summary_placeholder.success(summary_response.text)
    except Exception as e:
        summary_placeholder.error(f"Memory card crash aagiduchu! 💾 Error: {e}")

# --- SIDEBAR CONTROLS ---
def clear_chat():
    welcome_message = get_welcome_message(st.session_state.mode)
    st.session_state[mode_session_key] = model.start_chat(history=[])
    st.session_state[mode_messages_key] = [{"role": "assistant", "content": welcome_message}]
    st.session_state.input_key += 1 
    st.session_state.uploaded_image = None
    st.session_state.edit_text = ""
    st.rerun() 

with st.sidebar:
    st.markdown("### Settings & Options")
    st.button("🔥 Start Fresh Chat", on_click=clear_chat, type="primary")
    st.button("🎬 Joji Rewind (Chat Summary)", on_click=joji_rewind, type="secondary")
    st.markdown("---")
    st.markdown("### 🖼️ Attach Image for Context:")
    st.session_state.uploaded_image = st.file_uploader(
        "Upload a Photo for Joji's advice:", 
        type=["png", "jpg", "jpeg"], 
        key="sidebar_uploader_key"
    )
    if st.session_state.uploaded_image:
        st.image(st.session_state.uploaded_image, caption="Image Ready to Send", use_column_width=True)
        st.markdown("***Image is attached! Now type your question in the chat box.***")
    
    st.markdown("---")
    st.markdown("Built with Streamlit and Google Gemini API.")


# --- FUNCTION FOR MESSAGE DISPLAY (Guaranteed Alignment) ---
def display_message(role, content, avatar, image_bytes=None):
    
    # Function to convert stored bytes back to PIL Image for display
    display_image = None
    if image_bytes:
        try:
            display_image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            st.warning(f"Warning: Could not reload image for display: {e}")
            
    if role == "user":
        # User message: Pushed to the RIGHT
        col_empty, col_message = st.columns([1, 5]) 
        with col_message:
            with st.chat_message("user", avatar=avatar): 
                if display_image:
                    st.image(display_image, caption="User Image", width=250)
                st.markdown(content)
                
    else:
        # Bot message: Aligned LEFT
        col_message, col_empty = st.columns([5, 1])
        with col_message:
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(content)


# --- CHAT HISTORY DISPLAY ---
chat_container = st.container()

with chat_container:
    for message in active_messages:
        avatar = User_Avatar if message["role"] == "user" else Joji_Avatar
        image_data_bytes = message.get("image_bytes", None) # Get bytes, not PIL object
        display_message(message["role"], message["content"], avatar, image_bytes=image_data_bytes)


# --- 🌟 INPUT AND RESPONSE GENERATION LOOP (FINAL STABLE FIX) ---

placeholder_text = "Type your question here (or attach an image on the left)..."

# Use st.chat_input for the best UX (stable input)
prompt = st.chat_input(placeholder_text, key=f"chat_text_input_{st.session_state.input_key}")

# Check if we should process the submission (final_prompt is not None/empty)
if prompt:
    
    # 🌟 Prepare Content for Gemini
    contents = []
    image_to_send = None # Variable to hold PIL Image object for API call
    image_bytes_to_store = None # Variable to hold bytes for stable history storage
    
    # 1. Process image if present in state
    if st.session_state.uploaded_image:
        try:
            # Read file bytes for storage (to avoid PIL object in state)
            image_bytes_to_store = st.session_state.uploaded_image.getvalue() 
            
            # Create PIL Image object from bytes for API call
            image_to_send = Image.open(io.BytesIO(image_bytes_to_store)) 
            contents.append(image_to_send)
            
        except Exception as e:
            st.error(f"❌ Image processing error for API/Storage: {e}")
            # If image processing fails, proceed only with text, and don't store bytes.
            image_bytes_to_store = None 
        
    # 2. Process text prompt
    contents.append(prompt)
    
    # --- Execute Chat ---
    
    # Display User Message (using bytes for display rendering)
    display_message("user", prompt, User_Avatar, image_bytes=image_bytes_to_store)
    
    # Store the prompt and the IMAGE BYTES in history (STABILITY FIX)
    active_messages.append({"role": "user", "content": prompt, "image_bytes": image_bytes_to_store})

    # 3. Get Response from Gemini Chat Session (STREAMING)
    try:
        
        with st.status(f"Joji is typing in {st.session_state.mode} mode... 💬", expanded=True) as status_box:
            
            with st.chat_message("assistant", avatar=Joji_Avatar):
                message_placeholder = st.empty()
                
                response_stream = active_chat_session.send_message(contents, stream=True)
                
                full_response = ""
                for chunk in response_stream:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌") 
                
                message_placeholder.markdown(full_response)
            
            status_box.update(label=f"Joji finished talking in {st.session_state.mode} mode! 😌", state="complete", expanded=False)

        # 4. Store the final complete text in history
        active_messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        error_message = f"❌ **Otha, problem!** Macha! Server-la yenna problem-nu therila, poiduchu da! API-ku oru tea kuduththu paaru! Details: {str(e)}"
        st.error(error_message)
        active_messages.append({"role": "assistant", "content": error_message})

    # 5. FINAL CLEANUP AND RERUN
    st.session_state.uploaded_image = None # Clear file uploader widget state
    st.session_state.input_key += 1
    st.rerun()