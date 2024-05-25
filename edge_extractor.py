import requests
from bs4 import BeautifulSoup as bs
import json
from typing import *


class EdgeExtractor:

    def __init__(self, filename: str):
        # read json file
        with open(filename, "rb") as f:
            search_result = json.load(f)

        # sanity check
        assert isinstance(search_result, dict)
        for tag in search_result.values():
            print(tag)
            assert isinstance(tag, dict)
            assert "prob_list" in tag
            assert isinstance(tag["prob_list"], list)

        # get problems list
        self.prob_ids = []
        for tag in search_result.values():
            self.prob_ids += tag["prob_list"]

        print(
            f"[EdgeExtractor] Complete reading {len(self.prob_ids)} problems from {filename}"
        )

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
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"}
        page = requests.get(solved_status_url, headers=headers)
        soup = bs(page.text, "html.parser")

        # check if finished
        err_sign = soup.select("div.error-v1")
        if err_sign:
            return None

        # find user list
        entries = soup.select("div.col-md-10 tbody")[0]
        # double check if finished
        if len(entries) == 0:
            return None

        # fetch user list
        user_ids = []
        for entry in entries:
            elems = entry.select("td")
            user_id = elems[3].text
            user_ids.append(user_id)
        return user_ids

    def save_solved_users(self):
        # check already fetched data
        try:
            with open(self.temp_filename, "r") as f:
                data = json.load(f)
            assert isinstance(data, dict)

            print("[EdgeExtractor] Info")
            print(
                f"file {self.temp_filename} already contains solved users of {len(data)} problems; we will pass fetching these problems."
            )                
        except:
            data = {}

        # fetch solved user
        tot = len(self.prob_ids)
        for idx, prob_id in enumerate(self.prob_ids):
            # pass if already data exists
            if str(prob_id) in data:
                continue

            user_ids = self.get_solved_user_list(prob_id)
            data[prob_id] = user_ids

            print(f"Fetching solved users of prob_id {prob_id} finished.")
            print(f"Current status: {idx + 1}/{tot} problems fetched.")

            # save data right after fetching each problem's solved users
            with open(self.temp_filename, "w") as f:
                json.dump(data, f)

        print("[EdgeExtractor] Temporary Notice")
        print(f"Each problem's solved users saved at {self.temp_filename}.")
        print(
            f"From now on, EdgeExtractor will automatically use the data of {self.temp_filename}."
        )

    def extract_edges(self, alpha: float) -> List[Tuple[int, int]]:
        file_found = False
        data_mismatch = None

        try:
            with open(self.temp_filename, "r") as f:
                data = json.load(f)
            file_found = True

            # data check
            for prob_id in self.prob_ids:
                if str(prob_id) not in data:
                    data_mismatch = prob_id
                    raise Exception()

            print("[EdgeExtractor] Info")
            print(
                f"Successfully read solved users dataset: {self.temp_filename}."
            )
        except:
            print("[EdgeExtractor] Warning")
            if not file_found:
                print(f"JSON File {self.temp_filename} not found")
            elif data_mismatch is not None:
                print(
                    f"Data mismatch; counterexample: prob_id {prob_id} is not in {self.temp_filename}."
                )

            print(
                f"Starting to fetch each problem's solved users and save at {self.temp_filename}..."
            )
            self.save_solved_users()
            with open(self.temp_filename, "r") as f:
                data = json.load(f)

        # sanity check
        assert isinstance(data, dict)
        assert len(data) == len(self.prob_ids)
        for prob_id, users in data.items():
            assert isinstance(users, list)

        # build mapping from node_id to prob_id
        node_to_prob = []
        for idx, prob_id in enumerate(data.keys()):
            assert self.prob_ids[idx] == int(prob_id)
            node_to_prob.append({"node_id": idx, "prob_id": prob_id})

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
                    edges.append((idx1, idx2))
                    edges.append((idx2, idx1))
                    print(
                        f"=> Two edges connected between node1: {idx1} <=> node2: {idx2}, each of which represents prob_id1: {prob_id1}, prob_id2: {prob_id2}"
                    )

        return edges, node_to_prob

    def can_connect(self, users_set: Dict[int, Set[str]], alpha: float,
                    prob_id1: int, prob_id2: int) -> bool:
        users1, users2 = users_set[prob_id1], users_set[prob_id2]
        cnt1, cnt2 = len(users1), len(users2)
        common_cnt = len(users1.intersection(users2))

        if common_cnt >= alpha * (cnt1 + cnt2):
            print(f"Can connect prob_id1: {prob_id1}, prob_id2: {prob_id2}")
            print(
                f"cnt1: {cnt1}, cnt2: {cnt2}, common: {common_cnt}, ratio: {common_cnt / (cnt1 + cnt2)}"
            )
            return True
        else:
            return False

    def save_edges_at(self, edges: List[Tuple[int, int]],
                      node_to_prob: List[Dict[str, int]], filename: str):
        with open(filename, "w") as f:
            json.dump(edges, f)
        print("[EdgeExtractor] Finished")
        print(f"Edges successfully saved at: {filename}.")


# [Usage]
ee = EdgeExtractor("search_result.json")
edges, node_to_prob = ee.extract_edges(alpha=0.1)
ee.save_edges_at(edges, node_to_prob, "edges.json")
