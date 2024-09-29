'''
author : kabetani yusei
'''
from .generate_route import GENERATE_ROUTE

class GENERATE_ROUTE_WRAPPER:
    def __init__(self, user_data, database_data):
        self.userdata = user_data
        self.database_data = database_data
        self.data = {
            "required_time": self._time_to_minutes(self.userdata["required_time"]),
            "include_lunch" : self.userdata["include_lunch"],
            "spot_list": []
        }
        self.pre_process()

    def _time_to_minutes(self, time_str):
        # "hh:mm" の形式を ':' で分割して時間と分を取得
        hours, minutes = map(int, time_str.split(':'))
        total_minutes = hours * 60 + minutes
        return total_minutes

    def pre_process(self):
        for spot in self.database_data:
            print(f"現在処理中のスポット: {spot['spot_name']}, 座標: {spot['coordinate']}")
            if spot["spot_name"] == self.userdata["selected_place"]:
                self.data["selected_place_id"] = spot["id"]
            if spot["spot_name"] == self.userdata["start_station"]:
                self.data["start_id"] = spot["id"]
            if spot["spot_name"] == self.userdata["goal_station"]:
                self.data["goal_id"] = spot["id"]
            try:
                self.data["spot_list"].append({
                    "coordinate": self._coordinate_to_list(spot["coordinate"]),
                    "id": spot["id"],
                    "recommendation": spot["recommendation"],
                    "spot_type": spot["spot_type"],
                    "staying_time": spot["staying_time"]
                })
            except ValueError as e:
                print(f"エラーが発生したスポット: {spot['spot_name']}, エラー: {e}")

    def _coordinate_to_list(self, coordinate):
        if not coordinate or coordinate == '':  # 空の座標をチェック
            raise ValueError("座標が空です")
        
        try:
            coordinates = coordinate[1:-1].split(',')
            return list(map(int, coordinates))
        except ValueError as e:
            print(f"座標の変換中にエラーが発生しました: {e}, 座標: {coordinate}")
            raise e



    def execute_generate_route(self):
        func = GENERATE_ROUTE(self.data)
        return func.generate_route()