# Changelog

## v1.3.0

- \#27: Switched from `2022-02-22` to `2022-06-28` version of Notion API
- `Request()` (internal) method argument added
- \#27: Fix of parent object hierarchy
- \#27: `models.Block` now has non-empty `parent` attr
- `models.Database`: `is_inline` attr added
- `Notion()`: new optional arg `version` added to customize API interaction
- \#27: You must retrieve Page properties manually. `.get_page_properties` method added

### Breaking changes

- `Request()` method now looks for positional argument `api` for getting version (internal method)
- Page has title=`unknown` until you retrieve its properties