import json
import time
import logging
from typing import Union
from urllib.parse import urlparse, parse_qs

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import *
from selenium.webdriver.remote.webelement import WebElement

from kiteconnect import KiteConnect


logging.basicConfig(filename="login.log", level=logging.DEBUG)


class KiteLogin(object):
    """
    logins to kite-connect portal and saves the 'request_token'

    :return:
    """
    def __init__(self, headless: bool = True, login_url: str = None):
        """
        initializes webdriver, and other necessary attributes and runs 'login' method, which returns the 'request_token'

        Optional Parameters:
            headless: bool
                default True
            login_url: str
                KiteConnect.login_url (automatically takes from KiteConnect object)

        :param headless: True (runs in background)
        :param login_url: KiteConnect.login_url
        """
        self.timeout = 5

        self.__api_key = self.__username = self.__password = self.__pin = None
        self.__get_login_details()

        self.login_url = login_url if login_url else KiteConnect(api_key=self.__api_key).login_url()

        options = Options()
        options.headless = headless

        self.driver = Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.__request_token = self.__login()

    def __get_login_details(self) -> None:
        """
        extracts credentials from login.json file

        :return: None
        """
        try:
            with open("login.json") as file:
                login = json.load(file)
                self.__api_key = login["api_key"]
                self.__username = login['username']
                self.__password = login['password']
                self.__pin = login['pin']
        except Exception as e:
            logging.warning(e)

    def _get_element_by_css(self, selector: str) -> WebElement:
        """
        wait until the element appears and returns the element

        :param selector: css selector of element
        :return: Element
        """
        return WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def _find_error(self) -> Union[str, None]:
        """
        returns errors while login (if any) else None

        :return: error message
        """
        try:
            return self._get_element_by_css(".error").text
        except TimeoutException:
            return None

    def _raise_error(self) -> None:
        """
        raises error if _find_error()

        :return: None
        """
        has_error = self._find_error()
        if has_error:
            logging.warning(has_error)
            self.quit()
            raise ValueError(has_error)

    def _click_submit(self) -> None:
        self._get_element_by_css("button[type=submit]").click()

    def quit(self) -> None:
        """
        to close webdriver without any errors

        :return: None
        """
        self.driver.quit()
        time.sleep(1)

    def __login(self) -> str:
        """
        login to the kite connect using webdriver and returns request_token

        :return: request_token
        """
        self.driver.get(self.login_url)

        # raises AssertionError, when api_key is invalid
        try:
            body = self._get_element_by_css("body").text
            assert (body[0] != "{" and body[-1] != "}"), json.loads(body)['message']  # invalid API KEY.
        except AssertionError as e:
            logging.warning(e)
            self.quit()
            raise AssertionError(e)

        username = self._get_element_by_css("input#userid")
        password = self._get_element_by_css("input#password")

        username.send_keys(self.__username)
        password.send_keys(self.__password)

        # click login
        self._click_submit()
        # time.sleep(1)

        # if username or password is wrong raise error
        self._raise_error()

        pin = self._get_element_by_css("input#pin")
        pin.send_keys(self.__pin)

        current_url = self.driver.current_url

        self._click_submit()

        time.sleep(.5)
        if self.driver.current_url == current_url:
            # if pin is wrong raise error
            self._raise_error()

        time.sleep(.5)
        current_url = self.driver.current_url

        logging.info("Logged in successfully!!")
        print("logged in successfully", current_url)

        time.sleep(1)

        # request token
        rt = parse_qs(urlparse(current_url).query)['request_token'][0]

        logging.info(f"Request Token: {rt}")

        self.quit()
        return rt

    def get_request_token(self):
        return self.__request_token


if __name__ == "__main__":
    request_token = KiteLogin().get_request_token()
    print(request_token)
    
