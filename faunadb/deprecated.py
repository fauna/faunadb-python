import warnings
import functools

def deprecated(reason):
  def decorator(old_func):

    @functools.wraps(old_func)
    def new_func(*args, **kvargs):
      fmt = "{name}: {reason}"
      warnings.warn(
        fmt.format(name=old_func.__name__, reason=reason),
        category=DeprecationWarning,
        stacklevel=2
      )
      return old_func(*args, **kvargs)

    return new_func

  return decorator
