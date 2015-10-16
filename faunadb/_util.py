def no_null_values(dct):
  out = {}
  for key in dct:
    val = dct[key]
    if val is not None:
      out[key] = val
  return out
