import os
import discord
import tweepy
import asyncio
import urllib.request
import socket
import json
import numpy as np
from datetime import datetime, timezone
from dotenv import load_dotenv
from numpy import random


# Used to select a random entry in a given list/array
def random_selector(link_list):
    randomnum = random.randint(0, len(link_list))
    return randomnum


load_dotenv()  # Loads the .env file where the tokens are stored
gif_num = 0  # Here to prevent repeat gifs being sent by 'greepbot gif'

# Discord client
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
d_client = discord.Client(intents=discord.Intents.default())

# Twitter client
bearer_token = os.getenv('bearer_token')
t_client = tweepy.Client(bearer_token=bearer_token)

log = open('log.txt', 'w')

# IP pass
ip_pass = os.getenv('ip_pass')

# Server gif channel preferences
gif_preferences = {}
try:
    with open('gif_preferences.json', 'r') as openfile:
        gif_preferences = json.load(openfile)

except FileNotFoundError:
    pass


# Discord client startup tasks
@d_client.event
async def on_ready():
    print(f'{d_client.user} has connected to Discord')
    print(f' Severs: {d_client.guilds}')
    now = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
    print(f'{now}: Bot initialization', file=log)


# Bot message commands
@d_client.event
async def on_message(message):
    # Ignores any messages from the bot itself
    if message.author == d_client.user:
        return

    # Sends the text of Greep's latest tweet
    if message.content == 'greepbot':
        query = 'from:GeordieGreep -is:retweet'
        tweets = t_client.search_recent_tweets(query=query, max_results=10)
        most_reccent_tweet = tweets.data[0]
        response = most_reccent_tweet.text
        await message.channel.send(response)

        now = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
        print(f'{now}: Tweet Message', file=log)

    # Sends the number of days, hours, minutes, and seconds until Sunday
    if message.content == 'greepbot countdown':
        now = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
        full_days_until = 5 - now.weekday()
        if full_days_until == -1:
            await message.channel.send('It is currently Schlagenheim Sunday')
        else:
            total_seconds_until = full_days_until*86400 + \
                                  (86400 - (now-now.replace(hour=0, minute=0, second=0, microsecond=0)).seconds)

            days = total_seconds_until // (60**2 * 24)
            hours = (total_seconds_until - days * 86400) // (60**2)
            minutes = (total_seconds_until - days * 86400 - hours * 60**2) // 60
            seconds = total_seconds_until - days * 86400 - hours * 60**2 - minutes * 60
            if days == 0 and hours == 0 and minutes == 0:
                response1 = f'There are {seconds} seconds until Schagenheim Sunday'
            elif days == 0 and hours == 0:
                response1 = f'There are {minutes} minutes and {seconds} seconds until Schlagenheim Sunday'
            elif days == 0:
                response1 = f'There are {hours} hours, {minutes} minutes, ' \
                            f'and {seconds} seconds until Schlagenheim Sunday'
            elif days == 1:
                response1 = f'There is {days} day, {hours} hours, {minutes} minutes, ' \
                            f'and {seconds} seconds until Schlagenheim Sunday'
            else:
                response1 = f'There are {days} days, {hours} hours, {minutes} minutes, ' \
                        f'and {seconds} seconds until Schlagenheim Sunday'

            await message.channel.send(response1)

        print(f'{now}: Countdown Message', file=log)

    # Sends a random Greep-related gif
    if message.content == 'greepbot gif':
        gifs = np.loadtxt('gifs.txt', dtype=str)
        while True:
            gif_index = random_selector(gifs)
            global gif_num
            if gif_index != gif_num:
                gif_num = gif_index
                break

        response2 = gifs[gif_index]
        await message.channel.send(response2)

        now = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
        print(f'{now}: Gif Message', file=log)

    # IP request (dev use)
    if 'greepbot ip' in message.content:
        now = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
        if message.content == f'greepbot ip {ip_pass}':
            public_ip = urllib.request.urlopen('https://v4.ident.me').read().decode('utf-8')
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            try:
                s.connect(('10.254.254.254', 1))
                local_ip = s.getsockname()[0]
            except Exception:
                local_ip = '127.0.0.1'
            finally:
                s.close()

            await message.channel.send(f'Public IP: {public_ip}')
            await message.channel.send(f'Local IP: {local_ip}')
        else:
            await message.channel.send('Incorrect Password')

        print(f'{now}: IP Request', file=log)

    # Allows users to set a preferred channel for the Sunday gif
    if message.content == 'greepbot set gif channel':
        now = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
        gif_preferences.update({message.guild.id: message.channel.id})
        with open('gif_preferences.json', 'w') as outfile:
            json.dump(gif_preferences, outfile)

        await message.channel.send(f'Schlagenheim gif will be sent in "{message.channel}" for "{message.guild}"')
        print(f'{now}: Gif posting channel change (guild {message.guild.id})', file=log)

    # Sends BCNR easter egg
    bcnr_list = ['black country, new road', 'bcnr', 'black country new road', 'black country']
    for term in bcnr_list:
        if term in message.content.lower():
            response3 = 'https://cdn.discordapp.com/attachments/360236282267303966/1026729585804582962/unknown.png'
            await message.channel.send(response3)
            now = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
            print(f'{now}: BCNR Message', file=log)
            break


# Checks the day of the week and runs sunday() if it is Sunday
async def background_task1():
    while True:
        now = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
        if now.weekday() == 6:
            day_seconds = (now-now.replace(hour=0, minute=0, second=0, microsecond=0)).seconds
            while True:
                random_seconds = random.randint(0, high=86400)
                if day_seconds + random_seconds >= 86400:
                    continue
                else:
                    print(f'{now}: {random_seconds} seconds until gif is posted', file=log)
                    await asyncio.sleep(random_seconds)
                    await sunday()
                    await asyncio.sleep(86400)
                    break
        else:
            print(f'{now}: Day check', file=log)
            await asyncio.sleep(3600)


# Sends the Sunday gif
async def sunday():
    await d_client.wait_until_ready()
    channels = []
    for server in d_client.guilds:
        try:
            channels.append(d_client.get_channel(gif_preferences[str(server.id)]))
        except KeyError:
            for channel in server.channels:
                if str(channel.type) == 'text':
                    channels.append(channel)
                    break

    for channel in channels:
        sunday_gif = 'https://tenor.com/view/schlagenheim-black-midi-greep-geordie-greep-bmbmbm-gif-22879771'
        await channel.send(sunday_gif)
        now = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(tz=None)
        print(f'{now}: Sunday gif posted', file=log)


# Custom status background task
async def background_task2():
    songs = {'Hellfire': 84, 'Sugar/Tzu': 230, 'Eat Men Eat': 188, 'Welcome To Hell': 249, 'Still': 646, 'Half Time': 26
             , 'The Race Is About To Begin': 435, 'Dangerous Liaisons': 254, 'The Defence': 179, '27 Questions': 343,
             'John L': 313, 'Marlene Dietrich': 173, 'Chondromalacia Patella': 289, 'Slow': 337, 'Diamond Stuff': 380,
             'Dethroned': 302, 'Hogwash and Balderdash': 152, 'Ascending Forth': 593, '953': 320, 'Speedway': 197,
             'Reggae': 209, 'Near DT, MI': 140, 'Western': 488, 'Of Schlagenhgeim': 384, 'bmbmbm': 296,
             'Years Ago': 154, 'Ducter': 402}
    songlist = list(songs.keys())
    while True:
        song_index = random_selector(songlist)
        await d_client.wait_until_ready()
        await d_client.change_presence(activity=discord.Game(songlist[song_index]))
        await asyncio.sleep(songs[songlist[song_index]])

d_client.loop.create_task(background_task1())
d_client.loop.create_task(background_task2())
d_client.run(DISCORD_TOKEN)

