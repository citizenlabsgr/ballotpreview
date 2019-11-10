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
	@ poetry config virtualenvs.in-project true || poetry config settings.virtualenvs.in-project true
	poetry install
	@ touch $@

ifndef CI

poetry.lock: pyproject.toml
	poetry lock
	@ touch $@

runtime.txt: .python-version
	echo "python-$(shell cat $<)" > $@

requirements.txt: poetry.lock
	poetry export --format requirements.txt --output $@ || echo "ERROR: Poetry 1.x required to export dependencies"

endif

.PHONY: clean
clean:
	rm -rf .venv

###############################################################################
# Development Tasks

.PHONY: run
run: install
	QUART_APP=app.main:app poetry run quart run

.PHONY: format
format: install
	poetry run isort app tests --recursive --apply
	poetry run black app tests

.PHONY: check
check: install
	poetry run mypy app tests

.PHONY: test
test: install
	poetry run pytest --cov=app --cov-branch
	poetry run coveragespace citizenlabsgr/ballotshare overall

.PHONY: watch
watch: install
	poetry run pytest-watch --nobeep --runner="make test" --onpass="make check && clear && echo 'All tests passed.'"

###############################################################################
# Production Tasks

.PHONY: run-production
run-production: install
	poetry run heroku local
