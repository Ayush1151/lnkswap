import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7413512300:AAF0Poxlf9oQntk1yDtykr5bbYEI0Qb_6UI")
REPLACEMENT_LINK = os.getenv("REPLACEMENT_LINK", "https://www.jalwagame7.com/#/register?invitationCode=237152955859")

# Logging configuration
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
