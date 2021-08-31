import socket
import select
import sys
import threading
import os
import tqdm

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

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_chat1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_chat2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_chat3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))
client2.connect((HOST,PORT2))
client3.connect((HOST,PORT3))

client_chat1.connect((HOST, PORT))
client_chat2.connect((HOST,PORT2))
client_chat3.connect((HOST,PORT3))

print("Connected to server!")
#nickname = input("Please enter your username:")
nickname = ""
locked = True

def receive(client_res):
	global locked
	while True:
		try:	
			msg = client_res.recv(1024).decode('utf-8')
			
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
					client_res.send(res.encode('utf-8'))
					print("Response sent")
					
				elif msgtype == '~FILE~':
					split_msg = msg.split('~')
					filename = split_msg[0]
					filesize = int(split_msg[1])
					
					#progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
					with open(filename, "wb") as f:
						bytes_read = client_res.recv(4096)
						if not bytes_read:
							break
						
						f.write(bytes_read)
						#progress.update(len(bytes_read))
							
					print("File received")
				
				else:
					print("<Server>: "+ msg)
					
				
		except Exception as e:
			print("Error:",e)
			client_res.close()
			break
	
def chat():
	global nickname, locked
	req_ID = 0
	while True:
		msg = input("")
		if len(msg) == 0:
			continue
			
		split_msg = msg.split()
		if split_msg[0] == 'SIGNUP':
			nickname = split_msg[1]
			client.send(msg.encode('utf-8'))
			recvd_msg = client.recv(1024).decode('utf-8')
			client2.send(msg.encode('utf-8'))
			recvd_msg2 = client2.recv(1024).decode('utf-8')
			client3.send(msg.encode('utf-8'))
			recvd_msg3 = client3.recv(1024).decode('utf-8')
			
			if recvd_msg == 'Y':
				print("<Server>: Sign Up Successful!")
			
			else:
				if recvd_msg2 == 'Y':
					print("<Server>: Sign Up Successful!")
				
				else:
					if recvd_msg3 == 'Y':
						print("<Server>: Sign Up Successful!")
					
					else:
						print("<Server>: Sign Up Failed!")
				
			req_ID += 1
			continue
			
		if split_msg[0] == 'LOGIN':
			client.send(msg.encode('utf-8'))
			recvd_msg = client.recv(1024).decode('utf-8')
			client2.send(msg.encode('utf-8'))
			recvd_msg2 = client2.recv(1024).decode('utf-8')
			client3.send(msg.encode('utf-8'))
			recvd_msg3 = client3.recv(1024).decode('utf-8')
			
			ret_sock_msg = "RETURN_SOCK "+split_msg[1]
			client_chat1.send(ret_sock_msg.encode('utf-8'))
			client_chat2.send(ret_sock_msg.encode('utf-8'))
			client_chat3.send(ret_sock_msg.encode('utf-8'))
			
			if recvd_msg == 'Y':
				print("<Server>: Logged In!")
			
			else:
				if recvd_msg2 == 'Y':
					print("<Server>: Logged In!")
				
				else:
					if recvd_msg3 == 'Y':
						print("<Server>: Logged In!")
					
					else:
						print("<Server>: Log In Failed!")
				
			req_ID += 1
			continue
		
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
		recvd_msg = ""
		
		if req_ID % 3 == 0:
			client.send(msg.encode('utf-8'))
			recvd_msg = client.recv(1024).decode('utf-8')
		
		elif req_ID % 3 == 1:
			client2.send(msg.encode('utf-8'))
			recvd_msg = client2.recv(1024).decode('utf-8')
			
		else:
			client3.send(msg.encode('utf-8'))
			recvd_msg = client3.recv(1024).decode('utf-8')

		
		#rcv = recvd_msg.split('~')
		if len(recvd_msg) > 6 and recvd_msg[:6] == '~CHAT~':
			print(recvd_msg[6:])
		
		elif len(recvd_msg) > 6 and recvd_msg[:6] == '~JOIN~':
			split_msg = recvd_msg.split('~')
			user = split_msg[0]
			group = split_msg[1]
			print(f"User {user} wants to join group {group}. Press 'A' to accept, any other key to reject.")
			res = input("")
			if req_ID % 3 == 0:
				client.send(res.encode('utf-8'))
			elif req_ID % 3 == 1:
				client2.send(res.encode('utf-8'))
			elif req_ID % 3 == 2:
				client3.send(res.encode('utf-8'))
				
			print("Response sent")
			
		else:
			print("<Server>: "+ recvd_msg)
		
		
		req_ID+=1

chat_thread = threading.Thread(target=chat)
chat_thread.start()

recv_thread = threading.Thread(target=receive, args=(client_chat1,))
recv_thread.start()

recv_thread2 = threading.Thread(target=receive, args=(client_chat2,))
recv_thread2.start()

recv_thread3 = threading.Thread(target=receive, args=(client_chat3,))
recv_thread3.start()
