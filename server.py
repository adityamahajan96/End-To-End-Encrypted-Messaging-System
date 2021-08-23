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
groups = {} #In the format: grp_name: {owner: [group_members,...]}
user_groups = {} #In the format: username: [list of groups]

def send_fun(sender,receiver,msg,client_sender,groupname=""):
	print(sender, receiver, groupname)
	if len(groupname) > 0:
		print(groupname)
		print(groups)
		if groupname not in groups:
			print(groupname)
			print(groups)
			client_sender.send("No such group!".encode('utf-8'))
			return
	
	elif receiver not in clients:
		client_sender.send("No such recipient!".encode('utf-8'))
		return
		
	print(sender+" sending a message to "+receiver+" "+groupname)
	#print(client_sender, type(client_sender))
	#print(client_receiver, type(client_receiver))
	#print("<"+sender+">: "+msg)
	chat = "~CHAT~"+"<"+sender+">: "+msg
	#print(chat.encode('utf-8'))
	
	if receiver == 'GROUP':
		for user,groupnames in user_groups.items():
			if user == sender:
				for group in groupnames:
					if group == groupname:
						members = list(groups[group].values())[0]
						for member in members:
							if member == sender:
								continue
								
							print("Group chat sending to member: ", member)
							clients[member].send(chat.encode('utf-8'))
							
		return
		
		
	if receiver == 'BROADCAST':
		for user,client_receiver in clients.items():
			client_receiver.send(chat.encode('utf-8'))
			break
		
		return
	
	client_receiver = clients[receiver]
	client_receiver.send(chat.encode('utf-8'))
	client_sender.send("Message sent!".encode('utf-8'))
	
def create_group(username, client_sender, group_name):
	if group_name in groups:
		client_sender.send('Group already exists! Choose a different name.'.encode('utf-8'))
		return
	
	temp = {}
	temp[username] = [username]
	groups[group_name] = temp
	
	if username in user_groups:
		user_groups[username].append(group_name)
	else:
		user_groups[username] = [group_name]
		
	print(f'Group {group_name} successfully created by {username}!')
	client_sender.send(f'Group {group_name} successfully created!'.encode('utf-8'))
	
	
def join_group(username, client_sender, group_name):
	if group_name not in groups:
		create_group(username, client_sender, group_name)
		#client_sender.send(f'New group {group_name} created!'.encode('utf-8'))
		return
	
	owner = list(groups[group_name].keys())[0]
	try:
		req = "~JOIN~"+username+"~"+group_name+"~"
		clients[owner].send(req.encode('utf-8'))
		#print(clients[owner])
		res = clients[owner].recv(1024).decode('utf-8')
		print(res)
		if res == 'A':
			#Approved
			print("Entered")
			print(groups[group_name])
			print(dict(groups[group_name])[owner])
			print(groups[group_name][owner])
			groups[group_name][owner].append(username)
			print("No issue")
			print(groups[group_name][owner])
			if username in user_groups:
				user_groups[username].append(group_name)
			
			else:
				user_groups[username] = [group_name]
				
			print(user_groups[username])
			print("No issue")
			client_sender.send(f'You are added to group {group_name}!'.encode('utf-8'))
		
		else:
			#Rejected
			client_sender.send(f'Your request to join group {group_name} was rejected!'.encode('utf-8'))
	except:
		client_sender.send("Some issue occured. User cannot join the group".encode('utf-8'))
		
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
					
				if msg[1] == 'GROUP':
					groupname = msg[2]
					message = " ".join(msg[3:])
					print(groupname, message)
					send_fun(user, "GROUP", message, client, groupname=groupname)
					continue
				
				receiver = msg[1]
				message = " ".join(msg[2:])
				send_fun(user, receiver, message, client)
				
			if msg[0] == 'CREATE':
				if not logged_in:
					client.send("Please log in".encode('utf-8'))
					continue
					
				create_group(user, client, msg[1])
				
			if msg[0] == 'JOIN':
				if not logged_in:
					client.send("Please log in".encode('utf-8'))
					continue
				
				join_group(user, client, msg[1])
				
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
		
