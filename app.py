import streamlit as st
import grpc
import base64
from include import text2image_pb2
from include import text2image_pb2_grpc
from PIL import Image
import io
import os
import sys
    
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'include'))

# Set up gRPC client
channel = grpc.insecure_channel('localhost:50051')
stub = text2image_pb2_grpc.Text2ImageStub(channel)

# Streamlit UI
st.set_page_config(page_title="Text-to-Image Generator", layout="centered")
st.title("🖌️ Text-to-Image Generator (Stable Diffusion + gRPC)")

prompt = st.text_input("Enter prompt:")
context = st.text_area("Additional context (optional):")

if st.button("Generate Image"):
    if not prompt.strip():
        st.warning("Please enter a prompt.")
    else:
        with st.spinner("Generating image..."):
            request = text2image_pb2.TextRequest(prompt=prompt, context=context)
            response = stub.GenerateImage(request)

            if response.status == "success":
                # Convert base64 back to image
                image_data = base64.b64decode(response.image_base64)
                image = Image.open(io.BytesIO(image_data))
                st.image(image, caption="Generated Image", use_container_width=True)

                # Download button
                st.download_button(
                    label="Download Image",
                    data=image_data,
                    file_name="generated_image.png",
                    mime="image/png"
                )
            else:
                st.error(f"Error: {response.status}")