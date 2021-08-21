import socket
import select
import sys
import threading

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


def receive():
	while True:
		try:
			msg = client.recv(1024).decode('utf-8')
			if len(msg) > 0:
				print(msg)
			
		except Exception as e:
			print("Error:",e)
			client.close()
			break
	
def chat():
	global nickname
	while True:
		msg = input("")
		split_msg = msg.split()
		if split_msg[0]== 'SIGNUP':
			nickname = split_msg[1]
		
		if split_msg[0] == 'SEND':
			message = split_msg[2:]
			print("<"+nickname+">: ", "".join(message))
		
		#msg = f'{nickname}: {input("")}'
		client.send(msg.encode('utf-8'))
		recvd_msg = client.recv(1024).decode('utf-8')
		rcv = recvd_msg.split()
		"""if rcv[0] == '<CHAT>':
			print(rcv[1] + ": ", rcv[2:])
			continue"""
		
		print("<Server>: "+ recvd_msg)


chat_thread = threading.Thread(target=chat)
chat_thread.start()

recv_thread = threading.Thread(target=receive)
recv_thread.start()
