RUNTIME_IMAGE ?= python:3.6-alpine
DOCKER_RUN_FLAGS = -it --rm

ifdef FAUNA_ROOT_KEY
DOCKER_RUN_FLAGS += -e FAUNA_ROOT_KEY=$(FAUNA_ROOT_KEY)
endif

ifdef FAUNA_DOMAIN
DOCKER_RUN_FLAGS += -e FAUNA_DOMAIN=$(FAUNA_DOMAIN)
endif

ifdef FAUNA_SCHEME
DOCKER_RUN_FLAGS += -e FAUNA_SCHEME=$(FAUNA_SCHEME)
endif

ifdef FAUNA_PORT
DOCKER_RUN_FLAGS += -e FAUNA_PORT=$(FAUNA_PORT)
endif

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

docker-test:
	docker build -f Dockerfile.test -t faunadb-python-test:latest --build-arg RUNTIME_IMAGE=$(RUNTIME_IMAGE) .
	docker run $(DOCKER_RUN_FLAGS) faunadb-python-test:latest
