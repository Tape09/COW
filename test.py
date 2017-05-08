
import socket
import select
from lxml import etree
import time


def create_auth_message(user,pw):
	root = etree.Element("message", type="auth-request")
	auth = etree.Element("authentication", password="1", username="a1")
	root.append(auth);
	prefix = '<?xml version="1.0" encoding="UTF-8"?>'
	str = etree.tostring(root).decode("UTF-8");
	str = prefix+str;
	str = str.encode("UTF-8")
	str = str + b'\0'
	return str;		

	

n_agents = 20;
password = "1";
user_prefix = "a"

sockets = [];
usernames = [];
for i in range(20):
	usernames.append(user_prefix + str(i+1));
	sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM));
	# sockets[-1].setblocking(0);
	sockets[-1].connect(("localhost", 12300));
	sockets[-1].send(create_auth_message(usernames[-1],password));
	print("Connecting ", usernames[-1])

	
gdata = "";
while True:
	readable, writable, exceptional = select.select(sockets, sockets, []);
	for s in readable:
		data = s.recv(2**14);
		if(data):
			print(data);
			print();
			gdata = data;

		

		
		
# def handle_raw_message(data):
	
		
		
		
		
		
		
		
		
		
		
		
		
		
		

# if __name__ == "__main__":
	# main();
	


























