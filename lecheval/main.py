import json
import os
import requests
from bs4 import BeautifulSoup

import motor.motor_asyncio as mo
from pymongo import MongoClient

import time
import datetime
from datetime import date

import asyncio

from tqdm import tqdm
import traceback
from pprint import pprint

import boto3
from pymongo.server_api import ServerApi


from selenium import webdriver
from selenium.webdriver.common.by import By

# Set up the WebDriver (using Chrome in this example)
driver = webdriver.Chrome()


def get_all_dates():
    start_date = date(2022, 10, 1)
    end_date = date(2025, 1, 1)
    delta = datetime.timedelta(days=1)
    dates = []
    while start_date <= end_date:
        dates.append(
            f"{start_date.year}-{start_date.month:02d}-{start_date.day:02d}")
        start_date += delta
    return dates


def main():
    all_dates = get_all_dates()
    result = {}
    filename = "List_Url_By_Date.json"
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as json_file:
            result = json.load(json_file)

    with open(filename, 'w', encoding='utf-8') as json_file:
        for date in all_dates:
            result_dict = {}
        # Navigate to the URL
            url = "https://www.canalturf.com/courses_archives.php?date=" + date
            print(url)
            driver.get(url)

            try:
                race_elements = driver.page_source
                soup = BeautifulSoup(race_elements, 'lxml')
                accordion_div = soup.find(
                    "div", class_="panel-group accordion")
                for panel in accordion_div.find_all("div", class_="panel panel-bordered panel-dark"):
                    # Extract the text from the span with class 'text-lg'
                    text_lg = panel.find(
                        "span", class_="text-lg").get_text(strip=True)

                    # Find the list group container
                    list_group_div = panel.find(
                        "div", class_="list-group list-group-striped bord-no")

                    # Initialize a list to store tuples of URLs
                    links_list = []
                    # Iterate over each list group item
                    for list_item in list_group_div.find_all("li"):
                        # Find the button group within the list item
                        btn_group = list_item.find(
                            "div", class_="btn-group-vertical mar-rgt")

                        # Extract the two links (if available) from the button group
                        links = [a['href']
                                 for a in btn_group.find_all("a", href=True)[:2]]

                        # Add the tuple of URLs to the list
                        links_list.append(tuple(links))

                    # Add the extracted data to the result dictionary
                    result_dict[text_lg] = links_list
            except Exception as e:
                print(f"An error occurred: {e}")

            result[date] = result_dict
            json_file.seek(0)
            json.dump(result, json_file, indent=4)

    # print(result_dict)

    # Write the dictionary to a JSON file

    # Clean up and close the browser
    driver.quit()


if __name__ == "__main__":
    main()
