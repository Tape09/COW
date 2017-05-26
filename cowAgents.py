import sharedMemory as sm
from util import  *
from objectives import *
import random


sm.shared = None;


def before_each_round():    
    sm.shared.update_dists();
    sm.shared.update_herds();
    print("ITERATION: ",sm.shared.iteration)
    
    # assign button bitch
    # iterate over buttons we have seen
    for button in sm.shared.buttons:
        zone = sm.shared.fence_zone(button);#rect around fence
        if (zone == None):#don't where the fence is yet
            continue;
        if (len(sm.shared.buttons[button]) == 0):#button without fence
            continue;
        if (not sm.shared.feature_at(sm.shared.buttons[button][0], "closed_fence")):#if the fence is open, continue
            continue;
	    #if any agent is trying to control the button
        skip = False;
        for objective in sm.shared.objectives:
            if objective == None:
                continue;
            if objective.type == "button":
                if objective.button == button:
                    skip = True;
                    break;
		#there is already an agent working on this
        if (skip):
            continue;

        # if close to a closed fence

            # push_button = False;
            # # check if other agents in zone
            # for i, apos in enumerate(sm.shared.agents):
            #     if (i == agent_index):
            #         continue;
            #     if (point_in_zone(apos, zone)):
            #         push_button = True;
            #         break;

        push_button = True
        if (push_button):
            # select nearest agent to corresponding button
            path, dist = sm.shared.find_nearest(button, "my_agent", limit=50);
            if (len(path) == 0):
                continue;
            agent_pos = path[-1];
            path = path[:-1];
            path.reverse();

            if (len(path) == 0):
                continue;

            end_point = path[-1];
            if (not (end_point[0] == button[0] or end_point[1] == button[1])):
                new_ends = [(end_point[0] + 1, end_point[1]), (end_point[0] - 1, end_point[1]),
                            (end_point[0], end_point[1] + 1), (end_point[0], end_point[1] - 1)];
                good_end = False;
                for new_end in new_ends:
                    if (sm.shared.feature_at(new_end, "closed_fence") or sm.shared.feature_at(new_end, "open_fence")):
                        continue;
                    if (new_end[0] == button[0] or new_end[1] == button[1]):
                        good_end = True;
                        path.append(new_end);
                if (not good_end):
                    continue;
            agent_idx = sm.shared.get_agent_idx(agent_pos);
            if (agent_idx == None):
                continue;
            # set selected agents objective to "button"
            relink_followers(agent_idx);
            sm.shared.objectives[agent_idx] = ObjectiveButton(agent_idx, path[-1], button, moves=path);
            
            for j in range(len(sm.shared.herd_teams)):
                sm.shared.herd_teams[j].remove_agent(agent_idx);
           

            for i, pos in enumerate(sm.shared.agents):  # check if another agent is already going for this btton
                if (i == agent_idx):
                    continue;
                if (sm.shared.objectives[i] != None):
                    if (sm.shared.objectives[i].type == "button"):
                        if (sm.shared.objectives[i].button == button):
                            sm.shared.objectives[i] = None;
    
    ###################################
    # after initial exploration: team up!
    if(sm.shared.iteration > 20):
        jobless_agents = [];
        
        for i, pos in enumerate(sm.shared.agents): # agent is jobless if its not part of a team, not pushing a button, not moving, or has no objective
            skip = False;
            for j in range(len(sm.shared.herd_teams)):
                if(sm.shared.herd_teams[j].has_agent(i)):
                    skip = True;
                    break;
            if skip:
                continue;              
            
            if(sm.shared.objectives[i] != None):
                if(sm.shared.objectives[i].type == "button"):
                    continue;
    
            jobless_agents.append(i);
        
        random.shuffle(jobless_agents);
        while len(jobless_agents): # add jobless agents one by one randomly to the smallest team.
            smallest_team_idx = 0;
            smallest_team_size = 999;
            for j in range(len(sm.shared.herd_teams)):
                if(sm.shared.herd_teams[j].n_agents() < smallest_team_size):
                    smallest_team_size = sm.shared.herd_teams[j].n_agents();
                    smallest_team_idx = j;
            agent = jobless_agents.pop();
            sm.shared.herd_teams[smallest_team_idx].add_agent(agent);

    ##################################### 
    for i in range(len(sm.shared.herd_teams)):
        if sm.shared.herd_teams[i].herding or sm.shared.herd_teams[i].approaching:
            if(sm.shared.herd_teams[i].n_cows() < sm.shared.herd_size_threshold):
                sm.shared.herd_teams[i].reset_cows();
    
    
    fail = False;
    if(sm.shared.iteration > 50):
        # if team is not herding, find a herd and set the objective
        for i in range(len(sm.shared.herd_teams)):
            if not sm.shared.herd_teams[i].herding and not sm.shared.herd_teams[i].approaching:
                # find a herd
                herd = sm.shared.get_n_herds(1)[0];
                if len(herd) == 0:
                    fail = True;
                    break;
                    
                sm.shared.herd_teams[i].cows = herd;
                sm.shared.herd_teams[i].approaching = True;
                
                
        sm.shared.update_herds();
        
        # if approaching, find behind position and set leader to go there
        for i in range(len(sm.shared.herd_teams)):
            if sm.shared.herd_teams[i].approaching:
                # if finished approaching 
                leader = sm.shared.herd_teams[i].agents[0];
                if(sm.shared.objectives[leader] != None):
                    if(sm.shared.objectives[leader].type == "move_lazy"):
                        if(sm.shared.objectives[leader].complete()):
                            # finished moving to target
                            sm.shared.herd_teams[i].approaching = False;
                            sm.shared.herd_teams[i].herding = True;
                            continue;
                            
                # if not finished, set target and objective
                found_target = False;
                for p in reversed(sm.shared.herd_teams[i].perimeter_list):
                    if(sm.shared.free_at(p,True)):
                        found_target = True;
                        target_position = p;
                        break;
        
                if not found_target:
                    sm.shared.herd_teams[i].reset_cows();
                    fail = True;
                    continue;
                    
                
                sm.shared.objectives[leader] = ObjectiveMoveLazy(leader,target_position);
                # check again if finished
                if(sm.shared.objectives[leader].complete()):
                    sm.shared.herd_teams[i].approaching = False;
                    sm.shared.herd_teams[i].herding = True;
                    continue;
        
        

    # Team objectives
    for i in range(len(sm.shared.herd_teams)):
        if sm.shared.herd_teams[i].n_agents() <= 1:
            continue;
        leader = sm.shared.herd_teams[i].agents[0];
        # if team is not approaching and not herding, set leader to explore, and rest to follow
        if not sm.shared.herd_teams[i].herding and not sm.shared.herd_teams[i].approaching:
            sm.shared.herd_teams[i].reset_cows();
            sm.shared.objectives[leader] = ObjectiveExplore(leader);
            for j,agent in enumerate(sm.shared.herd_teams[i].agents):
                # skip leader
                if(j == 0):
                    continue;
                sm.shared.objectives[agent] = ObjectiveFollow(agent,sm.shared.herd_teams[i].agents[j-1]);
          
        # if team is approaching, set followers to follow
        if sm.shared.herd_teams[i].approaching:
            for j,agent in enumerate(sm.shared.herd_teams[i].agents):
                # skip leader
                if(j == 0):
                    continue;
                sm.shared.objectives[agent] = ObjectiveFollow(agent,sm.shared.herd_teams[i].agents[j-1]);        
        
        # if team is herding, set all agents to go to designated spots along perimeter
        if sm.shared.herd_teams[i].herding:
            perimeter = sm.shared.herd_teams[i].perimeter_list.copy();
            random.shuffle(perimeter);
            
            if len(perimeter) > sm.shared.herd_teams[i].n_agents():
                n = sm.shared.herd_teams[i].n_agents();
            else:
                n = len(perimeter);
                
            target_points = [perimeter[z] for z in range(n)];
            # calculate all dists to agents
            # assign minimum max dist
            dist_map = [[0 for x in range(sm.shared.herd_teams[i].n_agents())] for y in range(n)];
            # path_map = [[0 for x in range(sm.shared.herd_teams[i].n_agents())] for y in range(n)];
            
            for target in range(n):
                for ag in range(sm.shared.herd_teams[i].n_agents()):
                    agent = sm.shared.herd_teams[i].agents[ag];
                    agent_pos = sm.shared.agents[agent];
                    # path,dist = calc_path(agent_pos,target_points[target],static = True);
                    dist = grid_dist(agent_pos,target_points[target]);
                    dist_map[target][ag] = dist;
                    # path_map[target][ag] = path;
                        
            assigned_ag = [];
            assigned_target = [];
            for u in range(n):            
                minvals = [];
                for t in range(n):
                    if(t in assigned_target):
                        minvals.append(-1);
                        continue;
                        
                    minval = np.inf;
                    for a in range(len(dist_map[t])):
                        if a in assigned_ag:
                            continue;
                        if(dist_map[t][a] < minval):
                            minval = dist_map[t][a];
                    
                    
                    if(minval == np.inf):
                        minvals.append(-1);
                    else:
                        minvals.append(minval);
                    
                maxval = -1;
                for t in range(n):
                    if(minvals[t] > maxval):
                        maxval = minvals[t];
                        best_t = t;
                        
                if(maxval >= 0 and not maxval == np.inf):
                    # best_a = np.argmin(dist_map[best_t]);
                    minval = np.inf;
                    for a in range(len(dist_map[t])):
                        if a in assigned_ag:
                            continue;
                        if(dist_map[t][a] < minval):
                            minval = dist_map[t][a];
                            best_a = a;
                    
                    assigned_target.append(best_t);
                    assigned_ag.append(best_a);
                
            for j in range(len(assigned_ag)):
                ag = assigned_ag[j];
                agent = sm.shared.herd_teams[i].agents[ag];
                agent_pos = sm.shared.agents[agent];
                t = assigned_target[j];
                target = target_points[t];
                
                path,dist = calc_path(agent_pos,target,static = True);
                sm.shared.objectives[agent] = ObjectiveMove(agent,target,path);
        
            assigned_agents = [sm.shared.herd_teams[i].agents[j] for j in assigned_ag];
            for agent in sm.shared.herd_teams[i].agents:
                if (not agent in assigned_agents):
                    sm.shared.objectives[agent] = ObjectiveStandStill();
            
            # print("FREEEZER")
            # for j,agent in enumerate(sm.shared.herd_teams[i].agents):
                # sm.shared.objectives[agent] = ObjectiveStandStill();
    
        
    
    

def make_decision(agent_index):
    x, y = sm.shared.agents[agent_index];
    moves = sm.shared.valid_moves(agent_index);
    

    has_objective = (sm.shared.objectives[agent_index] != None) and (not sm.shared.objectives[agent_index].complete());

    # if(sm.shared.objectives[agent_index] != None):    
        # if(sm.shared.objectives[agent_index].type == "follow"):
            # print("PAPSPFOAS");
    
    # TESTING STUFF ##########
    
    # if(sm.shared.iteration > 10):
        # if(sm.shared.objectives[agent_index].type != "button"):
            # if(agent_index != 0):
                # for i in range(20):
                    # follow_id = (agent_index + i + 1) % 20;
                    # if(sm.shared.objectives[follow_id].type == "button"):
                        # continue;
                    # else:
                        # break;
                # sm.shared.objectives[agent_index] = ObjectiveFollow(agent_index,follow_id);
                
       
    
       
    # if(sm.shared.iteration > 30):
        # free = False;
        # if(sm.shared.objectives[agent_index] == None):
            # free = True;
        # elif(sm.shared.objectives[agent_index].type == "explore"):
            # free = True;
        
        # # check if there are any herds
        # if(len(sm.shared.herds) > 0 and free):       
            # # pick closest herd to corral and check if path exists from herd center to corral
            # herd_idx = -1;
            # min_dist = 999999;
            # for i,herd in enumerate(sm.shared.herds):
                # cows_pos = [sm.shared.cows[cow] for cow in herd ];
                # center = mean_pos(cows_pos);
                # dist = sm.shared.feature_at(center,"corral_dist");
                # if(dist >= 0):
                    # if(dist < min_dist):
                        # min_dist = dist;
                        # herd_idx = i;
            
            # if (herd_idx != -1):
                # # if found a good herd. assign agents to herd the cows in the herd
                # # get blob;
                # cows_pos = [sm.shared.cows[cow] for cow in sm.shared.herds[herd_idx] ];
                # center = mean_pos(cows_pos);
                # blob, edge = sm.shared.get_blob(center,limit=7);
                
                # #max dist position inside blob;
                # max_dist = -11;
                # max_pos = (0,0);
                # for pos in blob:                
                    # if(sm.shared.feature_at(pos,"corral_dist") > 0):
                        # if(sm.shared.feature_at(pos,"corral_dist") > max_dist):
                            # max_dist = sm.shared.feature_at(pos,"corral_dist");
                            # max_pos = pos;
                
                
                # for i,pos in enumerate(sm.shared.agents):
                    # reassign_agent = False;
                    # if(sm.shared.objectives[i] == None):
                        # reassign_agent = True;
                    # elif(sm.shared.objectives[i].type == "explore"):
                        # reassign_agent = True;
                        
                    # if(reassign_agent):
                        # sm.shared.objectives[i] = ObjectiveMove(i,max_pos);
            
        
    # assign agents to herd - remember cow IDs
    
    # calculate blob around herd center
    
    # get 10 highest distance points in blob
    
    # assign 10 nearest agents to 10 nearest points
    
    
    
    ##########################
    

    # try explore
    if (not has_objective):
        sm.shared.objectives[agent_index] = ObjectiveExplore(agent_index);
        if(not sm.shared.objectives[agent_index].complete()):
            has_objective = True;

    if (not has_objective):  # failed to explore
        my_move = random.choice(moves);
    else:  # has objective
        my_move = sm.shared.objectives[agent_index].next_move();

    # if(sm.shared.objectives[agent_index] != None):    
        # if(sm.shared.objectives[agent_index].type == "follow"):
            # print(my_move);
    
    # something went wrong (path blocked or something) and objective became impossible
    if (my_move == None):
        my_move = random.choice(moves);
        sm.shared.objectives[agent_index] = None;  # should be something smarter
        
    # if sm.shared.objectives[agent_index] != None:
        # print(sm.shared.objectives[agent_index].type)
        
    # print (my_move);
    return my_move;

def relink_followers(agent_index):  # makes all agent that are following me, follow who I am following. If not following anyone, set objective to none
    followers = following_me(agent_index);
    if(len(followers) == 0):
        return;
                
    # if someone is following me;   
    
    #if I am following someone, make guys behind me follow who I am following
    if sm.shared.objectives[agent_index].type == "follow":   
        my_leader = sm.shared.objectives[agent_index].other_agent_index;
        for f in followers:
            sm.shared.objectives[f].other_agent_index = my_leader;
    elif (sm.shared.objectives[agent_index].type == "move"):
        my_goal = sm.shared.objectives[agent_index].goal;
        if(my_goal == None):
            sm.shared.objectives[f] = None;
        else:
            for f in followers:
                sm.shared.objectives[f] = ObjectiveMove(f,my_goal);
    elif (sm.shared.objectives[agent_index].type == "explore"):
        for f in followers:
            sm.shared.objectives[f] = ObjectiveExplore(f);            
            
    else:
        for f in followers:
            sm.shared.objectives[f] = None; # something smarter maybe?
    
    
        
        
def following_me(agent_index): # return a list of agents that are following me
    followers = [];
    
    for i, pos in enumerate(sm.shared.agents):
        if(sm.shared.objectives[i] == None):
            continue;
        
        if(sm.shared.objectives[i].type == "follow"):
            if(sm.shared.objectives[i].other_agent_index == agent_index):
                followers.append(i);
            
    return followers;
            
            
            
            
            
            
            
            
            
            
            
            
            
            
