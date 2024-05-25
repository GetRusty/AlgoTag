from selenium import webdriver
from selenium.webdriver.common.by import By
import json
from typing import *
import time
import re


class Search:

    def __init__(self, cookie=None, filename="search_result.json"):
        self.filename = filename
        options = webdriver.ChromeOptions()
        # options.add_argument("headless")
        self.driver = webdriver.Chrome(options=options)
        self.driver.get("https://www.acmicpc.net")
        if cookie != None:
            self.driver.add_cookie(cookie)

    def save_to_file(self, dict):
        with open(self.filename, "w", encoding='utf-8') as f:
            json.dump(dict, f, ensure_ascii=False, indent=4)
        print("Successfully saved to", self.filename)

    #internal only
    def get_prob_list(self, tag_id):
        result = []
        dest_url = "https://www.acmicpc.net/problemset?sort=ac_desc&algo=" + tag_id + "&algo_if=and&page="
        iter = 0
        size = 0
        while True:
            iter += 1
            self.driver.get(dest_url + str(iter))
            tbody = self.driver.find_element(By.TAG_NAME, "tbody")
            entries = tbody.find_elements(By.TAG_NAME, "tr")
            if len(entries) == 0:
                break
            for entry in entries:
                elems = entry.find_elements(By.TAG_NAME, "td")
                if int(elems[3].text) > 1000:
                    continue
                size += 1
                result.append(int(elems[0].text))
                if size >= 50:
                    break
            if size >= 50:
                break
        return result

    def load_from_web(self, user_id):
        """Load lists of problems with corresponding algorithm tags
        we use top 20 tags (subject to change) for extracting problems
        for each tag, we extract 50 problems by solved desc, whose number of solved is lesser than 1000.
        """
        status_url = "https://www.acmicpc.net/problem/tags"
        self.driver.get(status_url)
        tbody = self.driver.find_element(By.TAG_NAME, "tbody")
        entries = tbody.find_elements(By.TAG_NAME, "tr")
        iter = 0
        dic = {}
        for entry in entries:
            iter += 1
            if iter > 30:
                break
            elems = entry.find_elements(By.TAG_NAME, "td")
            kor_text = elems[0].text
            eng_text = elems[1].text
            atag = elems[0].find_element(By.TAG_NAME, "a")
            tag_id = atag.get_attribute("href")
            tag_id = re.split("/problem/tag/", tag_id)[1]
            dic[tag_id] = {
                "kor_name": kor_text,
                "eng_name": eng_text,
                "tag_id": tag_id
            }

        dic2 = {}
        for d in dic.values():
            parse_result = self.get_prob_list(d['tag_id'])
            dic2[d['tag_id']] = {
                "kor_name": d['kor_name'],
                "eng_name": d['eng_name'],
                "prob_list": parse_result
            }

        self.save_to_file(dic2)
        self.driver.quit()
