import datetime
import os
import requests
import json
import discord
import pandas as pd
import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import matplotlib.pyplot as plt

import plotly.io as pio
import plotly
import plotly.express as px

pio.templates["custom_dark"] = pio.templates["plotly_dark"]
pio.templates["custom_dark"]['layout']['paper_bgcolor'] = '#30404D'
pio.templates["custom_dark"]['layout']['plot_bgcolor'] = '#30404D'

pio.templates['custom_dark']['layout']['yaxis']['gridcolor'] = '#4f687d'
pio.templates['custom_dark']['layout']['xaxis']['gridcolor'] = '#4f687d'

def get_config(log, file_name):
    log.info(str(datetime.datetime.now())+"|get_config|starting")
    if (file_name=="" or file_name==None):
        raise Exception(str(datetime.datetime.now())+"|get_config|file_name is invalid|file_name="+str(file_name))

    result=dict()
    root=ET.parse(file_name).getroot()
    for prop in root.findall('property'):
        result[prop.find('name').text]=prop.find('value').text

    log.info(str(datetime.datetime.now())+"|get_config|completed")
    return result

def parse_owners(log, df):
    log.info(str(datetime.datetime.now())+"|parse_owners|starting")

    mint_df=df[df["FROM_ADDR"]=="0x0000000000000000000000000000000000000000"]    
    gain_df=df[df["FROM_ADDR"]!="0x0000000000000000000000000000000000000000"] 
    lose_df=df[df["FROM_ADDR"]!="0x0000000000000000000000000000000000000000"]

    mint_df=mint_df[["TO_ADDR","TOKEN_ID"]]
    mint_df.rename(columns={"TO_ADDR":"WALLET"}, inplace=True) 
    mint_df["ACTION"]="MINT"
    mint_df["VALUE"]=1

    gain_df=gain_df[["TO_ADDR","TOKEN_ID"]]
    gain_df.rename(columns={"TO_ADDR":"WALLET"}, inplace=True)
    gain_df["ACTION"]="GAIN"
    gain_df["VALUE"]=1

    lose_df=lose_df[["FROM_ADDR","TOKEN_ID"]]
    lose_df.rename(columns={"FROM_ADDR":"WALLET"}, inplace=True)
    lose_df["ACTION"]="LOSE"
    lose_df["VALUE"]=-1

    total_df=pd.concat([mint_df,gain_df,lose_df])
    total_df=total_df.astype({"TOKEN_ID":int})

    owners=total_df.groupby(["WALLET"]).sum()
    owners=owners[owners["VALUE"]>0]

    log.info(str(datetime.datetime.now())+"|parse_owners|completed")
    return owners

def get_ether_last_price(es_key):
    url='''https://api.etherscan.io/api?module=stats&action=ethprice&apikey='''
    response=requests.request("GET", url+str(es_key))
    price=json.loads(response.text).get("result").get("ethusd")
    return price

def owner_dist_p(log, df):
    log.info(str(datetime.datetime.now())+"|owner_dist_p|starting")

    owners=parse_owners(log,df)

    tier1=len(owners[owners["VALUE"]==1])
    tier2=len(owners[owners["VALUE"]==2])
    tier3=len(owners[(owners["VALUE"]>=3) & (owners["VALUE"]<5)])
    tier4=len(owners[(owners["VALUE"]>=6) & (owners["VALUE"]<10)])
    tier5=len(owners[(owners["VALUE"]>=10) & (owners["VALUE"]<15)])
    tier6=len(owners[(owners["VALUE"]>=16) & (owners["VALUE"]<20)])
    tier7=len(owners[(owners["VALUE"]>=21) & (owners["VALUE"]<30)])
    tier8=len(owners[(owners["VALUE"]>=31) & (owners["VALUE"]<50)])
    tier9=len(owners[(owners["VALUE"]>=51) & (owners["VALUE"]<80)])
    tier10=len(owners[owners["VALUE"]>=80])
 
    label=["1","2","3-5","6-10","11-15","16-20","21-30","31-50","51-80","81-120"]
    val=[tier1,tier2,tier3,tier4,tier5,tier6,tier7,tier8,tier9,tier10]

    fig=go.Figure(data=[go.Pie(labels=label, values=val)])
    fig.update_layout(title=df.iloc[0]["TOKEN_NAME"]+" Owner Distribution")
    fig.layout.template='plotly_dark'
    pio.write_image(fig,"owner_dist_p.png",width=1000,height=750)

    log.info(str(datetime.datetime.now())+"|owner_dist_p|completed")

def owner_dist_h(log, df):
    log.info(str(datetime.datetime.now())+"|owner_dist_h|starting")
    owners=parse_owners(log,df)

    tier1=len(owners[owners["VALUE"]==1])
    tier2=len(owners[owners["VALUE"]==2])
    tier3=len(owners[(owners["VALUE"]>=3) & (owners["VALUE"]<5)])
    tier4=len(owners[(owners["VALUE"]>=6) & (owners["VALUE"]<10)])
    tier5=len(owners[(owners["VALUE"]>=10) & (owners["VALUE"]<15)])
    tier6=len(owners[(owners["VALUE"]>=16) & (owners["VALUE"]<20)])
    tier7=len(owners[(owners["VALUE"]>=21) & (owners["VALUE"]<30)])
    tier8=len(owners[(owners["VALUE"]>=31) & (owners["VALUE"]<50)])
    tier9=len(owners[(owners["VALUE"]>=51) & (owners["VALUE"]<80)])
    tier10=len(owners[owners["VALUE"]>=80])
 
    x=["1","2","3-5","6-10","11-15","16-20","21-30","31-50","51-80","81-120"]
    y=[tier1,tier2,tier3,tier4,tier5,tier6,tier7,tier8,tier9,tier10]

    fig=go.Figure(data=[go.Bar(
        x=x,
        y=y,
        text=y,
        textposition='auto',
    )])
    fig.update_layout(title=df.iloc[0]["TOKEN_NAME"]+" Owner Distribution",xaxis_title="NFT Count",yaxis_title="Owner Count")
    fig.layout.template='plotly_dark'
    pio.write_image(fig,"owner_dist_h.png",width=1000,height=750)

    log.info(str(datetime.datetime.now())+"|owner_dist_h|completed")

def get_erc721_transfers(log,es_key,contract_addr):
    log.info(str(datetime.datetime.now())+"|get_erc721_transfers|starting")

    url=('''https://api.etherscan.io/api?module=account&action=tokennfttx&contractaddress='''+contract_addr
+'''&startblock=0'''
+'''&endblock=99999999'''
+'''&sort=asc'''
+'''&apikey='''+es_key)

    response=requests.request("GET", url)

    if (response==None):
        raise Exception("response object is invalid")

    data=json.loads(response.text).get("result")
    cols=["BLOCK_NUM",
          "TIME_STAMP",
          "HASH",
          "NONCE",
          "BLOCK_HASH",
          "CONTRACT_ADDR",
          "TO_ADDR",
          "FROM_ADDR",
          "TOKEN_ID",
          "TOKEN_NAME",
          "TOKEN_SYMBOL",
          "TXN_INDEX",
          "GAS",
          "GAS_PRICE",
          "GAS_USED",
          "CUM_GAS_USED",
          "INPUT",
          "CONFIRMS"]

    log.info(str(datetime.datetime.now())+"|get_erc721_transfers|parsing response...")
 
    df=pd.DataFrame(columns=cols)
    for i in range(len(data)):    
        block_num=str(data[i].get("blockNumber"))
        time_stamp=str(data[i].get("timeStamp"))
        hash=str(data[i].get("hash"))
        nonce=str(data[i].get("nonce"))
        block_hash=str(data[i].get("blockHash"))
        contract_address=str(data[i].get("contractAddress"))
        to_address=str(data[i].get("to"))
        from_address=str(data[i].get("from"))
        token_id=int(data[i].get("tokenID"))
        token_name=str(data[i].get("tokenName"))
        token_symbol=str(data[i].get("tokenSymbol"))
        token_decimal=str(data[i].get("tokenDecimal"))
        txn_index=str(data[i].get("transactionIndex"))
        gas=str(data[i].get("gas"))
        gas_price=str(data[i].get("gasPrice"))
        gas_used=str(data[i].get("gasUsed"))
        cum_gas_used=str(data[i].get("cumulativeGasUsed"))
        input=str(data[i].get("input"))
        confirms=str(data[i].get("confirmations"))

        new_row={"BLOCK_NUM":block_num,
                 "TIME_STAMP":time_stamp,
                 "HASH":hash,
                 "NONCE":nonce,
                 "BLOCK_HASH":block_hash,
                 "CONTRACT_ADDR":contract_address,
                 "TO_ADDR":to_address,
                 "FROM_ADDR":from_address, 
                 "TOKEN_ID":token_id,
                 "TOKEN_NAME":token_name,
                 "TOKEN_SYMBOL":token_symbol,
                 "TXN_INDEX":txn_index,
                 "GAS":gas,
                 "GAS_PRICE":gas_price,
                 "GAS_USED":gas_used,
                 "CUM_GAS_USED":cum_gas_used,
                 "INPUT":input,
                 "CONFIRMS":confirms}
        df=df.append(new_row,ignore_index=True)

    log.info(str(datetime.datetime.now())+"|get_erc721_transfers|completed")
    return df

def owner_stats(log, df):
    log.info(str(datetime.datetime.now())+"|owner_stats|starting")

    mint_df=df[df["FROM_ADDR"]=="0x0000000000000000000000000000000000000000"]
    gain_df=df[df["FROM_ADDR"]!="0x0000000000000000000000000000000000000000"]
    lose_df=df[df["FROM_ADDR"]!="0x0000000000000000000000000000000000000000"]

    mint_df=mint_df[["TO_ADDR","TOKEN_ID"]]
    mint_df.rename(columns={"TO_ADDR":"WALLET"}, inplace=True)
    mint_df["ACTION"]="MINT"
    mint_df["VALUE"]=1

    gain_df=gain_df[["TO_ADDR","TOKEN_ID"]]
    gain_df.rename(columns={"TO_ADDR":"WALLET"}, inplace=True)
    gain_df["ACTION"]="GAIN"
    gain_df["VALUE"]=1

    lose_df=lose_df[["FROM_ADDR","TOKEN_ID"]]
    lose_df.rename(columns={"FROM_ADDR":"WALLET"}, inplace=True)
    lose_df["ACTION"]="LOSE"
    lose_df["VALUE"]=-1

    total_df=pd.concat([mint_df,gain_df,lose_df])
    total_df=total_df.astype({"TOKEN_ID":int})

    owners=parse_owners(log, df)
    owner_cnt=len(owners[owners["VALUE"]>0])
    most_owned=owners["VALUE"].max() 
    mean_owners=round(owners["VALUE"].mean(),2)

    # SUPPLY
    burn_df=df[df["TO_ADDR"]=="0x0000000000000000000000000000000000000000"]
    supply=len(mint_df)-len(burn_df)

    embed=discord.Embed(title=df.iloc[0]["TOKEN_NAME"]+" Owner Stats")
    embed.add_field(name="Owner Count",value=owner_cnt,inline=False)
    embed.add_field(name="Supply",value=supply,inline=False)
    embed.add_field(name="Most Owned",value=most_owned,inline=False)
    embed.add_field(name="Mean Owners",value=mean_owners,inline=False)

    log.info(str(datetime.datetime.now())+"|owner_stats|completed")
    return embed

def usage():
    stats_cmd="!owner_stats [contract_addr]"
    dist_cmd="!owner_dist [contract_addr] [pie/hist]"

    embed=discord.Embed()
    embed.add_field(name="OWNER STATS",value=stats_cmd,inline=False)
    embed.add_field(name="OWNER DISTRIBUTION",value=dist_cmd,inline=False)
    return embed
