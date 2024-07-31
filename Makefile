VIRTUAL_ENV ?= .venv

all: $(VIRTUAL_ENV)

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile

.PHONY: clean
# target: clean - Display callable targets
clean:
	rm -rf build/ dist/ docs/_build *.egg-info
	find $(CURDIR) -name "*.py[co]" -delete
	find $(CURDIR) -name "*.orig" -delete
	find $(CURDIR)/$(MODULE) -name "__pycache__" | xargs rm -rf

# =============
#  Development
# =============

$(VIRTUAL_ENV): poetry.lock .pre-commit-config.yaml
	@[ -d $(VIRTUAL_ENV) ] || python -m venv $(VIRTUAL_ENV)
	@poetry install --with dev
	@poetry run pre-commit install
	@touch $(VIRTUAL_ENV)

.PHONY: t test
# target: test - Runs tests
t test: $(VIRTUAL_ENV)
	@poetry run pytest tests

.PHONY: mypy
mypy: $(VIRTUAL_ENV)
	@poetry run mypy

.PHONY: example
example: $(VIRTUAL_ENV)
	@poetry run muffin example peewee_migrate
	@poetry run uvicorn --reload --port 5000 example:app

# ==============
#  Bump version
# ==============

.PHONY: release
VERSION?=minor
# target: release - Bump version
release: $(VIRTUAL_ENV)
	@$(eval VFROM := $(shell poetry version -s))
	@poetry version $(VERSION)
	@git commit -am "Bump version $(VFROM) → `poetry version -s`"
	@git tag `poetry version -s`
	@git checkout master
	@git merge develop
	@git checkout develop
	@git push --tags origin develop master

.PHONY: minor
minor: release

.PHONY: patch
patch:
	make release VERSION=patch

.PHONY: major
major:
	make release VERSION=major
