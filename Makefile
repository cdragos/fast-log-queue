# Define the name of the main virtual environment directory
DEV_VENV_DIR := .venv
# Define the Python executable to use
PYTHON := python3
# Define the command to create a virtual environment
VENV_CMD := $(PYTHON) -m venv $(BASE_VENV_DIR)
# Define the command to activate the base virtual environment
ACTIVATE_DEV := . $(DEV_VENV_DIR)/bin/activate

# ANSI color codes for red, green, and bold text
RED_BOLD := \033[1;31m
GREEN_BOLD := \033[1;32m
RESET := \033[0m

# Check if Python is available
check_python:
	@command -v $(PYTHON) >/dev/null 2>&1 || { \
		echo -e "$(RED_BOLD)Python is not installed. Aborting.$(RESET)"; \
		exit 1; \
	}

# Create the development virtual environment if it doesn't exist
create_dev_venv: check_python
	@if [ ! -d "$(DEV_VENV_DIR)" ]; then \
		echo -e "$(GREEN_BOLD)Creating development virtual environment...$(RESET)"; \
		$(VENV_CMD); \
	else \
		echo -e "\nDevelopment virtual environment already exists.\n"; \
	fi

# Activate the base virtual environment and install uv
install_uv_dev: create_dev_venv
	$(ACTIVATE_DEV) && pip install uv

# Compile and install development requirements using uv in the development virtual environment
install_dev_requirements: create_dev_venv
	@$(ACTIVATE_DEV) && \
	pip install uv && \
	uv pip compile pyproject.toml --extra dev -o requirements-dev.txt && \
	uv pip install -r requirements-dev.txt

# Setup the development environment
setup_dev: install_dev_requirements
	@echo -e "\n$(GREEN_BOLD)Development environment setup complete.$(RESET)\n"

.PHONY: \
	check_python \
	create_dev_venv \
	install_uv_dev \
	compile_dev_requirements \
	install_dev_requirements \
	setup_dev
