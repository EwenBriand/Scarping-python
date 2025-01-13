import requests
import json
from pprint import pprint
import pymongo
import time
from random import randint

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["lb"]
col = db["imo"]


def get_imo_page(nb_p):

    url = "https://api.leboncoin.fr/finder/search"

    payload = json.dumps({
        "filters": {
            "category": {
                "id": "9"
            },
            "enums": {
                "ad_type": [
                    "offer"
                ],
                "real_estate_type": [
                    "2"
                ]
            }
        },
        "limit": 100,
        "limit_alu": 3,
        "limit_sponsored": 1,
        "sort_by": "time",
        "sort_order": "desc",
        "offset": 35,
        "disable_total": True,
        "referrer_id": "01d47f1b-4369-4ddc-9964-1ff1d7a8e308",
        "pivot": "{\"es_pivot\":\"1696238945000|2409873251\",\"page_number\":" + str(nb_p) + "}",
        "extend": True,
        "listing_source": "pagination"
    })
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0',
        'Accept': '*/*',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.leboncoin.fr/f/ventes_immobilieres/real_estate_type--2/p-2',
        'api_key': 'ba0c2dad52b3ec',
        'content-type': 'application/json',
        'Origin': 'https://www.leboncoin.fr',
        'Connection': 'keep-alive',
        'Cookie': 'datadome=38N~r9BC6jIZViQ3MUHZ~l4bpNpK4kZ6xPGsKU6pfHr~eFbtD3OgT0uBx-c~i36eYUgGrzOHIO4QiHX7Rx~lItOmMO3j9QzpsdA3E1dBAyVtImPgxf9NfuANhIFXtwAX; __Secure-Install=5ececb36-5370-4627-adfd-1f2b74aabb68; __Secure-InstanceId=5ececb36-5370-4627-adfd-1f2b74aabb68; utag_main=v_id:018aefba5f1d00b0e3d4968a1bd805046001900900bd0$_sn:1$_ss:0$_pn:2%3Bexp-session$_st:1696240911038$ses_id:1696239083293%3Bexp-session; didomi_token=eyJ1c2VyX2lkIjoiMThhZWZiYTUtZTI0Ny02ZGJhLWIwZjAtMTlmMWQ1NjdiMDViIiwiY3JlYXRlZCI6IjIwMjMtMTAtMDJUMDk6MzE6MjYuNjM2WiIsInVwZGF0ZWQiOiIyMDIzLTEwLTAyVDA5OjMxOjI2LjYzNloiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYzpsYmNmcmFuY2UiLCJjOnJldmxpZnRlci1jUnBNbnA1eCIsImM6ZGlkb21pIiwiYzp6YW5veCIsImM6cHVycG9zZWxhLTN3NFpmS0tEIiwiYzppbmZlY3Rpb3VzLW1lZGlhIiwiYzp0dXJibyIsImM6YWRpbW8tUGhVVm02RkUiLCJjOnVuZGVydG9uZS1UTGpxZFRwZiIsImM6cm9ja2VyYm94LWZUTThFSjlQIiwiYzphZmZpbGluZXQiXX0sInB1cnBvc2VzIjp7ImVuYWJsZWQiOlsiZXhwZXJpZW5jZXV0aWxpc2F0ZXVyIiwibWVzdXJlYXVkaWVuY2UiLCJwZXJzb25uYWxpc2F0aW9ubWFya2V0aW5nIiwicHJpeCJdfSwidmVuZG9yc19saSI6eyJlbmFibGVkIjpbImdvb2dsZSIsImM6cHVycG9zZWxhLTN3NFpmS0tEIiwiYzppbmZlY3Rpb3VzLW1lZGlhIiwiYzp0dXJibyIsImM6YWRpbW8tUGhVVm02RkUiLCJjOnVuZGVydG9uZS1UTGpxZFRwZiIsImM6cm9ja2VyYm94LWZUTThFSjlQIiwiYzphZmZpbGluZXQiXX0sInZlcnNpb24iOjIsImFjIjoiRExXQXdBRVlBTElDU3dJQmdSSkFsSUIwNERxd0lHQVJVQWpuQkpPQ1dzRkJnS0VRVVdncm5oWUtGZ3dMYndYR0F1V0JnTURDSUdXby5ETFdBd0FFWUFMSUNTd0lCZ1JKQWxJQjA0RHF3SUdBUlVBam5CSk9DV3NGQmdLRVFVV2dybmhZS0Znd0xid1hHQXVXQmdNRENJR1dvIn0=; euconsent-v2=CPzBFAAPzBFAAAHABBENDYCgAP_AAH7AAAAAJoNB_G_dTyPi-f59YvtwcQ1P4VQnoyACjgaNAwwJiRLBMI0EhmAIKAHqAAACIBAkICZAAQBlCAHAAAAA4IEAASMMAAAAIRAIIgCAAEAAAmJICABZC5AAAQAQgkwAABUAgAICABsgSDAAAAAAFAAAAAgAAAAAAAAAAAAAQAAAAAAAAgAAAAAAAAAAAAAEABAAAAAAAAAAAAAAAAAEEAQATDQuIAGwJGQmkDCIAACMIAgCgBABRAJCwQAEBIgAEEYACjAAAABFAAAAAAAAEBAAAAAAgAQgAAAAYEAgAAAEAAAAEAgEAAAAACAAABAAAAAEAMAAAAAAgAIAAAIAQAAhAAgAJAgACAAAAgAAAAAAAAAgEAAAAAAAAAAAAAAAAQAxQAGAAIgoDAAMAARBQIAAYAAiCgAA.f_gAD9gAAAAA; include_in_experiment=true; ry_ry-l3b0nco_realytics=eyJpZCI6InJ5X0UwMTEwMTI3LUY5MDYtNEU5NC05RDcxLUUwMjZFNjY5NDc0OSIsImNpZCI6bnVsbCwiZXhwIjoxNzI3Nzc1MDg3NDY0LCJjcyI6bnVsbH0%3D; ry_ry-l3b0nco_so_realytics=eyJpZCI6InJ5X0UwMTEwMTI3LUY5MDYtNEU5NC05RDcxLUUwMjZFNjY5NDc0OSIsImNpZCI6bnVsbCwib3JpZ2luIjp0cnVlLCJyZWYiOm51bGwsImNvbnQiOm51bGwsIm5zIjpmYWxzZX0%3D; _gcl_au=1.1.1994808303.1696239087; _hjSessionUser_2783207=eyJpZCI6ImQ4NzZlNzNiLTMwODQtNWM4OS1iNjA2LWUzZThkNzgyMGQzNCIsImNyZWF0ZWQiOjE2OTYyMzkwODgxOTgsImV4aXN0aW5nIjpmYWxzZX0=; _hjFirstSeen=1; _hjIncludedInSessionSample_2783207=1; _hjSession_2783207=eyJpZCI6ImE3YmVkOWFjLTM3NTctNDRiZC04OWJkLTQ4NTVhNDE4MjQ0YiIsImNyZWF0ZWQiOjE2OTYyMzkwODgyMDAsImluU2FtcGxlIjp0cnVlLCJzZXNzaW9uaXplckJldGFFbmFibGVkIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=0; _sharedid=4e46faca-031d-4d7a-9902-9a202bed8b72; cto_bundle=-ekK_V9acVBmcDNCdWpyUW1CcmpVVUVNdThFdjJTcm9jZVpWZkFEMVZJWFdqeko0c0djSUVwdSUyRkdBT0tBUExteFglMkJjd2F5bnVKUjBQcjlVSjF1QyUyRlVWaiUyQktsbVFqcWk4bkRGQkllbjF6Tk0zZyUyQlIlMkZxS1NUQ1RhMkdGVzJYc2NwJTJGbWpKNlFCcm1ZYkw5ZTJwcUxHRldUOG5iQSUzRCUzRA; cto_bidid=emq8fV9HU0dXNnhGUEhLb0hzM3NlQTlCYyUyRmFZZUdiVDJ0S3NqWkxVYVBuR0xNRmNuYzJNdjkxZ3VJQ0ZwaiUyRnpoVWNQNlJqM1BQSFVSeHRiSHU1aHFTZVVtNlElM0QlM0Q; cto_dna_bundle=ZPmJJF80M0RITmhlJTJCZkMwOUJGQlhaMUN2czdES3ZsZHJNRTclMkI0NmdnU3VhYzk3YmVtNFY0M2olMkJHU01WRzklMkZTQm1FJTJCTg; __gads=ID=b2437c67626b9954:T=1696239118:RT=1696239118:S=ALNI_MaGpBFQyJWlqaNQp2V8LPyJv4nbsA; __gpi=UID=00000cb41a64a929:T=1696239118:RT=1696239118:S=ALNI_MZ6BrJpdC1if8E-zJIQ_HQg6-upIQ; __gsas=ID=83a1d5e6e663f23b:T=1696239335:RT=1696239335:S=ALNI_MagL2qTV2vcXUMoj-W_S5OpXdJ7XQ; datadome=6pvf_DysxihN6soYRKrQVUarYRPHf-jcdnsDytKHH3SCVVh5nzLzzDPdMErWC8ie5FbseC8MUUC4ivU0hojb_1KHo3QkUkSX18fmUKaaAK_BHBDPWnho0rngnb9JHj87',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'TE': 'trailers'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # print(response.text)
    print(len(response.json()["ads"]))
    # pprint(response.json()["ads"][0])

    return response.json()

act = get_imo_page(0)

for j in range(len(act["ads"])):
    col.update_one({'list_id': act["ads"][j]["list_id"]}, {"$set": act["ads"][j]}, upsert=True)

for i in range(0, 100):
    print(i)
    act = get_imo_page(i)
    for j in range(len(act["ads"])):
        col.update_one({'list_id': act["ads"][j]["list_id"]}, {"$set": act["ads"][j]}, upsert=True)
    time.sleep(randint(1, 5))
