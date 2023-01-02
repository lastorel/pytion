# Changelog

## v1.3.3

- [#46](https://github.com/lastorel/pytion/issues/46): `this_week` filter condition for database query
- `status` type Properties DB filtering added
- [#44](https://github.com/lastorel/pytion/issues/44): `workspace_name` for `bot` type User 
- [#43](https://github.com/lastorel/pytion/issues/43): full support of `heading` type blocks

## v1.3.2

- [#34](https://github.com/lastorel/pytion/issues/34): `status` Property type added

## v1.3.1

- [#32](https://github.com/lastorel/pytion/issues/32): Rollback of Page retrieving with properties
- [#35](https://github.com/lastorel/pytion/issues/35): Fix PropertyValue with rollup type

## v1.3.0

- [#27](https://github.com/lastorel/pytion/issues/27): Switched from `2022-02-22` to `2022-06-28` version of Notion API
- `Request()` (internal) method argument added
- [#27](https://github.com/lastorel/pytion/issues/27): Fix of parent object hierarchy
- [#27](https://github.com/lastorel/pytion/issues/27): `models.Block` now has non-empty `parent` attr
- `models.Database`: `is_inline` attr added
- `Notion()`: new optional arg `version` added to customize API interaction
- [#27](https://github.com/lastorel/pytion/issues/27): You must retrieve Page properties manually. `.get_page_properties` method added
- [#27](https://github.com/lastorel/pytion/issues/27): add support of `relation` type `Property`
- [#27](https://github.com/lastorel/pytion/issues/27): updates for `relation` type `PropertyValue`
- [#16](https://github.com/lastorel/pytion/issues/17): tests of Property model
- [#28](https://github.com/lastorel/pytion/issues/28): Add whoami method
- [#16](https://github.com/lastorel/pytion/issues/16): Add search engine

### Breaking changes

- `Request()` method now looks for positional argument `api` for getting version (internal method)
- Page has title=`unknown` until you retrieve its properties
- `PropertyValue` with `relation` type now represents by list of `LinkTo` object instead of list of IDs