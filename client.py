import socket
import select
import sys
import threading
import os
import tqdm

HOST = ""
PORT = ""

if len(sys.argv) != 3:
	HOST = '127.0.0.1'
	PORT = 8080

else:    	
	HOST = str(sys.argv[1])
	PORT = int(sys.argv[2])

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

print("Connected to server!")
#nickname = input("Please enter your username:")
nickname = ""
SEPARATOR = "<SEPARATOR>"
	
def receive():

	while True:
		try:
			msg = client.recv(1024).decode('utf-8')
			if len(msg) > 0:
				msgtype = msg[:6]
				msg = msg[6:]
				if msgtype == '~CHAT~':
					print(msg)
				
				elif msgtype == '~JOIN~':
					split_msg = msg.split('~')
					user = split_msg[0]
					group = split_msg[1]
					#print(f"User {user} wants to join group {group}. Press 'A' to accept, any other key to reject.")
					#res = input("")
					res = 'A'
					client.send(res.encode('utf-8'))
					print("Response sent")
					
				elif msgtype == '~FILE~':
					split_msg = msg.split('~')
					filename = split_msg[0]
					filesize = int(split_msg[1])
					
					#progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
					with open(filename, "wb") as f:
						bytes_read = client.recv(4096)
						if not bytes_read:
							break
						
						f.write(bytes_read)
						#progress.update(len(bytes_read))
							
					print("File received")			
					
				
		except Exception as e:
			print("Error:",e)
			client.close()
			break
	
def chat():
	global nickname
	while True:
		msg = input("Enter your command: ")
		if len(msg) == 0:
			continue
			
		split_msg = msg.split()
		if split_msg[0]== 'SIGNUP':
			nickname = split_msg[1]
		
		if split_msg[0] == 'SEND':
			if split_msg[1] == 'GROUP':
				message = split_msg[3:]
					
			else:
				message = split_msg[2:]
				
			print("<"+nickname+">: ", " ".join(message))
			
		if split_msg[0] == 'SENDFILE':
			filename = split_msg[1]
			filesize = os.path.getsize(filename)
			print("Filesize:", filesize)
			
			msg = msg+" "+str(filesize)
			client.send(msg.encode('utf-8'))
			res = client.recv(1024).decode('utf-8')
			if res != 'Y':
				print(res)
				continue
				

			#progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
			with open(filename, "rb") as f:
				while True:
					bytes_read = f.read(4096)
					#print("Sending", bytes_read)
					if not bytes_read:
						client.shutdown(socket.SHUT_WR)
						break
						
					client.sendall(bytes_read)
					#progress.update(len(bytes_read))

				
			print(f"File {filename} sent!")
			
			continue
			
		
		#msg = f'{nickname}: {input("")}'
		client.send(msg.encode('utf-8'))
		recvd_msg = client.recv(1024).decode('utf-8')
		#rcv = recvd_msg.split('~')
		if len(recvd_msg) > 6 and recvd_msg[:6] == '~CHAT~':
			print(recvd_msg[6:])
		
		elif len(recvd_msg) > 6 and recvd_msg[:6] == '~JOIN~':
			split_msg = recvd_msg.split('~')
			user = split_msg[0]
			group = split_msg[1]
			print(f"User {user} wants to join group {group}. Press 'A' to accept, any other key to reject.")
			res = input("")
			client.send(res.encode('utf-8'))
			print("Response sent")
			
		else:
			print("<Server>: "+ recvd_msg)


chat_thread = threading.Thread(target=chat)
chat_thread.start()

recv_thread = threading.Thread(target=receive)
recv_thread.start()
