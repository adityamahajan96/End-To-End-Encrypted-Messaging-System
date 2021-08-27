import socket
import threading
import sys
import tqdm
import os
from Crypto.Cipher import DES3
from Crypto import Random
from random import randint
from time import *

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
							
		client_sender.send("Message sent!".encode('utf-8'))
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
	import json
	groups_str = json.dumps(groups)
	client_sender.send(groups_str.encode('utf-8'))
	

def send_file(filename, receiver, filesize):
	client_receiver = clients[receiver]
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
				if not logged_in:
					client.send("Please log in".encode('utf-8'))
					continue
				
				else:
					client.send('Y'.encode('utf-8'))
				
				print("Receiving file")
				filename = msg[1]
				receiver = msg[2]
				filesize = int(msg[3])
				
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
		
