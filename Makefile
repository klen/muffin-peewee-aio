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

$(VIRTUAL_ENV): uv.lock pyproject.toml
	@uv sync
	@uv run pre-commit install
	@touch $(VIRTUAL_ENV)

.PHONY: t test
# target: test - Runs tests
t test: $(VIRTUAL_ENV)
	@uv run pytest tests

.PHONY: mypy
mypy: $(VIRTUAL_ENV)
	@uv run mypy

.PHONY: example
example: $(VIRTUAL_ENV)
	@uv run muffin example peewee_migrate
	@uv run uvicorn --reload --port 5000 example:app

# ==============
#  Bump version
# ==============

VERSION	?= minor
MAIN_BRANCH = master

.PHONY: release
VPART?=minor
# target: release - Bump version
release:
	git checkout master
	git pull
	git checkout develop
	git pull
	uvx bump-my-version bump $(VPART)
	uv lock
	@VERSION="$$(uv version --short)"; \
		{ \
			printf 'build(release): %s\n\n' "$$VERSION"; \
			printf 'Changes:\n\n'; \
			git log --oneline --pretty=format:'%s [%an]' $(MAIN_BRANCH)..develop | grep -Evi 'github|^Merge' || true; \
		} | git commit -a -F -; \
		git tag "$$VERSION";
	git checkout $(MAIN_BRANCH)
	git merge develop
	git checkout develop
	git merge $(MAIN_BRANCH)
	git push origin develop $(MAIN_BRANCH) --tags
	@echo "Release process complete for `uv version --short`"

.PHONY: minor
minor: release

.PHONY: patch
patch:
	make release VPART=patch

.PHONY: major
major:
	make release VPART=major

version v:
	uv version --short
