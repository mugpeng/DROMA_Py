# DROMA-Py Publishing Guide

This guide provides step-by-step instructions for publishing the DROMA-Py package to PyPI.

## Pre-Publication Checklist

### ✅ Package Structure Verification
```
250626-DROMA_py/
├── src/droma_py/           # Source code
│   ├── __init__.py
│   ├── database.py
│   ├── data.py
│   ├── exceptions.py
│   ├── harmonization.py
│   └── management.py
├── examples/               # Example scripts
│   ├── basic_usage.py
│   ├── batch_processing.py
│   ├── data_analysis.py
│   └── name_harmonization.py
├── pyproject.toml         # Package configuration
├── README.md              # Package documentation
├── LICENSE                # MPL 2.0 license
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # Contributor guide
├── MANIFEST.in            # Include additional files
└── .gitignore             # Git ignore rules
```

### ✅ Required Files Status
- [x] `pyproject.toml` - ✅ Complete with all metadata
- [x] `README.md` - ✅ Comprehensive documentation  
- [x] `LICENSE` - ✅ Mozilla Public License 2.0
- [x] `CHANGELOG.md` - ✅ Version 0.1.0 documented
- [x] `MANIFEST.in` - ✅ Includes examples and docs
- [x] `CONTRIBUTING.md` - ✅ Development guidelines
- [x] `.gitignore` - ✅ Comprehensive exclusions

### ✅ Package Configuration Review

#### Version Information
- **Package Name**: `droma-py`
- **Version**: `0.1.0`
- **Python Support**: `>=3.8`
- **License**: Mozilla Public License 2.0

#### Dependencies
```toml
dependencies = [
    "pandas>=1.3.0",
    "numpy>=1.21.0", 
    "rapidfuzz>=3.0.0",
    "typing-extensions>=4.0.0;python_version<'3.10'",
]
```

#### PyPI Classifiers
- Development Status :: 4 - Beta
- Intended Audience :: Science/Research
- License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)
- Programming Language :: Python :: 3.8+
- Topic :: Scientific/Engineering :: Bio-Informatics

## Publishing Process

### Step 1: Environment Setup

1. **Install build tools**
   ```bash
   pip install build twine
   ```

2. **Verify environment**
   ```bash
   python --version  # Should be 3.8+
   pip --version
   ```

### Step 2: Pre-Publication Testing

1. **Install package in development mode**
   ```bash
   pip install -e .
   ```

2. **Test import**
   ```bash
   python -c "import droma_py; print(droma_py.__version__)"
   ```

3. **Run examples** (if database available)
   ```bash
   # Update database path in examples first
   python examples/basic_usage.py
   ```

4. **Code quality checks**
   ```bash
   # Format code
   black src/ examples/
   isort src/ examples/
   
   # Linting
   flake8 src/ examples/
   
   # Type checking
   mypy src/
   ```

### Step 3: Build Package

1. **Clean previous builds**
   ```bash
   rm -rf build/ dist/ *.egg-info/
   ```

2. **Build distributions**
   ```bash
   python -m build
   ```

   This creates:
   - `dist/droma_py-0.1.0.tar.gz` (source distribution)
   - `dist/droma_py-0.1.0-py3-none-any.whl` (wheel distribution)

3. **Verify build contents**
   ```bash
   tar -tzf dist/droma-py-0.1.0.tar.gz | head -20
   unzip -l dist/droma_py-0.1.0-py3-none-any.whl
   ```

### Step 4: Test Distribution

1. **Check package with twine**
   ```bash
   twine check dist/*
   ```

2. **Test installation from wheel**
   ```bash
   # Create fresh environment
   python -m venv test_env
   source test_env/bin/activate  # On Windows: test_env\Scripts\activate
   
   # Install from wheel
   pip install dist/droma_py-0.1.0-py3-none-any.whl
   
   # Test import
   python -c "import droma_py; print('Success!')"
   
   # Clean up
   deactivate
   rm -rf test_env/
   ```

### Step 5: PyPI Account Setup

1. **Create PyPI account**
   - Go to https://pypi.org/account/register/
   - Verify email address

2. **Create API token**
   - Go to https://pypi.org/manage/account/
   - Create API token for entire account or specific project
   - Save token securely

3. **Configure twine**
   ```bash
   # Option 1: Use keyring
   pip install keyring
   keyring set https://upload.pypi.org/legacy/ __token__
   # Enter your API token when prompted
   
   # Option 2: Use .pypirc file
   cat > ~/.pypirc << EOF
   [distutils]
   index-servers = pypi
   
   [pypi]
   username = __token__
   password = pypi-YOUR_API_TOKEN_HERE
   EOF
   chmod 600 ~/.pypirc
   ```

### Step 6: Test Upload (Optional but Recommended)

1. **Upload to TestPyPI**
   ```bash
   # Create TestPyPI account at https://test.pypi.org/
   twine upload --repository testpypi dist/*
   ```

2. **Test installation from TestPyPI**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ droma-py
   ```

### Step 7: Production Upload

1. **Upload to PyPI**
   ```bash
   twine upload dist/*
   ```

2. **Verify upload**
   - Check package page: https://pypi.org/project/droma-py/
   - Test installation: `pip install droma-py`

### Step 8: Post-Publication

1. **Create Git tag**
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **Create GitHub release**
   - Go to repository releases page
   - Create new release with tag v0.1.0
   - Include changelog content

3. **Update documentation**
   - Update installation instructions
   - Announce release

## Version Management

### Semantic Versioning
- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

### Release Process
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release commit
4. Build and upload to PyPI
5. Create Git tag and GitHub release

### Example Version Updates
```toml
# Bug fix release
version = "0.1.1"

# New feature release  
version = "0.2.0"

# Breaking change release
version = "1.0.0"
```

## Troubleshooting

### Common Issues

1. **Build failures**
   ```bash
   # Check pyproject.toml syntax
   python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
   
   # Verify package structure
   python -m build --sdist --outdir dist/
   ```

2. **Upload failures**
   ```bash
   # Check package metadata
   twine check dist/*
   
   # Verify authentication
   twine upload --repository testpypi dist/* --verbose
   ```

3. **Installation issues**
   ```bash
   # Clear pip cache
   pip cache purge
   
   # Install with verbose output
   pip install -v droma-py
   ```

### Package Validation Commands

```bash
# Validate package structure
python setup.py check

# Check long description rendering
twine check dist/*

# Verify wheel contents
wheel show droma-py

# Test in clean environment
docker run --rm -it python:3.8 pip install droma-py
```

## Security Considerations

1. **API Token Security**
   - Never commit tokens to version control
   - Use environment variables or keyring
   - Rotate tokens regularly

2. **Package Integrity**
   - Always build from clean repository
   - Verify checksums before upload
   - Use trusted build environments

## Maintenance

### Regular Tasks
- Monitor download statistics
- Respond to user issues
- Update dependencies
- Security updates

### PyPI Project Management
- Add collaborators if needed
- Configure automatic yanking rules
- Monitor for typosquatting

## Support

- **PyPI Help**: https://pypi.org/help/
- **Packaging Guide**: https://packaging.python.org/
- **Twine Docs**: https://twine.readthedocs.io/
- **DROMA Support**: contact@droma.io 