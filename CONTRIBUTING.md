# Contributing to Hookswitch

Thank you for considering contributing to Hookswitch! Please follow these guidelines to help us maintain a healthy and collaborative project.

## Development Setup

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/hookswitch.git
   ```
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
4. Install the package in development mode with the development dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Testing

We use pytest to run the test suite. To run all tests:
   ```bash
   pytest
   ```

To run tests with coverage (if you have pytest-cov installed, which is in the dev dependencies? Not currently, but we can add it or just run without):
   ```bash
   pytest --cov=hookswitch
   ```

We use Ruff for linting and code formatting. To check your code:
   ```bash
   ruff check .
   ```

To automatically fix fixable issues:
   ```bash
   ruff check --fix .
   ```

## Submitting Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature-or-bugfix-name
   ```
2. Make your changes, ensuring you follow the existing code style and add tests for any new functionality.
3. Run the test suite and linting to ensure everything passes.
4. Commit your changes with a clear and descriptive commit message.
5. Push your branch to your fork on GitHub.
6. Open a pull request against the main branch of this repository.

Please ensure your pull request description clearly describes the changes and the motivation for them.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on the GitHub repository. Include as much detail as possible, including steps to reproduce for bugs.

Thank you again for your contribution!