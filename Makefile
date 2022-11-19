.PHONY: all
all: install

.PHONY: ci
ci: format check test

###############################################################################
# System Dependencies

.PHONY: doctor
doctor:
	bin/verchew --exit-code

.envrc:
	echo export BUGSNAG_API_KEY=??? >> $@
	echo >> $@
	echo export ELECTIONS_HOST=https://michiganelections.io >> $@
	echo export BUDDIES_HOST=https://app.michiganelections.io >> $@
	- direnv allow

###############################################################################
# Project Dependencies

.PHONY: install
install: .venv/.flag

.venv/.flag: poetry.lock runtime.txt requirements.txt
	@ poetry config virtualenvs.in-project true
	poetry run python -m pip install --upgrade pip setuptools
	poetry install
	@ touch $@

ifndef CI

poetry.lock: pyproject.toml
	poetry lock --no-update
	@ touch $@

runtime.txt: .python-version
	echo "python-$(shell cat $<)" > $@

requirements.txt: poetry.lock
	poetry export --format requirements.txt --output $@ --without-hashes

endif

.PHONY: clean
clean:
	rm -rf images
	rm -rf .venv

###############################################################################
# Validation Targets

.PHONY: format
format: install
	poetry run isort app tests
	poetry run black app tests

.PHONY: check
check: install format
ifdef CI
	git diff --exit-code
endif
	poetry run mypy app tests
	poetry run pylint app tests

.PHONY: test
test: install
	poetry run pytest --failed-first --maxfail=1 --cov=app --cov-branch --cov-report=term-missing:skip-covered --cov-report=html
	poetry run coveragespace update overall --exit-code
ifdef CI
	poetry run coveralls
endif

.PHONY: dev
dev: install
	poetry run pytest-watch --nobeep --runner="make test" --onpass="make check && clear && echo 'All tests passed.'"

###############################################################################
# Server Tasks

.PHONY: run
run: .envrc install
	poetry run python main.py

.PHONY: run-production
run-production: .envrc install
	poetry run heroku local

###############################################################################
# Release Tasks

DOMAIN ?= localhost:5000

.PHONY: e2e
e2e: install
	poetry install --extras e2e
	poetry run pomace alias $(DOMAIN) share.michiganelections.io
	poetry run pomace run $(DOMAIN) -p first_name -p last_name -p birth_date -p zip_code
