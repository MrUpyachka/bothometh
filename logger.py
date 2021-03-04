import os
import logging


LOG_LEVEL = os.environ.get('BOT_LOG_LEVEL', 'INFO').upper()
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=LOG_LEVEL)

LOG = logging
