.PHONY: lint type test isort isort-check build upload

PYMODULE:=kit_web_ui

all: lint isort-check type

lint:
	flake8 $(PYMODULE)

type:
	mypy $(PYMODULE)

isort-check:
	python -m isort --check $(PYMODULE)

isort:
	python -m isort $(PYMODULE)

build:
	python -m build

clean:
	rm -rf dist/* build/*
