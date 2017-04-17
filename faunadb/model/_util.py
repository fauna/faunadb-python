def dict_dup(data):
  """
  Copy of JSON data.
  Passes Refs and Sets through directly with no copying.
  """
  if isinstance(data, dict):
    obj = {}
    for key in data:
      obj[key] = dict_dup(data[key])
    return obj
  else:
    return data


def get_path(path, data):
  """
  Recursively looks for :samp:`path` in :samp:`data`.
  e.g. :samp:`get_path(["a", "b"], {"a": {"b": 1}})` should be 1.

  :param path: Dict keys, outermost to innermost.
  :param data: Dict of data (potentially nested).
  :return:
    :samp:`None` if the path can not be traversed to the end;
    else the value at the end of the path.
  """
  for path_elem in path:
    if (not isinstance(data, dict)) or path_elem not in data:
      return None
    data = data[path_elem]
  return data


def set_path(path, value, data):
  """
  Opposite of get_path.
  If path does not fully exist yet, creates parts of the path as it goes.
  e.g. :samp:`set_path(["a", "b"], 1, {"a": {}})` should change data to be :samp:`{"a": {"b": 1}}`.
  """
  for i in range(0, len(path) - 1):
    path_elem = path[i]
    if path_elem not in data:
      data[path_elem] = {}
    data = data[path_elem]
  data[path[-1]] = value


def calculate_diff(original, current):
  """
  Difference between two dicts.
  Removed fields are represented as being changed to None.
  (FaunaDB treats null sets as deletion.)
  """

  diff = {}

  for key in original.keys():
    if key not in current:
      diff[key] = None

  for key in current.keys():
    old = original.get(key)
    new = current[key]
    if isinstance(old, dict) and isinstance(new, dict):
      inner_diff = calculate_diff(old, new)
      if inner_diff:
        diff[key] = inner_diff
    elif old != new:
      diff[key] = new

  return diff

