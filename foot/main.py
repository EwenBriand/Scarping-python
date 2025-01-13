import json
import os
import requests
import httpx
from bs4 import BeautifulSoup

import motor.motor_asyncio as mo
from pymongo import MongoClient

import time
import datetime
from datetime import date

import asyncio

from tqdm import tqdm
import traceback
import pprint

import boto3
from pymongo.server_api import ServerApi

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cookie': 'didomi_token=eyJ1c2VyX2lkIjoiMTgyNzMyNTEtNzQ5OC02MmJiLWE3YTgtZmY5NTU2N2I4ZmFiIiwiY3JlYXRlZCI6IjIwMjItMDgtMDZUMTI6MzM6MTAuMTE3WiIsInVwZGF0ZWQiOiIyMDIyLTA4LTA2VDEyOjMzOjEwLjExN1oiLCJ2ZW5kb3JzIjp7ImRpc2FibGVkIjpbImFtYXpvbiIsImdvb2dsZSIsImM6YWN4aW9tIiwiYzpnb29nbGVhbmEtNFRYbkppZ1IiLCJjOnVucnVseWdyby1uS3lMcWRLaSJdfSwicHVycG9zZXMiOnsiZGlzYWJsZWQiOlsiZGV2aWNlX2NoYXJhY3RlcmlzdGljcyIsImdlb2xvY2F0aW9uX2RhdGEiXX0sInZlbmRvcnNfbGkiOnsiZW5hYmxlZCI6WyJnb29nbGUiXX0sInZlcnNpb24iOjIsImFjIjoiQUFBQS5DS1dBQ0NLVSJ9; _ga=GA1.2.415128595.1659789187; _gid=GA1.2.988074213.1659789187; euconsent-v2=CPdSNYAPdSNYAAHABBENCaCgAAAAAH_AAAAAAAAR2AJMNW4gC7EscCbaMIoUQIwrCQ6gUAFFAMLRBYQOrgp2VwE-sIWACAUARgRAhxBRgwCAAQCAJCIgJAjwQCIAiAQAAgAVAIQAEbAILACwMAgAFANCxQigCECQgyICI5TAgIkSCgnsrEEoO9DTCEOssAKDR_xUICJQAhWBkJCwchwRICXiyQLMUb5ACMEKAUSoAAAA.YAAAD_gAAAAA; _gat=1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'TE': 'trailers'
}

db_client = MongoClient('localhost', 27017)
collection = db_client.foot
db = collection.all_match
db2 = collection.all_stats

url_beg = "https://www.footmercato.net"
url_empty = "https://www.footmercato.net/france/ligue-1/"


def find_all_url(url):
    list_url = []
    response = requests.request("GET", url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    if soup == None:
        return []
    li_url = soup.find(['ul'], class_='selectBox__modal__content')
    if li_url == None:
        return []
    all_url = li_url.find_all(['li'])
    if all_url == None:
        return []
    print(len(all_url))
    for i in all_url:
        ok = i.find(['a'])
        if ok != None:
            list_url.append(ok['href'])
    pprint.pprint(list_url)
    return list_url


def find_score(info):
    v_d = info.find(
        ['span'], class_="matchItem__score__value matchItem__score__value--home")
    v_v = info.find(
        ['span'], class_="matchItem__score__value matchItem__score__value--away")
    if v_v is None or v_d is None:
        return 3
    val_d = int(v_d.text)
    val_v = int(v_v.text)

    if val_d > val_v:
        return 0
    if val_d < val_v:
        return 1
    if val_d == val_v:
        return 2


def add_day_in_db(url):
    print(url)
    list_url = []
    response = requests.request("GET", url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    li_url = soup.find(['ul'], class_='matches')
    li_match = li_url.find_all(['li'])
    li = []
    for i in range(len(li_match)):
        if li_match[i].has_attr("data-status") and li_match[i]["data-status"] == "played":
            li.append(li_match[i])
    print(len(li))

    li_matches = []
    for i in li:
        match = {}
        span_dom = i.find(
            ['span'], class_="matchItem__team matchItem__team--home")
        span_vis = i.find(
            ['span'], class_="matchItem__team matchItem__team--away")
        span_info = i.find(['span'], class_="matchItem__infos")
        match['name_dom'] = span_dom.find(
            ['span'], class_="matchItem__team__name").text.strip()
        match['name_vis'] = span_vis.find(
            ['span'], class_="matchItem__team__name").text.strip()
        match['result'] = find_score(span_info)
        if match['result'] == 3:
            continue
        match['url'] = url
        db.update_one({'url': match['url'], 'result': match['result'], 'name_vis': match['name_vis'],
                      'name_dom': match['name_dom']}, {'$set': match}, upsert=True)


# all_year = []
# for i in range(22):
#     all_year.append(str(2000 + i) + '-' + str(2001 + i))
# print(all_year)
# for i in all_year:
#     res = find_all_url(url_empty + i + "/resultat")
#     add_day_in_db(url_empty + "2020-2021" + "/resultat")
#     for i in range(0, len(res)):
#         add_day_in_db(url_beg + res[i])


all_db = list(db.find({'_id': {'$exists': True}}))
print(len(all_db))

print(all_db[0])


for i in all_db:
    case = 0
    exist = db2.find_one({'equipe1': i['name_dom'], 'equipe2': i['name_vis']})

    if exist == None:
        exist = db2.find_one(
            {'equipe1': i['name_vis'], 'equipe2': i['name_dom']})
        if exist == None:
            db2.insert_one({'equipe1': i['name_dom'], 'equipe2': i['name_vis'],
                            'egaliter': 0, 'equipe1_win': 0, 'equipe2_win': 0, 'nb_total_match': 0})
            exist = db2.find_one(
                {'equipe1': i['name_dom'], 'equipe2': i['name_vis']})
        else:
            case = 1

    if i['result'] == 2:
        db2.update_one({'_id': exist['_id']}, {
                       '$set': {'egaliter': exist['egaliter'] + 1}})
    elif i['result'] == 0 and case == 0:
        db2.update_one({'_id': exist['_id']}, {
                       '$set': {'equipe1_win': exist['equipe1_win'] + 1}})
    elif i['result'] == 1 and case == 0:
        db2.update_one({'_id': exist['_id']}, {
                       '$set': {'equipe2_win': exist['equipe2_win'] + 1}})
    elif i['result'] == 1 and case == 1:
        db2.update_one({'_id': exist['_id']}, {
                       '$set': {'equipe1_win': exist['equipe1_win'] + 1}})
    elif i['result'] == 0 and case == 1:
        db2.update_one({'_id': exist['_id']}, {
                       '$set': {'equipe2_win': exist['equipe2_win'] + 1}})

    db2.update_one({'_id': exist['_id']}, {
        '$set': {'nb_total_match': exist['nb_total_match'] + 1}})

all_db = list(db2.find({'_id': {'$exists': True}}))

for i in all_db:
    perc_e1 = i['equipe1_win'] * 100 / (i['nb_total_match'])
    perc_e2 = i['equipe2_win'] * 100 / (i['nb_total_match'])
    perc_eg = i['egaliter'] * 100 / (i['nb_total_match'])
    db2.update_one({'_id': i['_id']}, {
        '$set': {'perc_equipe1_win': perc_e1, 'perc_egaliter': perc_eg, 'perc_equipe2_win': perc_e2}})
