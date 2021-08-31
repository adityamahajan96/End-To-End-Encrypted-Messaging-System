import socket
import threading
import sys
import tqdm
import os
from Crypto.Cipher import DES3
from Crypto import Random
from random import randint
from time import *
import json
import pickle

HOST = ""
PORT = PORT2 = PORT3 = ""

if len(sys.argv) != 5:
	HOST = '127.0.0.1'
	PORT = 8080
	PORT2 = 8081
	PORT3 = 8082
	

else:	
	HOST = str(sys.argv[1])
	PORT = int(sys.argv[2])
	PORT2 = int(sys.argv[3])
	PORT3 = int(sys.argv[4])

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST,PORT))

server.listen()

clients = {}
client_ret_sock = {}
client_creds = {}
groups = {} #In the format: grp_name: {owner: [group_members,...]}
user_groups = {} #In the format: username: [list of groups]
isActive = {}

def send_fun(sender,receiver,msg,client_sender,groupname=""):
	#print(sender, receiver, groupname)
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
		
	elif not isActive[receiver]:
		client_sender.send("User is not active!".encode('utf-8'))
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
							client_ret_sock[member].send(chat.encode('utf-8'))
							
		client_sender.send("Message sent!".encode('utf-8'))
		return
		
		
	if receiver == 'BROADCAST':
		for user,client_receiver in client_ret_sock.items():
			client_receiver.send(chat.encode('utf-8'))
			break
		
		return
	
	client_receiver = client_ret_sock[receiver]
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
		print(req)
		#client_ret_sock[owner].send(req.encode('utf-8'))
		#print("JOIN REQ SENT TO CLIENT")
		#print(clients[owner])
		#res = client_ret_sock[owner].recv(1024).decode('utf-8')
		#print("JOIN RESPONSE GOT")
		#print(res)
		res = 'A'
		if res == 'A':
			#Approved
			groups[group_name][owner].append(username)
			
			if username in user_groups:
				user_groups[username].append(group_name)
			
			else:
				user_groups[username] = [group_name]
				
			client_sender.send(f'You are added to group {group_name}!'.encode('utf-8'))
		
		else:
			#Rejected
			client_sender.send(f'Your request to join group {group_name} was rejected!'.encode('utf-8'))
	except:
		client_sender.send("Some issue occured. User cannot join the group".encode('utf-8'))
		
		
def leave_group(username, client_sender, group_name):
	if group_name not in groups:
		client_sender.send(f'No such group exists!'.encode('utf-8'))
		return
	
	try:
		for grp in user_groups[username]:
			if grp == group_name:
				user_groups[username].remove(grp)
				break
				
		for owner, members in groups[group_name]:
			for member in members:
				if member == username:
					members.remove(member)
					client_sender.send(f'Removed from group {group_name}!'.encode('utf-8'))
					return
					
	except:
		client_sender.send('Some error occured!'.encode('utf-8'))
		

def list_groups(client_sender):
	groups_str = json.dumps(groups)
	client_sender.send(groups_str.encode('utf-8'))
	

def send_file(filename, receiver, filesize, groupname=""):
	client_receiver = client_ret_sock[receiver]
	msg = "~FILE~"+filename+"~"+str(filesize)
	#print("Filesize:", os.path.getsize(filename))
	print(f"Sending file {filename} to {receiver}")
	client_receiver.send(msg.encode('utf-8'))

	#progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
	with open(filename, "rb") as f:
		while True:
			bytes_read = f.read(4096)
			if not bytes_read:
				client_receiver.shutdown(socket.SHUT_WR)
				break
						
			client_receiver.sendall(bytes_read)
			#progress.update(len(bytes_read))
	
	os.remove(filename)
			
	print(f"File {filename} sent!")
	
	
		
def signup(username, password, client):
	if username == 'GROUP':
		return False
		
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
	
def sync_servers():
	#clients_str = pickle.dumps(clients).encode('utf-8')
	client_creds_str = pickle.dumps(client_creds)
	groups_str = pickle.dumps(groups)
	user_groups_str = pickle.dumps(user_groups)
	isActive_str = pickle.dumps(isActive)
	
	server_as_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_as_client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	try:
		server_as_client.connect((HOST, PORT2))
		
		server_as_client.send("~SYNC~".encode('utf-8'))
		rcv = server_as_client.recv(1024).decode('utf-8')
		if rcv == 'Y':
			#server_as_client.send(clients_str)
			server_as_client.send(client_creds_str)
			
		rcv = server_as_client.recv(1024).decode('utf-8')
		if rcv == 'Y':
			server_as_client.send(groups_str)
		
		rcv = server_as_client.recv(1024).decode('utf-8')
		if rcv == 'Y':
			server_as_client.send(user_groups_str)
			
		rcv = server_as_client.recv(1024).decode('utf-8')
		if rcv == 'Y':
			server_as_client.send(isActive_str)
			
		rcv = server_as_client.recv(1024).decode('utf-8')
		
		server_as_client.close()
		
	except Exception as e:
		print("Error",e)
		print(f"Server {HOST}:{PORT2} is down.")
		server_as_client.close()
	
	try:
		server_as_client2.connect((HOST, PORT3))
		
		server_as_client2.send("~SYNC~".encode('utf-8'))
		rcv = server_as_client2.recv(1024).decode('utf-8')
		if rcv == 'Y':
			#server_as_client.send(clients_str)
			server_as_client2.send(client_creds_str)
			
		rcv = server_as_client2.recv(1024).decode('utf-8')
		if rcv == 'Y':
			server_as_client2.send(groups_str)
		
		rcv = server_as_client2.recv(1024).decode('utf-8')
		if rcv == 'Y':
			server_as_client2.send(user_groups_str)
			
		rcv = server_as_client2.recv(1024).decode('utf-8')
		if rcv == 'Y':
			server_as_client2.send(isActive_str)
			
		rcv = server_as_client2.recv(1024).decode('utf-8')
		
		server_as_client2.close()
		
	except Exception as e:
		print("Error",e)
		print(f"Server {HOST}:{PORT3} is down.")
		server_as_client2.close()
	
	
		
def handle(client):
	global client_creds, groups, user_groups, isActive
	logged_in = False
	user = ""
	
	while True:
		try:
			raw_msg = client.recv(1024).decode('utf-8')
			#print(msg)
			if raw_msg[:6] == '~SYNC~':
				client.send("Y".encode('utf-8'))
				#print("Synced")
				#rcv1 = client.recv(1024).decode('utf-8')
				rcv2 = client.recv(1024)
				client.send("Y".encode('utf-8'))
				#print(rcv2)
				rcv3 = client.recv(1024)
				client.send("Y".encode('utf-8'))
				#print(rcv3)
				rcv4 = client.recv(1024)
				client.send("Y".encode('utf-8'))
				rcv5 = client.recv(1024)
				client.send("Y".encode('utf-8'))
				#print(rcv4)
				
				#clients = rcv1.loads()
				client_creds = pickle.loads(rcv2)
				groups = pickle.loads(rcv3)
				user_groups = pickle.loads(rcv4)
				isActive = pickle.loads(rcv5)
				
				#print(clients)
				#print(client_creds)
				#print(groups)
				#print(user_groups)
				
				continue
				
			if len(raw_msg) == 0:
				continue
				
			msg = raw_msg.split()
			if msg[0] == 'SIGNUP':
				username = msg[1]
				password = msg[2]
				isActive[username] = False
				
				if signup(username, password, client):
					print(f'Sign Up for {username} successful!')
					client.send("Y".encode('utf-8'))
				
				else:
					print(f'Sign Up for {username} failed!')
					client.send("N".encode('utf-8'))
			
			if msg[0] == 'RETURN_SOCK':
				client_ret_sock[msg[1]] = client
				
			if msg[0] == 'LOGIN':
				username = msg[1]
				password = msg[2]
				if login(username, password):
					print(f'{username} logged in!')
					client.send("Y".encode('utf-8'))
					logged_in = True
					user = username
					isActive[user] = True
				
				else:
					print(f'Failed to login!')
					client.send("N".encode('utf-8'))
					
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
				
			if msg[0] == 'LEAVE':
				if not logged_in:
					client.send("Please log in".encode('utf-8'))
					continue
				
				leave_group(user, client, msg[1])
				
			if msg[0] == 'LIST':
				if not logged_in:
					client.send("Please log in".encode('utf-8'))
					continue
					
				list_groups(client)
				
			if msg[0] == 'SENDFILE':
				print("File to server")
				groupname = ""
				filename = msg[1]
				receiver = msg[2]
				filesize = 0
				if receiver == "GROUP":
					groupname = msg[3]
					filesize = int(msg[4])
				
				else:
					filesize = int(msg[3])
					
				if not logged_in:
					client.send("Please log in".encode('utf-8'))
					continue
				
				else:
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
						
					elif not isActive[receiver]:
						client_sender.send("User is not active!".encode('utf-8'))
						return
						
					client.send('Y'.encode('utf-8'))
				
				print("Receiving file")
				
				#progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
				print("Start receiving..")
				with open(filename, "wb") as f:
					while True:
						bytes_read = client.recv(4096)
						print("Received", bytes_read)
						if not bytes_read:
							break
							
						f.write(bytes_read)
						#progress.update(len(bytes_read))
				
				print("Received file")
				send_file(filename, receiver, filesize)
				
			if msg[0] == 'LOGOUT':
				logged_in = False
				user = ""
				isActive[user] = False
				client.send("Logged Out!".encode('utf-8'))
			
			sync_servers()
			
		
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
		
