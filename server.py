import socket
import threading
import sys

HOST = ""
PORT = ""

if len(sys.argv) != 3:
	HOST = '127.0.0.1'
	PORT = 8080

else:	
	HOST = str(sys.argv[1])
	PORT = int(sys.argv[2])

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST,PORT))

server.listen()

clients = {}
client_creds = {}

def send_fun(receiver,msg,client_sender):
	sender = ""
	for user,client in clients.items():
		if client == client_sender:
			sender = user
			break
			
	print(sender+" sending a message to "+receiver)
	client_receiver = clients[receiver]
	#print(client_sender, type(client_sender))
	#print(client_receiver, type(client_receiver))
	#print("<"+sender+">: "+msg)
	chat = "<"+sender+">: "+msg
	#print(chat.encode('utf-8'))
	client_receiver.send(chat.encode('utf-8'))
	
	if receiver == 'BROADCAST':
		for user,client_receiver in clients.items():
			client_receiver.send(chat.encode('utf-8'))
			break
	
	client_sender.send("Message sent!".encode('utf-8'))
		
def signup(username, password, client):
	try:
		clients[username] = client
		client_creds[username] = password
		return True
	except:
		return False

def login(username, password):
	for user,passw in client_creds.items():
		if username == user and password == passw:
			return True
	
	return False
	
		
def handle(client):
	logged_in = False
	user = ""
	
	while True:
		try:
			raw_msg = client.recv(1024).decode('utf-8')
			msg = raw_msg.split()
			#print(msg)
			if msg[0] == 'SIGNUP':
				username = msg[1]
				password = msg[2]
				if signup(username, password, client):
					print(f'Sign Up for {username} successful!')
					client.send("Sign Up successful!".encode('utf-8'))
				
				else:
					print(f'Sign Up for {username} failed!')
					client.send("Sign Up failed!".encode('utf-8'))
			
			if msg[0] == 'LOGIN':
				username = msg[1]
				password = msg[2]
				if login(username, password):
					print(f'{username} logged in!')
					client.send("Logged In!".encode('utf-8'))
					logged_in = True
					user = username
				
				else:
					print(f'Failed to login!')
					client.send("Log In Failed!".encode('utf-8'))
					
			if msg[0] == 'SEND':
				if not logged_in:
					client.send("Please log in".encode('utf-8'))
					continue
				
				username = msg[1]
				message = "".join(msg[2:])
				send_fun(username, message, client)
				
			#broadcast(msg)
		
		except:
			#index = clients.index(client)
			clients.pop(user)
			client.close()
			#nickname = nicknames[index]
			#broadcast(f'{nickname} left the chat!'.encode('utf-8'))
			#nicknames.remove(nickname)
			break

def receive():
	while True:
		client,addr = server.accept()
		print(f"Connected with {str(addr)}!")
		#client.send("<NICKNAME>".encode('utf-8'))
		#nickname = client.recv(1024)
		#nicknames.append(nickname)
		#clients.append(client)
		#broadcast(f"{nickname} connected to the server!".encode('utf-8'))
		#client.send("Connected with the server!".encode('utf-8'))
		
		thread = threading.Thread(target=handle, args=(client,))
		thread.start()
	
	
print("Server running...")
receive()	
		
