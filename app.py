import streamlit as st
from html import escape
from datetime import datetime
import base64
from supabase import create_client, Client

# Initialize Supabase from Streamlit Secrets
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[:-8]
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()
st.set_page_config(page_title="Login",layout="centered")
#-load css-
def load_css():
    file=open("style.css")
    css=file.read()
    #link the css to our application
    st.markdown(f"<style>{css}</style>",unsafe_allow_html=True)
load_css()
#----------login ui----------
#display the login heading
def login_page():
    st.markdown('<h1>Login</h1>',unsafe_allow_html=True)
    #display a description message
    st.markdown('<div class="login-description">'
                'Please enter your login details'
                '</div>',unsafe_allow_html=True)
    username=st.text_input("Username",placeholder="Enter your username")
    password=st.text_input("Password",placeholder="Enter your password",type="password")
    if st.button("Submit"):
        if username=="":
            st.warning("Fill in the username")
        elif password=="":
            st.warning("Fill in the password")
        else:
            file=open("database.txt")
            data=file.readlines()
            flag=0
            for i in data:
                u,p=i.strip().split(",")
                if username==u and password==p:
                    flag=1
                    st.success("Login successful")
                    st.session_state.logged_in=True
                    st.session_state.username=username
                    st.rerun()
                    break
            if flag==0:
                st.warning("Username or password does not exsits")
#----------session state----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in=False
if "my_story" not in st.session_state:
    st.session_state.my_story = None
if "username" not in st.session_state:
    st.session_state.username=""
if "selected_user" not in st.session_state:
    st.session_state.selected_user="Avner"
if "messages" not in st.session_state:
    st.session_state.messages={
        "Aarav": [
{"sender": "Aarav", "message": "Hey! How are you?", "time": "10:30 AM"},
        {"sender": "Me", "message": "I am good! What about you?", "time": "10:32 AM"},
        {"sender": "Aarav", "message": "Doing great 😄", "time": "10:33 AM"}
    ],
    "Riya": [{"sender": "Riya", "message": "Did you complete the project?", "time": "9:45 AM"}],
    "Rahul": [{"sender": "Rahul", "message": "Let's meet tomorrow.", "time": "Yesterday"}],
    "Ananya": [{"sender": "Ananya", "message": "Check this photo 😂", "time": "Yesterday"}]
        }
#------------------sidebar-------------------
def sidebar():
    st.sidebar.markdown('<h2>💬Chatly</h2>',unsafe_allow_html=True)
    st.sidebar.divider()
    st.sidebar.markdown(
        f'''<div class="profile-container">
<div class="avatar">👤</div>
<div>
<b>{escape(st.session_state.username)}</b>
<br>
<small style="color:green">●Online</small>
</div>
</div>
        ''',unsafe_allow_html=True
        )
    st.sidebar.divider()
    menu=st.sidebar.radio("Navigation",["💬Chats","📸 Stories", "👥 Contacts", "⚙️ Settings"],label_visibility="collapsed")
    st.sidebar.divider()
    if st.sidebar.button("🚪logout",use_container_width=True):
        st.session_state.logged_in=False
        st.session_state.username=""
        st.rerun()
    return menu
def chat_list():
    st.markdown('<div class="chatlist-header">Chats</div>', unsafe_allow_html=True)
    search = st.text_input("Search", placeholder="Search chats...", label_visibility="collapsed")
    st.write("")
    
    users = [
        ("Aarav", "😎", "How's your day?"),
        ("Riya", "🥳", "I am good!"),
        ("Rahul", "😅", "Hi"),
        ("Ananya", "😭", "Hello")
    ]
    
    for name, avatar, last_message in users:
        if search and (search.lower() not in name.lower()):
            continue
        col1, col2, col3 = st.columns([1, 3, 1.5], vertical_alignment="center")
        with col1:
            st.markdown(f'<div class="avatar">{avatar}</div>', unsafe_allow_html=True)
        with col2:
            # FIXED: Added explicit bright text colors for names and preview messages
            st.markdown(
                f'<b style="color: #ffffff; font-size: 16px;">{escape(name)}</b><br>'
                f'<small style="color: #d1d7db; font-size: 13px;">{escape(last_message)}</small>', 
                unsafe_allow_html=True
            )
        with col3:
            if st.button("open", key=f"open_{name}", use_container_width=True):
                st.session_state.selected_user = name
                st.rerun()
# ------------------ SUPABASE MESSAGE FUNCTIONS -------------------

def get_messages(user1, user2):
    """Fetch messages between two users from Supabase"""
    try:
        response = supabase.table("messages").select("*").execute()
        all_msgs = response.data
        
        # Filter messages where (sender=user1 AND recipient=user2) OR (sender=user2 AND recipient=user1)
        conversation = [
            m for m in all_msgs 
            if (m["sender"] == user1 and m["recipient"] == user2) or 
               (m["sender"] == user2 and m["recipient"] == user1)
        ]
        # Sort chronologically
        conversation.sort(key=lambda x: x["id"])
        return conversation
    except Exception as e:
        st.error(f"Error fetching messages: {e}")
        return []

def send_message_callback():
    msg = st.session_state.get("message_input", "").strip()
    if msg != "":
        current_user = st.session_state.get("username", "Anonymous")
        recipient = st.session_state.get("selected_user", "")
        current_time = datetime.now().strftime("%I:%M %p")
        
        try:
            supabase.table("messages").insert({
                "sender": current_user,
                "recipient": recipient,
                "type": "text",
                "content": msg,
                "time": current_time
            }).execute()
            st.session_state.message_input = ""
        except Exception as e:
            st.error(f"Database Error Details: {e}")

def chat_window():
    user = st.session_state.selected_user
    current_user = st.session_state.username
    
    # Header
    st.markdown(
        f'<div class="chat-header"><div class="chat-header-content"><div class="avatar">👤</div><div>'
        f'<div class="chat-username" style="color: white; font-weight: bold;">{escape(user)}</div>'
        f'<div class="online-status" style="color:#00a884;">● Online</div>'
        f'</div></div></div>', unsafe_allow_html=True
    )
    
    # Fetch real-time conversation from Supabase
    messages = get_messages(current_user, user)
    
    chat_html = '<div class="chat-area">'
    for msg in messages:
        sender = msg["sender"]
        time = escape(str(msg["time"]))
        msg_type = msg.get("type", "text")
        
        if msg_type == "text":
            message = escape(str(msg.get("content", "")))
            content_html = f'<div class="message-text">{message}</div>'
        elif msg_type == "image":
            content_html = f'<img src="data:image/png;base64,{msg["content"]}" style="max-width: 250px; border-radius: 8px; margin-bottom: 5px;">'
        elif msg_type == "video":
            content_html = f'<video width="250" controls style="border-radius: 8px; margin-bottom: 5px;"><source src="data:video/mp4;base64,{msg["content"]}" type="video/mp4"></video>'
            
        # If logged-in user sent it -> Right side, else -> Left side
        if sender == current_user:
            chat_html += f'<div class="message-wrapper right"><div class="message message-right">{content_html}<div class="message-time">{time} ✓✓</div></div></div>'
        else:
            chat_html += f'<div class="message-wrapper left"><div class="message message-left">{content_html}<div class="message-time">{time}</div></div></div>'
            
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)
    st.write("")
    
    # Input Bar
    col1, col2, col3, col4 = st.columns([1, 1, 7, 1])
    
    with col1:
        with st.popover("📎", use_container_width=True):
            st.markdown("**Attach Media**")
            upload_media = st.file_uploader("Upload Image or Video", type=["jpg", "jpeg", "png", "mp4"], label_visibility="collapsed")
            if upload_media:
                if st.button("📤 Send", type="primary", use_container_width=True):
                    current_time = datetime.now().strftime("%I:%M %p")
                    file_bytes = upload_media.getvalue()
                    b64_file = base64.b64encode(file_bytes).decode()
                    media_type = "video" if upload_media.name.endswith(".mp4") else "image"
                    
                    supabase.table("messages").insert({
                        "sender": current_user,
                        "recipient": recipient,
                        "type": media_type,
                        "content": b64_file,
                        "time": current_time
                    }).execute()
                    st.rerun()

    with col2:
        if st.button("😎", key="emoji_button", use_container_width=True):
            st.info("Emoji sent")

    with col3:
        st.text_input("Message", placeholder=f"Type a message to {user}...", label_visibility="collapsed", key="message_input", on_change=send_message_callback)

    with col4:
        st.button("➤", key="send_button", use_container_width=True, type="primary", on_click=send_message_callback)
def stories():
    st.header("📸 Stories")
    st.caption("Share what is happening around you")
    st.divider()
    
    cols = st.columns(5)
    
    # Change the avatar icon if the user has posted a story
    my_story_avatar = "🖼️" if st.session_state.get("my_story") else "+"
    stories_data = [(my_story_avatar, "Your stories"), ("😎", "Aarav"), ("🥳", "Riya"), ("😅", "Rahul"), ("😭", "Ananya")]
    
    for col, (avatar, name) in zip(cols, stories_data):
        with col:
            st.markdown(f'<div class="story"><div class="story-avatar avatar">{avatar}</div><b>{escape(name)}</b></div>', unsafe_allow_html=True)
            
    # Display the active story if one exists (Removed border_radius)
    if st.session_state.get("my_story"):
        st.write("### Your Current Story")
        st.image(st.session_state.my_story, width=250)

    st.divider()
    st.subheader("Upload New Story")
    upload_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    if upload_file:
        st.image(upload_file, caption="Preview", use_container_width=True)
        if st.button("📤 Post Story", type="primary"):
            st.session_state.my_story = upload_file.getvalue()
            st.success("Story posted successfully!")
            st.rerun()

#--------main code--------
if st.session_state.logged_in==False:
    login_page()
else:
    menu=sidebar()
    if menu=="💬Chats":
        left,right=st.columns([4,4],gap="medium")
        with left:
            chat_list()
        with right:
            chat_window()
    elif menu=="📸 Stories":
        stories()
