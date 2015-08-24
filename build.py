from pynt import task
from subprocess import check_call

@task()
def document():
  check_call(["sphinx-build", "-b", "html", "docs", "built-docs"])


_common_lint_opts = ["--reports=n", "--indent-string='  '", "--indent-after-paren=2"]
_common_lint_disable = "invalid-name,locally-disabled,missing-docstring,too-few-public-methods"


@task()
def lint_faunadb():
  check_call(["pylint", "faunadb"] + _common_lint_opts + ["--disable=%s" % _common_lint_disable])


@task()
def lint_tests():
  test_disable = "no-member,no-self-use,relative-import,too-many-public-methods"
  disable = "--disable=%s,%s" % (_common_lint_disable, test_disable)
  check_call(["pylint", "tests"] + _common_lint_opts + [disable])


@task(lint_faunadb, lint_tests)
def lint():
  pass


@task()
def test():
  check_call(["nosetests"])


@task(document, lint, test)
def __DEFAULT__():
  pass
