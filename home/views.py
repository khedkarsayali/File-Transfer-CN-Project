from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse
import threading
import socket
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        logging.error(f"Error getting local IP: {e}")
        return "127.0.0.1"

def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def home(request):
    return render(request, 'home.html')

def start_server(request):
    server_ip = get_local_ip()
    
    if request.method == "POST":
        file_path = request.POST.get("file_path")
        if not file_path:
            return HttpResponse("No file path provided.", status=400)
        
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            return HttpResponse("File not found. Please provide a valid file path.", status=404)

        def stream_file_sending():
            try:
                yield "<h2>Preparing to send the file...</h2>"
                run_server(file_path, server_ip)
                yield "<h2>File sent successfully!</h2>"
            except Exception as e:
                logging.error(f"Server error: {e}")
                yield f"<h2>Error occurred: {str(e)}</h2>"
            yield "<script>window.location.href='/'</script>"

        return StreamingHttpResponse(stream_file_sending(), content_type="text/html")
    
    return render(request, 'start_server.html', {'server_ip': server_ip})

def start_client(request):
    if request.method == "POST":
        receiver_ip = request.POST.get("receiver_ip")
        if not is_valid_ip(receiver_ip):
            return HttpResponse("Invalid IP address provided.", status=400)

        result = {"success": False, "message": ""}

        def stream_file_reception():
            try:
                run_client(receiver_ip, result)
                if result["success"]:
                    yield "<h2>File received successfully!</h2>"
                else:
                    yield f"<h2>Error: {result['message']}</h2>"
                time.sleep(1)
            except Exception as e:
                logging.error(f"Client error: {e}")
                yield f"<h2>Error occurred: {str(e)}</h2>"
            yield "<script>window.location.href='/'</script>"

        return StreamingHttpResponse(stream_file_reception(), content_type="text/html")
    
    return render(request, 'start_client.html')

def run_server(file_path, server_ip):
    try:
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError("The specified file does not exist.")

        port = 12345
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((server_ip, port))
            s.listen(1)
            logging.info(f"Server listening on {server_ip}:{port}")
            
            conn, addr = s.accept()
            logging.info(f"Connected to client: {addr}")
            
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            conn.sendall(f"{file_name}|{file_size}\n".encode())

            with open(file_path, 'rb') as f:
                while (chunk := f.read(1024)):
                    conn.sendall(chunk)

            logging.info("File sent successfully.")
    except Exception as e:
        logging.error(f"Server error: {e}")

def run_client(server_ip, result):
    try:
        port = 12345
        save_dir = os.path.join(os.getcwd(), "uploaded_files")
        os.makedirs(save_dir, exist_ok=True)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_ip, port))
            logging.info("Connected to server.")

            metadata = b""
            while not metadata.endswith(b'\n'):
                metadata += s.recv(1024)
            metadata = metadata.decode().strip()

            try:
                file_name, file_size = metadata.split("|")
                file_size = int(file_size)
            except ValueError:
                raise ValueError("Invalid metadata format received.")

            save_path = os.path.join(save_dir, file_name)
            logging.info(f"Receiving file: {file_name} ({file_size} bytes)")

            with open(save_path, 'wb') as f:
                total_received = 0
                while total_received < file_size:
                    data = s.recv(1024)
                    if not data:
                        break
                    f.write(data)
                    total_received += len(data)

            if total_received == file_size:
                result["success"] = True
                result["message"] = f"File received successfully: {save_path}"
                logging.info(result["message"])
            else:
                raise IOError("File transfer incomplete.")
    except Exception as e:
        result["success"] = False
        result["message"] = str(e)
        logging.error(f"Client error: {e}")
