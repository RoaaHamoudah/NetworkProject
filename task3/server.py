import socket
import random
import time
import threading

# Game questions
questions = [
    ("What is the capital of Palestine?", "Jerusalem"),
    ("What is the best football club in the world?", "Real Madrid"),
    ("How many minutes are in a full week?", "10800"),
    ("How many dots are on one six-sided die?", "21"),
    ("What is the nickname of Walter White in Breaking Bad?", "Heisenberg"),
    ("In which year did World War I begin?", "1914"),
    ("What are diamonds made of?", "Carbon")
]

server_ip = '0.0.0.0'
server_port = 5698
buffer_size = 2048
active_clients = {}
scores = {}
game_active = False

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((server_ip, server_port))

print(f"Trivia Game Server is up and listening on IP {socket.gethostbyname(socket.gethostname())}, port {server_port}")

def broadcast_message(message):
    """Send a message to all active clients."""
    for client in active_clients:
        server_socket.sendto(message.encode(), client)

def remove_disconnected_clients():
    """Remove clients that are no longer responding."""
    for client in list(active_clients):
        try:
            server_socket.settimeout(1)
            server_socket.sendto("Connection check".encode(), client)
        except Exception:
            print(f"Client {active_clients[client]} has disconnected.")
            del active_clients[client]
            del scores[client]

def handle_game_round():
    """Conduct a round of trivia, asking questions and handling scoring."""
    global game_active
    game_active = True

    if len(active_clients) < 2:
        print("Not enough players. Waiting for more clients...")
        return

    broadcast_message("Game starting now! Get ready!")
    time.sleep(2)

    round_scores = {client: 0 for client in active_clients}
    used_questions = []
    total_questions = len(questions)

    for i in range(total_questions):
        remove_disconnected_clients()

        available_questions = [q for q in questions if q not in used_questions]
        if not available_questions:
            break

        question, answer = random.choice(available_questions)
        used_questions.append((question, answer))

        print(f"Broadcasting Question {i + 1}/{total_questions}: {question}")
        broadcast_message(f"Question {i + 1}/{total_questions}: {question}")

        start_time = time.time()
        answered_clients = {}
        fastest_client = None
        fastest_time = float('inf')

        while time.time() - start_time < 15:
            try:
                server_socket.settimeout(1)
                message, client_address = server_socket.recvfrom(buffer_size)
                response = message.decode().strip().lower()

                if client_address in active_clients:
                    if client_address not in answered_clients:
                        answered_clients[client_address] = response
                        if response == answer.lower():
                            time_elapsed = time.time() - start_time
                            points = 10 if time_elapsed <= 5 else 5 if time_elapsed <= 10 else 2
                            round_scores[client_address] += points
                            scores[client_address] += points
                            if time_elapsed < fastest_time:
                                fastest_time = time_elapsed
                                fastest_client = client_address
            except socket.timeout:
                continue

        for client in active_clients:
            if client not in answered_clients:
                broadcast_message(f"{active_clients[client]} did not answer in time.")

        broadcast_message(f"Time's up! The correct answer was: {answer}")

        leaderboard = "\n".join([f"{active_clients[client]}: {scores[client]} points" for client in scores])
        broadcast_message("Current Scores:\n" + leaderboard)
        print(f"Leaderboard after Question {i + 1}")
        print(leaderboard)
        time.sleep(5)

    game_active = False
    max_score = max(scores.values(), default=0)
    winners = [active_clients[client] for client in scores if scores[client] == max_score]

    if winners:
        winner_names = ", ".join(winners)
        broadcast_message(f"Game Over! The winners are: {winner_names} with {max_score} points!")
    else:
        broadcast_message("Game Over! No winner this time.")

    final_scores = "\n".join([f"{active_clients[client]}: {scores[client]} points" for client in scores])
    broadcast_message("Final Scores:\n" + final_scores)
    print("Final Scores:")
    print(final_scores)

# new Client can join but an error will occure on the server side!!
def handle_new_client(client_address, username):
    if username in active_clients:
        server_socket.sendto("The user name you entered is already used!!", client_address)

    active_clients[client_address] = username
    scores[client_address] = 0
    print(f"New client joined: {username} from {client_address}")
    broadcast_message(f"{username} has joined the game.")

    # If a game is in progress, put the new player on the wait list and add them on the next round
    if game_active:
        server_socket.sendto("A game is currently in progress. You'll join the next round.".encode(), client_address)
    else:
        if len(active_clients) >= 2:
            # Start a new game round in a separate thread
            game_thread = threading.Thread(target=handle_game_round)
            game_thread.start()

def server_main():
    global game_active
    while True:
        try:
            message, client_address = server_socket.recvfrom(buffer_size)
            username = message.decode().strip()
            handle_new_client(client_address, username)
        except KeyboardInterrupt:
            print("Shutting down server...")
            break

    server_socket.close()

server_main()