import os
import time
import unicodedata
from datetime import datetime

import fire
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webdriver import WebDriver


def login(driver: WebDriver, username: str, password: str):
    username_elem = driver.find_element_by_name("username")
    username_elem.clear()
    username_elem.send_keys(username)

    password_elem = driver.find_element_by_name("password")
    password_elem.clear()
    password_elem.send_keys(password)

    password_elem.send_keys(Keys.RETURN)


def navigate_to_ifund(driver: WebDriver, sleep_sec: int):
    ifund_elem = driver.find_element_by_name("ifund")
    ifund_elem.click()
    time.sleep(sleep_sec)

    for window_after in driver.window_handles:
        print("window_after", window_after)
        driver.switch_to.window(window_after)
        login_elem = driver.find_elements_by_xpath("//a[@href='javascript:btn_Click(\"0\")']")

        if len(login_elem) == 0:
            continue
        else:
            login_elem[0].click()
            return None

    raise ValueError("Something is wrong in the login page, cannot find login button")


def navigate_to_portfolio(driver: WebDriver):
    to_portfolio_elem = driver.find_elements_by_xpath("//a[@href='portfolio.asp']")
    to_portfolio_elem[0].click()


def save_portfolio_info(driver: WebDriver, output_path: str):
    table_elem = driver.find_elements_by_xpath('//table[@width="98%"]')
    html_doc = table_elem[0].get_attribute('innerHTML')

    today_str = datetime.strftime(datetime.today(), "%Y-%m-%d")

    with open(os.path.join(output_path, "html", f"{today_str}.html"), "w") as f:
        f.write(html_doc)

    soup = BeautifulSoup(html_doc, 'html.parser')

    data = []
    for row in soup.find_all('tr'):
        row_data = []
        for col in row.find_all('td'):
            col_val = unicodedata.normalize('NFD', col.text).replace(u'\xa0', u' ').strip()

            try:
                col_val = float(col_val.replace(",", ""))
            except ValueError:
                col_val = col_val

            if isinstance(col_val, float) or len(col_val) > 0:
                row_data.append(col_val)
        if len(row_data) == 11:
            data.append(row_data)

    col_names = ["fund", "avg_price", "unit", "budget", "total_price", "P/L", "%P/L", "NAV_current",
                 "NAV_updated", "fund_house", "limit_time"]
    nav_df = pd.DataFrame(data, columns=col_names)
    nav_df["NAV_updated"] = pd.to_datetime(nav_df["NAV_updated"], format="%d-%b-%y")

    budget = nav_df["budget"].sum()
    profit_loss = nav_df["total_price"].sum() - budget

    summary_data = {
        "fund": ["Summary"],
        "avg_price": [None],
        "unit": [None],
        "budget": [nav_df["budget"].sum()],
        "total_price": [nav_df["total_price"].sum()],
        "P/L": [profit_loss],
        "%P/L": [profit_loss / budget * 100],
        "NAV_current": [None],
        "NAV_updated": [None],
    }
    nav_df = nav_df.append(pd.DataFrame(summary_data), ignore_index=True)[col_names]
    print(nav_df)

    output_path = os.path.join(output_path, "json", f"{today_str}.json")
    nav_df.to_json(output_path, orient="records", lines=True)


def main(output_dir: str,
         firefox_driver_path: str = "geckodriver",
         username: str = None,
         password: str = None,
         nomura_url: str = None,
         sleep_sec: int = 5):

    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override",
                           "Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0")
    profile.set_preference("javascript.enabled", True)
    driver = webdriver.Firefox(profile, executable_path=firefox_driver_path)

    if nomura_url is None:
        nomura_url = "https://www.nomuradirect.com/en/main/default.aspx"
    driver.get(nomura_url)

    time.sleep(sleep_sec)
    if username is None:
        username = os.getenv("USERNAME")

    if password is None:
        password = os.getenv("PASSWORD")

    login(driver, username=username, password=password)

    time.sleep(sleep_sec)
    navigate_to_ifund(driver, sleep_sec)

    time.sleep(sleep_sec)
    navigate_to_portfolio(driver)

    time.sleep(sleep_sec)
    save_portfolio_info(driver, output_dir)

    driver.quit()


if __name__ == "__main__":
    fire.Fire(main)
