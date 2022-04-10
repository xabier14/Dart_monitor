import pandas as pd
import requests
from zipfile import ZipFile
from io import BytesIO
import json
from bs4 import BeautifulSoup
from datetime import date
import datetime
import sys
import re

# 모든 회사별 dart의 고유번호 받기
api_key = 'dart api key 입력'
code_url = 'https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key=%s' % api_key
response = requests.get(code_url)
zip_file = ZipFile(BytesIO(response.content))
files = zip_file.namelist()
soup = ''

with zip_file.open(files[0]) as csvfile:
    soup = BeautifulSoup(csvfile.read(), 'lxml')
    soup = soup.findAll('list')

data = []
for company in soup:
    data.append({
        'corp_code' : company.corp_code.text,
        'corp_name' : company.corp_name.text,
        'stock_code' : company.stock_code.text,
        'modify_date' : company.modify_date.text
    })
data = pd.DataFrame(data)

# 모니터링하고자 하는 기업들의 종목코드를 리스트로 작성
code_li = ['005930','000660']  # 삼성전자, SK하이닉스

# 고유번호와 종목코드 매칭
idx_li = []
corp_code_li = {}
for i in code_li:
    idx_li.append(data.index[data['stock_code']==i].tolist())
for i in idx_li:
    corp_code_li[data['corp_code'][i[0]]] = data['corp_name'][i[0]]

today = datetime.date.today().strftime('%Y%m%d')

saving_df = pd.DataFrame()
report_num_li = []
def Monitoring():
    global saving_df
    global report_num_li
    if len(saving_df) != 0:
        for k in saving_df.index:
            report_num_li.append(saving_df['보고서번호'][k])
    for i in corp_code_li.keys():
        now = datetime.datetime.now()
        print(str(now))
        url = "https://opendart.fss.or.kr/api/list.json?crtfc_key=%s&corp_code=%s&end_de=%s&page_count=100" % (api_key, i, today)
        response = requests.get(url)
        data_json = json.loads(response.text)
        items = ['rcept_dt','corp_name','report_nm','rcept_no','flr_nm']  # 필요한 칼럼명
        cols = ['접수일자','종목명','보고서명','보고서번호','공시제출인명']  # 필요한 칼럼 한글명
        link_base = 'http://dart.fss.or.kr/dsaf001/main.do?rcpNo='   # 기본 사용되는 요청 url
        result = []
        if data_json['status'] == '000':
            for data in data_json['list']:
                result.append([])
                for item in items:
                    if item in data.keys():
                        result[-1].append(data[item])
                    else:
                        result[-1].append('')
            df = pd.DataFrame(result, columns=cols)
            df['보고서링크'] = link_base + df['보고서번호']
            print('%s : **************공시있음**************' % corp_code_li[i])
            if len(saving_df) == 0:
                saving_df = df
                saving_df = saving_df.reset_index(drop=True)
            else:
                for t in df.index:
                    if df['보고서번호'][t] in report_num_li:
                        df = df.drop(index=t, axis=0)
                saving_df = pd.concat([saving_df,df])
                saving_df = saving_df.reset_index(drop=True)
            print(df)
        else:
            print('%s : 공시없음' % corp_code_li[i])