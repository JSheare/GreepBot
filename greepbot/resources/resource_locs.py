"""A module containing the locations of the various resource file indexes used by the bot."""
import pathlib


RESOURCE_LOC = str(pathlib.Path(__file__).parent)
RANDOM_GIFS_TXT = f'{RESOURCE_LOC}/random_gifs.txt'
QUOTES_TXT = f'{RESOURCE_LOC}/quotes.txt'
SONGS_JSON = f'{RESOURCE_LOC}/songs.json'
