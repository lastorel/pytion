# -*- coding: utf-8 -*-

import yaml

# Base URL
NOTION_URL = "https://api.notion.com/v1/"

# Access token
with open("token") as f:
    NOTION_SECRET = f.read()

# Current API Version
NOTION_VERSION = "2021-08-16"

# Find database params
with open("config.yaml") as f:
    config = yaml.safe_load(f)
    NOTION_DATABASE_ID = config["database"]["id"]

# every resource has `object` property (type declaration)
# every resource has `id` property (UUIDv4)
# every property is in snake_case only
# temporal values - ISO 8601
# 2020-08-12T02:12:33.231Z
# 2020-08-12

# empty strings DOES NOT supported. use `None` (python) or `null` (JSON)
