
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

.PHONY: docs
docs:
	rm -Rf html
	pdoc --html src
	mkdocs build  -d./_site
	mv html _site/python-site

.PHONY: rel-agent
rel-agent: check-version
	rm -Rf $(ROOT_DIR)/dist
	sed -i "s/[0-9]*\.[0-9]*\.[0-9]*/$(VERSION)/" $(ROOT_DIR)/src/deep/version.py

	python -m build $(ROOT_DIR)

	python -m twine upload $(ROOT_DIR)/dist/*

.PHONY: rel-docker-test-app
rel-docker-test-app:
	docker build -t ghcr.io/intergral/deep-python-client:simple-app $(ROOT_DIR)/examples/simple-app-docker

	docker push ghcr.io/intergral/deep-python-client:simple-app
