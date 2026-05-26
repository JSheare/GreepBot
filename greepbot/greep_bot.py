"""A module containing the class that implements the bot."""
import asyncio
import datetime
import discord
import logging
import socket
import urllib.request
from discord.ext import tasks
from numpy import random
from typing import Dict

import greepbot.config.parameters as params
import greepbot.data.data_locs as data_locs
from greepbot.helpers.helper_funcs import read_file, read_json, write_json, random_selector
from greepbot.validation.config_validation import BotModel


class GreepBot(discord.Client):
    def __init__(self, config: BotModel, **kwargs) -> None:
        super().__init__(**kwargs)
        self._config = config
        self._logger = logging.getLogger('discord')

        self._songs = read_json(data_locs.SONGS_JSON)

        self._quotes = read_file(data_locs.QUOTES_TXT)
        self._quote_num = 0  # Here to prevent repeat quotes being sent by 'greepbot' command
        self._quote_lock = asyncio.Lock()

        self._gifs = read_file(data_locs.GIFS_TXT)
        self._gif_num = 0  # Here to prevent repeat gifs being sent by 'greepbot gif' command
        self._gif_lock = asyncio.Lock()

        self._sunday_cooldown = asyncio.Event()

        # Server gif channel preferences
        self._gif_preferences = self._read_gif_preferences()

    @staticmethod
    def _read_gif_preferences() -> Dict[str, int]:
        """Reads Guild channel gif preferences from a file."""
        try:
            gif_preferences = read_json(f'{params.DATA_LOC}/gif_preferences.json')
        except FileNotFoundError:
            gif_preferences = {}

        return gif_preferences

    def _write_gif_preferences(self) -> None:
        """Writes Guild channel gif preferences to a file."""
        write_json(self._gif_preferences, f'{params.DATA_LOC}/gif_preferences.json')

    # Discord client startup tasks
    async def on_ready(self) -> None:
        """Discord client startup tasks."""
        self._logger.info(f'{self.user} has connected to Discord.')

    async def on_message(self, message: discord.Message) -> None:
        """Processes messages for commands."""
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
            for term in ['black country, new road', 'bcnr', 'black country new road', 'black country']:
                if term in message.content.lower():
                    await self.send_bcnr(message)
                    break

            # Rolls dice on voice channel easter egg
            if 'greepbot' in message.content:
                await self.roll_dice(message)

    async def send_quote(self, message: discord.Message) -> None:
        """Sends a random Greep quote from the list."""
        async with self._quote_lock:
            while True:
                quote_index = random_selector(self._quotes)
                if quote_index != self._quote_num:
                    self._quote_num = quote_index
                    break

            await message.channel.send(self._quotes[quote_index])

    @staticmethod
    async def send_countdown(message: discord.Message) -> None:
        """Sends the number of days, hours, minutes, and seconds until Sunday."""
        now = datetime.datetime.now(datetime.UTC)
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

    async def send_gif(self, message: discord.Message) -> None:
        """Sends a random Greep-related gif."""
        async with self._gif_lock:
            while True:
                gif_index = random_selector(self._gifs)
                if gif_index != self._gif_num:
                    self._gif_num = gif_index
                    break

            await message.channel.send(self._gifs[gif_index])

    async def send_ip(self, message: discord.Message) -> None:
        """Sends IP request message (dev use)."""
        if (message.author.id == self._config.privileged_user or
                message.content == f'greepbot ip {self._config.ip_pass}'):
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

    async def set_pref_gif_channel(self, message: discord.Message) -> None:
        """Sets the preferred channel for the Sunday gif."""
        self._gif_preferences[str(message.guild.id)] = message.channel.id
        await asyncio.to_thread(self._write_gif_preferences)
        await message.channel.send(f'Schlagenheim gif will be sent in "{message.channel}" for "{message.guild}"')

    @staticmethod
    async def send_bcnr(message: discord.Message) -> None:
        """Sends BCNR easter egg."""
        await message.channel.send(content=data_locs.BCNR_PNG)

    async def roll_dice(self, message):
        """Rolls the dice and initiates the voice channel Easter egg."""
        likelihood = 0.25
        if random.random() <= likelihood:
            await self.greep_scream(message)

    @staticmethod
    async def greep_scream(message: discord.Message) -> None:
        """Plays the Greep scream in the user's voice channel."""
        if message.author.voice:
            voice_client = await message.author.voice.channel.connect()
            voice_client.play(discord.FFmpegPCMAudio(data_locs.GREEP_SCREAM_MP3))
            await asyncio.sleep(2.5)
            await voice_client.disconnect()

    async def send_sunday_gif(self) -> None:
        """Sends the Sunday gif."""
        await self.wait_until_ready()
        channels = []
        for server in self.guilds:
            try:
                channels.append(self.get_channel(self._gif_preferences[str(server.id)]))
            except KeyError:
                for channel in server.channels:
                    if str(channel.type) == 'text':
                        channels.append(channel)
                        break

        for channel in channels:
            await channel.send(content=data_locs.SUNDAY_GIF)

    @tasks.loop(hours=1)
    async def check_dow_background(self) -> None:
        """Checks the day of the week and runs sunday() if it is Sunday."""
        await self.wait_until_ready()
        if not self._sunday_cooldown.is_set():
            now = datetime.datetime.now(datetime.UTC)
            if now.weekday() == 6:
                day_seconds = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).seconds
                self._sunday_cooldown.set()  # To prevent the gif from being sent multiple times a day
                while True:
                    random_seconds = random.randint(0, high=86400)
                    if day_seconds + random_seconds < 86400:
                        break

                await asyncio.sleep(random_seconds)
                await self.send_sunday_gif()
                await asyncio.sleep(86400)
                self._sunday_cooldown.clear()

    @tasks.loop()
    async def custom_status_background(self) -> None:
        """Runs the custom status background task."""
        await self.wait_until_ready()
        song_list = list(self._songs.keys())
        song_index = random_selector(song_list)
        await self.wait_until_ready()
        await self.change_presence(activity=discord.Activity(name=song_list[song_index],
                                                             type=discord.ActivityType.listening))
        await asyncio.sleep(self._songs[song_list[song_index]])

    async def setup_hook(self) -> None:
        self.check_dow_background.start()
        self.custom_status_background.start()

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Removing a gif preference when we are removed from a Guild."""
        del self._gif_preferences[str(guild.id)]
        await asyncio.to_thread(self._write_gif_preferences)
