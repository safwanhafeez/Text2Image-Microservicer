import requests
import socket
import sys
import time
import argparse

def check_port(host, port):
    """Check if a port is open on a host."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except:
        return False

def check_streamlit(host, port):
    """Check if Streamlit is responding."""
    try:
        response = requests.get(f"http://{host}:{port}", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description='Check deployment status of the text-to-image services')
    parser.add_argument('--host', default='localhost', help='Host to check')
    parser.add_argument('--wait', action='store_true', help='Wait for services to come online')
    args = parser.parse_args()
    
    print(f"Checking services on {args.host}...")
    
    if args.wait:
        max_retries = 30
        retry = 0
        all_up = False
        
        while retry < max_retries and not all_up:
            grpc_status = check_port(args.host, 50051)
            streamlit_status = check_streamlit(args.host, 8501)
            all_up = grpc_status and streamlit_status
            
            if all_up:
                break
                
            print(f"Waiting for services to come online ({retry+1}/{max_retries})...")
            retry += 1
            time.sleep(5)
    else:
        grpc_status = check_port(args.host, 50051)
        streamlit_status = check_streamlit(args.host, 8501)
    
    print("\nService Status:")
    print(f"gRPC Server (port 50051): {'UP' if grpc_status else 'DOWN'}")
    print(f"Streamlit App (port 8501): {'UP' if streamlit_status else 'DOWN'}")
    
    if not grpc_status or not streamlit_status:
        print("\nSome services are not running. Check logs with:")
        print("  docker-compose logs")
        return 1
    else:
        print("\nAll services are up and running!")
        print(f"Access the application at: http://{args.host}:8501")
        return 0

if __name__ == "__main__":
    sys.exit(main())