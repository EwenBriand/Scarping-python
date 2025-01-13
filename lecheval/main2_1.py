from pymongo.server_api import ServerApi
import boto3
import re
from pprint import pprint
import traceback
# from tqdm import tqdm
import json
import os
import requests
from bs4 import BeautifulSoup

import motor.motor_asyncio as mo
from pymongo import MongoClient

import time
from datetime import datetime, date

import aiohttp
import json
from tqdm.asyncio import tqdm
from datetime import datetime
from queue import Queue

import asyncio
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


async def fetch(session, url, headers):
    async with session.get(url, headers=headers, ssl=False) as response:
        raw_bytes = await response.read()
        try:
            return raw_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return raw_bytes.decode('latin-1')


def get_some_info(soup):
    div = soup.find("div", {"class": "col-md-8"})
    race_info = div.find('span', class_='h4').prettify()
    race_info = race_info.replace('<span class="h4">', '').replace(
        '\n', '').replace('<small>', '').replace('</small>', '').split('<br/>')

    # Extracting specific details
    race_name = race_info[0].strip()  # "PRIX DE LA CONCORDE"
    location_time = race_info[1].split('-')
    location = location_time[1].strip().split(' ')[-1]  # "ENGHIEN"
    details = race_info[2].split(' - ')
    race_type = details[0].strip()  # "TROT ATTELE"
    distance = details[1].strip()  # "2875m"
    prize = details[2].strip().split('.')[0]  # "60000.00€"

    # Creating the list with the extracted information
    res = {"nom_de_la_course": race_name, "lieux": location,
           "type_de_course": race_type, "distance": distance, "prix": prize, "heure": location_time[0]}
    return res


def get_prono_info(soup):
    table = soup.find("table", {
                      "class": "table table-striped table-condensed bord-all", "id": "TablePartants"})
    headTable = table.find_all('th')
    headers = []

    for header in headTable:
        if header.find('a') is not None:
            headers.append(header.find('a').find('img').get('alt'))
        else:
            headers.append(header.text.strip())
        if "/" in headers[-1]:
            headers[-1] = "Jockey"
            headers.append("Entraineur")

    # print(headers)

    rows = []
    i = 0
    for row in table.find_all('tr')[1:]:  # Skip the header row
        cols = {}
        i = 0
        for col in row.find_all('td'):
            if col.find('strong') is not None:
                if col.find('a') and 'cheval' in col.find('a').get('title', ''):
                    cols[headers[i]] = col.find('strong').get_text()
                else:
                    cols[headers[i]] = col.find('strong').get_text()
                    i += 1
                    cols[headers[i]] = col.find('small').get_text()
            else:
                cols[headers[i]] = col.text.strip()
            i += 1
        rows.append(cols)

    # pprint(rows)

    return rows


def get_result_info(soup, partant):
    table = soup.find("table", {
                      "class": "table table-striped table-condensed bord-all"})
    if table is None:
        return ([], 0)
    headTable = table.find_all('th')
    headers = []

    for header in headTable:
        if header.find('a') is not None:
            headers.append(header.find('a').find('img').get('alt'))
        else:
            headers.append(header.text.strip())

    # print(headers)

    rows = []
    i = 0
    for row in table.find_all('tr')[:-1]:  # Skip the header row
        cols = {}
        i = 0
        for col in row.find_all('td'):
            if col.find('a') is not None:
                if 'cheval' in col.find('a').get('title', ''):
                    cols["fiche_cheval"] = col.find('a').get('href')
                elif 'jockey' in col.find('a').get('title', ''):
                    cols["fiche_jockey"] = col.find('a').get('href')
            cols[headers[i]] = col.text.strip()
            i += 1
        rows.append(cols)

    # pprint(rows)

    non_partant_number = partant

    div = soup.find("div", {"class": "well well-sm"})
    if div is not None and 'Non-partant' in div.text:
        match = re.search(r'\d+', div.text[::-1])
        if match:
            non_partant_number = int(match.group()[::-1])

    return (rows, non_partant_number)


# Set up the WebDriver (using Chrome in this example)


async def extract_course(url, date, session):
    # print(url)
    res = {}
    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.canalturf.com/pronostics-PMU/2005-08-11/enghien/11703_prix-de-la-muette.html',
        'Connection': 'keep-alive',
        'Cookie': 'ct_params=%7B%22mobile%22%3A%220%22%7D; _ga_8RVTQ8Q422=GS1.1.1736245603.3.0.1736245603.60.0.0; _ga=GA1.1.260454489.1736155003; _sharedID=1cefc8b7-bd30-4b6f-8fd2-a2e52b2e429e; _sharedID_cst=kSylLAssaw%3D%3D',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache'
    }

    prono = await fetch(session, url[0], headers)
    result = await fetch(session, url[1], headers)

    soup_p = BeautifulSoup(prono, 'html.parser')
    soup_r = BeautifulSoup(result, 'html.parser')

    info1 = get_some_info(soup_p)
    info2 = get_prono_info(soup_p)
    info3, partant = get_result_info(soup_r, len(info2))
    # pprint(info2)

    res["urls"] = url
    res["prix"] = info1["prix"]
    res["distance"] = info1["distance"]
    res["type_de_course"] = info1["type_de_course"]
    res["lieux"] = info1["lieux"]
    res["heure"] = info1["heure"]
    res["nom_de_la_course"] = info1["nom_de_la_course"]
    res["date"] = date

    res["nb_participants"] = len(info2)
    res["list_participants_and_prono"] = info2
    res["nb_participants_partants"] = partant
    res["resultat"] = info3
    return res


def get_all_urls():
    result_dict = {}
    with open("List_Url_By_Date.json", 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)
        for date2, reunions in json_data.items():
            url_list = []
            for reunion, events in reunions.items():
                for event in events:
                    # Add all URLs from the event list to url_list
                    url_list.append(event)
            # Assign the list of URLs to the date
            result_dict[date2] = url_list
    return result_dict


async def process_url(url_list, date2, session):
    error = []
    list_road = {"courses": [], "nb_courses": 0}

    with open(f"data_b_dates/{date2}.json", 'w', encoding='utf-8') as json_file:
        with open(f"data_b_dates_err/{date2}.json", 'w', encoding='utf-8') as error_file:
            for url in tqdm(url_list, desc=f"Processing URLs for {date2}", leave=False):
                try:
                    course_data = await extract_course(url, date2, session)
                    list_road["courses"].append(course_data)
                    list_road["nb_courses"] += 1
                    json_file.seek(0)
                    json.dump(list_road, json_file,
                              ensure_ascii=False, indent=4)
                except Exception as e:
                    tmp = {"url": url, "date": date2, "error": str(e)}
                    error.append(tmp)
                    error_file.seek(0)
                    json.dump(error, error_file, ensure_ascii=False, indent=4)

    if len(error) == 0:
        os.remove(f"data_b_dates_err/{date2}.json")

    if list_road["nb_courses"] == 0:
        os.remove(f"data_b_dates/{date2}.json")


async def worker(queue, session):
    while not queue.empty():
        date2, url_list = queue.get()
        # for url in tqdm(url_list, desc=f"Processing URLs for {date2}", leave=False):
        await process_url(url_list, date2, session)
        queue.task_done()


async def main():

    last_date = date(2021, 4, 1)

    all_dates = get_all_urls()
    # pprint(all_dates["2008-01-01"])

    queue = Queue()

    for date2, url_list in all_dates.items():
        if datetime.strptime(date2, "%Y-%m-%d").date() >= last_date:
            queue.put((date2, url_list))

    print_lock = asyncio.Lock()
    async with print_lock:
        print(queue.qsize())
        print(len(all_dates))

    async with aiohttp.ClientSession() as session:
        tasks = []
        num_workers = 50  # Number of concurrent workers
        for _ in range(num_workers):
            tasks.append(worker(queue, session))
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
