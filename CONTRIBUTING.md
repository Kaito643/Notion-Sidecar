# Contributing to Notion Sidecar

# Contributing to Notion Sidecar

First off, thanks for taking the time to contribute! :heart:

Thank you for your interest in contributing to Notion Sidecar.

The following guidelines are intended to facilitate contributions to this project. Please use your best judgment and feel free to propose improvements to this document in a pull request.

## Code of Conduct

This project and everyone participating in it is governed by the [Notion Sidecar Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as much detail as possible.
- **Provide specific examples** to demonstrate the steps.
- **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
- **Explain which behavior you expected to see instead and why.**

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion, including completely new features and minor improvements to existing functionality.

- **Use a clear and descriptive title** for the issue to identify the suggestion.
- **Provide a step-by-step description of the suggested enhancement** in as much detail as possible.
- **Explain why this enhancement would be useful** to most Notion Sidecar users.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Python Styleguide

- All Python code is linted with `ruff` and formatted with `black`.
- We use type hints (`mypy`) wherever possible.

```bash
# Run formatters and linters locally
pip install -r requirements-dev.txt
black .
ruff check .
mypy src
```

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/notion-sidecar.git
   cd notion-sidecar
   ```

2. Set up virtual environment
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks
   ```bash
   pre-commit install
   ```


