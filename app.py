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

# Must be the first Streamlit command
st.set_page_config(page_title="Text-to-Image Generator", layout="centered")

# Make sure Python can find the modules in the include directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'include'))

# Function to check if the gRPC server is running
def is_server_running():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', 50051)) == 0
    except:
        return False

# Check if the server is running, if not, start it
if not is_server_running():
    st.info("Starting gRPC server... Please wait.")
    
    # Path to the server script
    server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                'include', 'grpc_server.py')
    
    # Start the server as a subprocess
    if os.name == 'nt':  # Windows
        server_process = subprocess.Popen(
            [sys.executable, server_script],
            cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'include'),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    
    # Wait for the server to start
    for _ in range(30):  # Wait up to 15 seconds
        if is_server_running():
            break
        time.sleep(0.5)
    
    if is_server_running():
        st.success("gRPC server is now running!")
    else:
        st.error("Failed to start gRPC server. Please start it manually and refresh this page.")
        st.stop()

# Set up gRPC client
channel = grpc.insecure_channel('localhost:50051')
stub = text2image_pb2_grpc.Text2ImageStub(channel)

# Streamlit UI
st.markdown(
    '<h1 style="white-space: nowrap; text-align: center; margin: 0 auto;">Text to Image Generator</h1>',
    unsafe_allow_html=True
)

# Add custom CSS to increase text area size
st.markdown("""
    <style>
        .stTextArea textarea {
            font-size: 16px;
            height: 80px !important;
        }
    </style>
""", unsafe_allow_html=True)


prompt = st.text_input("Enter prompt:")
context = st.text_area("Additional context (optional):")

st.markdown("### Image Size")

col1, col2 = st.columns(2)
with col1:
    width = st.slider("Width", min_value=256, max_value=1024, value=512, step=64)
with col2:
    height = st.slider("Height", min_value=256, max_value=1024, value=512, step=64)

if st.button("Generate Image"):
    if not prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Generating image..."):
            try:
                request = text2image_pb2.TextRequest(
                    prompt=prompt,
                    context=context,
                    width=width,
                    height=height
                )
                response = stub.GenerateImage(request)

                if response.status == "success":
                    # Convert base64 back to image
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
