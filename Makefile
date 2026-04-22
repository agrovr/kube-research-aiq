APP_DIR := apps/research-service
DASHBOARD_DIR := apps/dashboard
CHART := charts/kube-research-aiq
IMAGE ?= kube-research-aiq/research-service:dev
UI_IMAGE ?= kube-research-aiq/dashboard:dev

.PHONY: install test lint run-api run-worker dashboard-install dashboard-build docker-build docker-build-ui helm-template helm-lint

install:
	cd $(APP_DIR) && python -m pip install -e ".[dev]"

test:
	cd $(APP_DIR) && pytest

lint:
	cd $(APP_DIR) && ruff check src tests

run-api:
	cd $(APP_DIR) && KRAI_STORAGE_PATH=./jobs.json uvicorn kube_research_aiq.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	cd $(APP_DIR) && python -m kube_research_aiq.worker

dashboard-install:
	cd $(DASHBOARD_DIR) && npm install

dashboard-build:
	cd $(DASHBOARD_DIR) && npm run build

docker-build:
	docker build -t $(IMAGE) $(APP_DIR)

docker-build-ui:
	docker build -t $(UI_IMAGE) $(DASHBOARD_DIR)

helm-template:
	helm template kuberesearch $(CHART) --namespace aiq-system --create-namespace

helm-lint:
	helm lint $(CHART)
