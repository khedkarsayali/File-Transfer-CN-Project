import socket
import os

# Initialize socket
s = socket.socket()
host = socket.gethostname()
port = 12345
s.bind((host, port))

# Start listening
s.listen(5)
server_ip = socket.gethostbyname(host)
print("\nListening to IP:", server_ip)
print('Waiting for connection...')

# Accept connection
conn, addr = s.accept()
print(f"\nConnection established with {addr[0]} : {addr[1]}\n")

# List files in the current directory and let the user choose a file
print("Available files:")
files = os.listdir(".")
for i, file in enumerate(files, 1):
    print(f"{i}. {file}")

file_choice = int(input("Enter the number of the file to send: ")) - 1
filename = files[file_choice]

# Get file size and send metadata (filename|file_size)
file_size = os.path.getsize(filename)
metadata = f"{os.path.basename(filename)}|{file_size}"
conn.sendall(metadata.encode())
print(f"Sent metadata: {metadata}")

# Send the file in chunks
with open(filename, 'rb') as f:
    while True:
        data = f.read(1024)
        if not data:
            break
        conn.sendall(data)

print('File sent successfully\n\n')

# Close the connection
conn.close()
