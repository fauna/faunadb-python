all: test lint doc

doc:
	sphinx-build -E -b html docs docs/_build/html

test:
	python -m unittest discover

coverage:
	coverage run -m unittest discover
	coverage report -m
	coverage html

lint: lint_faunadb lint_tests

lint_faunadb:
	pylint faunadb --reports=n --indent-string='  ' --indent-after-paren=2 --disable=invalid-name,locally-disabled,missing-docstring,too-few-public-methods,too-many-arguments

lint_tests:
	pylint tests --reports=n --indent-string='  ' --indent-after-paren=2 --disable=invalid-name,locally-disabled,missing-docstring,too-few-public-methods,too-many-arguments,no-member,no-self-use,protected-access,relative-import,too-many-public-methods
