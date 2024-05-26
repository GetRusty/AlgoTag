from login import Login
from getpass import getpass
from search import Search
from feature_extractor import FeatureExtractor
import json
from typing import *


############ LOGIN ############

# loginObject = Login()
# id = input("[0-1] Input original id: ")
# password = getpass("[0-1] Input password: ")
# old_cookie = loginObject.login(id, password)
# print("Login Succeeded!\n")
# loginObject.quit()


############ SEARCH ############

# searchEngine = Search()
# searchEngine.load_from_web(id)


############ FeatureExtractor ############

f = FeatureExtractor()
f.save_features()