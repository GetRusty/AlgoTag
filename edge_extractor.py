from selenium import webdriver
from selenium.webdriver.common.by import By
import json
from typing import *


class EdgeExtractor:

    def __init__(self, filename: str):
        # read json file
        with open(filename, "r") as f:
            problems = json.load(f)

        # sanity check
        assert isinstance(problems, list)
        print(
            f"[EdgeExtractor] Complete reading {len(problems)} problems from {filename}"
        )

        self.prob_ids = list(map(int, problems))

        # temporary JSON file name (for saving solved users)
        self.temp_filename = "_temp_fetched_solved_users.json"

    def get_solved_user_list(self, prob_id: int) -> List[int]:
        user_ids = []
        page_num = 1
        while True:
            # try each page
            ret = self._get_solved_user_list_at_page(prob_id, page_num)
            if ret is None:
                break

            user_ids += ret
            page_num += 1

        return user_ids

    # internal only
    def _get_solved_user_list_at_page(self, prob_id: int,
                                      page_num: int) -> Optional[List[int]]:
        solved_status_url = f"https://www.acmicpc.net/problem/status/{prob_id}/{page_num}"
        self.driver.get(solved_status_url)

        # check if finished
        err_sign = self.driver.find_elements(By.CLASS_NAME, "error-v1")
        if err_sign:
            return None

        # find user list
        table = self.driver.find_element(By.CLASS_NAME, "col-md-10")
        tbody = table.find_element(By.TAG_NAME, "tbody")
        entries = tbody.find_elements(By.TAG_NAME, "tr")

        # double check if finished
        if len(entries) == 0:
            return None

        # fetch user list
        user_ids = []
        for entry in entries:
            elems = entry.find_elements(By.TAG_NAME, "td")
            user_id = elems[3].text
            user_ids.append(user_id)

        return user_ids

    def save_solved_users(self):
        # open chrome webriver
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=options)

        # fetch data
        data = {}
        for prob_id in self.prob_ids:
            user_ids = self.get_solved_user_list(prob_id)
            data[prob_id] = user_ids

        # close webdriver and save data
        self.driver.close()
        with open(self.temp_filename, "w") as f:
            json.dump(data, f)
        print("[EdgeExtractor] Temporary Notice")
        print(f"Each problem's solved users saved at {self.temp_filename}.")
        print(
            f"From now on, EdgeExtractor will automatically use the data of {self.temp_filename}."
        )

    def extract_edges(self, alpha: float) -> List[Tuple[int, int]]:
        # load solved users data
        temp_filename = "_temp_fetched_solved_users.json"
        try:
            with open(temp_filename, "r") as f:
                data = json.load(f)
            print("[EdgeExtractor] Info")
            print(
                f"Successfully read solved users dataset: {self.temp_filename}."
            )
        except:
            print("[EdgeExtractor] Warning")
            print(f"JSON File {self.temp_filename} not found.")
            print(
                f"Starting to fetch each problem's solved users and save at {self.temp_filename}..."
            )
            self.save_solved_users()
            with open(temp_filename, "r") as f:
                data = json.load(f)

        # sanity check
        assert isinstance(data, dict)

        # make set()
        users_set = {}
        for prob_id, users in data.items():
            s = set(users)
            users_set[int(prob_id)] = s

        # calculate edge
        edges = []
        prob_num = len(self.prob_ids)
        for idx1 in range(prob_num):
            prob_id1 = self.prob_ids[idx1]
            for idx2 in range(idx1 + 1, prob_num):
                prob_id2 = self.prob_ids[idx2]

                if self.can_connect(users_set, alpha, prob_id1, prob_id2):
                    edges.append((prob_id1, prob_id2))
                    edges.append((prob_id2, prob_id1))

        return edges

    def can_connect(self, users_set: Dict[int, Set[str]], alpha: float,
                    prob_id1: int, prob_id2: int) -> bool:
        users1, users2 = users_set[prob_id1], users_set[prob_id2]
        cnt1, cnt2 = len(users1), len(users2)
        common_cnt = len(users1.intersection(users2))

        print(
            f"prob_id1: {prob_id1}, prob_id2: {prob_id2} => cnt1: {cnt1}, cnt2: {cnt2}, common: {common_cnt}, ratio: {common_cnt / (cnt1 + cnt2)}"
        )
        return common_cnt / (cnt1 + cnt2) >= alpha
    
    def save_edges_at(self, edges: List[Tuple[int, int]], filename: str):
        with open(filename, "w") as f:
            json.dump(edges, f)
        print("[EdgeExtractor] Finished")
        print(f"Edges successfully saved at: {filename}.")


# [Usage]
# ee = EdgeExtractor("temp_probs.json")
# edges = ee.extract_edges(alpha=0.1)
# ee.save_edges_at(edges, "edges.json")
