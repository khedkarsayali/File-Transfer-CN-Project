import os
import logging
import socket
from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse
from django.conf import settings

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper function to get local IP
def get_local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        logging.error(f"Error getting local IP: {e}")
        return "127.0.0.1"


# Helper function to validate IP address
def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


# Home view
def home(request):
    return render(request, 'home.html')


# Start server view
def start_server(request):
    server_ip = get_local_ip()  # Get the server's local IP address

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return HttpResponse("No file provided. Please upload a valid file.", status=400)

        # Save the uploaded file temporarily
        file_path = os.path.join(settings.MEDIA_ROOT, "uploads", uploaded_file.name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        def stream_file_sending():
            try:
                yield "<h2>Preparing to send the file...</h2>"
                run_server(file_path, server_ip)  # Function to send the file
                yield "<h2>File sent successfully!</h2>"
                yield "<script>window.location.href='/success/sent'</script>"
            except Exception as e:
                logging.error(f"Server error: {e}")
                yield f"<h2>Error occurred: {str(e)}</h2>"
                yield "<script>window.location.href='/success/sent'</script>"
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)  # Clean up the temporary file after sending

        return StreamingHttpResponse(stream_file_sending(), content_type="text/html")

    return render(request, 'start_server.html', {'server_ip': server_ip})


# Start client view
def start_client(request):
    if request.method == "POST":
        receiver_ip = request.POST.get("receiver_ip")
        
        if not is_valid_ip(receiver_ip):
            return HttpResponse("Invalid IP address provided.", status=400)
        
        result = {"success": False, "message": ""}

        def stream_file_reception():
            try:
                run_client(receiver_ip, result)  # Your client-side function to start receiving the file
                if result["success"]:
                    yield "<script>window.location.href='/success/received'</script>"
                else:
                    # Show a pop-up for failure and redirect to the home page
                    yield f"<script>alert('No connection available for IP address: {receiver_ip}'); window.location.href='/';</script>"
            except Exception as e:
                logging.error(f"Client error: {e}")
                # Show a pop-up for the exception and redirect to the home page
                yield f"<script>alert('Error occurred: {str(e)}'); window.location.href='/';</script>"

        return StreamingHttpResponse(stream_file_reception(), content_type="text/html")

    return render(request, 'start_client.html')


# Run server function to send the file
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
            logging.debug(f"Sending file: {file_name} of size {file_size} bytes")
            conn.sendall(f"{file_name}|{file_size}\n".encode())

            with open(file_path, 'rb') as f:
                while (chunk := f.read(1024)):
                    logging.debug(f"Sending chunk of size {len(chunk)} bytes")
                    conn.sendall(chunk)

            logging.info("File sent successfully.")
    except FileNotFoundError as e:
        logging.error(f"File error: {e}")
        raise
    except Exception as e:
        logging.error(f"Server error: {e}")
        raise


# Run client function to receive the file
def run_client(server_ip, result):
    try:
        port = 12345
        save_dir = os.path.join(settings.MEDIA_ROOT, "uploaded_files")
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
                logging.debug(f"Receiving file: {file_name} with expected size {file_size} bytes")
            except ValueError:
                raise ValueError("Invalid metadata format received.")

            save_path = os.path.join(save_dir, file_name)
            logging.debug(f"Saving file to {save_path}")

            with open(save_path, 'wb') as f:
                total_received = 0
                while total_received < file_size:
                    data = s.recv(1024)
                    if not data:
                        break
                    f.write(data)
                    total_received += len(data)
                    logging.debug(f"Received chunk of size {len(data)} bytes")

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


# Success view for sending or receiving files
def success(request, action):
    return render(request, 'success.html', {'action': action})
