import json
import time
import requests
import matplotlib.pyplot as plt
import numpy as np

def create_champion_key_dict():
    champion_url = 'https://ddragon.leagueoflegends.com/cdn/14.2.1/data/en_US/champion.json'
    response = requests.get(champion_url)
    champion_data = response.json()
    champion_dict = {}
    for key, value in champion_data['data'].items():
        champion_id = value['key']
        champion_name = value['id']
        champion_dict[champion_name] = int(champion_id)
    return champion_dict

champion_dict = create_champion_key_dict()

# get all matchup data for a particular champion in a role
def get_matchups(patch, champion, role):
    matchup_page_link = f"https://ax.lolalytics.com/mega/?ep=champion&p=d&v=1&patch={patch}&cid={champion}&lane={role}&tier=emerald_plus&queue=420&region=all"
    matchup_page = requests.get(matchup_page_link)
    matchup_page_json = matchup_page.json()
    return(matchup_page_json)

# get all synergy data for a particular champion in a role
def get_teammates(patch, champion, role):
    teammate_page_link = f"https://ax.lolalytics.com/mega/?ep=champion2&p=d&v=1&patch={patch}&cid={champion}&lane={role}&tier=emerald_plus&queue=420&region=all"
    teammate_page = requests.get(teammate_page_link)
    teammate_page_json = teammate_page.json()
    return(teammate_page_json)

# get all playrate data for a particular role
def get_role_playrates(patch, role):
    role_page_link = f"https://ax.lolalytics.com/tierlist/1/?lane={role}&patch={patch}&tier=emerald_plus&queue=420&region=all"
    role_page = requests.get(role_page_link)
    role_page_json = role_page.json()
    return role_page_json['cid']

lanes = ['top', 'jungle', 'middle', 'bottom', 'support']

def normalize_winrate(patch, champion, role):
    #map champion name to id
    champion_id = champion_dict[champion]

    #get enemy and allied jsons
    matchups = get_matchups(patch, champion_id, role)
    teammates = get_teammates(patch, champion_id, role)

    #unadjusted winrate
    unadjusted_winrate = sum([matchup[2] for matchup in matchups[f'enemy_{role}']]) / sum([matchup[1] for matchup in matchups[f'enemy_{role}']])

    #initialize zero numerator and denominator
    aggregate = 0

    for lane in lanes:
        #sleep so as not to upset LoLalytics
        time.sleep(0.4)

        #initialize zero numerator and denominator
        numerator = 0
        denominator = 0
        #get lane json
        lane_playrates = get_role_playrates(patch, lane)

        #sum up multiplication of matchup winrate by number of games in role for each champion
        numerator += sum([(matchup[2] / matchup[1]) * lane_playrates[f'{matchup[0]}'][4] for matchup in matchups[f'enemy_{lane}']])

        #get total number of games in role
        denominator += sum([lane_playrates[f'{matchup[0]}'][4] for matchup in matchups[f'enemy_{lane}']])
        aggregate += unadjusted_winrate - (numerator / denominator)

        #repeat for allied champions
    for lane in lanes:
        time.sleep(0.4)
        numerator = 0
        denominator = 0
        lane_playrates = get_role_playrates(patch, lane)
        if lane == role:
            continue
        numerator += sum([(teammate[2] / teammate[1]) * lane_playrates[f'{teammate[0]}'][4] for teammate in teammates[f'team_{lane}']])
        denominator += sum([lane_playrates[f'{teammate[0]}'][4] for teammate in teammates[f'team_{lane}']])
        aggregate += unadjusted_winrate - (numerator / denominator)
    print(champion)
    return (champion, unadjusted_winrate, unadjusted_winrate - aggregate)
        
reversed_champion_dict = {value: key for key, value in champion_dict.items()}

def get_most_played(patch, role, n):
    role_playrates = get_role_playrates(patch, role)
    sorted_by_playrates = sorted(role_playrates, key=lambda k: role_playrates[k][4], reverse=True)
    return [reversed_champion_dict[int(item)] for item in sorted_by_playrates[:n]]

# sample usage
results = []
for champion in get_most_played('14.2', 'middle', 30):
        results.append(normalize_winrate('14.2', champion, 'middle'))

def plot_data(data):
    labels, x_values, y_values = zip(*data)
    plt.figure(figsize=(12, 12))

    for label, x, y in data:
        plt.scatter(100*x, 100*(x-y), label=label)
        plt.text(100*x, 100*(x-y), label)
        
    plt.axhline(0, color='gray', linestyle='--')

    plt.xlabel('Observed Winrate')
    plt.ylabel('Inflation Percentage')
    plt.title('Emerald+ Winrate Inflation, Meta-Normalized')
    plt.grid(True)
    plt.show()

plot_data(results)

