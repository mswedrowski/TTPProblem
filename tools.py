import random
import loader
import numpy as np
import pandas as pd
from operator import itemgetter

np.set_printoptions(threshold=np.nan)


# Data import

basic_info, nodes, items = loader.load('medium_0.ttp')

KNP_greedy_strategies = ['most_expensive','lightest','best_ratio']  #ratio = profit/weight

#Calculate max amount of items
def max_amount_items():
    return np.max(np.bincount(items.transpose()[3]))

# Assign items to cities

# city_item_list[city_index - 1] = list of items for city with city_index      /each item is stored as a list [index,profit,weight]

city_item_list = [None] * len(items)

for x in range (len(items)):
    if(city_item_list[items[x][3] -1] is None):
        city_item_list[items[x][3] - 1] = [list(items[x][:3])]
    else:
        city_item_list[(items[x][3] - 1)].append(list(items[x][:3]))


# Gathering index

index_array = np.zeros(shape=nodes.__len__(), dtype=int)
for x in range(nodes.__len__()):
    index_array[x] = (nodes[x][0])

# Calculate distance - pythagoras

distance_array = np.zeros(shape=[nodes.__len__(), nodes.__len__()])
for x in range(nodes.__len__()):
    distance_array[x] = np.power(np.power(nodes.transpose()[1] - nodes[x][1],2) + np.power(nodes.transpose()[2] - nodes[x][2],2),1/2)


# Generate random TSP solution

def generate_TSP_solution():
    index_pool = list(np.copy(index_array))
    route = np.empty(shape=index_array.__len__())

    for x in range (index_array.__len__()):
        node_index = random.choice(index_pool)
        route[x] = node_index
        index_pool.remove(node_index)
    return route  # returning [route]


# Calculate velocity
def get_velocity(current_cap):
    return basic_info["max speed"] - current_cap*((basic_info["max speed" ]- basic_info["min speed"])/basic_info["KNP cap"])

# Calculate time - f(x) function
def get_travel_time(start_index,destination_index,curr_cap):
        return distance_array[start_index][destination_index]/get_velocity(curr_cap)


# Get all items for a city
def get_items_for_city(index):
    """:rtype: list"""
    result = city_item_list[index-1]
    return result

# Get list of all items:
def get_all_items():
    all_items=[]
    for x in items:
        all_items.append(list(x[:3]))
    return all_items

# Get item - use this function if u assume that u're trying to pick up items every time we visit a city

def get_item(city_index,strategy,current_cap):
    picked_item = None
    city_items = []
    if(strategy == 'most_expensive'):
        city_items = sorted(city_item_list[city_index - 1].copy(),key=itemgetter(1),reverse=True)                       # copy array and sort items by profit

    # - HAVEN'T TESTED IT YET
    elif(strategy=='lightest'):
        city_items = sorted(city_item_list[city_index - 1].copy(), key=itemgetter(2))                                   #copy array and sort items by weight(lighter first)

    while city_items.__len__()> 0 and picked_item is None:
        if(basic_info['KNP cap'] - current_cap >= city_items[0][2]):                                                    # if we have cap
            picked_item = city_items[0]
        else:
            city_items.remove(city_items[0])
    return picked_item

# Use this if you know whole item pool before you start moving between cities
def get_list_of_ordered_items(strategy):

    ordered_list=[]
    if (strategy == KNP_greedy_strategies[0]):                                                                          #most expensive
        ordered_list = sorted(get_all_items(),key=itemgetter(1),reverse=True)
    elif(strategy==KNP_greedy_strategies[1]):                                                                           #lightest
        ordered_list = sorted(get_all_items(), key=itemgetter(2))
    elif(strategy == KNP_greedy_strategies[2]):                                                                         #best ratio
        ratio_ranking = np.empty(shape=(get_all_items().__len__(),2))                                                   #[node_index,ratio] X 510
        all_items=get_all_items()
        for x in range(all_items.__len__()):
            ratio_ranking[x]=np.array([all_items[x][0],all_items[x][1] / all_items[x][2]])
        ratio_ranking = np.flip(ratio_ranking[ratio_ranking[:,1].argsort()],0)

        #Garbage code
        for x in ratio_ranking:
            for y in all_items:
                if(x[0]==y[0]):
                    ordered_list.append(y)

    solution=[]
    sum_weight=0
    itr=0

    while sum_weight + ordered_list[itr + 1][1] < basic_info['KNP cap']:
        solution.append(ordered_list[itr])
        sum_weight+= ordered_list[itr][1]
        itr += 1
    return solution

# Sum of picked items - g(y)
def sum_item_values(solution):
    return sum(profit for inx , profit , weight in solution[2])

# Travel cost  - f(x,y)
def get_travel_cost(solution):

    list_of_choosed_items = get_list_of_ordered_items('best_ratio')
    travel_cost = 0
    route = solution
    itr =0
    current_cap = 0
    item_list = []

    while itr + 1 < len(route):
        travel_cost += get_travel_time(int(route[itr])-1 ,int(route[itr+1])-1,current_cap)

        items_for_city = get_items_for_city(int(route[itr]))
        if (items_for_city is not None):
            for item in items_for_city:
                if(list_of_choosed_items.__contains__(item)):
                    current_cap += item[2]
                    item_list.append(item)
        itr += 1

    travel_cost += get_travel_time(len(route)-1,0,current_cap)          # Back to first city

    return (travel_cost,item_list)    #Travel_cost & list of items



# I'M ONLY RETURNING ROUTE
def crossover_new_route(parent_1, parent_2):

    children1 = parent_1

    index_pool_1 = list(parent_1)                 # we will need pool of all indexes to fix our children

    divide_index = round(parent_1.__len__()/2)

    for x in range (divide_index):
        index_pool_1.remove(parent_1[x])

    for x in range (divide_index,parent_1.__len__()):

        if children1[:x].__contains__(parent_2[x]):
            children1[x] = random.choice(index_pool_1)
        else:
            children1[x] = parent_2[x]
        index_pool_1.remove(children1[x])

    return children1



def tournament(solution_ranking,percentage):                                                                            #precentage range 0.00 - 1.00

    size_of_tournament = int(np.floor(solution_ranking.__len__() * percentage))
    if(size_of_tournament % 2):
        size_of_tournament += 1

    candidates_pool = solution_ranking.copy()

    tournament_participants = pd.DataFrame()


    # Picking participants
    picked_indexes=[]

    for x in range(size_of_tournament):
        participant_index = random.randint(0,solution_ranking.__len__() - 1)
        while(picked_indexes.__contains__(participant_index)):
            participant_index = random.randint(0, solution_ranking.__len__() - 1)
        picked_indexes.append(participant_index)

        row = candidates_pool.loc[participant_index]
        candidates_pool = candidates_pool.drop(participant_index, axis=0)
        tournament_participants = tournament_participants.append(row)

    tournament_participants =  tournament_participants.reset_index(drop=True)

    #Fight!
    picked_indexes = []
    starting_number_of_contestants = tournament_participants.__len__()
    while(tournament_participants.__len__()>0):

        duel_candidate_1_inx, duel_candidate_2_inx = getTwoDiff(starting_number_of_contestants - 1)

        while(duel_candidate_1_inx == duel_candidate_2_inx or picked_indexes.__contains__(duel_candidate_1_inx) or  picked_indexes.__contains__(duel_candidate_2_inx) ):
            duel_candidate_1_inx, duel_candidate_2_inx = getTwoDiff(starting_number_of_contestants - 1)

        picked_indexes.append(duel_candidate_1_inx)
        picked_indexes.append(duel_candidate_2_inx)



        duel_candidate_1 = tournament_participants.loc[duel_candidate_1_inx]
        duel_candidate_2 = tournament_participants.loc[duel_candidate_2_inx]


        if(duel_candidate_1['score'] > duel_candidate_2['score']):
            candidates_pool = candidates_pool.append(duel_candidate_2)
        else:
            candidates_pool = candidates_pool.append(duel_candidate_1)
        tournament_participants = tournament_participants.drop([duel_candidate_1_inx,duel_candidate_2_inx], axis=0)

    return candidates_pool

# Returns two different values from certain range
def getTwoDiff(range):
    index_1 = random.randint(0, range)
    index_2 = random.randint(0,range)
    while (index_1 == index_2):
        index_2 = random.randint(0,range)
    return index_1,index_2