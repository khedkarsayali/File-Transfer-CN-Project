import socket
import os

# Initialize socket
s = socket.socket()

host = input("\nEnter the sender IP address: ")
port = 12345

# Connect to sender
s.connect((host, port))

print('Connected to sender')

# Receive the file metadata (filename|file_size)
metadata = s.recv(1024).decode()
filename, file_size = metadata.split("|")
file_size = int(file_size)

# Ask user where to save the received file
save_path = input(f"Enter the path where you'd like to save the file (default: {filename}): ")
if not save_path:
    save_path = filename

# Receive and write the file in chunks
with open(save_path, 'wb') as f:
    while True:
        data = s.recv(1024)
        if not data:
            break
        f.write(data)

print(f"File received and saved as {save_path}")

# Close the connection
s.close()
