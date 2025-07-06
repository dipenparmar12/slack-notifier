## Publishing to PyPI

This project uses [twine](https://twine.readthedocs.io/en/stable/) for securely uploading Python packages to PyPI. For security, your PyPI API token should be stored in a `.env` file as `PYPI_TOKEN`.

### 1. Prerequisites

- Ensure you have an account on [PyPI](https://pypi.org/).
- Install the required tools:
  ```bash
  pip install build twine python-dotenv
  ```
- Your project should have a valid `pyproject.toml` and `setup.cfg`/`setup.py`.

### 2. Set Up Your `.env` File

Create a `.env` file in the project root (do **not** commit this file):

```
PYPI_TOKEN=pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Build the Distribution

Clean previous builds (optional but recommended):
```bash
rm -rf dist/
```

Build the source and wheel distributions:
```bash
python -m build
```

This will create files in the `dist/` directory, e.g.:
- `py_slack_notifier-0.1.0-py3-none-any.whl`
- `py-slack-notifier-0.1.0.tar.gz`

### 4. Publish to PyPI

You can use the following script to publish using the token from `.env`:

```bash
# Load the PYPI_TOKEN from .env and publish
export $(grep PYPI_TOKEN .env | xargs) 
twine upload --non-interactive -u __token__ -p "$PYPI_TOKEN" dist/*
```

#### One-liner (safe for zsh/bash):
```bash
export $(grep PYPI_TOKEN .env | xargs) && twine upload --non-interactive -u __token__ -p "$PYPI_TOKEN" dist/*
```

- `-u __token__` tells twine to use token-based auth.
- `-p "$PYPI_TOKEN"` uses your token from the environment.

### 5. Test Your Upload (Optional)

To test your upload process without publishing to the real PyPI, use [TestPyPI](https://test.pypi.org/):

1. Get a token from https://test.pypi.org/manage/account/
2. Add it to your `.env` as `PYPI_TOKEN`.
3. Upload to TestPyPI:
   ```bash
   export $(grep PYPI_TOKEN .env | xargs) && twine upload --repository testpypi -u __token__ -p "$PYPI_TOKEN" dist/*
   ```
4. Install from TestPyPI:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ py-slack-notifier
   ```

### 6. Troubleshooting

- Ensure your `.env` is not committed to version control.
- If you see authentication errors, double-check your token and that you are using `__token__` as the username.
- For more info, see the [Twine docs](https://twine.readthedocs.io/en/stable/) and [PyPI token guide](https://pypi.org/help/#apitoken).

---

**Security tip:** Never share your PyPI token or commit it to your repository.
