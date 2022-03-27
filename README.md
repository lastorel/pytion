# pytion
Unofficial Python client for official Notion API (for internal integrations only)

Supports Notion API version = **"2022-02-22"**

Works with **Python 3.8+**

## Quick start
There is no package yet. Clone repo.

Create new integration and get your Notion API Token at notion.so -> /my-integrations

Invite your new integration 'manager' to your Notion workspace or particular pages.

`from pytion import Notion; no = Notion(token=SOME_TOKEN)`

Or put your token for Notion API into file `token` at script directory and use simple `no = Notion()`
```
from pytion import Notion
no = Notion(token=SOME_TOKEN)
page = no.pages.get("PAGE ID")
database = no.databases.get("Database ID")
pages = database.db_filter(property_name="Done", property_type="checkbox", value=False, descending="title")
```
```
In [12]: no = Notion(token=SOME_TOKEN)

In [13]: my_page = no.blocks.get("7584bc0bfb3b409cb17f957e51c9188a")

In [14]: blocks = my_page.get_block_children_recursive()

In [15]: print(blocks)
Notion/blocks/BlockArray(Heading 2 level Paragraph      blo)

In [16]: print(blocks.obj)
Heading 2 level
Paragraph
        block inside block
some text
```
## Available methods
### pytion.api.Element
`.get(id_)` - Get Element by ID.

`.get_parent(id_)` - Get parent object of current object if possible.

`.get_block_children(id_, limit)` - Get children Block objects of current Block object (tabulated texts) if exist

`.get_block_children_recursive(id_, max_depth, limit, force)` - Get children Block objects of current Block object (tabulated texts) if exist recursive

`.get_page_property(property_id, id_, limit)` - Retrieve a page property item.

`.db_query(id_, limit, filter_, sorts)` - Query Database

`.db_filter(...see desc...)` - Query Database

`.db_create(database_obj, parent, properties, title)` - Create Database

`.db_update(id_, title, properties)` - Update Database

`.page_create(page_obj, parent, properties, title)` - Create Page

`.page_update(id_, properties, title, archived)` - Update Page

`.block_update(id_, block_obj, new_text, arcived)` - Update text in Block.

`.block_append(id_, block, blocks)` - Append block or blocks children

More details and examples of this methods you can see into func descriptions.
### pytion.models.*
There are user classmethods for models:
`RichTextArray.create()`, `Property.create()`, `PropertyValue.create()`, `Database.create()`, `Page.create()`, `Block.create()`, `LinkTo.create()`
## Logging
Logging is muted by default. To enable to stdout and to file:
```
from pytion import setup_logging

setup_logging(level="debug", to_console=True, filename="pytion.log")
```