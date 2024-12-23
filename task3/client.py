import socket

buffer_size = 2048

server_ip = input("Enter the server IP address: ")
server_port = int(input("Enter the server port: "))

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

username = input("Enter your username: ")
client_socket.sendto(username.encode(), (server_ip, server_port))

print(f"Connected to the Trivia Game Server at {server_ip}:{server_port}")

try:
    while True:
        message, _ = client_socket.recvfrom(buffer_size)
        decoded_message = message.decode()
        print("\n" + decoded_message)
        
        if "Question" in decoded_message:
            answer = input("Your answer (press Enter to skip): ").strip()
            client_socket.sendto(answer.encode(), (server_ip, server_port))

except KeyboardInterrupt:
    print("\nExiting the game...")
finally:
    client_socket.close()

