'''
author : kabetani yusei
実行時間294 ms
メモリ93700 KB
'''
import random

class PLACE_TYPE:
    TEMPLE = 0
    RESTAURANT = 1
    SOUVENIR = 2
    STATION = 3

class GENERATE_ROUTE:
    def __init__(self, data):
        self.selected_place_id = data['selected_place_id']
        self.required_time = data['required_time']
        self.include_lunch = data['include_lunch']
        self.now_time = 600 # 発表時間が午後であることを考えて、10:00スタートになるように埋め込む

        # それぞれのタイプで観光地のリストを作成する
        self.temple_list = []
        self.restaurant_list = []
        self.souvenir_list = []
        self.station_list = []
        self.selected_place_spot_type = -1
        self.selected_place = None
        self.selected_place_idx = None
        self.update_spot_list(data['spot_list'])

        # start地点とgoal地点を追加
        self.start = None
        self.goal = None
        for place in self.station_list:
            if place['id'] == data['start_id']:
                self.start = place
            if place['id'] == data['goal_id']:
                self.goal = place

    def update_spot_list(self, spot_list):
        for place in spot_list:
            place['recommendation'] += random.choice([-1, 0, 1]) # 満足度を適当にいじって同じルートが選択されることを防ぐ
            if place['id'] == self.selected_place_id:
                self.selected_place = place
                self.selected_place_spot_type = place['spot_type']
            if place['spot_type'] == PLACE_TYPE.TEMPLE:
                self.temple_list.append(place)
            elif place['spot_type'] == PLACE_TYPE.RESTAURANT:
                self.restaurant_list.append(place)
            elif place['spot_type'] == PLACE_TYPE.SOUVENIR:
                self.souvenir_list.append(place)
            elif place['spot_type'] == PLACE_TYPE.STATION:
                self.station_list.append(place)

    def _select_restaurant(self):
        if self.selected_place_spot_type == PLACE_TYPE.RESTAURANT:
            return self.selected_place
        return random.choice(self.restaurant_list)

    def _select_souvenir(self):
        if self.selected_place_spot_type == PLACE_TYPE.SOUVENIR:
            return self.selected_place
        return random.choice(self.souvenir_list)

    def _search_best_route(self, dp):
        # ゴール地点の最適解を求める
        best_recommendation = 0
        best_state = None
        for i in range(2 ** len(dp[0])):
            #2つの条件を満たす必要がある
            #1. 制限時間以内である
            #2. 確定で通りたいやつを通る
            if ((dp[i][-1][0] <= self.required_time) and
                ((self.selected_place_idx == None) or (i & (2 ** self.selected_place_idx) != 0))):
                if best_state is None:
                    best_recommendation = dp[i][-1][1]
                    best_state = i
                elif dp[i][-1][1] > dp[best_state][-1][1]:
                    best_recommendation = dp[i][-1][1]
                    best_state = i
        return best_state

    def generate_route(self):
        # 経路を考えるにあたり、回る候補を求める
        # 飲食店、お土産屋さんは1つずつ選ぶ
        place_candidate_list = [self.start] + self.temple_list
        if self.include_lunch:
            place_candidate_list.append(self._select_restaurant())
        place_candidate_list.append(self._select_souvenir())
        place_candidate_list.append(self.goal)
        for i, place in enumerate(place_candidate_list):
            if place['id'] == self.selected_place_id:
                self.selected_place_idx = i

        # 以下、bitDPを行う
        cand_list_length = len(place_candidate_list)
        # dpの初期化 tuple(最短時間, おすすめ度の合計)
        dp = [[(100000, 0)] * cand_list_length for _ in range(2 ** cand_list_length)]
        prev = [[-1] * cand_list_length for _ in range(2 ** cand_list_length)]

        # スタート地点の初期値
        dp[0][0] = (0, 0)
        dp[1][0] = (0, 0)
        for i in range(2 ** cand_list_length):
            for j in range(cand_list_length):
                if dp[i][j][0] < 100000:

                    for k in range(1, cand_list_length):
                        if (i // (2 ** k)) % 2 == 0:
                            dist = abs(place_candidate_list[j]['coordinate'][0] - place_candidate_list[k]['coordinate'][0]) + abs(place_candidate_list[j]['coordinate'][1] - place_candidate_list[k]['coordinate'][1])             
                            # 飲食店の場合の計算
                            if place_candidate_list[k]['spot_type'] == PLACE_TYPE.RESTAURANT:
                                calc_time = self.now_time + dp[i][j][0] + dist
                                if 690 <= calc_time <= 780:
                                    recommendation = 100
                                elif 690 <= calc_time <= 840:
                                    recommendation = 50
                                else:
                                    recommendation = 10
                            else:
                                recommendation = place_candidate_list[k]['recommendation']
                            staying_time = place_candidate_list[k]['staying_time']
                            new_time = dp[i][j][0] + dist + staying_time
                            new_recommendation = dp[i][j][1] + recommendation
                            
                            if ((new_recommendation > dp[i + (2 ** k)][k][1]) or
                                (new_recommendation == dp[i + (2 ** k)][k][1]) and (new_time < dp[i + (2 ** k)][k][0])):
                                dp[i + (2 ** k)][k] = (new_time, new_recommendation)
                                prev[i + (2 ** k)][k] = j  # 経路の遷移元を記録

        # 出力
        best_state = self._search_best_route(dp)
        if best_state == None:
            print("条件を満たす経路が見つかりませんでした")
            return False

        # 経路復元
        route = []
        state = best_state
        now = cand_list_length - 1  # ゴール地点

        while now != -1:
            route.append(now)
            next_state = state - (2 ** now)
            now = prev[state][now]
            state = next_state
        route.reverse()

        # 経路の表示
        place_id_list = [place_candidate_list[idx]['id'] for idx in route]  
        return place_id_list