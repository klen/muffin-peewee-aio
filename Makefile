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

.PHONY: types
# target: types - Check typing
types: $(VIRTUAL_ENV)
	@echo 'Checking typing...'
	@uv run pyrefly check

.PHONY: lint
# target: lint - Check code
lint: $(VIRTUAL_ENV)
	@make types
	@uv run ruff check

.PHONY: link
# target: link - Alias for lint
link: lint

.PHONY: example
example: $(VIRTUAL_ENV)
	@uv run muffin example peewee_migrate
	@uv run uvicorn --reload --port 5000 example:app

# ==============
#  Bump version
# ==============

MAIN_BRANCH = master
STAGE_BRANCH = develop

.PHONY: release
VPART?=minor
# target: release - Bump version
release:
	git checkout $(MAIN_BRANCH)
	git pull
	git checkout $(STAGE_BRANCH)
	git pull
	uvx bump-my-version bump $(VPART)
	uv lock
	@VERSION="$$(uv version --short)"; \
		{ \
			printf 'build(release): %s\n\n' "$$VERSION"; \
			printf 'Changes:\n\n'; \
			git log --oneline --pretty=format:'%s [%an]' $(MAIN_BRANCH)..$(STAGE_BRANCH) | grep -Evi 'github|^Merge' || true; \
		} | git commit -a -F -; \
		git tag -a "$$VERSION" -m "$$VERSION"; \
		git rev-parse -q --verify "refs/tags/$$VERSION" >/dev/null
	git checkout $(MAIN_BRANCH)
	git merge $(STAGE_BRANCH)
	git checkout $(STAGE_BRANCH)
	git merge $(MAIN_BRANCH)
	@git -c push.followTags=false push origin $(STAGE_BRANCH) $(MAIN_BRANCH)
	@VERSION="$$(uv version --short)"; \
		git push origin "refs/tags/$$VERSION"
	@echo "Release process complete for `uv version --short`"

.PHONY: minor
minor: release

.PHONY: patch
patch:
	$(MAKE) release VPART=patch

.PHONY: major
major:
	$(MAKE) release VPART=major

version v:
	uv version --short
