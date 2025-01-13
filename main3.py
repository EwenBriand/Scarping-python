from urllib.parse import urlparse, parse_qs
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


def extract_idjockey(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('idjockey', [None])[0]


folder_path = "data_b_dates"


async def fetch(session, url, headers):
    try:
        async with session.get(url, headers=headers, ssl=False) as response:
            raw_bytes = await response.read()
            try:
                return raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return raw_bytes.decode('latin-1')
    except Exception as e:
        print(e)
        return ""


def get_all_urls():
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    cheveau_list = []
    jocket_list = []

    for json_file in json_files:
        file_path = os.path.join(folder_path, json_file)
        try:
            if os.stat(file_path).st_size > 0:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for course in data["courses"]:
                        temp = [d["fiche_cheval"] for d in course["resultat"]]
                        temp2 = [d["fiche_jockey"] for d in course["resultat"]]
                        cheveau_list.append(temp)
                        jocket_list.append(temp2)
        except Exception as e:
            print(file_path)
            print(e)
            continue

    return (cheveau_list, jocket_list)


def get_cheval_info(table):
    data = {}

    if table:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 2:
                key = cols[0].text.strip().replace('\xa0', ' ')
                value = cols[1].text.strip().replace('\xa0', ' ')
                data[key] = value

    return data


def extract_table_info2(table, keys):
    table_data = []

    if table:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            i = 0
            tmp = {}
            for col in cols:
                if col.find('a') is not None:
                    tmp[keys[i]] = col.find('a').get('href')
                else:
                    tmp[keys[i]] = col.text.strip()
                i += 1

                if i == len(keys):
                    break
            table_data.append(tmp)
    return table_data


def extract_table_info(soup, keys, start=3):
    data = {}

    h2_tags = soup.find_all('h2')[start:]
    for h2 in h2_tags:
        table = h2.find_next(
            'table', {"class": "table table-striped table-condensed bord-all"})
        if table:
            rows = table.find_all('tr')
            table_data = []
            for row in rows:
                cols = row.find_all('td')
                i = 0
                tmp = {}
                for col in cols:
                    tmp[keys[i]] = col.text.strip()
                    i += 1
                    if i == len(keys):
                        break
                table_data.append(tmp)
            data[h2.text.strip()] = table_data

    return data


async def extract_cheval(url, session):
    try:
        res = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cookie': 'ct_params=%7B%22mobile%22%3A%220%22%7D; _ga_8RVTQ8Q422=GS1.1.1736601872.15.0.1736601872.60.0.0; _ga=GA1.1.260454489.1736155003; _sharedID=1cefc8b7-bd30-4b6f-8fd2-a2e52b2e429e; _sharedID_cst=kSylLAssaw%3D%3D; interstitiel=1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'trailers'
        }

        html = await fetch(session, url, headers)
        soup_p = BeautifulSoup(html, 'html.parser')
        div = soup_p.find("div", {"class": "panel-body"})
        count = 0
        while (div is None or count == 20):
            count += 1
            html = await fetch(session, url, headers)
            soup_p = BeautifulSoup(html, 'html.parser')
            div = soup_p.find("div", {"class": "panel-body"})
        all_table = div.find_all(
            "table", {"class": "table table-striped table-condensed bord-all"})

        res["Nom du cheval"] = soup_p.find(
            "h1", {"class": "page-header"}).text.strip().split(" - ")[0]

        res["info_cheval"] = get_cheval_info(all_table[0])
        res["Palmares"] = get_cheval_info(all_table[1])
        res["Derniere_performance"] = extract_table_info2(
            all_table[2], ["Place", "Date", "course information"])
        res.update(extract_table_info(
            div, ["Place", "Nombre de fois", "Pourcentage"]))

        # pprint(res)

        return res
    except Exception as e:
        print(url)
        print(e)
        with open(f"data_cheveaux_err/{url.split('=')[-1]}.txt", "a") as f:
            f.write(url + "\n" + str(e) + "\n" + html)
        return {}


async def extract_jocket(url, session):
    try:
        res = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.canalturf.com/resultats-PMU/2025-01-06/lyon-la-soie/359838_prix-des-terres-froides.html',
            'Connection': 'keep-alive',
            'Cookie': 'ct_params=%7B%22mobile%22%3A%220%22%7D; _ga_8RVTQ8Q422=GS1.1.1736685058.17.1.1736685089.29.0.0; _ga=GA1.1.260454489.1736155003; _sharedID=1cefc8b7-bd30-4b6f-8fd2-a2e52b2e429e; _sharedID_cst=kSylLAssaw%3D%3D; interstitiel=1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

        html = await fetch(session, url, headers)
        soup_p = BeautifulSoup(html, 'html.parser')
        div = soup_p.find("div", {"class": "panel-body"})
        count = 0
        while (div is None or count == 20):
            count += 1
            html = await fetch(session, url, headers)
            soup_p = BeautifulSoup(html, 'html.parser')
            div = soup_p.find("div", {"class": "panel-body"})
        all_table = div.find_all(
            "table", {"class": "table table-striped table-condensed bord-all"})

        res["Nom du jocket"] = soup_p.find(
            "h1", {"class": "page-header"}).text.strip().split(" - ")[0]

        res["Derniere_performance"] = extract_table_info2(
            all_table[0], ["Place", "Date", "course information"])
        res.update(extract_table_info(
            div, ["Place", "Nombre de fois", "Pourcentage"], 2))

        return res
    except Exception as e:
        print(url)
        print(e)
        with open(f"data_jockets_err/{extract_idjockey(url)}.txt", "a") as f:
            f.write(url + "\n" + str(e) + "\n" + html)
        return {}


async def process_url_c(url, session):
    id = url.split("=")[-1]

    if os.path.exists(f"data_cheveaux/{id}.json"):
        return

    cheval_data = await extract_cheval(url, session)

    with open(f"data_cheveaux/{id}.json", 'w', encoding='utf-8') as json_file:
        json_file.seek(0)
        json.dump(cheval_data, json_file,
                  ensure_ascii=False, indent=4)
    if cheval_data == {}:
        os.remove(f"data_cheveaux/{url.split('=')[-1]}.json")


async def process_url_j(url, session):
    id = extract_idjockey(url)

    if os.path.exists(f"data_jockets/{id}.json"):
        return

    jocket_data = await extract_jocket(url, session)

    with open(f"data_jockets/{id}.json", 'w', encoding='utf-8') as json_file:
        json_file.seek(0)
        json.dump(jocket_data, json_file,
                  ensure_ascii=False, indent=4)
    if jocket_data == {}:
        os.remove(f"data_jockets/{id}.json")


async def worker(queue, session, type, pbar):
    while not queue.empty():
        url = queue.get()
        # for url in tqdm(url_list, desc=f"Processing URLs for {date2}", leave=False):
        if type == "cheval":
            await process_url_c(url, session)
        else:
            await process_url_j(url, session)
        queue.task_done()
        pbar.update(1)


async def main():

    last_date = date(2021, 4, 1)

    cheveaux, jockeys = get_all_urls()
    # pprint(all_dates["2008-01-01"])

    queue = Queue()
    queue2 = Queue()

    for url in cheveaux:
        for u in url:
            queue.put((u))

    for url in jockeys:
        for u in url:
            queue2.put((u))

    print(queue.qsize())
    print(queue2.qsize())
    # print_lock = asyncio.Lock()
    # async with print_lock:
    #     print(queue.qsize())
    #     print(len(all_dates))

    async with aiohttp.ClientSession() as session:
        tasks = []
        num_workers = 50  # Number of concurrent workers
        with tqdm(total=queue.qsize(), desc="Processing cheveaux") as pbar:
            for _ in range(num_workers):
                tasks.append(worker(queue, session, "cheval", pbar))
            await asyncio.gather(*tasks)

    async with aiohttp.ClientSession() as session:
        tasks = []
        num_workers = 50  # Number of concurrent workers
        with tqdm(total=queue2.qsize(), desc="Processing jockets") as pbar:
            for _ in range(num_workers):
                tasks.append(worker(queue2, session, "jocket", pbar))
            await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
