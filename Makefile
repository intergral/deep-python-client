SHELL:=/bin/bash -O globstar

ROOT_DIR=$(shell pwd)

.PHONY: check-version
check-version:
ifdef v
VERSION=$(v)
endif
ifdef V
VERSION=$(V)
endif
ifndef VERSION
	$(error VERSION argument must be defined. (make rel-agent VERSION=0.0.2))
endif

.PHONY: test
test:
	pytest test

.PHONY: lint
lint:
	flake8

.PHONY: flake
flake: lint

.PHONY: check-python-vars
check-python-vars:
ifndef TWINE_USER
	$(error TWINE_USER argument must be defined.)
endif
ifndef TWINE_PASSWORD
	$(error TWINE_PASSWORD argument must be defined.)
endif

.PHONY: rel-agent
rel-agent: check-version check-python-vars
	rm -Rf $(ROOT_DIR)/dist
	sed -i "s/[0-9]*\.[0-9]*\.[0-9]*/$(VERSION)/" $(ROOT_DIR)/src/deep/version.py

	python -m build $(ROOT_DIR)

	python -m twine upload -u $(TWINE_USER) -p $(TWINE_PASSWORD) $(ROOT_DIR)/dist/*

.PHONY: rel-docker-test-app
rel-docker-test-app:
	docker build -t intergral/deep-python:latest $(ROOT_DIR)/examples/simple-app-docker

	docker push intergral/deep-python:latest

.PHONY: docs
docs:
	python $(ROOT_DIR)/scripts/gendocs.py $(ROOT_DIR)
	mkdocs build --config-file=$(ROOT_DIR)/mkdocs-mod.yml

.PHONY: clean
clean:
	rm -Rf _site docs/apidocs .pytest_cache test/.pytest_cache