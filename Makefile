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

ifdef FAUNA_TIMEOUT
DOCKER_RUN_FLAGS += -e FAUNA_TIMEOUT=$(FAUNA_TIMEOUT)
endif

all: test lint doc

doc:
	sphinx-build -E -b html docs docs/_build/html

test:
	python -Wd -m nose2

coverage:
	python -Wd -m nose2 --with-coverage --coverage-report html

lint: lint-faunadb lint-tests

lint-faunadb:
	pylint faunadb --reports=n --indent-string='  ' --indent-after-paren=2 --disable=invalid-name,locally-disabled,missing-docstring,too-few-public-methods,too-many-arguments

lint-tests:
	pylint tests --reports=n --indent-string='  ' --indent-after-paren=2 --disable=invalid-name,locally-disabled,missing-docstring,too-few-public-methods,too-many-arguments,no-member,no-self-use,protected-access,relative-import,too-many-public-methods

jenkins-test:
	python -Wd -m nose2 --with-coverage --coverage-report xml --plugin nose2.plugins.junitxml --junit-xml && mv coverage.xml nose2-junit.xml results/ || { code=$$?; mv coverage.xml nose2-junit.xml results/; exit $$code; }

docker-wait:
	dockerize -wait $(FAUNA_SCHEME)://$(FAUNA_DOMAIN):$(FAUNA_PORT)/ping -timeout $(FAUNA_TIMEOUT)
