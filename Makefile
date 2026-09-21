.PHONY: help install dev test test-upload frontend-install frontend-build build upload update clean

PYTHON ?= python
NPM ?= npm
STATIC_DIR := src/bailian_rag_demo/static

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	    awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install pinned dependencies
	$(PYTHON) -m pip install -r requirements.txt

dev:  ## Run uvicorn locally (requires .env or shell exports)
	$(PYTHON) -m uvicorn bailian_rag_demo.main:app --reload --host 127.0.0.1 --port 8000

test:  ## Run pytest
	$(PYTHON) -m pytest tests/ -v

test-upload:  ## Curl-based smoke test against locally-running server
	bash scripts/test_local.sh

frontend-install:  ## Install MateChat frontend dependencies
	cd frontend && $(NPM) install

frontend-build: frontend-install  ## Build the MateChat frontend and copy it into the package (served at "/")
	cd frontend && $(NPM) run build
	rm -rf $(STATIC_DIR)
	mkdir -p $(STATIC_DIR)
	cp -r frontend/dist/. $(STATIC_DIR)/

build: frontend-build  ## Build wheel, bundling the MateChat frontend (artifact in dist/)
	$(PYTHON) -m pip install --quiet build
	$(PYTHON) -m build

upload:  ## Upload to Bailian (usage: make upload NAME=my-rag-agent). Requires MODELSTUDIO_WORKSPACE_ID + ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET in the environment.
ifndef NAME
	$(error NAME is required, e.g. make upload NAME=my-rag-agent)
endif
	$(PYTHON) -m pip install --quiet "agentscope-runtime" alibabacloud-oss-v2 alibabacloud-credentials alibabacloud-tea-util
	runtime-fc-deploy --deploy-name "$(NAME)" --whl-path dist/*.whl

update:  ## Update a deployed app (usage: make update APP_ID=xxx)
ifndef APP_ID
	$(error APP_ID is required, e.g. make update APP_ID=d8a48e...)
endif
	$(PYTHON) -m pip install --quiet "agentscope-runtime" alibabacloud-oss-v2 alibabacloud-credentials alibabacloud-tea-util
	runtime-fc-deploy --update "$(APP_ID)" --whl-path dist/*.whl

clean:  ## Remove build artifacts
	rm -rf build/ dist/ src/*.egg-info src/bailian_rag_demo.egg-info $(STATIC_DIR) frontend/dist

