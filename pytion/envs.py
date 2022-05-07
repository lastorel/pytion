# -*- coding: utf-8 -*-

import logging


# Base URL (mandatory)
NOTION_URL = "https://api.notion.com/v1/"

# Access token (optional)
try:
    with open("token") as f:
        NOTION_SECRET = f.read()
except FileNotFoundError:
    NOTION_SECRET = None

# Current API Version (mandatory)
NOTION_VERSION = "2022-02-22"

# Logging settings (mandatory)
LOGGING_BASE_LEVEL = logging.WARNING
LOGGING_TO_CONSOLE = False
# set `None` to do not logging into file
LOGGING_FILE = None

# every resource has `object` property (type declaration)
# every resource has `id` property (UUIDv4)
# every property is in snake_case only
# temporal values - ISO 8601
# 2020-08-12T02:12:33.231Z
# 2020-08-12T02:12:33.231+00:00
# 2020-08-12

# empty strings ARE NOT supported. use `None` (python) or `null` (JSON)
