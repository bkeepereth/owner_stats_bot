#!/usr/bin/env python
import getopt
import logging
import os
import sys
import discord
import requests
import datetime
import traceback

sys.path.insert(1,'../lib/')
import owner_lib

client=discord.Client()
log=logging.getLogger()
es_key=""

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author==client.user:
        return

    if message.content.startswith("!hello"):
        msg='Hello{0.author.mention}'.format(message)
        channel=message.channel
        await channel.send(msg)

    if message.content.startswith("!usage"):
        try:
            channel=message.channel
            await channel.send(embed=owner_lib.usage())
        except:
            pass            

    if message.content.startswith("!owner_stats"):
        try:
            msg_list=str(message.content).split(" ")
                 
            channel=message.channel 
            owner_df=owner_lib.get_erc721_transfers(log,es_key,msg_list[1])
            embed=owner_lib.owner_stats(log,owner_df)
            await channel.send(embed=embed)
        except:
            pass

    if message.content.startswith('!owner_dist'):
        try:
            msg_list=str(message.content).split(" ")    

            if (len(msg_list)==3):
                addr=msg_list[1]
                graph_type=msg_list[2]

                if (graph_type=="pie"):
                    owner_df=owner_lib.get_erc721_transfers(log,es_key,addr)
                    owner_lib.owner_dist_p(log,owner_df)

                    f=discord.File("owner_dist_p.png")
                    channel=message.channel
                    await channel.send(file=f)

                else:  # default to hist, on err
                    owner_df=owner_lib.get_erc721_transfers(log,es_key,addr)
                    owner_lib.owner_dist_h(log,owner_df)

                    f=discord.File("owner_dist_h.png")        
                    channel=message.channel
                    await channel.send(file=f)

            else:  # default to pie w/o opt
                addr=msg_list[1]    
                owner_df=owner_lib.get_erc721_transfers(log,es_key,addr)    
                owner_lib.owner_dist_p(log,owner_df)

                f=discord.File("owner_dist_p.png")
                channel=message.channel
                await channel.send(file=f)
        except:
            pass

@client.event
async def on_ready():
     log.info("Logged in as:"+str(client.user.name))

def Usage():
    print("Usage:./owner_stats_bot.py -c [config]")    

def main(argv):
    dt=str(datetime.datetime.now()).replace(" ","T")
    logging.getLogger("discord").setLevel(logging.WARNING)

    logging.basicConfig(filename="../log/"+dt[:-7]+".owner_stats_bot.log",filemode="w")
    log.setLevel(logging.INFO)
    log.info(str(datetime.datetime.now())+"|main|starting")

    try:
        (opts,args)=getopt.getopt(argv, "hc:", ["help"])
        file_name=""

        for (opt,arg) in opts:
            if (opt in ("-h","--help")):
                Usage()
                sys.exit()
            elif (opt in ("-c")):
                file_name=str(arg)
            else:
                Usage()
                sys.exit()

        config=owner_lib.get_config(log, file_name)
        es_key=str(config.get("ES_KEY"))
        client.run(config.get("DS_TOKEN"))
    except:
        log.error(traceback.print_exc())

    log.info(str(datetime.datetime.now())+"|main|completed")

if __name__=="__main__":
    main(sys.argv[1:])

