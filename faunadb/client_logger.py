from faunadb._json import to_json


def logger(logger_func):
  """
  Function that can be the ``observer`` for a :any:`Client`.
  Will call ``logger_func`` on a string representation of each :any:`RequestResult`.

  Use it like::

    def log(logged):
      print logged
    client = Client(observer=logger(log), ...)
    client.ping() # Calls `log`

  :param logger_func: Callback taking a string to be logged.
  """
  return lambda request_result: logger_func(show_request_result(request_result))


def show_request_result(request_result):
  """Translates a :any:`RequestResult` to a string suitable for logging."""
  rr = request_result
  parts = []
  log = parts.append

  def _indent(s):
    """Adds extra spaces to the beginning of every newline."""
    indent_str = "  "
    return ("\n" + indent_str).join(s.split("\n"))

  if rr.query:
    query_string = "?" + "&".join(("%s=%s" % (k, v) for k, v in rr.query))
  else:
    query_string = ""

  log("Fauna %s /%s%s\n" % (rr.method, rr.path, query_string))
  log("  Credentials: %s\n" % ("None" if rr.auth is None else "%s:%s" % rr.auth))
  if rr.request_content is not None:
    log("  Request JSON: %s\n" % _indent(to_json(rr.request_content, pretty=True)))
  log("  Response headers: %s\n" % _indent(to_json(dict(rr.response_headers), pretty=True)))
  log("  Response JSON: %s\n" % _indent(to_json(rr.response_content, pretty=True)))
  log("  Response (%i): Network latency %ims\n" % (rr.status_code, int(rr.time_taken * 1000)))

  return "".join(parts)
