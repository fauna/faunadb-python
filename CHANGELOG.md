## 2.10.0
- Added `merge`, `format`, `reduce`
- Send X-Fauna-Driver with HTTP requests
- Added `move_database`, `range`

## 2.7.0
- Support new schema names: Class -> Collection; Instance -> Document
  Deprecated `create_class`, `class_expr`, `class_`, `classes`
  Added `create_collection`, `collection`, `collections`
- Added `to_seconds`, `to_millis`, `to_micros`, `day_of_week`, `day_of_month`, `day_of_year`, `month`, `hour`, `minute`, `second`.
- Added `create_role`, `role`, `roles`
- Added `find_str`, `find_str_regex`, `replace_str`, `replace_str_regex`,   `length`, `lowercase`, `uppercase`, `titlecase`, `ltrim`, `rtrim`, `space`, `substring`, `repeat`

## 2.6.0
- Expose last seen txn via `get_last_txn_time`
- Update documentation links

## 2.5.0 (August 1, 2018)
- Added `ngram` function
- Added `is_empty` and `is_nonempty` functions
- Added `to_string`, `to_number`, `to_time`, and `to_date` functions

## 2.0.0 (March 19, 2018)

- Added support for recursive references
- Added `abort` function
- Added `normalizer` argument to `casefold` function
- Added `new_id` function
- Deprecated `next_id` function in favor of `new_id`
- Added `identity` and `has_identity` functions
- Added `singleton` and `events` functions
- Added `select_all` function

## 1.1.0 (September 12, 2017)

- Added `call`, `query`, and `create_function` query functions
- Added `@query` type support

## 1.0.0 (March 13, 2017)

- Official release

## 0.1.2 (February 28, 2017)

- Added `key_for_secret` and `at` query functions
- Added `@bytes` type support (via `bytearray`)

## 0.1.1 (December 6, 2016)

- Fix default endpoint

## 0.1.0 (December 2, 2016)

- Initial release
