"""A module containing the locations of the various data files used by the bot."""
import pathlib


DATA_LOC = str(pathlib.Path(__file__).parent)
BCNR_PNG = f'{DATA_LOC}/bcnr.png'
GIFS_TXT = f'{DATA_LOC}/gifs.txt'
GREEP_SCREAM_MP3 = f'{DATA_LOC}/greep_scream.mp3'
QUOTES_TXT = f'{DATA_LOC}/quotes.txt'
SONGS_JSON = f'{DATA_LOC}/songs.json'
SUNDAY_GIF = f'{DATA_LOC}/sunday.gif'
