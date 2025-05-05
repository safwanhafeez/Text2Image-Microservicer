import streamlit as st
import grpc
import base64
from include import text2image_pb2
from include import text2image_pb2_grpc
from PIL import Image
import io
import os
import sys
import subprocess
import time
import socket
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Text-to-Image Generator", layout="centered")
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'include'))

def is_server_running():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', 50051)) == 0
    except:
        return False

if not is_server_running():
    st.info("Starting gRPC server... Please wait.")
    server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'include', 'grpc_server.py')
    if os.name == 'nt':
        subprocess.Popen(
            [sys.executable, server_script],
            cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'include'),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    for _ in range(30):
        if is_server_running():
            break
        time.sleep(0.5)
    if is_server_running():
        st.success("gRPC server is now running!")
    else:
        st.error("Failed to start gRPC server. Please start it manually and refresh this page.")
        st.stop()

channel = grpc.insecure_channel('localhost:50051')
stub = text2image_pb2_grpc.Text2ImageStub(channel)

# UI Header
st.markdown('<h1 style="white-space: nowrap; text-align: center; margin: 0 auto;">Text to Image Generator</h1>', unsafe_allow_html=True)

st.markdown("""
    <style>
        .stTextInput label, .stTextArea label, .stSelectbox label {
            font-size: 22px !important;
            
            font-weight: 700 !important;
        }
        .stTextArea textarea {
            font-size: 16px;
            height: 50px !important;
        }
        /* Additional margin for labels */
        .stTextInput label, .stTextArea label, .stSelectbox label {
            margin-bottom: 8px !important;
            display: block !important;
        }
        /* Make select box text larger */
        div.stSelectbox div[data-baseweb="select"] {
            font-size: 18px !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    div[data-baseweb="radio"] > div {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        width: 100% !important;
        max-width: 600px !important;
    }
    div[data-baseweb="radio"] > div > label {
        font-size: 18px !important;
        font-weight: 600 !important;
        margin: 0 !important;
        padding: 5px 10px !important;
        flex: 1 !important;
        text-align: center !important;
    }
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Option Selector using columns and buttons
st.markdown("### Select Mode")

# Create session state to store the selected mode if it doesn't exist
if 'mode' not in st.session_state:
    st.session_state.mode = "Text to Image"

# Function to update the mode when a button is clicked
def set_mode(selected_mode):
    st.session_state.mode = selected_mode

# Create three columns for the mode buttons
col1, col2, col3 = st.columns(3)

# Custom style for the selected and unselected buttons
selected_style = """
    background-color: #ff4b4b;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    width: 100%;
    font-weight: bold;
"""

unselected_style = """
    background-color: #31333F;
    color: white;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 10px 20px;
    width: 100%;
    opacity: 0.85;
"""

# Add a button to each column
with col1:
    button1_style = selected_style if st.session_state.mode == "Text to Image" else unselected_style
    if st.button("Text to Image", key="btn_text2img", use_container_width=True, 
                 help="Generate images from text descriptions"):
        set_mode("Text to Image")
        st.rerun()

with col2:
    button2_style = selected_style if st.session_state.mode == "Image to Image" else unselected_style
    if st.button("Image to Image", key="btn_img2img", use_container_width=True,
                 help="Transform uploaded images using text prompts"):
        set_mode("Image to Image")
        st.rerun()

with col3:
    button3_style = selected_style if st.session_state.mode == "Freehand Drawing" else unselected_style
    if st.button("Freehand Drawing", key="btn_drawing", use_container_width=True,
                 help="Draw an image and transform it"):
        set_mode("Freehand Drawing")
        st.rerun()

# Style the buttons based on selection state
st.markdown(f"""
    <style>
        div[data-testid="stButton"] button[kind="secondary"][data-testid="baseButton-secondary"]:nth-of-type(1) {{
            {button1_style}
        }}
        div[data-testid="stButton"] button[kind="secondary"][data-testid="baseButton-secondary"]:nth-of-type(2) {{
            {button2_style}
        }}
        div[data-testid="stButton"] button[kind="secondary"][data-testid="baseButton-secondary"]:nth-of-type(3) {{
            {button3_style}
        }}
    </style>
""", unsafe_allow_html=True)

# Get the selected mode from session state
mode = st.session_state.mode

prompt = st.text_input("Enter Prompt:")

if mode != "Freehand Drawing":
    style = st.selectbox(
        "Choose Style",
        [
            "None",
            "Vintage",
            "Anime",
            "Realistic",
            "Cyberpunk",
            "Fantasy",
            "Ghibli",
            "Steampunk",
            "Minimalist"
        ]
    )
else:
    style = "None"

if style != "None":
    prompt = f"{prompt or ''}, in {style} style"

# Canvas only appears for Freehand Drawing
if mode == "Freehand Drawing":
    st.markdown("### Draw something below")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=4,
        stroke_color="#000000",
        background_color="#ffffff",
        height=364,
        width=768,
        drawing_mode="freedraw",
        key="canvas"
    )
    input_image = None
    strength = None
elif mode == "Image to Image":
    input_image = st.file_uploader("Upload Input Image:", type=["jpg", "jpeg", "png"])
    strength = st.slider("Strength of Image Influence)", min_value=0.1, max_value=1.0, value=0.75, step=0.05)
else:
    input_image = None
    strength = None

# Image Size section
st.markdown("### Image Size")
col1, col2 = st.columns(2)
with col1:
    width = st.slider("Width", min_value=256, max_value=1024, value=512, step=64)
with col2:
    height = st.slider("Height", min_value=256, max_value=1024, value=512, step=64)

# Generate button
if st.button("Generate Image"):
    if mode != "Freehand Drawing" and not prompt.strip():
        st.warning("Please enter a prompt.")
    elif mode == "Image to Image" and input_image is None:
        st.warning("Please upload an input image.")
    elif mode == "Freehand Drawing" and (canvas_result.image_data is None):
        st.warning("Please draw something on the canvas.")
    else:
        with st.spinner("Generating image..."):
            try:
                if mode == "Text to Image":
                    request = text2image_pb2.TextRequest(
                        prompt=prompt,
                        width=width,
                        height=height
                    )
                    response = stub.GenerateImage(request)

                elif mode == "Image to Image":
                    image_bytes = input_image.read()
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

                    request = text2image_pb2.Img2ImgRequest(
                        prompt=prompt,
                        input_image_base64=image_b64,
                        width=width,
                        height=height,
                        strength=strength
                    )
                    response = stub.GenerateImageFromImage(request)

                elif mode == "Freehand Drawing":
                    # Convert NumPy canvas to PNG bytes
                    image = Image.fromarray((canvas_result.image_data[:, :, :3]).astype('uint8'))
                    buf = io.BytesIO()
                    image.save(buf, format='PNG')
                    image_bytes = buf.getvalue()
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

                    request = text2image_pb2.Img2ImgRequest(
                        prompt=prompt,
                        input_image_base64=image_b64,
                        width=width,
                        height=height,
                        strength=0.75  # Default for drawing
                    )
                    response = stub.GenerateImageFromImage(request)

                if response.status == "success":
                    image_data = base64.b64decode(response.image_base64)
                    image = Image.open(io.BytesIO(image_data))
                    st.image(image, use_container_width=True)

                    st.download_button(
                        label="Download Image",
                        data=image_data,
                        file_name="generated_image.png",
                        mime="image/png"
                    )
                else:
                    st.error(f"Error: {response.status}")

            except Exception as e:
                st.error(f"Error communicating with the server: {str(e)}")