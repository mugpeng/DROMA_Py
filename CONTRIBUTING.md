# Contributing to DROMA-Py

We welcome contributions to the DROMA-Py project! This document provides guidelines for contributing.

## Development Setup

### Prerequisites
- Python 3.8 or higher
- Git

### Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/droma01/droma
   cd droma/250521-DROMA_package/250626-DROMA_py
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Code Quality Standards

### Code Formatting
We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run all quality checks:
```bash
# Format code
black src/ examples/
isort src/ examples/

# Check linting
flake8 src/ examples/

# Type checking
mypy src/
```

### Type Hints
All code must include type hints. We use:
- `typing` module for Python < 3.9 compatibility
- `typing_extensions` for advanced typing features

### Documentation
- All functions must have docstrings in Google style
- Include examples in docstrings where appropriate
- Update README.md for major changes

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=droma_py

# Run specific test
pytest tests/test_database.py
```

### Writing Tests
- Write tests for all new functionality
- Use descriptive test names
- Include both positive and negative test cases
- Mock external dependencies (databases, etc.)

## Submitting Changes

### Workflow
1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Add tests for new functionality**
5. **Run quality checks**
6. **Commit your changes**
   ```bash
   git commit -m "Add: description of your change"
   ```
7. **Push to your fork**
8. **Create a Pull Request**

### Commit Messages
Use conventional commit format:
- `Add: new feature`
- `Fix: bug description`
- `Update: existing feature`
- `Remove: deprecated feature`
- `Docs: documentation changes`

### Pull Request Guidelines
- Include a clear description of changes
- Reference any related issues
- Ensure all tests pass
- Update documentation if needed
- Add changelog entry for user-facing changes

## Code Organization

### Module Structure
```
src/droma_py/
├── __init__.py          # Package initialization and exports
├── database.py          # Database connection management
├── data.py             # Data retrieval functions
├── management.py       # Database management functions
├── harmonization.py    # Name harmonization functions
└── exceptions.py       # Custom exception classes
```

### Naming Conventions
- **Functions**: snake_case (`get_feature_from_database`)
- **Classes**: PascalCase (`DROMADatabase`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT`)
- **Private functions**: _leading_underscore (`_clean_name`)

## Issue Reporting

### Bug Reports
Include:
- Python version
- DROMA-Py version
- Operating system
- Minimal code example
- Error messages/traceback
- Expected vs actual behavior

### Feature Requests
Include:
- Clear use case description
- Proposed API design
- Examples of usage
- Integration considerations

## Development Guidelines

### Error Handling
- Use custom exception classes from `exceptions.py`
- Provide detailed error messages
- Include context and suggestions for fixing

### Performance
- Use pandas operations efficiently
- Minimize database queries
- Consider memory usage for large datasets

### Compatibility
- Maintain Python 3.8+ compatibility
- Keep consistent with R DROMA package APIs
- Test on multiple platforms

## Documentation

### API Documentation
- Use Google-style docstrings
- Include parameter and return type descriptions
- Provide usage examples
- Document exceptions that may be raised

### Example Scripts
- Keep examples simple and focused
- Include error handling
- Add comments explaining key concepts
- Test examples regularly

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag
4. Build and upload to PyPI
5. Update documentation

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/droma01/droma/issues)
- **Discussions**: [GitHub Discussions](https://github.com/droma01/droma/discussions)
- **Email**: contact@droma.io

## License

By contributing to DROMA-Py, you agree that your contributions will be licensed under the Mozilla Public License 2.0. 