from pynt import task
from subprocess import call, check_call

@task()
def document():
  # -E added to prevent random errors where an old version of docs persisted.
  check_call(["sphinx-build", "-E", "-b", "html", "docs", "docs/_build/html"])


_common_lint_opts = ["--reports=n", "--indent-string='  '", "--indent-after-paren=2"]
_common_lint_disable =\
  "invalid-name,locally-disabled,missing-docstring,too-few-public-methods,too-many-public-methods,too-many-arguments"


@task()
def lint_faunadb():
  call(["pylint", "faunadb"] + _common_lint_opts + ["--disable=%s" % _common_lint_disable])


@task()
def lint_tests():
  test_disable = "no-member,no-self-use,protected-access,relative-import,too-many-public-methods"
  disable = "--disable=%s,%s" % (_common_lint_disable, test_disable)
  call(["pylint", "tests"] + _common_lint_opts + [disable])


@task(lint_faunadb, lint_tests)
def lint():
  pass


@task()
def test():
  check_call(["nosetests"])


@task(document, lint, test)
def __DEFAULT__():
  pass
