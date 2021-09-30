## 4.1.1 [current]
- Exposes all the fields in the `errors` object
- Allows setting select function's default parameter as None value 
- Notifies about new package version

## 4.1.0
- Bearer auth token support
- Added runtime environment headers
- Adds support for Select's default parameter

## 4.0.1
- Fixes broken v4.0.0 by adding streams package to setup.py

## 4.0.0 [broken]
- Introduce document streaming api
- Add third party auth functions
- Bump api_version to `4`
- Add nightly and stable CI for Python 2.7, 3.4 and 3.8

## 3.0.0

- Refactored `contains` into `contains_path`, `contains_value`, `contains_path`
- Added `reverse` function
- Bump api version to `3`
- Add tests for versioned lambdas

## 2.12.0

- Added client specified query timeout
- Added Python 3.7 and 3.8 to CI

## 2.11.0

- Added `documents`, `now`
- Added `any` , `all`
- Added `count`, `sum`, `mean`
- Added `time_add`, `time_subtract`, `time_diff`
- Added `starts_with`, `ends_with`, `contains_str`, `contains_str_regex`, `regex_escape`
- Updated references to documentation

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
