import os
import requests
import json
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt

import plotly.io as pio
import plotly
import plotly.express as px
#import numpy as np

def get_ether_last_price(config):
    url='''https://api.etherscan.io/api?module=stats&action=ethprice&apikey='''
    key='''IAZRGUHTGTJE12A9CJZVFZ86SZC9CM8EFF'''

    response=requests.request("GET", url+key)
    price=json.loads(response.text).get("result").get("ethusd")
    return price

def get_banana_price():
    url="https://api.coingecko.com/api/v3/simple/price?ids=banana&vs_currencies=eth%2Cusd"

    response=requests.get(url)
    eth_result=json.loads(response.text).get("banana").get("usd")
    return eth_result

def get_honeyd_price():
    url="https://api.coingecko.com/api/v3/simple/price?ids=honey-deluxe&vs_currencies=usd"
    
    response=requests.get(url)
    eth_result=json.loads(response.text).get("honey-deluxe").get("usd")
    return eth_result

def get_volt_price():
    url="https://api.coingecko.com/api/v3/simple/price?ids=voltage&vs_currencies=usd" 
    
    response=requests.get(url)
    eth_result=json.loads(response.text).get("voltage").get("usd")
    return eth_result

def get_nftl_price():
    url="https://api.coingecko.com/api/v3/simple/price?ids=nifty-league&vs_currencies=usd"

    response=requests.get(url)
    eth_result=json.loads(response.text).get("nifty-league").get("usd")
    return eth_result

def get_ucd_price():
    url="https://api.coingecko.com/api/v3/simple/price?ids=unicandy&vs_currencies=usd"
    response=requests.get(url)
    eth_result=json.loads(response.text).get("unicandy").get("usd")
    return eth_result

def get_dex_config(file_name):
    f=open(file_name,"r")
    file=json.load(f)
    return file

def get_floor_prices(config):
    dict={}
    urls=config.get("urls")
    for k,v in urls.items():
        if (k=="cyberkongz" or k=="kaiju-kingz"):
            dict[k]=config.get("floor_prices").get(k)
        else:
            prefix="https://api.opensea.io/api/v1/collection/"
            collection_name=v.split("/")[-1]
            url=(prefix+collection_name)

            response=requests.request("GET",url)        
            data=json.loads(response.text)
            dict[k]=(data.get("collection").get("stats").get("floor_price"))        
    return dict
 
def get_dex_prices(config):
    dex_list=config.get("dex_mapping")
    dex_prices=config.get("dex_prices")
    for proj,token in dex_list.items():
        if (proj=="cyberkongz"):
            dex_prices[token]=get_banana_price()
        elif (proj=="bears-deluxe"):
            dex_prices[token]=get_honeyd_price()
        elif (proj=="supducks"):
            dex_prices[token]=get_volt_price()
        elif(proj=="niftydegen"):
            dex_prices[token]=get_nftl_price()
        elif(proj=="ununicornsofficial"):
            dex_prices[token]=get_ucd_price()
    return dex_prices

def collect_data():
    config=get_dex_config("dex.json")

    if (os.path.exists("prev.csv")):
        print("PREV DAY FILE EXISTS, PROCESSING....")

        floor_dict=get_floor_prices(config)
        dex_dict=get_dex_prices(config)
        eth_price=float(get_ether_last_price(""))

        cols=["DIFF",
            "LAST_RANK",
            "PROJECT",
            "PREV_FLOOR_ETH",
            "PREV_FLOOR_USD",
            "FLOOR_ETH",
            "FLOOR_USD",
            "DIFF_24HR",
            "TOKEN",
            "PREV_TOKEN_USD",
            "TOKEN_USD",
            "DAILY_YIELD",
            "DAILY_USD",
            "STAKE",
            "ROI",
            "BREAKEVEN_DAYS"]
        df=pd.DataFrame(columns=cols)
    
        for (k,v) in config.get("dex_mapping").items():
            project=k
            eth_flr=float(floor_dict.get(k))
            token=v
            daily_yield=float(config.get("yield_mapping").get(k))
            token_usd=float(dex_dict.get(v))

            row={"DIFF":0,
                "LAST_RANK":"N/A",
                "PROJECT":k,
                "PREV_FLOOR_ETH":0,
                "PREV_FLOOR_USD":0,
                "FLOOR_ETH":eth_flr,
                "FLOOR_USD":0,
                "DIFF_24HR":0,
                "TOKEN":v,
                "PREV_TOKEN_USD":"",
                "DAILY_YIELD":daily_yield,
                "DAILY_USD":"",
                "TOKEN_USD":token_usd,
                "STAKE":"",
                "ROI":"",
                "BREAKEVEN_DAYS":0}
            df=df.append(row,ignore_index=True)

        df["FLOOR_USD"]=round(df["FLOOR_ETH"]*eth_price,2)
        df["DAILY_USD"]=round(df["TOKEN_USD"]*df["DAILY_YIELD"],2)
        df["BREAKEVEN_DAYS"]=round(df["FLOOR_USD"]/df["DAILY_USD"],1)
    
        df=df.sort_values(by=["BREAKEVEN_DAYS"])   
        df=df.reset_index()
        del df['index']    

        fig=go.Figure(data=[go.Table(
            header=dict(values=list(df.columns),
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[df.DIFF,
                               df.LAST_RANK,
                               df.PROJECT, 
                               df.PREV_FLOOR_ETH,
                               df.PREV_FLOOR_USD,
                               df.FLOOR_ETH,
                               df.FLOOR_USD,
                               df.DIFF_24HR,
                               df.TOKEN,
                               df.PREV_TOKEN_USD,
                               df.TOKEN_USD,
                               df.DAILY_YIELD,
                               df.DAILY_USD,
                               df.STAKE,
                               df.ROI,
                               df.BREAKEVEN_DAYS],
                       fill_color='lavender',
                       align='left'))
        ])
        fig.show()
        pio.write_image(fig, "yield_index_daily.png", width=1700, height=750)
    else:
        floor_dict=get_floor_prices(config)
        dex_dict=get_dex_prices(config)
        eth_price=float(get_ether_last_price(""))

        cols=["RANK",
            "PROJECT",
            "FLOOR_ETH",
            "FLOOR_USD",
            "TOKEN",
            "TOKEN_USD",
            "DAILY_YIELD",
            "DAILY_USD",
            "STAKE",
            "ROI",
            "BREAKEVEN_DAYS"]
        df=pd.DataFrame(columns=cols)
    
        for (k,v) in config.get("dex_mapping").items():
            project=k
            eth_flr=float(floor_dict.get(k))
            token=v
            daily_yield=float(config.get("yield_mapping").get(k))
            token_usd=float(dex_dict.get(v))
            stake_flg=config.get("stake_mapping").get(k)

            row={"PROJECT":k,
                "FLOOR_ETH":eth_flr,
                "FLOOR_USD":0,
                "TOKEN":v,
                "DAILY_YIELD":daily_yield,
                "DAILY_USD":"",
                "TOKEN_USD":token_usd,
                "STAKE":stake_flg,
                "ROI":"",
                "BREAKEVEN_DAYS":0}
            df=df.append(row,ignore_index=True)

        df["FLOOR_USD"]=round(df["FLOOR_ETH"]*eth_price,2)
        df["DAILY_USD"]=round(df["TOKEN_USD"]*df["DAILY_YIELD"],2)
        df["ROI"]=round((((df["DAILY_USD"]*365)/df["FLOOR_USD"])*100),2)
        df["BREAKEVEN_DAYS"]=round(df["FLOOR_USD"]/df["DAILY_USD"],1)   

        df["STAKE"]=df["STAKE"].str.replace("1","Y")
        df["STAKE"]=df["STAKE"].str.replace("0","N")
 
        df=df.sort_values(by=["BREAKEVEN_DAYS"])   
        df=df.reset_index()
        del df['index']    

        fig=go.Figure(data=[go.Table(
            columnwidth=[2,8,4,4,4,5,4,4,3,3,4],
            header=dict(values=list(df.columns),
                        fill_color='paleturquoise',
                        align=['center']),
            cells=dict(values=[df.index.values,
                               df.PROJECT, 
                               df.FLOOR_ETH,
                               df.FLOOR_USD,
                               df.TOKEN,
                               df.TOKEN_USD,
                               df.DAILY_YIELD,
                               df.DAILY_USD,
                               df.STAKE,
                               df.ROI,
                               df.BREAKEVEN_DAYS],
                       fill_color='lavender',
                       align=['center','center','left','left','center','left','left','left','center','left','left']))
        ])
        fig.show()
        pio.write_image(fig, "yield_index_daily.png", width=1700, height=750)
