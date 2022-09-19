import pandas as pd
import numpy as np
import requests 
import io
import math
from io import StringIO
from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import streamlit as st
import warnings
warnings.filterwarnings("ignore")

#import monthly sales data and stock data at VPN level from Looker
#login credentials to get looker data
id = "vmz4KgsBY3b3gbfkSqqJ"
secret = "FxdRn3YjzfzbGvrDzpx9BsTY"
base_url = "https://chalhoubgroup.de.looker.com:19999/api/3.0"

def log_me_in(id,secret, base_url):
    payload = {'client_id': id, 'client_secret': secret}
    url = base_url + '/login'
    r = requests.post(url, data=payload)
    # check for successful auth
    if r.status_code == 200:
        token = r.json()['access_token']
        return token
    else: 
        print('Authentication failed')

def get_look(token, look_id, base_url):
    # hard coded for json format response
    url = base_url +'/looks/' + look_id + '/run/json?access_token=' + token + '&limit=' + str(-1)
    r = requests.get(url)
    return(r)

def get_data_look(lookid):   
    #logging in with credentials
    token =log_me_in(id,secret, base_url)
    #Getting the product attributes
    data = get_look(token, lookid, base_url)
    output = pd.json_normalize(data.json())
    return(output)

def read_from_googlesheet(url, sheet_name = ''):
    df = pd.read_excel(url, sheet_name=sheet_name)
    return df

def grade(df, store_col = '',group_on='',measure='', ratio = [60,30,10] , grade_labels = ["A","B","C"]):
    fin_df = pd.DataFrame()
    if len(df) > 0:
        for i in df.store_name.unique():
            sub_df = df[df.store_name == i]
            sub_df = sub_df[[store_col, group_on ,measure]].groupby([store_col,group_on]).sum().reset_index().sort_values(by=measure, ascending=False).reset_index(drop=True)
            sub_df['cum_pct'] = 100*(sub_df[measure].cumsum() / sub_df[measure].sum())
            bins= [0] + [sum(ratio[:i+1]) for i in range(len(ratio))][:2] + [101]
            labels = grade_labels
            sub_df[group_on+'_grade'] = pd.cut(sub_df['cum_pct'], bins=bins, labels=labels)
            sub_df = sub_df.drop(['cum_pct'],axis=1)
            sub_df[group_on+'_grade'] = np.where(sub_df[measure] <= 0, 'Z', sub_df[group_on+'_grade'])
            fin_df = fin_df.append(sub_df)
    else:
        sub_df = pd.DataFrame()
        fin_df = fin_df.append(sub_df)
    
    return fin_df

def allocation_algo(donor_sub, recepient_sub, donor_qty_col = 'donate_qty', recep_qty_col = 'required_qty' , store_name_col = 'store_name' ):
    for i in range(0,len(recepient_sub)):
        req_qty = recepient_sub[recep_qty_col][i]
        store = recepient_sub[store_name_col][i]
        for j in range(0,len(donor_sub)):
            if req_qty >= donor_sub.donate_qty_cusum[j]:
                can_donate = donor_sub[donor_qty_col][j]
                donor_sub.loc[j,store] = can_donate
                ## updating donate_qty and req_qty
                req_qty = req_qty - can_donate
                donor_sub.loc[j,donor_qty_col] = 0
                donor_sub['donate_qty_cusum'] = donor_sub[donor_qty_col].cumsum()
            else:
                can_donate = req_qty
                donor_sub.loc[j,store] = can_donate    
                ## updating donate_qty and req_qty
                req_qty = 0
                donor_sub.loc[j,donor_qty_col] = donor_sub.loc[j,donor_qty_col] - can_donate
                donor_sub['donate_qty_cusum'] = donor_sub[donor_qty_col].cumsum()
                
    donor_sub = donor_sub.drop(['donate_qty','donate_qty_cusum'],axis=1)
            
    return donor_sub

## This function transforms the Recepient store name and Received units from row format to column.. finally we have a df which has recipient store name in the same row as the donor .. i.e. a recipient tagged to a donor'''

def data_prep_v1(donor_df, recepient_sub):
    main_df = pd.DataFrame()
    for i in range(0,len(donor_df)):
        algo_used_col_index = donor_df.columns.get_loc("algo_used")
        tmp_1 = pd.DataFrame(donor_df.iloc[i,  :algo_used_col_index+1 ]).transpose()
        tmp_2 = pd.DataFrame(donor_df.iloc[i, algo_used_col_index+1: ]).reset_index()
        tmp_2.columns=['recipient_store_name','qty_received']
        tmp_2.qty_received = tmp_2.qty_received.fillna(0)
        tmp_main = tmp_1.append(tmp_2).reset_index(drop=True)
        tmp_main.iloc[:,:-2] = tmp_main.iloc[:,:-2].ffill()
        tmp_main = tmp_main.iloc[1:,:].reset_index(drop=True)
        main_df = main_df.append(tmp_main,ignore_index=True)

    main_df = main_df.reset_index(drop=True)
    return main_df

def to_excel(df_sheet = {}):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    for sheet_name , df in df_sheet.items():
        df.to_excel(writer, sheet_name=sheet_name)
        df.to_excel(writer, sheet_name=sheet_name)
    workbook = writer.book
    writer.save()
    processed_data = output.getvalue()
    return processed_data

headerColor = 'grey'
rowEvenColor = 'lightgrey'
rowOddColor = 'white'

def table_plotly(df, wide=500, length=300 , title = ''):
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    line_color='darkslategray',
                    fill_color=headerColor,
                    align=['left','center'],
                    font=dict(color='white', size=12)),
        cells=dict(values=[df[i] for i in df.columns],
                   line_color='darkslategray',
                    # 2-D list of colors for alternating rows
                    fill_color = [[rowOddColor,rowEvenColor,rowOddColor, rowEvenColor,rowOddColor]*5],
                    align = ['left', 'center'],
                    font = dict(color = 'darkslategray', size = 11)))
    ])
    
    fig.update_layout(title = title ,width = wide,height =  length)
    return fig
