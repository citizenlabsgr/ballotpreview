.PHONY: all
all: install

.PHONY: ci
ci: format check test

###############################################################################
# System Dependencies

.PHONY: doctor
doctor:
	bin/verchew --exit-code

###############################################################################
# Project Dependencies

.PHONY: install
install: .venv/.flag

.venv/.flag: poetry.lock runtime.txt requirements.txt
	@ poetry config virtualenvs.in-project true
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
# Development Tasks

.PHONY: run
run: install
	poetry run python main.py

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

.PHONY: watch
watch: install
	poetry run pytest-watch --nobeep --runner="make test" --onpass="make check && clear && echo 'All tests passed.'"

###############################################################################
# Release Tasks

SITE ?= share.michiganelections.io

.PHONY: e2e
e2e: install
	poetry install --extras e2e
	poetry run pomace run $(SITE) -p first_name -p last_name -p birth_date -p zip_code

###############################################################################
# Production Tasks

.PHONY: run-production
run-production: install
	poetry run heroku local
