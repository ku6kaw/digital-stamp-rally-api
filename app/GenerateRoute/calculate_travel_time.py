'''
author : kabetani yusei
'''
class CALCULATE_TRAVEL_TIME:
    def __init__(self, route, database_data):
        self.route = route
        self.database_data = database_data
        self.route_data = [None] * len(route)
        self.pre_process()
    
    def pre_process(self):
        for spot in self.database_data:
            if spot["id"] in self.route:
                self.route_data[self.route.index(spot["id"])] = {
                    "coordinate": self._coordinate_to_list(spot["coordinate"]),
                    "id": spot["id"],
                    "spot_name": spot["spot_name"],
                    "recommendation": spot["recommendation"],
                    "spot_type": spot["spot_type"],
                    "staying_time": spot["staying_time"]
                }


    def _coordinate_to_list(self, coordinate):
        return list(map(int, coordinate[1:-1].split(',')))

    def calculate_travel_time(self):
        places = []
        now_time = 600 # 現在時刻を10:00に設定
        total_time = 0
        include_lunch = False
        for i in range(len(self.route_data)):
            if self.route_data[i]["spot_type"] == 1: include_lunch = True
            start_time = now_time + total_time
            end_time = now_time + total_time + self.route_data[i]["staying_time"]
            total_time += self.route_data[i]["staying_time"]
            if i < len(self.route_data) - 1:
                next_place_travel_time = abs(self.route_data[i]["coordinate"][0] - self.route_data[i + 1]["coordinate"][0]) + abs(self.route_data[i]["coordinate"][1] - self.route_data[i + 1]["coordinate"][1])
            else:
                next_place_travel_time = None
            places.append({
                "place_name": self.route_data[i]["spot_name"],
                "stay_time": f"{start_time // 60:02}:{start_time % 60:02}-{end_time // 60:02}:{end_time % 60:02}",
                "next_place_travel_time": next_place_travel_time
            })
        total_time += self.route_data[-1]["staying_time"]

        route_info = {
            "places": places,
            "total_time": f"{total_time // 60:02}:{total_time % 60:02}",
            "lunch_included": include_lunch
        }
        return route_info