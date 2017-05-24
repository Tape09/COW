import numpy as np
from util import Node,get_neighbors
from queue import Queue, PriorityQueue
from scipy.signal import convolve2d
import random


class HerdTeam:
    def __init__(self, agents = None, cows = None):
        if agents:
            self.agents = agents;
        else:
            self.agents = [];
            
        if cows:
            self.cows = cows;
        else:
            self.cows = [];
        
    def has_agent(self, id):
        return id in self.agents;
        
    def has_cow(self, id):
        return id in cows;
        
    def add_agent(self, id):
        self.agents.append(id);
        
    def remove_agent(self,id):
        if(self.has_agent(id)):
            self.agents.remove(id);
            
    def remove_cow(self,id):
        if(self.has_cow(id)):
            self.cows.remove(id);
        
    def add_cow(self, id):
        self.cows.append(id);
        
    def n_agents(self):
        return len(self.agents);
        
    def n_cows(self):
        return len(self.cows);
    


shared = None
class SharedMemory:  # NEED TO ADD DIST TO CORRAL
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
        self.fence_zone_radius = 8;

        self.cows_in_corral = 0;
        self.agents = [(0, 0)] * n_agents;
        self.objectives = [None] * n_agents;
        self.cows = dict();
        
        
        # self.herd_team_size = 10;
        
        self.herd_teams = [HerdTeam(), HerdTeam()];

        self.buttons = dict();

        self.request_ids = set();
        self.iteration = 0;
        
        self.herd_diameter = 7;
        self.herd_radius = self.herd_diameter // 2;
        self.herd_threshold = 5;
        self.herds = []; # herd center -> list of cow IDs
        
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
        self.types["corral_dist"] = 10;

        self.move_to_string = dict();
        self.move_to_string[(0, 0)] = "skip";
        self.move_to_string[(0, 1)] = "south";
        self.move_to_string[(0, -1)] = "north";
        self.move_to_string[(1, 0)] = "east";
        self.move_to_string[(-1, 0)] = "west";
        self.move_to_string[(1, 1)] = "southeast";
        self.move_to_string[(-1, -1)] = "northwest";
        self.move_to_string[(-1, 1)] = "southwest";
        self.move_to_string[(1, -1)] = "northeast";

        self.block = np.array([0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0]);
        self.static_block = np.array([0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0]);

        self.fullmap = np.zeros((width, height, len(self.types)));
        self.fullmap[:, :, self.types["corral_dist"]] -= 1;

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
    def random_pos(self):
        x = np.random.randint(1,self.width-1);
        y = np.random.randint(1,self.height-1);        
        while not self.free_at((x,y)):
            x = np.random.randint(1,self.width-1);
            y = np.random.randint(1,self.height-1);
            
        return (x,y);
    
    def get_agent_idx(self, agent_pos):
        for idx, pos in enumerate(self.agents):
            if (pos == agent_pos):
                return (idx);
        return None;

    def fence_zone(self, button):
        if (len(self.buttons[button]) == 0):
            return None;

        x_borders = [0, 0];
        x_borders[0] = self.buttons[button][0][0];
        x_borders[1] = self.buttons[button][-1][0];

        y_borders = [0, 0];
        y_borders[0] = self.buttons[button][0][1];
        y_borders[1] = self.buttons[button][-1][1];

        x_min = min(x_borders);
        x_max = max(x_borders);

        y_min = min(y_borders);
        y_max = max(y_borders);

        x_min -= self.fence_zone_radius;
        x_max += self.fence_zone_radius;

        y_min -= self.fence_zone_radius;
        y_max += self.fence_zone_radius;

        return (x_min, x_max, y_min, y_max);

    def inside_map(self, pos):
        if (pos[0] < 0 or pos[0] >= self.width):
            return False;
        if (pos[1] < 0 or pos[1] >= self.height):
            return False;
        return True;

    def setmap(self, x, y, features):
        self.fullmap[x, y] = features;

    def modmap(self, pos, type, val):
        self.fullmap[pos[0], pos[1], self.types[type]] = val;

    def feature_at(self, pos, feature):
        if (self.inside_map(pos)):
            return (self.fullmap[pos[0], pos[1], self.types[feature]]);
        else:
            return False;

    def at(self, pos):
        return self.fullmap[pos[0], pos[1]];

    def free_at(self, pos, static=False):
        if (pos[0] < 0 or pos[0] >= self.width):
            return False;
        if (pos[1] < 0 or pos[1] >= self.height):
            return False;
            
        if static:
            return not np.dot(self.at(pos), self.static_block);
        else:
            return not np.dot(self.at(pos), self.block);

    def find_nearest(self, pos, type, inverse=False, limit=0):
        visited = set();
        q = Queue();

        out = [];

        q.put((Node(pos), 0));
        visited.add(pos);

        while not q.empty():
            N, dist = q.get();

            if (limit > 0):
                if (dist > limit):
                    break;

            if (bool(inverse) != bool(self.feature_at(N.pos, type) > 0)):  # found feature
                temp = N;
                while temp.prev != None:
                    out.append(temp.pos);
                    temp = temp.prev;

                out.reverse();
                return out, len(out);

            neighbors = get_neighbors(N.pos);
            random.shuffle(neighbors)
            for neighbor in neighbors:
                if (neighbor in visited):
                    continue;
                if (bool(inverse) != bool(self.feature_at(neighbor, type) > 0)):  # found feature
                    temp = Node(neighbor, N);
                    while temp.prev != None:
                        out.append(temp.pos);
                        temp = temp.prev;

                    out.reverse();
                    return out, len(out);
                if (shared.free_at(neighbor)):
                    q.put((Node(neighbor, N), dist + 1));
                    visited.add(neighbor);
        return out, np.inf;

    def get_blob(self, pos, limit=10, static = True): # returns a set of positions that are distance <= limit from pos.
        visited = set();
        edge_points = set();
        q = Queue();

        out = [];

        q.put((Node(pos), 0));
        visited.add(pos);

        while not q.empty():
            N, dist = q.get();

            if (limit > 0):
                if (dist >= limit):
                    edge_points.add(N);
                    continue;

            neighbors = get_neighbors(N.pos);
            random.shuffle(neighbors)
            for neighbor in neighbors:
                if (neighbor in visited):
                    continue;
                
                if (shared.free_at(neighbor,static = static)):
                    q.put((Node(neighbor, N), dist + 1));
                    visited.add(neighbor);
        return visited, edge_points;
        
        
    def valid_moves(self, idx):
        moves = [];
        moves.append((0, 0));

        pos = self.agents[idx];

        for dx in range(-1, 2):
            for dy in range(-1, 2):
                newpos = (pos[0] + dx, pos[1] + dy);
                if (newpos[0] < 0 or newpos[0] >= self.width):
                    continue;
                if (newpos[1] < 0 or newpos[1] >= self.height):
                    continue;

                if (self.free_at(newpos)):
                    moves.append((dx, dy));

        return moves;

    def set_my_corral(self, x0, x1, y0, y1):
        self.corral_x0 = x0;
        self.corral_x1 = x1;
        self.corral_y0 = y0;
        self.corral_y1 = y1;
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                self.modmap((x, y), "explored", 1);
                self.modmap((x, y), "my_corral", 1);
                self.modmap((x, y), "corral_dist", 0);

    def __str__(self):
        out = "";
        for h in range(self.height):
            for w in range(self.width):
                if (self.fullmap[w, h, self.types["explored"]] == 0):
                    # print("?",end="");
                    out += "?";
                elif (self.fullmap[w, h, self.types["tree"]] >= 1):
                    # print("#",end="");
                    out += "#";
                elif (self.fullmap[w, h, self.types["my_agent"]] >= 1):
                    # print("X",end="");
                    out += "X";
                elif (self.fullmap[w, h, self.types["enemy_agent"]] >= 1):
                    # print("E",end="");
                    out += "E";
                elif (self.fullmap[w, h, self.types["button"]] >= 1):
                    # print("O",end="");
                    out += "B";
                elif (self.fullmap[w, h, self.types["cow"]] >= 1):
                    # print("O",end="");
                    out += "ö";
                elif (self.fullmap[w, h, self.types["closed_fence"]] >= 1):
                    # print("=",end="");
                    out += "=";
                elif (self.fullmap[w, h, self.types["my_corral"]] >= 1):
                    # print(".",end="");
                    out += ".";
                elif (self.fullmap[w, h, self.types["enemy_corral"]] >= 1):
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
            base_dist = shared.feature_at(base_pos, "corral_dist");
            dist = base_dist + 1;
            # get neighbors
            for dx in range(-1, 2):
                x = base_pos[0] + dx;
                if (x < 0 or x >= shared.width):  # if outside map
                    continue;

                for dy in range(-1, 2):
                    y = base_pos[1] + dy;
                    if (y < 0 or y >= shared.height):  # if outside map
                        continue;

                    pos = (x, y);
                    if (pos in explored):  # if already explored
                        continue;

                    explored.add(pos);

                    if (shared.feature_at(pos, "explored") == 0):
                        shared.modmap(pos, "corral_dist", -1);
                        continue;

                    if (shared.feature_at(pos, "tree") >= 1):  # if tree = no dist
                        shared.modmap(pos, "corral_dist", -1);
                        continue;

                    if (shared.feature_at(pos, "button") >= 1):  # if button = no dist
                        shared.modmap(pos, "corral_dist", -1);
                        continue;

                    old_dist = shared.feature_at(pos, "corral_dist");

                    explore_q.put(pos);

                    if (old_dist < 0):
                        shared.modmap(pos, "corral_dist", dist);
                    else:
                        shared.modmap(pos, "corral_dist", min(dist, old_dist));

    def update_herds(self):
        self.herds = []; # reset herd list
        cowmap = self.fullmap[:,:,self.types["cow"]]; # cow layer
        cowmap = cowmap > 0; # 1 is cow 0 is not cow        
        filter = np.ones((self.herd_diameter,self.herd_diameter));
        
        filtered = convolve2d(cowmap,filter,mode = "same", boundary = "fill");
        filtered = filtered >= self.herd_threshold; # 1 is center of herd that is larger than herd threshold
        
        for x in range(filtered.shape[0]):
            for y in range(filtered.shape[1]):
                if(filtered[x,y]): # if herd here
                    zone = [x - self.herd_radius, x + self.herd_radius, y - self.herd_radius, y + self.herd_radius];
                    zone_cows = self.cows_in_zone(zone);
                    
                    self.herds.append( zone_cows);
        
        
        
    def cows_in_zone(self,zone):
        out = [];
        
        for x in range(zone[0],zone[1]+1):
            for y in range(zone[2],zone[3]+1):
                cow = self.feature_at((x,y),"cow");
                if(cow):
                    out.append(cow);
        return out;
        
        