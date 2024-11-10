from django.shortcuts import render
from django.http import HttpResponse
import threading
import socket
import os

# Start server to send file
def start_server(request):
    # Get the device's local IP address
    server_ip = socket.gethostbyname(socket.gethostname())
    
    if request.method == "POST":
        file_path = request.POST.get("file_path")
        if not os.path.exists(file_path):
            return HttpResponse("File not found. Please provide a valid file path.")
        
        # Start the server thread as a daemon
        server_thread = threading.Thread(target=run_server, args=(file_path,), daemon=True)
        server_thread.start()
        return HttpResponse(f"Server started and ready to send the file. Share this IP with the client: {server_ip}")
    
    return render(request, 'start_server.html', {'server_ip': server_ip})

# Start client to receive file
def start_client(request):
    if request.method == "POST":
        receiver_ip = request.POST.get("receiver_ip")
        
        # Start the client thread as a daemon
        client_thread = threading.Thread(target=run_client, args=(receiver_ip,), daemon=True)
        client_thread.start()
        return HttpResponse("Client started and waiting to receive the file.")
    
    return render(request, 'start_client.html')

# Define the server logic
def run_server(file_path):
    try:
        # Bind the server to the device's IP and a port
        host = socket.gethostbyname(socket.gethostname())  # Automatically gets the device's local IP
        port = 12345
        
        # Initialize socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen(1)
            print(f"Server listening on {host}:{port}")
            
            conn, addr = s.accept()
            print(f"Connected to receiver: {addr}")
            
            # Send file metadata
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            conn.send(f"{file_name}|{file_size}".encode())
            
            # Send the file in chunks
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    conn.sendall(data)
            
            print("File sent successfully.")
            conn.close()
    except Exception as e:
        print(f"Error in server: {e}")

# Define the client logic
def run_client(receiver_ip):
    try:
        port = 12345
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((receiver_ip, port))  # Connect to the specified receiver's IP
            print("Connected to the sender.")
            
            # Receive metadata
            metadata = s.recv(1024).decode()
            file_name, file_size = metadata.split("|")
            file_size = int(file_size)
            
            # Save the file
            with open(file_name, 'wb') as f:
                received = 0
                while received < file_size:
                    data = s.recv(1024)
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
            
            print(f"File '{file_name}' received successfully.")
    except Exception as e:
        print(f"Error in client: {e}")
