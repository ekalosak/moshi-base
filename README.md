# moshi-base

This Python package contains the lightweight base requirements for ChatMoshi.

1. logging (loguru)
2. types (dataclasses)

# Install
You'll need the keyring packages installed and valid gcloud auth, but then:
`pip install --extra-index-url https://us-central1-python.pkg.dev/moshi-3/pypi/simple/ moshi-base`
See `make auth-install`.

# Develop
1. Activate the virtual environment: `source venv/bin/activate.fish`
2. Install build and auth dependencies: `make setup`

# Test
`make test`

# Publish
After setting up the development environment: `make publish`
