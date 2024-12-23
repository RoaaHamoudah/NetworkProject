from socket import *
import threading

serverPort = 5698
serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.bind(("", serverPort))
serverSocket.listen(1)

print(f'The server is ready and listening on IP {gethostbyname(gethostname())} and port 5698...')

# Read the "not found" page in advance
with open("notFound.html", "rb") as not_found_file:
    not_found_data = not_found_file.read()

# Function to handle client requests
def handle_client(connectionSocket, addr):
    try:
        sentence = connectionSocket.recv(2048).decode()

        print("IP Address:", addr)
        print("Received Sentence:", sentence)

        ip = addr[0]
        port = addr[1]
        client_ip_port = f"{ip}:{port}"

        if sentence.startswith("GET /") and (" HTTP/1.1" in sentence or " HTTP/1.0" in sentence):
            path = sentence.split(" ")[1].replace("?", " ")

            content_type = "text/html"
            filename = path[1:]
            

            if "/search" in path:
                path = path.split(" ")[1]
                path = path.split('=')[1].replace("+", " ")
                filename = f"Resources/{path}"
                

            if path in ["/", "/index.html", "/main_en.html", "/en"]:
                filename = "main_en.html"

            elif path in ["/ar", "/main_ar.html"]:
                filename = "main_ar.html"

            print(path)
            if path.endswith(".css"):
                content_type = "text/css"

            elif path.endswith(".png"):
                content_type = "image/png"

            elif path.endswith(".jpg"):
                content_type = "image/jpg"

            elif path.endswith(".mp4"):
                content_type = "video/mp4"

            try:
                # Open and send the requested file
                with open(filename, "rb") as file:
                    fileData = file.read()
                    connectionSocket.send("HTTP/1.1 200 OK\r\n".encode())
                    connectionSocket.send(f"Content-Type: {content_type}; charset=utf-8\r\n".encode())
                    connectionSocket.send("\r\n".encode())
                    connectionSocket.send(fileData)

            except FileNotFoundError:  
                if content_type.endswith('/mp4'):
                    filename = filename[10:-4]
                    # Send HTTP 307 Temporary Redirect response
                    connectionSocket.send("HTTP/1.1 307 Temporary Redirect\r\n".encode())
                    # Specify the new location where the client should go
                    redirect_url = f"https://www.youtube.com/results?search_query={filename}"
                    connectionSocket.send(f"Location: {redirect_url}\r\n".encode())
                    # End the headers section
                    connectionSocket.send("\r\n".encode())
                    connectionSocket.close()
                
                elif content_type.endswith('/png') | content_type.endswith('/jpg'):
                    filename = filename[10:-4]
                    # Send HTTP 307 Temporary Redirect response
                    connectionSocket.send("HTTP/1.1 307 Temporary Redirect\r\n".encode())
                    # Specify the new location where the client should go
                    redirect_url = f"https://www.google.com/search?q={filename}"
                    connectionSocket.send(f"Location: {redirect_url}\r\n".encode())
                    # End the headers section
                    connectionSocket.send("\r\n".encode())
                    connectionSocket.close()
                # Send a 404 Not Found response if the file doesn't exist
                with open("NotFound.html", "r", encoding="utf-8") as file:
                    fileData = file.read().replace("{client_ip_port}", client_ip_port)
                    connectionSocket.send("HTTP/1.1 404 Not Found\r\n".encode())
                    connectionSocket.send("Content-Type: text/html; charset=utf-8\r\n".encode())
                    connectionSocket.send("\r\n".encode())
                    connectionSocket.send(fileData.encode())
                    connectionSocket.close()
                    return
        else:
            # Send a 404 Not Found response for invalid requests
            with open("NotFound.html", "r", encoding="utf-8") as file:
                fileData = file.read().replace("{client_ip_port}", client_ip_port)
                connectionSocket.send("HTTP/1.1 404 Not Found\r\n".encode())
                connectionSocket.send("Content-Type: text/html; charset=utf-8\r\n".encode())
                connectionSocket.send("\r\n".encode())
                connectionSocket.send(fileData.encode())
                connectionSocket.close()

    except OSError:
        print("IO error")
    finally:
        connectionSocket.close()

# Main server loop
while True:
    try:
        # Accept new client connection
        connectionSocket, addr = serverSocket.accept()
        
        # Create and start a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr))
        client_thread.start()

    except OSError:
        print("IO error")
