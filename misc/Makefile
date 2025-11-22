PYTHON ?= python3
WORKFLOW := project_management/data_workflows.py
SEASON ?= $(shell date +%Y)
WEEK ?=
SEASON_TYPE ?= regular
API_KEY ?=
MIGRATED ?= model_pack/${SEASON}_starter_pack_migrated.csv
EPOCHS ?= 300
LR ?= 0.001

ifeq ($(strip $(WEEK)),)
WEEK_FLAG :=
else
WEEK_FLAG := --week $(WEEK)
endif

ifeq ($(strip $(API_KEY)),)
API_FLAG :=
else
API_FLAG := --api-key $(API_KEY)
endif

.PHONY: help bootstrap-notebooks update-starter-data extend-training train-fastai update-data tests verify-data

help:
	@echo "Available targets:"
	@echo "  make bootstrap-notebooks     # Injects auto-setup cells"
	@echo "  make update-starter-data     # Pulls fresh CFBD games"
	@echo "  make extend-training         # Appends migrated data"
	@echo "  make train-fastai            # Trains FastAI neural model"
	@echo "  make update-data             # Runs starter-data + extend + train"
	@echo "  make tests                   # Runs pytest suite"
	@echo "  make verify-data             # Runs validation, remediation, and admin audits"

bootstrap-notebooks:
	@$(PYTHON) project_management/TOOLS_AND_CONFIG/inject_notebook_bootstrap.py

update-starter-data:
	@$(PYTHON) $(WORKFLOW) starter-data --season $(SEASON) $(WEEK_FLAG) --season-type $(SEASON_TYPE) $(API_FLAG)

extend-training:
	@$(PYTHON) $(WORKFLOW) extend-training --migrated-file $(MIGRATED)

train-fastai:
	@$(PYTHON) $(WORKFLOW) train-fastai --epochs $(EPOCHS) --learning-rate $(LR)

update-data: update-starter-data extend-training train-fastai

tests:
	@$(PYTHON) -m pytest -v

verify-data:
	@echo "🔍 Running data validation script..."
	@$(PYTHON) DATA_VALIDATION_SCRIPT.py
	@echo "🛠️  Running data remediation script..."
	@$(PYTHON) DATA_REMEDIATION_SCRIPT.py
	@echo "📊 Running master admin system audit..."
	@$(PYTHON) MASTER_ADMIN_SYSTEM_AUDIT.py
