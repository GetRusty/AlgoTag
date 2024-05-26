import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
import json
from typing import *

class FeatureExtractor:

    def __init__(self, cookie=None, filename="search_result.json"):
        
        # options = webdriver.ChromeOptions()
        # options.add_argument("headless")
        # self.driver = webdriver.Chrome(options=options)
        # self.driver.get("https://www.acmicpc.net")
        if cookie != None:
            self.driver.add_cookie(cookie)
        
        self.filename = filename
        # read json file
        with open(filename, "rb") as f:
            search_result = json.load(f)

        # sanity check
        assert isinstance(search_result, dict)
        for tag in search_result.values():
            # print(tag)
            assert isinstance(tag, dict)
            assert "prob_list" in tag
            assert isinstance(tag["prob_list"], list)

        # get problems list
        self.prob_ids = []
        temp_prob_ids = []
        for tag in search_result.values():
            temp_prob_ids += tag["prob_list"]
        
        for val in temp_prob_ids:
            if val not in self.prob_ids:
                self.prob_ids.append(val)

        self.temp_filename = "_temp_fetched_features.json"
        self.search_result = search_result

    def _get_features_at_page(self, prob_id: int,
                                      page_num: int) -> Optional[tuple[list[int], list[int], list[int]]]:
        solved_status_url = f"https://www.acmicpc.net/problem/status/{prob_id}/1001/{page_num}" # filter C++ only
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
        }
        page = requests.get(solved_status_url, headers=headers)
        soup = bs(page.text, "html.parser")

        # check if finished
        err_sign = soup.select("div.error-v1")
        if err_sign:
            return None
        
        l = soup.select("div.col-md-10 thead tr th")
        assert(l[-2].text == "코드 길이")
        assert(l[-4].text == "시간")
        assert(l[-5].text == "메모리")

        # find user list
        entries = soup.select("div.col-md-10 tbody")[0]
        # double check if finished
        if len(entries) == 0:
            return None

        # fetch memory, time, length
        memory = []
        time = []
        length = []
        for entry in entries:
            elems = entry.select("td")
            memory.append(int(elems[-5].text))
            time.append(int(elems[-4].text))
            length.append(int(elems[-2].text))
            
        return (memory, time, length)
    
    def _get_user_features(self, prob_id: int) -> tuple[float, float, float]:
        memory = []
        time = []
        length = []
        page_num = 1
        while True:
            # try each page
            ret = self._get_features_at_page(prob_id, page_num)
            if ret is None:
                break
            
            (m, t, l) = ret
            memory += m
            time += t
            length += l
            page_num += 1

        def median(l : list[int]) -> float:
            l.sort()
            m = len(l)
            if m == 0:
                return 0.0
            
            if m % 2 == 0:
                return (l[m//2-1] + l[m//2]) / 2
            else:
                return l[m//2]
            
        return (float(median(memory)), float(median(time)), float(median(length)))
    
    def _get_text_features(self, prob_id: int) -> Optional[tuple[str, str, str]]:
        solved_status_url = f"https://www.acmicpc.net/problem/{prob_id}"
        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
        }
        page = requests.get(solved_status_url, headers=headers)
        soup = bs(page.text, "html.parser")

        # check if finished
        err_sign = soup.select("div.error-v1")
        if err_sign:
            return None
        
        # find texts
        problem_text = ""
        input_text = ""
        output_text = ""

        entries = soup.select("#problem_description")
        for entry in entries:
            problem_text += entry.text
        
        entries = soup.select("#problem_input")
        for entry in entries:
            input_text += entry.text
            
        entries = soup.select("#problem_output")
        for entry in entries:
            output_text += entry.text
        
        return (problem_text[1:], input_text[1:], output_text[1:])
        
    def get_features(self, prob_id: int) -> dict[str, Union[str, float]]:
        
        while True:
            result = self._get_text_features(prob_id)
            if result:
                (problem_text, input_text, output_text) = result
                break
            else:
                print(f"Got errors while calling get_text of problem id : {prob_id}, retrying...")
        
        (med_memory, med_time, med_length) = self._get_user_features(prob_id)

        return {"problem_text": problem_text, "input_text": input_text, "output_text": output_text,
                "memory_median": med_memory, "time_median": med_time, "length_median": med_length}
    
    def get_label(self, prob_id: int) -> list[int]:
        result = []
        for dic in self.search_result.values():
            found = 0
            for pid in dic["prob_list"]:
                if pid == prob_id:
                    found = 1
            result.append(found)
        return result

    def save_features(self):
        # check already fetched data
        try:
            with open(self.temp_filename, "r", encoding='utf-8') as f:
                data = json.load(f)
            #assert isinstance(data, dict)

            print("[FeatureExtractor] Info")
            print(
                f"file {self.temp_filename} already contains solved users of {len(data)} problems; we will pass fetching these problems."
            )
        except:
            print("[FeatureExtractor] Info")
            print(f"Making new File: {self.temp_filename}")
            data = {}
        
        tot = len(self.prob_ids)
        for idx, prob_id in enumerate(self.prob_ids):
            if str(idx) in data.keys():
                continue

            feature = self.get_features(prob_id)
            label = self.get_label(prob_id)
            feature["label"] = label
            data[idx] = feature

            print(f"Fetching features of prob_id {prob_id} finished.")
            print(f"Current status: {idx + 1}/{tot} problems fetched.")

            # save data right after fetching each problem's solved users
            with open(self.temp_filename, "w", encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
        print("[FeatureExtractor] Temporary Notice")
        print(f"Each problem's solved users saved at {self.temp_filename}.")
        print(
            f"From now on, FeatureExtractor will automatically use the data of {self.temp_filename}."
        )
        
# e = EdgeExtractor()
#print(e.get_features(1486))