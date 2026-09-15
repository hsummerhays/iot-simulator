# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Created [.gitignore](.gitignore) covering certificates, keys (`certs/`, `*.pem`, `*.key`, `*.crt`), local environment files (`.env`), raw AWS IoT policies (`policy.json`, `policy_utf8.json`), and Python virtual environments.
- Added [.dockerignore](.dockerignore) to prevent certificates, local `.env` secrets, and build artifacts from ever leaking into Docker images.
- Added [.env.example](.env.example) configuration template.
- Added [policy_template.json](policy_template.json) sanitized IoT policy template with `<AWS_ACCOUNT_ID>` and `<AWS_REGION>` placeholders.
- Added [requirements.txt](requirements.txt) declaring `awsiotsdk>=1.22.0` and `python-dotenv>=1.0.0`.
- Added comprehensive [README.md](README.md) covering overview, project layout, setup steps, diagnostics script, and Docker usage.

### Changed
- Sanitized [simulator.py](simulator.py): removed hardcoded AWS IoT endpoint and certificate hashes, requiring explicit configuration from the environment, and added pre-flight verification of required certificates.
- Updated [Dockerfile](Dockerfile) to copy only application source files (`simulator.py`) and prepare `/app/certs` as a runtime volume mount point instead of `COPY . .`.
- Updated [README.md](README.md) Docker instructions to standardize on runtime read-only volume mounting (`/app/certs:ro`).
- Parameterized [check_iot_config.ps1](check_iot_config.ps1) using environment variables loaded via `dotenv` with safe fallbacks.
- Reorganized certificate layout: moved all client certificates, private keys, and Amazon Root CAs into the dedicated `certs/` subfolder.
- Replaced monolithic hardcoded paths with dynamic `CERTS_DIR` resolution.
