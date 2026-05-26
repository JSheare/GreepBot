"""A module containing parameters used by the bot."""
import platformdirs

APP_NAME = 'greepbot'
CONFIG_FILE = 'greepbot.ini'
MAX_LOG_SIZE_BYTES = 10000000
MAX_LOG_ROLLOVERS = 5
DATA_LOC = f'{platformdirs.user_data_dir(APP_NAME, appauthor=False)}'