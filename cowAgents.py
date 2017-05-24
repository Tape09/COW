import sharedMemory as sm
from util import  *
from objectives import *
import random


sm.shared = None;


def before_each_round():
    sm.shared.update_herds();
    sm.shared.update_dists();
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
    if(sm.shared.iteration > 2):
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
            print("======")
            print(smallest_team_idx);
            print(len(sm.shared.herd_teams[0].agents))
            print(len(sm.shared.herd_teams[1].agents))
            print("======")
    
    print(len(sm.shared.herd_teams))
    print(len(sm.shared.herd_teams[0].agents))
    print(len(sm.shared.herd_teams[1].agents))
    ##################################### THIS WILL CHANGE
    # Team objectives
    for j in range(len(sm.shared.herd_teams)):
        for i,agent in enumerate(sm.shared.herd_teams[j].agents):
            # skip leader for now
            if(i == 0):
                continue;
            sm.shared.objectives[agent] = ObjectiveFollow(agent,sm.shared.herd_teams[j].agents[i-1]);
    
    

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
            
            
            
            
            
            
            
            
            
            
            
            
            
            
