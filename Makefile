###############################################################################
# System Dependencies

.PHONY: bootstrap
bootstrap: ## Attempt to install system dependencies
	asdf plugin add python || asdf plugin update python
	asdf plugin add poetry || asdf plugin update poetry
	asdf install

.PHONY: doctor
doctor: ## Check for required system dependencies
	bin/verchew --exit-code

.envrc:
	echo export QUART_APP=app.views:app >> $@
	echo export #BUGSNAG_API_KEY=??? >> $@
	echo >> $@
	echo export ELECTIONS_HOST=https://michiganelections.io >> $@
	echo export BUDDIES_HOST=https://app.michiganelections.io >> $@
	echo export #TEST_VOTER=First,Last,YYYY-MM-DD,12345 >> $@
	echo export DEBUG=true >> $@
	- direnv allow

###############################################################################
# Project Dependencies

.PHONY: install
install: .venv/.flag ## Install project dependencies

.venv/.flag: poetry.lock
	@ rm -rf ~/Library/Preferences/pypoetry
	@ poetry config virtualenvs.in-project true
	poetry install
	@ touch $@

ifndef CI
poetry.lock: pyproject.toml
	poetry lock --no-update
	@ touch $@
endif

###############################################################################
# Validation Targets

.PHONY: format
format: install ## Format the code
	poetry run isort app tests
	poetry run black app tests

.PHONY: check
check: install format ## Run static analysis
ifdef CI
	git diff --exit-code
endif
	poetry run mypy app tests
	poetry run pylint app tests

.PHONY: test
test: install ## Run all tests
	poetry run pytest --failed-first --maxfail=1 --cov=app --cov-branch --cov-report=term-missing:skip-covered --cov-report=html
	poetry run coveragespace update overall --exit-code
ifdef CI
	poetry run coveralls
endif

.PHONY: all
all: format check test ## Run all CI targets

.PHONY: dev
dev: install ## Run all CI targets (loop)
	poetry run pytest-watch --nobeep --runner="make test" --onpass="make check && clear && echo 'All tests passed.'"

###############################################################################
# Server Tasks

HONCHO := .venv/bin/honcho

.PHONY: run
run: .envrc install ## Run the development server
ifdef PORT
	poetry run python main.py
else
	$(HONCHO) start --no-prefix --procfile=Procfile.dev preview reload
endif

.PHONY: run/all
run/all: .envrc install
	$(HONCHO) start --procfile=Procfile.dev

.PHONY: run/production
run/production: .envrc install
	poetry run heroku local

###############################################################################
# Release Tasks

DOMAIN ?= localhost:5000

.PHONY: e2e
e2e: install
	poetry install --extras e2e
	poetry run pomace alias $(DOMAIN) share.michiganelections.io
	poetry run pomace run $(DOMAIN) -p first_name -p last_name -p birth_date -p zip_code

###############################################################################
# Cleanup

.PHONY: clean
clean: ## Delete all temporary files
	rm -rf images
	rm -rf .venv

.PHONY: help
help: install
	@ grep -E '^[a-zA-Z/_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
