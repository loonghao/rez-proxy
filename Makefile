# Makefile for rez-proxy
# All commands use nox for consistency between local and CI environments

.PHONY: help install test test-fast test-unit test-integration test-routers coverage coverage-html
.PHONY: lint lint-fix format mypy security safety quality pre-commit ci ci-fast
.PHONY: serve serve-debug serve-prod serve-remote serve-tolerant
.PHONY: build clean release-check demo docs dev
.PHONY: install-hooks uninstall-hooks

# Default target
help: ## Show this help message
	@echo "rez-proxy Development Commands"
	@echo "=============================="
	@echo ""
	@echo "All commands use nox for consistency between local and CI environments."
	@echo ""
	@echo "🧪 Testing & Coverage:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(test|coverage)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "🔍 Code Quality:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(lint|format|mypy|security|safety|quality|pre-commit|ci)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "🚀 Development Server:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(serve|demo)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "🔧 Utilities:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '(install|build|clean|docs|dev|hooks)' | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "💡 Examples:"
	@echo "  make install        # Set up development environment"
	@echo "  make test           # Run all tests with coverage"
	@echo "  make serve          # Start development server"
	@echo "  make ci             # Run full CI pipeline locally"
	@echo ""
	@echo "📖 For more details: uvx nox -l"

# Development setup
install: ## Install development environment
	uvx nox -s dev

dev: ## Show development environment info
	uvx nox -s dev

# Testing
test: ## Run all tests with coverage
	uvx nox -s test

test-fast: ## Run tests without coverage (faster)
	uvx nox -s test_fast

test-unit: ## Run only unit tests
	uvx nox -s test_unit

test-integration: ## Run integration tests
	uvx nox -s test_integration

test-routers: ## Run router tests
	uvx nox -s test_routers

test-watch: ## Run tests in watch mode
	uvx nox -s test_watch

# Coverage
coverage: ## Generate coverage report
	uvx nox -s coverage

coverage-html: ## Generate and open HTML coverage report
	uvx nox -s coverage_html

# Code quality
lint: ## Run linting checks
	uvx nox -s lint

lint-fix: ## Run linting and fix issues
	uvx nox -s lint_fix

format: ## Format code
	uvx nox -s format

mypy: ## Run type checking
	uvx nox -s mypy

security: ## Run security scanning
	uvx nox -s security

safety: ## Check dependencies for security vulnerabilities
	uvx nox -s safety

quality: ## Run all quality checks
	uvx nox -s quality

pre-commit: ## Run pre-commit checks
	uvx nox -s pre_commit

# CI/CD
ci: ## Run full CI pipeline
	uvx nox -s ci

ci-fast: ## Run fast CI checks
	uvx nox -s ci_fast

# Development server
serve: ## Start development server with auto-reload
	uvx nox -s serve

serve-debug: ## Start server with enhanced debugging
	uvx nox -s serve_debug

serve-prod: ## Start production-like server
	uvx nox -s serve_prod

serve-remote: ## Start server for remote access
	uvx nox -s serve_remote

serve-tolerant: ## Start server in tolerant mode
	uvx nox -s serve_tolerant

# Utilities
build: ## Build package
	uvx nox -s build

clean: ## Clean build artifacts
	uvx nox -s clean

release-check: ## Run release checks
	uvx nox -s release_check

demo: ## Run API demo
	uvx nox -s demo

docs: ## Show documentation info
	uvx nox -s docs

# Git hooks
install-hooks: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed"
	@echo "💡 Run 'make pre-commit' to test hooks"

uninstall-hooks: ## Uninstall pre-commit hooks
	pre-commit uninstall
	pre-commit uninstall --hook-type commit-msg
	@echo "✅ Pre-commit hooks uninstalled"

# Quick development workflow
quick-start: ## Quick start: install deps and start server
	uvx nox -s quick_start

# Show all available nox sessions
list-sessions: ## List all available nox sessions
	uvx nox -l
