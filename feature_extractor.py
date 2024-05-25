from selenium import webdriver
from selenium.webdriver.common.by import By
import json
from typing import *

class EdgeExtractor:

    def __init__(self, filename: str):
        # read json file
        with open(filename, "r") as f:
            result = json.load(f)