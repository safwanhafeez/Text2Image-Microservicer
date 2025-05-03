from flask import Flask, request, jsonify
import grpc
import text2image_pb2
import text2image_pb2_grpc

app = Flask(__name__)

# Connect to gRPC server
channel = grpc.insecure_channel('localhost:50051')
stub = text2image_pb2_grpc.Text2ImageStub(channel)

@app.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get('prompt', '')

    grpc_request = text2image_pb2.TextRequest(prompt=prompt)
    grpc_response = stub.GenerateImage(grpc_request)

    return jsonify({
        'status': grpc_response.status,
        'image_base64': grpc_response.image_base64
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000)
