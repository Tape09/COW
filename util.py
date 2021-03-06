from queue import Queue, PriorityQueue
import numpy as np
import random

class Node:
    def __init__(self, pos, prev=None):
        self.pos = pos;
        self.prev = prev;


def valid_move(move):
    return (move[0] in [-1, 0, 1]) and (move[1] in [-1, 0, 1]);


def make_zone(pos, radius):
    zone = [pos[0] - radius, pos[0] + radius, pos[1] - radius, pos[1] + radius];
    return zone;
    
def point_in_zone(pos, zone):
    # checks if pos is inside zone (inclusive)
    # zone is a rectangle defined as (x0,x1,y0,y1);
    return pos[0] >= zone[0] and pos[0] <= zone[1] and pos[1] >= zone[2] and pos[1] <= zone[3];


def calc_path(posA, posB, limit=0, static = False, extra_block = None):  # from A to B
    import sharedMemory as sm

    # A star search to find path from A to B
    # return list of positions. excluding posA, includeing posB.
    # global shared;

    out = [];

    visited = set();
    q = PriorityQueue();
    dist = grid_dist(posA, posB);
    counter = 0;
    q.put((dist, counter, Node(posA)));
    counter += 1;
    visited.add(posA);

    while not q.empty():
        N = q.get()[2];
        if (N.pos == posB):
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
            free = sm.shared.free_at(neighbor, static = static);
            for i in range(len(sm.shared.herd_teams)):
                if sm.shared.herd_teams[i].blocking(neighbor):
                    free = False;
                    break;
            if(extra_block):
                for p in extra_block:
                    if neighbor == p:
                        free = False;
                        break;
            if (free):
                # if(free_at_fake(neighbor)):
                dist = grid_dist(neighbor, posB);
                if (limit > 0):
                    if (dist > limit):
                        continue;
                q.put((dist, counter, Node(neighbor, N)));
                counter += 1;
                visited.add(neighbor);

    return out, np.inf;

def calc_path_to(posA, posB, limit=0, static = False, extra_block = None):  # from A to B
    import sharedMemory as sm

    # A star search to find path from A to B
    # return list of positions. excluding posA, includeing posB.
    # global shared;

    out = [];

    visited = set();
    q = PriorityQueue();
    dist = grid_dist(posA, posB);
    counter = 0;
    q.put((dist, counter, Node(posA)));
    counter += 1;
    visited.add(posA);

    while not q.empty():
        N = q.get()[2];
        if (N.pos == posB):
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
            if(neighbor == posB):
                temp = Node(neighbor,N);
                while temp.prev != None:
                    out.append(temp.pos);
                    temp = temp.prev;

                out.reverse();
                return out, len(out);
                
            free = sm.shared.free_at(neighbor, static = static);
            for i in range(len(sm.shared.herd_teams)):
                if sm.shared.herd_teams[i].blocking(neighbor):
                    free = False;
                    break;
            if(extra_block):
                for p in extra_block:
                    if neighbor == p:
                        free = False;
                        break;
            if (free):
                dist = grid_dist(neighbor, posB);
                if (limit > 0):
                    if (dist > limit):
                        continue;
                q.put((dist, counter, Node(neighbor, N)));
                counter += 1;
                visited.add(neighbor);

    return out, np.inf;
    

def free_at_fake(pos):
    width = 7;
    height = 7;

    if (pos[0] < 0 or pos[0] >= width):
        return False;
    if (pos[1] < 0 or pos[1] >= height):
        return False;

    return (not (pos[1] == 3 and pos[0] > 0));


def test_pathfinding():
    posA = (6, 0);
    posB = (6, 6);

    path = calc_path(posA, posB);
    print(len(path), path)


def get_neighbors(pos):
    out = [None] * 8;
    idx = 0;
    for x in range(-1, 2):
        for y in range(-1, 2):
            if x == 0 and y == 0:
                continue;
            out[idx] = (pos[0] + x, pos[1] + y);
            idx += 1;
    return out;


def end_game():
    import sharedMemory as sm

    # global shared;
    print("GAME OVER!")
    print("RESULT:", sm.shared.final_result);
    print("SCORE:", sm.shared.final_score);


def grid_dist(posA, posB):
    return max(abs(posA[0] - posB[0]), abs(posA[1] - posB[1]));

def mean_pos(positions):
    x = 0;
    y = 0;
    for pos in positions:
        x += pos[0];
        y += pos[1];
        
    x = int(x / len(positions));
    y = int(y / len(positions));
    
    return (x,y);
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    