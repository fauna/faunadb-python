"Types used in queries and responses."

class Ref(object):
  """
  FaunaDB reference.
  Wraps around ref_str.
  """

  def __init__(self, ref_str):
    self.ref_str = ref_str

  def __str__(self):
    return self.ref_str

  def __repr__(self):
    return "Ref(%s)" % repr(self.ref_str)

  def __eq__(self, other):
    return isinstance(other, Ref) and self.ref_str == other.ref_str

  def to_class(self):
    if self.ref_str.startswith("classes"):
      # It looks like "classes/xxx/123", take "classes/xxx"
      return Ref(self.ref_str.split('/', 3)[0:2].join('/'))
    else:
      # It looks like "users/123", take "users"
      return Ref(self.ref_str.split('/', 2)[0])


class Set(object):
  """
  Set object for making FaunaDB queries.
  For constructiong sets out of other sets, see set functions in faunadb.query.
  """

  def __init__(self, match, index):
    self.match = match
    self.index = index

  def __str__(self):
    return "Set(%s, %s)" % (str(self.match), str(self.index))

  def __repr__(self):
    return "Set(%s, %s)" % (repr(self.match), repr(self.index))

  def __eq__(self, other):
    return isinstance(other, Set) and self.match == other.match and self.index == other.index


class Obj(object):
  """
  FaunaDB object.
  This may be necessary to distinguish query data from a function call.
  """

  def __init__(self, **kwargs):
    self.dct = kwargs

  def __str__(self):
    parts = [k + "=" + str(v) for k, v in self.dct.iteritems()]
    return "Obj(%s)" % ", ".join(parts)

  def __eq__(self, other):
    return isinstance(other, Obj) and  self.dct == other.dct


class Event(object):
  "FaunaDB event. See 'Events' in <https://faunadb.com/documentation#queries-values>."
  # pylint: disable=invalid-name
  def __init__(self, ts, action, resource):
    """
    :param ts: UNIX timestamp in microseconds.
    :param action: "create" or "delete".
    :param resource: Ref of instance that was changed.
    """

    self.ts = ts
    assert action in [None, "create", "delete"]
    self.action = action
    self.resource = resource

  def __str__(self):
    return "Event(ts=%s, action=%s, resource=%s)" % (self.ts, self.action, self.resource)

  def __eq__(self, other):
    return isinstance(other, Event) and \
      self.ts == other.ts and \
      self.action == other.action and \
      self.resource == other.resource
