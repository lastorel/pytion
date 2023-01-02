# pytion

[![PyPI](https://img.shields.io/pypi/v/pytion.svg)](https://pypi.org/project/pytion)
![PyVersion](https://img.shields.io/pypi/pyversions/pytion)
![CodeSize](https://img.shields.io/github/languages/code-size/lastorel/pytion)
[![LICENSE](https://img.shields.io/github/license/lastorel/pytion)](LICENSE)

Independent unofficial **Python client** for the official **Notion API** (for internal integrations only)

Client is built with its own object model based on API

So if you are using **notion.so** and want to automate some stuff with the original API, you're welcome!  
You can read any available data, create basic models, and even work with databases.

Current Notion API version = **"2022-06-28"**

_*does not use notion-sdk-py client_

See [Change Log](./CHANGELOG.md)

# Contents

1. [Quick Start](#quick-start)
2. [Pytion API](#pytion-api)
   1. [Searching](#search)
   2. [pytion.api.Element](#pytionapielement)
3. [Models](#models)
   1. [pytion.models](#pytionmodels)
   2. [Supported block types](#supported-block-types)
   3. [Supported Property types](#supported-property-types)
   4. [Block creating examples](#block-creating-examples)
4. [Logging](#logging)

## Quick start

```
pip install pytion
```

Create new integration and get your Notion API Token at notion.so -> [here](https://www.notion.com/my-integrations).  
Invite your new integration 'manager' to your pages or databases.

```python
from pytion import Notion; no = Notion(token=SOME_TOKEN)
```

Or put your token for Notion API into file `token` at script directory and use simple `no = Notion()`

```python
from pytion import Notion
no = Notion(token=SOME_TOKEN)
page = no.pages.get("PAGE ID")  # retrieve page data (not content) and create object
blocks = page.get_block_children()  # retrieve page content and create list of objects
database = no.databases.get("Database ID")  # retrieve database data (not content) and create object
# retrieve database content by filtering with sorting
pages = database.db_filter(property_name="Done", property_type="checkbox", value=False, descending="title")
```

```
In [1]: from pytion import Notion

In [2]: no = Notion(token=SOME_TOKEN)

In [3]: page = no.pages.get("a458613160da45fa96367c8a594297c7")
In [4]: print(page)
Notion/pages/Page(Example page)

In [5]: blocks = page.get_block_children_recursive()

In [6]: print(blocks)
Notion/blocks/BlockArray(## Migration planning [x] Rese)

In [7]: print(blocks.obj)
## Migration planning
[x] Reset new switch 2022-05-12T00:00:00.000+03:00 → 2022-05-13T01:00:00.000+03:00 
	- reboot
	- hold reset button
[x] Connect to console with baud rate 9600
[ ] Skip default configuration dialog
Use LinkTo(configs) 
[Integration changes](https://developers.notion.com/changelog?page=2)

In [8]: print(blocks.obj.simple)
Migration planning
Reset new switch 2022-05-12T00:00:00.000+03:00 → 2022-05-13T01:00:00.000+03:00 
	reboot
	hold reset button
Connect to console with baud rate 9600
Skip default configuration dialog
Use https://api.notion.com/v1/pages/90ea1231865f4af28055b855c2fba267 
https://developers.notion.com/changelog?page=2
```

## Pytion API

Almost all operations are carried out through `Notion` or `Element` object:

```python
page = no.pages.get("a458613160da45fa96367c8a594297c7")

# no -> Notion
# pages -> URI in https://api.notion.com/v1/PAGES/a458613160da45fa96367c8a594297c7
# get -> pytion API method
# page -> Element
# page.obj -> Page (main data structure)
```

so:

- `isinstance(no, Notion) == True`
- `isinstance(no.pages, Element) == True`
- `isinstance(no.databases, Element) == True`
- `isinstance(page, Element) == True`
- `isinstance(page.obj, Page) == True`

and if you want to retrieve a database - you must use _"databases"_ URI

```python
database = no.databases.get("123412341234")
```

and the same applies for _"blocks"_ and _"users"_. Valid URI-s are:

- _pages_
- _blocks_
- _databases_
- _users_

When you work with existing `Element` object like `page` above, all [methods](#pytionapielement) below will be applied to this Page:

```python
new_page = page.page_update(title="new page name 2")

# new_page is not a new page, it is updated page
# new_page.obj is equal page.obj except title and last_edited properties
```

### Search

There is a search example:
```python
no = Notion(token)

r = no.search("updating", object_type="page")
print(r.obj)
# output:
# Page for updating
# Page to updating databases
```


### pytion.api.Element

There is a list of available methods for communicate with **api.notion.com**. These methods are better structured in [next chapter](#pytionmodels).

`.get(id_)` - Get Element by ID.

`.get_parent(id_)` - Get parent object of current object if possible.

`.get_block_children(id_, limit)` - Get children Block objects of current Block object (tabulated texts) if exist.

`.get_block_children_recursive(id_, max_depth, limit, force)` - Get children Block objects of current Block object (tabulated texts) if exist recursive.

`.get_page_property(property_id, id_, limit)` - Retrieve a page property item.

`.get_page_properties(title_only, obj)` - Retrieve the title or all properties of current Page or Page `obj`
*(deprecated, useful for v1.3.0 only)*

`.db_query(id_, limit, filter_, sorts)` - Query Database.

`.db_filter(...see desc...)` - Query Database.

`.db_create(database_obj, parent, properties, title)` - Create Database.

**_There is no way to delete a database object yet!_**

`.db_update(id_, title, properties)` - Update Database.

`.page_create(page_obj, parent, properties, title)` - Create Page.

`.page_update(id_, properties, title, archived)` - Update Page.

`.block_update(id_, block_obj, new_text, archived)` - Update text in Block.

`.block_append(id_, block, blocks)` - Append block or blocks children.

`.get_myself()` - Retrieve my bot User.

`.from_linkto(linkto)` - Creates new Element object based on LinkTo information.

`.from_object(model)` - Creates new Element object from Page, Block or Database object. Usable while Element object contains an Array.

> More details and usage examples of these methods you can see into func descriptions.

## Models

### pytion.models

There are classes **based on API** structures:

- `RichText` based on [Rich text object](https://developers.notion.com/reference/rich-text)
- `RichTextArray` is a list of RichText objects with useful methods
  - You can create object by simple `RichTextArray.create("My title text")` and then use it in any methods
  - Any Rich Text getting from API will be RichTextArray
  - `str()` returns plain text of all "Rich Texts". ez
  - `+` operator is available with `str` and `RichTextArray`
  - `.simple` property returns stripped plain text without any markdown syntax. useful for URL
- `Database` based on [Database object](https://developers.notion.com/reference/database)
  - You can create object `Database.create(...)` and/or use `.db_create(...)` API method
  - attrs represent API model. Complex structures like `created_by` are wrapped in internal objects
  - use `.db_update()` API method for modify a real database (for ex. properties or title)
  - use `.db_query()` to get all database content (it will be `PageArray`)
  - use `.db_filter()` to get database content with filtering and/or sorting
  - has `.is_inline` attr with the value True if the database appears in the page as an inline block
- `Page` based on [Page object](https://developers.notion.com/reference/page)
  - You can create object `Page.create(...)` and/or use `.page_create(...)` API method
  - use `.page_update()` method to modify attributes or delete the page
  - use `.get_block_children()` to get page content (without nested blocks) (it will be `BlockArray`)
  - use `.get_block_children_recursive()` to get page content with nested blocks
  - use `.get_page_property()` to retrieve the specific `PropertyValue` of the page
- `Block` based on [Block object](https://developers.notion.com/reference/block)
  - You can create object `Block.create(...)` of specific type from [_support matrix_](#supported-block-types) below and then use it while creating pages or appending
  - use `.block_update()` to replace content or change _extension attributes_ or delete the block
  - use `.block_append()` to add a new block to a page or add a nested block to another block
  - use `.get_block_children()` to get first level nested blocks
  - use `.get_block_children_recursive()` to get all levels nested blocks
- `User` based on [User object](https://developers.notion.com/reference/user)
  - You can create object `User.create(...)` and use it in some properties like `people` type property
  - You can retrieve more data about a User by his ID using `.get()`
  - use `.get_myself()` to retrieve the current bot User
- `Property` based on [Property object](https://developers.notion.com/reference/property-object)
  - You can create object `Property.create(...)` while creating or editing database: `.db_create()` or `.db_update()`
  - `formula`, `rollup` type properties configuration is not supported
- `PropertyValue` based on [Property values](https://developers.notion.com/reference/property-value-object)
  - You can create object `PropertyValue.create(...)` to set or edit page properties by `.page_create()` or `.page_update()`
  - `files`, `formula`, `rollup` type properties are not editable

There are also useful **internal** classes:

- `BlockArray` is found when API returns page content in "list of blocks" format
  - it is useful to represent all content by `str()`
  - also it has `simple` property like `RichTextArray` object
  - it automatically indents `str` output of nested blocks
- `PageArray` is found when API returns the result of database query (list of pages)
- `LinkTo` is basic internal model to link to any Notion object
  - You can create object `LinkTo.create()` and use it in many places and methods
  - use `LinkTo(from_object=my_page1)` to quickly create a link to any existing object of pytion.models
  - `link` property of `LinkTo` returns expanded URL
- `ElementArray` is found while using `.search()` endpoint. It's a parent of `PageArray`

> And every model has a `.get()` method that returns API friendly JSON.
 
### Supported Property types

| Property type            | value type          | read (DB) | read value (Page) | create (DB) | create value (Page) | Oper attrs                          | Config attrs                        |
|--------------------------|---------------------|-----------|-------------------|-------------|---------------------|-------------------------------------|-------------------------------------|
| `title`                  | `RichTextArray`     | +         | +                 | +           | +                   |                                     |                                     |
| `rich_text`              | `RichTextArray`     | +         | +                 | +           | +                   |                                     |                                     |
| `number`                 | `int`/`float`       | +         | +                 | +           | +                   |                                     | ~~format~~                          |
| `select`                 | `str`               | +         | +                 | +           | +                   |                                     | ~~options~~                         |
| `multi_select`           | `List[str]`         | +         | +                 | +           | +                   |                                     | ~~options~~                         |
| `status`                 | `str`               | +         | +                 | +           | +\*\*\*\*           |                                     | `options`, `groups` (read-only)     |
| `date`                   | `str`               | +         | +                 | +           | +                   | `start: datetime` `end: datetime`\* |                                     |
| `people`                 | `List[User]`        | +         | +                 | +           | +\*\*               |                                     |                                     |
| `files`                  |                     | +         | -                 | +           | -                   |                                     |                                     |
| `checkbox`               | `bool`              | +         | +                 | +           | +                   |                                     |                                     |
| `url`                    | `str`               | +         | +                 | +           | +                   |                                     |                                     |
| `email`                  | `str`               | +         | +                 | +           | +                   |                                     |                                     |
| `phone_number`           | `str`               | +         | +                 | +           | +                   |                                     |                                     |
| `formula`                |                     | -         | +                 | -           | -                   |                                     |                                     |
| `relation`               | `List[LinkTo]`      | +         | +                 | +           | +                   |                                     | `single_property` / `dual_property` |
| `rollup`                 | depends on relation | -         | +                 | -           | -                   |                                     |                                     |
| `created_time`\*\*\*     | `datetime`          | +         | +                 | +           | -                   |                                     |                                     |
| `created_by`\*\*\*       | `User`              | +         | +                 | +           | -                   |                                     |                                     |
| `last_edited_time`\*\*\* | `datetime`          | +         | +                 | +           | -                   |                                     |                                     |
| `last_edited_by`\*\*\*   | `User`              | +         | +                 | +           | -                   |                                     |                                     |

> [\*] - Create examples:  
> `pv = PropertyValue.create(type_="date", value=datetime.now())`  
> `pv = PropertyValue.create(type_="date", date={"start": str(datetime(2022, 2, 1, 5)), "end": str(datetime.now())})`  
> [\*\*] - Create example:  
> `user = User.create('1d393ffb5efd4d09adfc2cb6738e4812')`  
> `pv = PropertyValue.create(type_="people", value=[user])`  
> [\*\*\*] - Every Base model like Page already has mandatory attributes created/last_edited returned by API  
> [\*\*\*\*] - Status type is not configurable. API doesn't support NEW options added via Property modify or updating a Page


### Supported block types

At present the API only supports the block types which are listed in the reference below. Any unsupported block types will continue to appear in the structure, but only contain a `type` set to `"unsupported"`.
Colors are not yet supported.

Every Block has mandatory attributes and extension attributes. There are mandatory:

- `id: str` - UUID-64 without hyphens
- `object: str` - always `"block"` (from API)
- `created_time: datetime` - from API
- `created_by: User` - from API
- `last_edited_time: datetime` - from API
- `last_edited_by: User` - from API
- `type: str` - the type of block (from API)
- `has_children: bool` - does the block have children blocks (from API)
- `archived: bool` - does the block marked as deleted (from API)
- `text: Union[str, RichTextArray]` - **main content**
- `simple: str` - only simple text string (url expanded)

Extension attributes are listed below in support matrix:

| Block Type           | Description                               | Read support | Create support | Can have children | Extension attributes                              |
|----------------------|-------------------------------------------|--------------|----------------|-------------------|---------------------------------------------------|
| `paragraph`          | Simple Block with text                    | +            | +              | +                 |                                                   |
| `heading_1`          | Heading Block with text highest level     | +            | +              | -/+\*             | `is_toggleable: bool`                             |
| `heading_2`          | Heading Block with text medium level      | +            | +              | -/+\*             | `is_toggleable: bool`                             |
| `heading_3`          | Heading Block with text lowest level      | +            | +              | -/+\*             | `is_toggleable: bool`                             |
| `bulleted_list_item` | Text Block with bullet                    | +            | -              | +                 |                                                   |
| `numbered_list_item` | Text Block with number                    | +            | -              | +                 |                                                   |
| `to_do`              | Text Block with checkbox                  | +            | +              | +                 | `checked: bool`                                   |
| `toggle`             | Text Block with toggle to children blocks | +            | -              | +                 |                                                   |
| `code`               | Text Block with code style                | +            | +              | +                 | `language: str`, `caption: RichTextArray`         |
| `child_page`         | Page inside                               | +            | -              | +                 |                                                   |
| `child_database`     | Database inside                           | +            | -              | +                 |                                                   |
| `embed`              | Embed online content                      | +            | -              | -                 | `caption: RichTextArray`                          |
| `image`              | Embed image content                       | +            | -              | -                 | `caption: RichTextArray`, `expiry_time: datetime` |
| `video`              | Embed video content                       | +            | -              | -                 | `caption: RichTextArray`, `expiry_time: datetime` |
| `file`               | Embed file content                        | +            | -              | -                 | `caption: RichTextArray`, `expiry_time: datetime` |
| `pdf`                | Embed pdf content                         | +            | -              | -                 | `caption: RichTextArray`, `expiry_time: datetime` |
| `bookmark`           | Block for URL Link                        | +            | -              | -                 | `caption: RichTextArray`                          |
| `callout`            | Highlighted footnote text Block           | +            | -              | +                 | `icon: dict`                                      |
| `quote`              | Text Block with quote style               | +            | -              | +                 |                                                   |
| `equation`           | KaTeX compatible text Block               | +            | -              | -                 |                                                   |
| `divider`            | Simple line to divide the page            | +            | -              | -                 |                                                   |
| `table_of_contents`  | Block with content structure in the page  | +            | -              | -                 |                                                   |
| `column`             |                                           | -            | -              | +                 |                                                   |
| `column_list`        |                                           | -            | -              | -                 |                                                   |
| `link_preview`       | Same as `bookmark`                        | +            | -              | -                 |                                                   |
| `synced_block`       | Block for synced content aka parent       | +            | -              | +                 | `synced_from: LinkTo`                             |
| `template`           | Template Block title                      | +            | -              | +                 |                                                   |
| `link_to_page`       | Block with link to particular page `@...` | +            | -              | -                 | `link: LinkTo`                                    |
| `table`              | Table Block with some attrs               | +            | -              | +                 | `table_width: int`                                |
| `table_row`          | Children Blocks with table row content    | +            | -              | -                 |                                                   |
| `breadcrumb`         | Empty Block actually                      | +            | -              | -                 |                                                   |
| `unsupported`        | Blocks unsupported by API                 | +            | -              | -                 |                                                   |

> [\*] - `heading_X` blocks can have children if `is_toggleable` is True 

### Block creating examples

Create `paragraph` block object and add it to Notion:

```python
from pytion.models import Block
my_text_block = Block.create("Hello World!")
my_text_block = Block.create(text="Hello World!", type_="paragraph")  # the same

# indented append my block to other known block:
no.blocks.block_append("5f60073a9dda4a9c93a212a74a107359", block=my_text_block)

# append my block to a known page (in the end)
no.blocks.block_append("9796f2525016128d9af4bf12b236b555", block=my_text_block)  # the same operation actually

# another way to append:
my_page = no.pages.get("9796f2525016128d9af4bf12b236b555")
my_page.block_append(block=my_text_block)
```

Create `to_do` block object:

```python
from pytion.models import Block
my_todo_block = Block.create("create readme documentation", type_="to_do")
my_todo_block2 = Block.create("add 'create' method", type_="to_do", checked=True)
```

Create `code` block object:

```python
from pytion.models import Block
my_code_block = Block.create("code example here", type_="code", language="javascript")
my_code_block2 = Block.create("another code example", type_="code", caption="it will be plain text code block with caption")
```

Create `heading` block object:

```python
from pytion.models import Block
my_code_block = Block.create("Title 1 example here", type_="heading_1")
my_code_block2 = Block.create("Toggle Title 2", type_="heading_2", is_toggleable=True)
```

### Block deleting

```python
no.blocks.block_update("3d4af9f0f98641dea8c44e3864eed4d0", archived=True)
# or if you have Element with Block object already
block.block_update(archived=True)
```

## Logging

Logging is muted by default. To enable to stdout and/or to file:

```python
from pytion import setup_logging

setup_logging(level="debug", to_console=True, filename="pytion.log")
```
