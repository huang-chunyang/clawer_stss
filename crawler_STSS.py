import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

event = ["500m"]
# from standings_url
standings_url = "https://shorttrack.sportresult.com/?evt=11213100000088&__VIEWSTATEGENERATOR=CA0B0334"
# 获取各个比赛的url
data = requests.get(standings_url)
soup = BeautifulSoup(data.text)
links_a = soup.find("div", {"id": "contentrightsmall"}).find_all('a')
# links 是各个比赛的url
# names 是各个url 的name
links = ["https://shorttrack.sportresult.com/" +
         l.get("href") for l in links_a]
names = [n.contents[0] for n in links_a]

race_tables = []

# 进入各种比赛
for num, name in enumerate(names):
    sex, project, level = name.split(" - ")
    # 进入决赛
    if level == "Finals" and project in event:
        print(names[num])
        result_data = requests.get(links[num])
        # result tables, eg: Final A
        tables = pd.read_html(result_data.text)[2:]
        split_data = BeautifulSoup(result_data.text).find_all(
            "div", {"class": "tabletitle"})
        split_links = [l.find("a").get("href") for l in split_data]
        table_names = [re.sub('[\r\n\t ]', '', table.find('b').text)
                       for table in split_data]
        # 进入split
        race_num = len(tables)
        for i in range(race_num):
            rows, columns = tables[i].shape
            tables[i]["event"] = np.zeros(rows)
            tables[i]["month"] = np.zeros(rows)
            tables[i]["level"] = np.zeros(rows)
            
            for index in range(rows):
                tables[i]["event"][index] = event[0]
                tables[i]["month"][index] = 2
                tables[i]["level"][index] = table_names[i]
                
            split_link = split_links[i]
            split_data = requests.get(split_link)
            split_tables = pd.read_html(split_data.text)
            if len(split_tables) > 1:
                split_table = pd.read_html(split_data.text)[1]
                # 处理split_table
                split_table_T = split_table.set_index("Unnamed: 0").T
                x, y = split_table_T.shape
                lap_time = split_table_T
                for l in range(x):
                    for m in range(y):
                        z = re.match('.+\((\d+\.\d+)\)',
                                     split_table_T.iloc[l, m])
                        lap_time.iloc[l, m] = z.group(1)
                lap_time = lap_time.rename_axis('index').reset_index().rename({
                    "index": "Name"}, axis=1)

                # 生成一个小的dataframe
                merge_table = pd.merge(tables[i], lap_time, how="inner", on="Name")
                race_tables.append(merge_table)
            else:
                # 待删去"Unnamed: 7" 这一列
                table = tables[i]
                race_tables.append(table)

result = pd.concat(race_tables)
result.to_csv("data/" + event[0] + ".csv")
