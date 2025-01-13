from bs4 import BeautifulSoup
from matplotlib.cbook import ls_mapper
import pandas as pd

with open(r'/home/ebriand/python/scraping/oasis/html/bestiaire.html', "r") as f:
    page = f.read()


def get_image(my_td):
    temp = my_td.find(['div'])
    if temp == None:
        temp = my_td.find(['img'])['src']
        if temp == None:
            return None
        else:
            return temp
    temp = temp.find(['img'])['src']
    return temp


def get_name(my_td):
    temp = my_td.find(['b'])
    print(my_td)
    if temp == None:
        temp = my_td.find(['div'])
        if temp == None:
            return None
    return temp.text


def get_description(my_td):
    temp = my_td.find(['div'])
    if temp == None:
        temp = my_td.find(['div'])
        if temp == None:
            return None
    return temp.text


def get_butin(butin):
    pos = 0
    if (len(butin) < 2):
        return ''
    for i in range(1, len(butin)):
        if butin[i].isdigit() and (butin[i - 1].isalpha() or butin[i - 1] == ')') and not butin[i - 1].isspace():
            temp = butin[:i]
            temp += '\n'
            temp += butin[i:]
            butin = temp
    while butin[pos] == '\n' or butin[pos] == ' ':
        butin = butin[1::]
        ++pos
    pos = 0
    butin = butin[::-1]
    while butin[pos] == '\n' or butin[pos] == ' ':
        butin = butin[1::]
        ++pos
    butin = butin[::-1]
    return butin


soup = BeautifulSoup(page, "html.parser")
table = soup.find(
    ['table'], style="border-collapse:collapse;border-color:rgb(136,136,136);border-width:1px")
all_line = table.find_all(['tr'])
all_line = all_line[1::]
final_table = []

for line in all_line:
    final_dict = {}
    all_column = line.find_all(['td'])
    final_dict['Image'] = get_image(all_column[0])
    final_dict['Nom'] = get_name(all_column[1])
    final_dict['Description'] = get_description(all_column[2])
    final_dict['Pouvoir'] = all_column[3].text
    final_dict['Niveau'] = all_column[4].text
    final_dict['PV '] = all_column[5].text
    final_dict['Att Phys'] = all_column[6].text
    final_dict['Def Phys'] = all_column[7].text
    final_dict['Att Mag'] = all_column[8].text
    final_dict['Def Mag'] = all_column[9].text
    final_dict['PA'] = all_column[10].text
    final_dict['PM'] = all_column[11].text
    final_dict['Initiative'] = all_column[12].text
    final_dict['XP'] = all_column[13].text
    final_dict['Butin'] = get_butin(all_column[14].text)
    final_dict['Localisation'] = get_description(all_column[15])
    final_table.append(final_dict)

df = pd.DataFrame(final_table, columns=["Image", "Nom", "Description", "Pouvoir", "Niveau",
                                        "PV", "Att Phys", "Def Phys", "Att Mag", "Def Mag", "PA", "PM", "Initiative", "XP", "Butin", "Localisation"])
df.head(10)
df.to_csv('../csv/bestiaire.csv', index=False, encoding='utf-8')
