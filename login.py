from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import *


class Login:

    def __init__(self, headless=False):
        if headless:
            options = webdriver.ChromeOptions()
            options.add_argument("headless")
            self.driver = webdriver.Chrome(options=options)
        else:
            self.driver = webdriver.Chrome()
        self.wait10 = WebDriverWait(self.driver, 10)
        self.wait100 = WebDriverWait(self.driver, 100)

    def login(self, user_id, password):
        self.driver.delete_all_cookies()

        login_url = "https://www.acmicpc.net/login"
        self.driver.get(login_url)

        id_input = self.driver.find_element(By.NAME, "login_user_id")
        id_input.send_keys(user_id)

        pw_input = self.driver.find_element(By.NAME, "login_password")
        pw_input.send_keys(password)

        login_btn = self.driver.find_element(By.ID, "submit_button")
        login_btn.click()

        ec_bot_detection = EC.element_to_be_clickable(
            (By.XPATH, "/html/body/div[4]"))
        ec_login_succeed = EC.title_is("Baekjoon Online Judge")
        ec_login_failed = EC.text_to_be_present_in_element((By.CLASS_NAME, "color-red"),\
            "아이디 / 이메일 또는 비밀번호가 잘못되었습니다.")

        while True:
            self.wait10.until(
                EC.any_of(ec_bot_detection, ec_login_succeed, ec_login_failed))

            # BOT DETECTION
            if self.driver.find_elements(By.XPATH, "/html/body/div[4]") != []:
                print("Please solve the CAPTCHA Bot detection...")
                self.wait100.until(EC.none_of(ec_bot_detection))
            # Wrong ID / PW
            elif self.driver.find_elements(By.CLASS_NAME, "color-red") != []:
                print("Wrong ID or PW.")
                raise Exception("login failed")
            # Login Succeed
            else:
                break

        login_cookie = self.driver.get_cookie("OnlineJudge")
        print('login_cookie:', login_cookie)

        return login_cookie

    def quit(self):
        self.driver.quit()
