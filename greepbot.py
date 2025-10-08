import asyncio
import discord
import json
import logging
import os
import socket
import urllib.request
from datetime import datetime
from discord.ext import tasks
from dotenv import load_dotenv
from numpy import random


# Used to select a random entry in a given array
def random_selector(arr):
    randomnum = random.randint(0, len(arr))
    return randomnum


class Greepbot(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        load_dotenv()  # Loads the .env file where the tokens are stored
        self.discord_token = os.getenv('DISCORD_TOKEN')
        self.ip_pass = os.getenv('ip_pass')
        self.privileged_user = int(os.getenv('privileged_user'))

        self.quote_num = 0  # Here to prevent repeat quotes being sent by 'greepbot' command
        self.quote_lock = asyncio.Lock()

        self.gif_num = 0  # Here to prevent repeat gifs being sent by 'greepbot gif' command
        self.gif_lock = asyncio.Lock()

        self.sunday_cooldown = asyncio.Event()

        # Server gif channel preferences
        try:
            with open('gif_preferences.json', 'r') as openfile:
                self.gif_preferences = json.load(openfile)

        except FileNotFoundError:
            self.gif_preferences = {}

    # Discord client startup tasks
    async def on_ready(self):
        print('Severs:')
        for guild in self.guilds:
            print(f'{guild.name} (id: {guild.id})')

    # Bot message commands
    async def on_message(self, message):
        # Ignores any messages from the bot itself
        if message.author == self.user:
            return
        else:
            # Sends a random Greep quote from the list
            if message.content == 'greepbot':
                await self.send_quote(message)
            # Sends the number of days, hours, minutes, and seconds until Sunday
            elif message.content == 'greepbot countdown':
                await self.send_countdown(message)

            # Sends a random Greep-related gif
            elif message.content == 'greepbot gif':
                await self.send_gif(message)
            # IP request (dev use)
            elif 'greepbot ip' in message.content:
                await self.send_ip(message)
            # Allows users to set a preferred channel for the Sunday gif
            elif message.content == 'greepbot set gif channel':
                await self.set_pref_gif_channel(message)

            # Sends BCNR easter egg
            bcnr_list = ['black country, new road', 'bcnr', 'black country new road', 'black country']
            for term in bcnr_list:
                if term in message.content.lower():
                    await self.send_bcnr(message)
                    break

            # Rolls dice on voice channel easter egg
            if 'greepbot' in message.content:
                await self.roll_dice(message)

    # Sends a random Greep quote from the list
    async def send_quote(self, message):
        async with self.quote_lock:
            with open('quotes.txt') as file:
                quotes = file.readlines()

            while True:
                quote_index = random_selector(quotes)
                if quote_index != self.quote_num:
                    self.quote_num = quote_index
                    break

            await message.channel.send(quotes[quote_index])

    # Sends the number of days, hours, minutes, and seconds until Sunday
    @staticmethod
    async def send_countdown(message):
        now = datetime.now()
        full_days_until = 5 - now.weekday()
        if full_days_until == -1:
            await message.channel.send('It is currently Schlagenheim Sunday')
        else:
            total_seconds_until = full_days_until * 86400 + \
                                  (86400 - (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).seconds)

            days = total_seconds_until // (60 ** 2 * 24)
            hours = (total_seconds_until - days * 86400) // (60 ** 2)
            minutes = (total_seconds_until - days * 86400 - hours * 60 ** 2) // 60
            seconds = total_seconds_until - days * 86400 - hours * 60 ** 2 - minutes * 60
            if days == 0 and hours == 0 and minutes == 0:
                response = f'There are {seconds} seconds until Schagenheim Sunday'
            elif days == 0 and hours == 0:
                response = f'There are {minutes} minutes and {seconds} seconds until Schlagenheim Sunday'
            elif days == 0:
                response = f'There are {hours} hours, {minutes} minutes, ' \
                           f'and {seconds} seconds until Schlagenheim Sunday'
            elif days == 1:
                response = f'There is {days} day, {hours} hours, {minutes} minutes, ' \
                           f'and {seconds} seconds until Schlagenheim Sunday'
            else:
                response = f'There are {days} days, {hours} hours, {minutes} minutes, ' \
                           f'and {seconds} seconds until Schlagenheim Sunday'

            await message.channel.send(response)

    # Sends a random Greep-related gif
    async def send_gif(self, message):
        async with self.gif_lock:
            with open('gifs.txt') as file:
                gifs = file.readlines()

            while True:
                gif_index = random_selector(gifs)
                if gif_index != self.gif_num:
                    self.gif_num = gif_index
                    break

            await message.channel.send(gifs[gif_index])

    # IP request (dev use)
    async def send_ip(self, message):
        if message.author.id == self.privileged_user or message.content == f'greepbot ip {self.ip_pass}':
            public_ip = urllib.request.urlopen('https://v4.ident.me').read().decode('utf-8')
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            try:
                s.connect(('10.254.254.254', 1))
                local_ip = s.getsockname()[0]
            except Exception as ex:
                logging.getLogger('discord').error(ex)
                local_ip = '127.0.0.1'
            finally:
                s.close()

            await message.channel.send(f'Public IP: {public_ip}')
            await message.channel.send(f'Local IP: {local_ip}')
        else:
            await message.channel.send('Incorrect Password')

    # Allows users to set a preferred channel for the Sunday gif
    async def set_pref_gif_channel(self, message):
        self.gif_preferences[message.guild.id] = message.channel.id
        with open('gif_preferences.json', 'w') as outfile:
            json.dump(self.gif_preferences, outfile)

        await message.channel.send(f'Schlagenheim gif will be sent in "{message.channel}" for "{message.guild}"')

    # Sends BCNR easter egg
    @staticmethod
    async def send_bcnr(message):
        response = 'https://cdn.discordapp.com/attachments/360236282267303966/1026729585804582962/unknown.png'
        await message.channel.send(response)

    # Rolls the dice and initiates the voice channel easter egg
    async def roll_dice(self, message):
        likelihood = 0.25
        if random.random() <= likelihood:
            await self.greep_scream(message)

    @staticmethod
    async def greep_scream(message):
        if message.author.voice:
            voice_client = await message.author.voice.channel.connect()
            voice_client.play(discord.FFmpegPCMAudio('greep_scream.mp3'))
            await asyncio.sleep(2.5)
            await voice_client.disconnect()

    # Sends the Sunday gif
    async def send_sunday_gif(self):
        await self.wait_until_ready()
        channels = []
        for server in self.guilds:
            try:
                channels.append(self.get_channel(self.gif_preferences[str(server.id)]))
            except KeyError:
                for channel in server.channels:
                    if str(channel.type) == 'text':
                        channels.append(channel)
                        break

        for channel in channels:
            sunday_gif = 'https://tenor.com/view/schlagenheim-black-midi-greep-geordie-greep-bmbmbm-gif-22879771'
            await channel.send(sunday_gif)

    # Checks the day of the week and runs sunday() if it is Sunday
    @tasks.loop(hours=1)
    async def check_dow_background(self):
        await self.wait_until_ready()
        if not self.sunday_cooldown.is_set():
            now = datetime.now()
            if now.weekday() == 6:
                day_seconds = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).seconds
                self.sunday_cooldown.set()  # To prevent the gif from being sent multiple times a day
                while True:
                    random_seconds = random.randint(0, high=86400)
                    if day_seconds + random_seconds < 86400:
                        break

                await asyncio.sleep(random_seconds)
                await self.send_sunday_gif()
                await asyncio.sleep(86400)
                self.sunday_cooldown.clear()

    # Custom status background task
    @tasks.loop()
    async def custom_status_background(self):
        await self.wait_until_ready()
        with open('songs.json', 'r') as file:
            songs = json.load(file)

        song_list = list(songs.keys())
        song_index = random_selector(song_list)
        await self.wait_until_ready()
        await self.change_presence(activity=discord.Activity(name=song_list[song_index],
                                                             type=discord.ActivityType.listening))
        await asyncio.sleep(songs[song_list[song_index]])

    async def setup_hook(self):
        self.check_dow_background.start()
        self.custom_status_background.start()

    # Removing player when we are removed from a guild
    async def on_guild_remove(self, guild):
        del self.gif_preferences[guild.id]
        with open('gif_preferences.json', 'w') as outfile:
            json.dump(self.gif_preferences, outfile)


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    log_handler = logging.FileHandler(filename='log.txt', encoding='utf-8', mode='w')
    greep = Greepbot(intents=intents)
    greep.run(greep.discord_token, log_handler=log_handler, log_level=logging.INFO)


if __name__ == '__main__':
    main()
