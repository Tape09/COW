
import socket
import select
import numpy as np;
import random;
from lxml import etree
import time
import sys;
from queue import Queue, PriorityQueue;

shared = None;

def make_decision(agent_index):
	global shared;
	
	x, y = shared.agents[agent_index];
	moves = shared.valid_moves(agent_index);
	
	
	return (0,0);
	
def end_game():
	global shared;
	print("GAME OVER!")
	print("RESULT:", shared.final_result);
	print("SCORE:", shared.final_score);
	
	
def grid_dist(posA,posB):
	return max(abs(posA[0] - posB[0]), abs(posA[1] - posB[1]));
	
class Node:
	def __init__(self,pos,prev = None):
		self.pos = pos;
		self.prev = prev;
	
def calc_path(posA,posB, limit = 0): # from A to B
	# A star search to find path from A to B
	# return list of positions. excluding posA, includeing posB.
	global shared;
	
	out = [];
	
	visited = set();
	q = PriorityQueue();	
	dist = grid_dist(posA,posB);
	counter = 0;
	q.put( (dist,counter,Node(posA)) );
	counter += 1;
	visited.add(posA);
	
	while not q.empty():
		N = q.get()[2];
		if(N.pos == posB):
			temp = N;
			while temp.prev != None:
				out.append(temp.pos);
				temp = temp.prev;
				
			out.reverse();
			return out, len(out);
			
		neighbors = get_neighbors(N.pos);
		for neighbor in neighbors:
			if(neighbor in visited):
				continue;
			if(shared.free_at(neighbor)):
			# if(free_at_fake(neighbor)):
				dist = grid_dist(neighbor,posB);
				if(limit > 0):
					if(dist > limit):
						continue;
				q.put((dist,counter,Node(neighbor,N)));
				counter += 1;
				visited.add(neighbor);
		
	return out, np.inf;
	

def free_at_fake(pos):
	width = 7;
	height = 7;

	if(pos[0] < 0 or pos[0] >= width):
		return False;
	if(pos[1] < 0 or pos[1] >= height):
		return False;
	
	return(not (pos[1] == 3 and pos[0] > 0));
	
def test_pathfinding():
	posA = (6,0);
	posB = (6,6);
	
	path = calc_path(posA,posB);
	print(len(path),path)
	
	
def get_neighbors(pos):
	out = [None] * 8;
	idx = 0;
	for x in range(-1,2):
		for y in range(-1,2):
			if x==0 and y==0:
				continue;
			out[idx] = (pos[0] + x, pos[1] + y);
			idx += 1;
	return out;
	
def main():
	n_agents = 20;
	
	if(len(sys.argv)<3):
		print("USAGE: cowAgents_old.py user_prefix password")
		sys.exit()
	
	password = sys.argv[2];
	user_prefix = sys.argv[1];

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
		time.sleep(0.01);
		for s in readable:
			data = s.recv(2**15);
			if(data):				
				# print(data);
				agent_index = sockets.index(s);
				print("RECEIVED MESSAGE FOR AGENT", agent_index);
				response = handle_raw_message(data,agent_index);
				if(response):
					if(response == "end"):
						end_game();
						return;
					else:
						s.send(response);
						print("RESPONSE SENT")
				
		

def create_action_message(type,id):
	root = etree.Element("message", type="action")
	action = etree.Element("action", type=type, id=id)
	root.append(action);
	prefix = '<?xml version="1.0" encoding="UTF-8"?>'
	str = etree.tostring(root).decode("UTF-8");
	str = prefix+str;
	str = str.encode("UTF-8")
	str = str + b'\0'
	return str;		
	
		
def create_auth_message(user,pw):
	root = etree.Element("message", type="auth-request")
	auth = etree.Element("authentication", password=pw, username=user)
	root.append(auth);
	prefix = '<?xml version="1.0" encoding="UTF-8"?>'
	str = etree.tostring(root).decode("UTF-8");
	str = prefix+str;
	str = str.encode("UTF-8")
	str = str + b'\0'
	return str;		
		
		
def handle_raw_message(data,agent_index):
	root = etree.fromstring(data);
	
	response = None;
	# determine message type
	if(root.attrib["type"] == "request-action"):
		id = handle_ra(root, agent_index);
		print("HANDLING REQUEST",id);
		move = make_decision(agent_index);
		string_move = shared.move_to_string[move];
		response = create_action_message(string_move,id);
		# print(data);
		# print(response)
		# print();
	elif(root.attrib["type"] == "sim-start"):
		handle_simstart(root);
	elif(root.attrib["type"] == "auth-response"):
		print("Authenticated!")
	elif(root.attrib["type"] == "sim-end"):
		handle_simend(root);
		response = "end";
	else:
		#nothing?
		print(data)
		print("ERROR: bad message")
		
	return response;
	
def handle_simend(root):
	global shared;
	sim = root.getchildren()[0];
	shared.final_score = float(sim.attrib["averageScore"]);
	shared.final_result = sim.attrib["result"];
	
		
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
	
	id = perception.attrib["id"];
	
	shared.agents[agent_index] = (x_agent, y_agent);
	shared.cows_in_corral = int(perception.attrib["cowsInCorral"]);
	cells = perception.getchildren();
	
	for c in cells: # NEED TO CONSIDER IMERFECT VISION !!!
		features = [0]*len(shared.types);
		features[0] = 1; # mark as explored
		features[10] = -1; # mark as unreachable
		
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
				cow_id = int(s.attrib["ID"]) + 1;
				if(cow_id in shared.cows):
					shared.modmap(shared.cows[cow_id],"cow",0);
				shared.cows[cow_id] = (x,y);
				features[shared.types["cow"]] = cow_id;
			elif(stype == "corral"):
				if(s.attrib["type"] == "ally"):
					features[shared.types["my_corral"]] = 1;
					features[shared.types["corral_dist"]] = 0;
				else:
					features[shared.types["enemy_corral"]] = 1;
			elif(stype == "switch"):
				features[shared.types["button"]] = 1;
				fence = [];
				found_fence = False;
				#find fence
				#up
				fx,fy = x,y-1;
				if(shared.feature_at((fx,fy),"open_fence") or shared.feature_at((fx,fy),"closed_fence")):
					while (shared.feature_at((fx,fy),"open_fence") or shared.feature_at((fx,fy),"closed_fence")):
						fence.append((fx,fy));
						fy -= 1;
						found_fence = True;
				
				fx,fy = x,y+1;
				if(not found_fence):
					if(shared.feature_at((fx,fy),"open_fence") or shared.feature_at((fx,fy),"closed_fence")):
						while (shared.feature_at((fx,fy),"open_fence") or shared.feature_at((fx,fy),"closed_fence")):
							fence.append((fx,fy));
							fy += 1;
							found_fence = True;
							
				fx,fy = x-1,y;		
				if(not found_fence):
					if(shared.feature_at((fx,fy),"open_fence") or shared.feature_at((fx,fy),"closed_fence")):
						while (shared.feature_at((fx,fy),"open_fence") or shared.feature_at((fx,fy),"closed_fence")):
							fence.append((fx,fy));
							fx -= 1;
							found_fence = True;		
						
				fx,fy = x+1,y;		
				if(not found_fence):
					if(shared.feature_at((fx,fy),"open_fence") or shared.feature_at((fx,fy),"closed_fence")):
						while (shared.feature_at((fx,fy),"open_fence") or shared.feature_at((fx,fy),"closed_fence")):
							fence.append((fx,fy));
							fx += 1;
							found_fence = True;
							
				if(found_fence):
					shared.buttons[(x,y)] = fence;
				
		shared.setmap(x,y,features);
	shared.update_dists();
	return id;
	
def valid_move(move):
	return (move[0] in [-1,0,1]) and (move[1] in [-1,0,1]);
	
class Objective:
	def __init__(self,type,posA,posB,moves = None):
		self.type = type;
		if(moves == None):
			self.moves = calc_path(posA,posB);
		else:
			self.moves = moves;
		self.goal = posB;
		self.index = 0;

	def next_move(self,my_pos):
		pos = self.moves[self.index];
		move = (pos[0]-my_pos[0], pos[1]-my_pos[1]);
		if shared.free_at(pos) and valid_move(move): #if next move is free and valid
			self.index += 1;
			return move;
		else: # if not free/valid. calc new path
			self.moves, dist = calc_path(my_pos,self.goal);
			if(len(self.moves) == 0):
				return None; #no path exists				
			
			self.index = 0;
			return self.next_move(my_pos);
		
	def complete(self):
		global shared;
		if(len(self.moves) == 0):
			return True;
	
		if(type == "explore"):
			return shared.feature_at(self.moves[-1],"explored");
				
		return True;
	
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
		self.fence_zone_radius = 15;
		
		self.cows_in_corral = 0;
		self.agents = [(0,0)] * n_agents;
		self.objectives = [None] * n_agents;
		self.cows = dict();
		self.types = dict();
		
		self.buttons = dict();		
		
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
		self.types["corral_dist"] = 10;
		
		self.move_to_string = dict();
		self.move_to_string[(0,0)] = "skip";
		self.move_to_string[(0,1)] = "south";
		self.move_to_string[(0,-1)] = "north";
		self.move_to_string[(1,0)] = "east";
		self.move_to_string[(-1,0)] = "west";
		self.move_to_string[(1,1)] = "southeast";
		self.move_to_string[(-1,-1)] = "northwest";
		self.move_to_string[(-1,1)] = "southwest";
		self.move_to_string[(1,-1)] = "northeast";
		
		self.block = np.array([0,1,1,1,1,1,0,1,0,0,0]);
		
		self.fullmap = np.zeros((width,height,len(self.types)));
		self.fullmap[:,:,self.types["corral_dist"]] -= 1;
		
		self.corral_x0 = None;
		self.corral_x1 = None;
		self.corral_y0 = None;
		self.corral_y1 = None;
		
		self.final_score = None;
		self.final_result = None;
		
		# set borders to explored + tree # NO; BAD
		# for w in range(self.width):
			# self.modmap((w,0),"explored",1);
			# self.modmap((w,self.height-1),"explored",1);
			# self.modmap((w,0),"tree",1);
			# self.modmap((w,self.height-1),"tree",1);
			
		# for h in range(self.height):
			# self.modmap((0,h),"explored",1);
			# self.modmap((self.width-1,h),"explored",1);
			# self.modmap((0,h),"tree",1);
			# self.modmap((self.width-1,h),"tree",1);
	
	def inside_map(self,pos):
		if(pos[0] < 0 or pos[0] >= self.width ):
			return False;
		if(pos[1] < 0 or pos[1] >= self.height ):
			return False;
		return True;
	
	def setmap(self,x,y,features):
		self.fullmap[x,y] = features;
	
	def modmap(self,pos,type,val):
		self.fullmap[pos[0],pos[1],self.types[type]] = val;
		
	def feature_at(self,pos,feature):
		if(self.inside_map(pos)):
			return (self.fullmap[pos[0],pos[1],self.types[feature]]);
		else:
			return False;
		
	def at(self, pos):
		return self.fullmap[pos[0],pos[1]];
		
	def free_at(self,pos):
		if(pos[0] < 0 or pos[0] >= self.width ):
			return False;
		if(pos[1] < 0 or pos[1] >= self.height ):
			return False;
		return not np.dot(self.at(pos),self.block);
		
	def find_nearest(self,pos,type, inverse = False, limit = 0):
		visited = set();
		q = Queue();
		
		out = [];
		
		q.put((Node(pos),0));
		visited.add(pos);
		
		while not q.empty():
			N, dist = q.get();
			
			if(limit > 0):
				if(dist > limit):
					break;
			
			if(bool(inverse) != bool(self.feature_at(N.pos,type) > 0)): #found feature
				temp = N;
				while temp.prev != None:
					out.append(temp.pos);
					temp = temp.prev;
					
				out.reverse();
				return out, len(out);
			
			
			neighbors = get_neighbors(N.pos);
			random.shuffle(neighbors)
			for neighbor in neighbors:
				if(neighbor in visited):
					continue;
				if(shared.free_at(neighbor)):
					q.put((Node(neighbor,N),dist+1));
					visited.add(neighbor);			
		return out, np.inf;
		
		
	def valid_moves(self, idx):
		moves = [];
		moves.append((0,0));
		
		pos = self.agents[idx];
		
		for dx in range(-1,2):
			for dy in range(-1,2):
				newpos = (pos[0] + dx, pos[1] + dy);
				if(newpos[0] < 0 or newpos[0] >= self.width ):
					continue;
				if(newpos[1] < 0 or newpos[1] >= self.height ):
					continue;
					
				if(self.free_at(newpos)):
					moves.append((dx,dy));
		
		return moves;
					
		
	def set_my_corral(self,x0,x1,y0,y1):
		self.corral_x0 = x0;
		self.corral_x1 = x1;
		self.corral_y0 = y0;
		self.corral_y1 = y1;
		for x in range(x0,x1+1):
			for y in range(y0,y1+1):
				self.modmap((x,y),"explored",1);
				self.modmap((x,y),"my_corral",1);
				self.modmap((x,y),"corral_dist",0);

				
	def __str__(self):
		out = "";
		for h in range(self.height):
			for w in range(self.width):
				if(self.fullmap[w,h,self.types["explored"]] == 0):
					# print("?",end="");
					out += "?";
				elif(self.fullmap[w,h,self.types["tree"]] >= 1):
					# print("#",end="");
					out += "#";
				elif(self.fullmap[w,h,self.types["my_agent"]] >= 1):
					# print("X",end="");
					out += "X";
				elif(self.fullmap[w,h,self.types["enemy_agent"]] >= 1):
					# print("E",end="");
					out += "E";
				elif(self.fullmap[w,h,self.types["button"]] >= 1):
					# print("O",end="");
					out += "B";
				elif(self.fullmap[w,h,self.types["cow"]] >= 1):
					# print("O",end="");
					out += "ö";
				elif(self.fullmap[w,h,self.types["closed_fence"]] >= 1):
					# print("=",end="");
					out += "=";
				elif(self.fullmap[w,h,self.types["my_corral"]] >= 1):
					# print(".",end="");
					out += ".";
				elif(self.fullmap[w,h,self.types["enemy_corral"]] >= 1):
					# print(",",end="");
					out += ",";
				else:
					# print(" ",end="");
					out += " ";
			out += "\n";
					
		return out;
		
		
		
	def update_dists(self):
		explored = set();
		explore_q = Queue();
		
		start_x = int((self.corral_x0 + self.corral_x1) / 2);
		start_y = int((self.corral_y0 + self.corral_y1) / 2);
		start_pos = (start_x, start_y);
		
		explored.add(start_pos);		
		explore_q.put(start_pos);
		

		while not explore_q.empty():
			base_pos = explore_q.get();
			# print(base_pos);
			# print(shared.at(base_pos));
			base_dist = shared.feature_at(base_pos,"corral_dist");
			dist = base_dist + 1;			
			# get neighbors
			for dx in range(-1,2):
				x = base_pos[0] + dx;
				if(x < 0 or x >= shared.width): #if outside map
					continue;
					
				for dy in range(-1,2):					
					y = base_pos[1] + dy;
					if(y < 0 or y >= shared.height): #if outside map
						continue;
					
					pos = (x,y);
					if(pos in explored): #if already explored
						continue;
					
					explored.add(pos);
					
					if(shared.feature_at(pos,"explored") == 0):
						shared.modmap(pos, "corral_dist", -1);
						continue;					
						
					if(shared.feature_at(pos,"tree") >= 1): #if tree = no dist
						shared.modmap(pos, "corral_dist", -1);
						continue;
						
					if(shared.feature_at(pos,"button") >= 1): #if button = no dist
						shared.modmap(pos, "corral_dist", -1);
						continue;

					old_dist = shared.feature_at(pos,"corral_dist");
					
					explore_q.put(pos);
					
					if(old_dist < 0):
						shared.modmap(pos, "corral_dist", dist);
					else:						
						shared.modmap(pos, "corral_dist", min(dist, old_dist));
					
					

		
if __name__ == "__main__":
	main();
	


























