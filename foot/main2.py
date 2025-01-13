import json
import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient

import traceback
import pprint


db_client = MongoClient('localhost', 27017)
collection = db_client.foot
db = collection.all_day
db2 = collection.all_year

url = "https://www.ligue1.fr/calendrier-resultats?seasonId=1993-1994&matchDay=4"
url_empty = "https://www.ligue1.fr/calendrier-resultats?seasonId="
url_end = "&matchDay="

payload = {}
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Connection': 'keep-alive',
    'Cookie': 'SC_ANALYTICS_GLOBAL_COOKIE=4f82881f67214f898935cf2c22833d07|False; didomi_token=eyJ1c2VyX2lkIjoiMTgyNzM3YzUtNDZlMy02ZjI5LWIzMzYtYWQxOTYxMTc4MzhhIiwiY3JlYXRlZCI6IjIwMjItMDgtMDZUMTQ6MDg6MjYuNTQ0WiIsInVwZGF0ZWQiOiIyMDIyLTA4LTA2VDE0OjA4OjI2LjU0NFoiLCJ2ZW5kb3JzIjp7ImRpc2FibGVkIjpbInR3aXR0ZXIiLCJnb29nbGUiLCJjOnNwb3RpZnktZW1iZWQiLCJjOmluc3RhZ3JhbSIsImM6Z29vZ2xlYW5hLVZKeHd3YTRVIiwiYzphcHBsaWNhdGlvLXB5SnpWdzZaIiwiYzpzaXRlY29yZS1keGlVTXdLQSIsImM6YnJpZ2h0Y292ZS1UWVFZeTZ0eCIsImM6ZGlkb21pLW5ybmoyakVlIl19LCJwdXJwb3NlcyI6eyJkaXNhYmxlZCI6WyJtZXN1cmVkYS1UbU00aXRYZiIsImdlb2xvY2F0aW9uX2RhdGEiXX0sInZlbmRvcnNfbGkiOnsiZGlzYWJsZWQiOlsiZ29vZ2xlIl19LCJ2ZXJzaW9uIjoyLCJhYyI6IkFBQUEuQUFBQSJ9; ai_user=fPrss|2022-08-06T14:08:24.786Z; euconsent-v2=CPdSNYAPdSNYAAHABBENCaCgAAAAAAAAAAqIAAAAAAAA.YAAAAAAAAAAA; sxa_site=Ligue1; dtCookie=v_4_srv_6_sn_5C6BD1974E2DEAB9B52C13D879DAFB02_perc_100000_ol_0_mul_1_app-3A7b029300a64a1262_0; rxVisitor=1659794903991TIULNLI0EVJI8CHQU14T77QQOV8BHINS; dtPC=6$260072025_136h-vKPRJLVHVOPHAMRAEWAAMBLRDKIHLLAMR-0e0; rxvt=1659861872303|1659860054643; dtLatC=4; dtSa=-; ASP.NET_SessionId=1n1mucboqznhtumrdzlok4ch; ai_session=r69dX|1659860057912|1659860072205',
    'TE': 'trailers'
}

response = requests.request("GET", url, headers=headers, data=payload)


def get_a_res(result):
    sc = result.find_all(['span'])
    if sc != None and sc[3].text != "":
        return int(sc[3].text)
    return None


def get_h_res(result):
    sc = result.find_all(['span'])
    if sc != None and sc[1].text != "Reporté":
        return int(sc[1].text)
    return None


def get_ul_info(info):
    res = {}
    all_li = info.find_all(['li'], class_="match-result")

    for i in all_li:
        line = i.find(['a'], class_="clubs-container left")
        home = line.find(['div'], class_="club home").find(
            ['span']).text.replace('.', '')
        result = line.find(['div'], class_="Calendar-clubResult result")
        away = line.find(['div'], class_="club away").find(
            ['span']).text.replace('.', '')
        res_h = get_h_res(result)
        res_a = get_a_res(result)
        print(res_h, res_a)
        if res_h != None and res_a != None:
            if res_h == res_a:
                res[home] = "E"
                res[away] = "E"
            elif res_h > res_a:
                res[home] = "V"
                res[away] = "D"
            elif res_h < res_a:
                res[home] = "D"
                res[away] = "V"
        else:
            res[home] = "R"
            res[away] = "R"
    return res


def get_all_info(url, year):
    try:
        list_url = {'year': year, 'jour': int(url.split('=')[-1]), 'url': url}
        response = requests.request("GET", url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find(['div'], class_="calendar-widget full-page")
        all_ul = table.find_all(['ul'])
        for i in all_ul:
            list_url = list_url | get_ul_info(i)

        print(len(all_ul))
        pprint.pprint(list_url)
        db.update_one({'url': url}, {'$set': list_url}, upsert=True)
        return list_url

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        get_all_info(url, year)


def find_nb_page(url):
    try:
        response = requests.request("GET", url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        bar = soup.find(
            ['div'], class_="Scorebar-journeyList js-Scorebar-journeyList")
        all_a = bar.find_all(['a'])
        ok = all_a[-1].text[1:].strip()
        return int(ok[1:])
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        find_nb_page(url)


all_year = []
for i in range(29):
    all_year.append(str(1993 + i) + '-' + str(1994 + i))
print(all_year)

my_db = []
for i in all_year:
    year = {'year': i}
    print(url_empty + i + url_end + "1")
    nb_day = find_nb_page(url_empty + i + url_end + "1")
    if isinstance(nb_day, int):
        for j in range(1, nb_day):
            year['day ' + str(j)] = get_all_info(url_empty +
                                                 i + url_end + str(j), i)
        db2.update_one({'year': i}, {'$set': year}, upsert=True)
        my_db.append(year)

with open("all_year.json", "w") as final:
    ok = json.dump(my_db, final)
