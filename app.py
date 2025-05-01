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
        .stTextInput label, .stTextArea label {
            font-size: 20px !important;
            font-weight: bold;
        }
        .stTextArea textarea {
            font-size: 16px;
            height: 80px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Option Selector
mode = st.radio("Select Mode", ["Text to Image", "Image to Image"])

prompt = st.text_input("Enter prompt:")
context = st.text_area("Additional context (optional):")

if mode == "Image to Image":
    input_image = st.file_uploader("Upload input image (JPG,PNG,JPEG):", type=["jpg", "jpeg", "png"])
    strength = st.slider("Strength (Image Influence)", min_value=0.1, max_value=1.0, value=0.75, step=0.05)
else:
    input_image = None
    strength = None

st.markdown("### Image Size")
col1, col2 = st.columns(2)
with col1:
    width = st.slider("Width", min_value=256, max_value=1024, value=512, step=64)
with col2:
    height = st.slider("Height", min_value=256, max_value=1024, value=512, step=64)

if st.button("Generate Image"):
    if not prompt.strip():
        st.warning("Please enter a prompt.")
    elif mode == "Image to Image" and input_image is None:
        st.warning("Please upload an input image.")
    else:
        with st.spinner("Generating image..."):
            try:
                if mode == "Text to Image":
                    request = text2image_pb2.TextRequest(
                        prompt=prompt,
                        context=context,
                        width=width,
                        height=height
                    )
                    response = stub.GenerateImage(request)

                else:
                    image_bytes = input_image.read()
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

                    request = text2image_pb2.Img2ImgRequest(
                        prompt=prompt,
                        context=context,
                        input_image_base64=image_b64,
                        width=width,
                        height=height,
                        strength=strength
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
