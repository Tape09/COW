
import socket
import select
import numpy as np;
from lxml import etree



shared = None;

def make_decision(agent_index):
	global shared;
	
	
def main():
	n_agents = 20;
	password = "1";
	user_prefix = "a"

	sockets = [];
	usernames = [];
	for i in range(n_agents):
		usernames.append(user_prefix + str(i+1));
		sockets.append(socket.socket(socket.AF_INET, socket.SOCK_STREAM));
		# sockets[-1].setblocking(0);
		sockets[-1].connect(("localhost", 12300));
		sockets[-1].send(create_auth_message(usernames[-1],password));
		print("Connecting ", usernames[-1])

		
	while True:
		readable, writable, exceptional = select.select(sockets, sockets, []);
		for s in readable:
			data = s.recv(2**14);
			if(data):				
				# print();
				agent_index = sockets.index(s);
				print("RECEIVED MESSAGE FOR AGENT ", agent_index);
				handle_raw_message(data,agent_index);
				
		
		
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
		
		
def handle_raw_message(data,agent_index):
	root = etree.fromstring(data);
	
	# determine message type
	if(root.attrib["type"] == "request-action"):
		handle_ra(root, agent_index);
	elif(root.attrib["type"] == "sim-start"):
		handle_simstart(root);
	elif(root.attrib["type"] == "auth-response"):
		print("Authenticated!")
	else:
		#nothing?
		print(data)
		print("ERROR: bad message")
		
	
		
		
def handle_simstart(root):
	global shared;
	sim = root.getchildren()[0];
	width = int(sim.attrib["gsizex"]);
	height = int(sim.attrib["gsizey"]);
	x0 = int(sim.attrib["corralx0"]);
	x1 = int(sim.attrib["corralx1"]);
	y0 = int(sim.attrib["corraly0"]);
	y1 = int(sim.attrib["corraly1"]);
	
	shared = SharedMemory(width,height,20);
	shared.set_my_corral(x0,x1,y0,y1);
	print("SIMULATION STARTED")
	print(shared)
	
		
def handle_ra(root,agent_index): # HANDLE DISTANCE TO CORRAL CALCULATIONS HERE?
	global shared;
	perception = root.getchildren()[0];
	x_agent = int(perception.attrib["posx"]);
	y_agent = int(perception.attrib["posy"]);
	
	shared.agents[agent_index] = (x_agent, y_agent);
	shared.cows_in_corral = int(perception.attrib["cowsInCorral"]);
	cells = perception.getchildren();
	
	for c in cells: # NEED TO CONSIDER IMERFECT VISION !!!
		features = [0]*10;
		features[0] = 1; # mark as explored
		
		x = int(c.attrib["x"]) + x_agent;
		y = int(c.attrib["y"]) + y_agent;
		stuff = c.getchildren();
		for s in stuff:
			stype = s.tag;
			if(stype == "fence"):
				if(s.attrib["open"] == "true"):
					features[shared.types["open_fence"]] = 1;
				else:
					features[shared.types["closed_fence"]] = 1;
			elif(stype == "agent"):
				if(s.attrib["type"] == "ally"):
					features[shared.types["my_agent"]] = 1;
				else:
					features[shared.types["enemy_agent"]] = 1;
			elif(stype == "obstacle"):
				features[shared.types["tree"]] = 1;
			elif(stype == "cow"):
				features[shared.types["cow"]] = 1; # COW ID POSSIBLE TO GET BUT DONT DO IT
			elif(stype == "corral"):
				if(s.attrib["type"] == "ally"):
					features[shared.types["my_corral"]] = 1;
				else:
					features[shared.types["enemy_corral"]] = 1;
			elif(stype == "switch"):
				features[shared.types["button"]] = 1;
			
		shared.setmap(x,y,features);
		
		
class SharedMemory:	# NEED TO ADD DIST TO CORRAL
	# fullmap 3rd dimension code:
	# 0 : explored
	# 1 : tree
	# 2 : cows
	# 3 : my agent
	# 4 : enemy agent
	# 5 : button
	# 6 : open fence
	# 7 : closed fence
	# 8 : my corral
	# 9 : enemy corral
	def __init__(self, width, height, n_agents):
		self.width = width;
		self.height = height;
		self.fullmap = np.zeros((width,height,10));
		self.cows_in_corral = 0;
		self.agents = [(0,0)] * n_agents;
		self.types = dict();
		self.types["explored"] = 0;
		self.types["tree"] = 1;
		self.types["cow"] = 2;
		self.types["my_agent"] = 3;
		self.types["enemy_agent"] = 4;
		self.types["button"] = 5;
		self.types["open_fence"] = 6;
		self.types["closed_fence"] = 7;
		self.types["my_corral"] = 8;
		self.types["enemy_corral"] = 9;
		
		# set borders to explored + tree
		for w in range(self.width):
			self.modmap(w,0,"explored",1);
			self.modmap(w,self.height-1,"explored",1);
			self.modmap(w,0,"tree",1);
			self.modmap(w,self.height-1,"tree",1);
			
		for h in range(self.height):
			self.modmap(0,h,"explored",1);
			self.modmap(self.width-1,h,"explored",1);
			self.modmap(w,h,"tree",1);
			self.modmap(self.width-1,h,"tree",1);
	
	def setmap(self,x,y,features):
		self.fullmap[x,y] = features;
	
	def modmap(self,pos,type,val):
		self.fullmap[pos.x,pos.y,self.types[type]] = val;
		
	def modmap(self,x,y,type,val):	
		self.fullmap[x,y,self.types[type]] = val;
		
	def set_my_corral(self,x0,x1,y0,y1):
		for x in range(x0,x1+1):
			for y in range(y0,y1+1):
				self.modmap(x,y,"explored",1);
				self.modmap(x,y,"my_corral",1);

				
	def __str__(self):
		out = "";
		for h in range(self.height):
			for w in range(self.width):
				if(self.fullmap[w,h,self.types["explored"]] == 0):
					# print("?",end="");
					out += "?";
				elif(self.fullmap[w,h,self.types["tree"]] == 1):
					# print("#",end="");
					out += "#";
				elif(self.fullmap[w,h,self.types["my_agent"]] == 1):
					# print("X",end="");
					out += "X";
				elif(self.fullmap[w,h,self.types["enemy_agent"]] == 1):
					# print("E",end="");
					out += "E";
				elif(self.fullmap[w,h,self.types["button"]] == 1):
					# print("O",end="");
					out += "O";
				elif(self.fullmap[w,h,self.types["closed_fence"]] == 1):
					# print("=",end="");
					out += "=";
				elif(self.fullmap[w,h,self.types["my_corral"]] == 1):
					# print(".",end="");
					out += ".";
				elif(self.fullmap[w,h,self.types["enemy_corral"]] == 1):
					# print(",",end="");
					out += ",";
				else:
					# print(" ",end="");
					out += " ";
			out += "\n";
					
		return out;
		
		
		
		
if __name__ == "__main__":
	main();
	


























