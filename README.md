# ZK-STARK FRI Prover Agent

A Python educational implementation of finite-field polynomial evaluation, Merkle commitments, binary FRI folding and complete-trace consistency checking. Also includes an independent parameter-audit agent and an optional FastAPI service.

> **Important:** This repository is not a secure or production-ready STARK implementation, zero-knowledge proof system, succinct verifier, or implementation validated against NIST FIPS standards. The verifier requires the complete polynomial evaluation trace and does not implement a cryptographically bound Fiat–Shamir transcript. Reported soundness estimates are heuristic and must not be interpreted as security guarantees.

## Features

- Pure Python (standard-library) finite-field arithmetic, subgroup generation, polynomial evaluation and FRI folding.
- Merkle tree commitments and opening checks, complete FRI trace checks and configurable degree claims.
- CLI examples for evaluation, domain generation, Merkle trees, folding and FRI demonstration.
- Browser FRI demonstration using Pyodide; all entered coefficients are processed in-browser after downloading the Python runtime. No backend is necessary for this demonstration.
- Optional local FastAPI parameter-audit API and operations UI. The audit thresholds are demonstrations and do not establish cryptographic validity.
- HMAC-SHA256 chained audit records. Audit records are process-local and not durable or independently anchored.

## Run in the browser

The static application is built from `web/index.html` plus `zk_stark_fri/engine.py` by the Pages workflow. GitHub Pages must be enabled using GitHub Actions as its source before the app can be published; do not treat a workflow file alone as confirmation of a working deployment. The browser needs internet access to download Pyodide from the pinned CDN URL. Sensitive information should not be entered.

## Local installation

Requires Python 3.9 or later; GitHub Actions tests 3.10, 3.11 and 3.12.

```bash
git clone https://github.com/abusuraihsakhri/zk-stark-fri-prover-agent.git
cd zk-stark-fri-prover-agent
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[server,test]"
python -m pytest -v
```

### FRI CLI

```bash
python cli.py eval --coefficients "[1,2,3,4]" --x 2 --prime 65537
python cli.py domain --size 16 --prime 65537
python cli.py demo --coefficients "[1,2,3,4]" --domain-size 16 --num-queries 3
python cli.py soundness --degree 8 --field-size 65537 --num-queries 5 --num-rounds 4
```

### Optional backend

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
uvicorn agents.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. The FRI demo executes locally in-browser; the parameter-audit form posts to `/api/audit`. Other endpoints include `/health`, `/metrics` (JSON), and `/api/chat`. The audit-log endpoint `/api/audit/logs` is disabled unless `AUDIT_ADMIN_TOKEN` is set, and requires the `X-Audit-Token` header.

### Docker

```bash
docker build -t zk-stark-fri-prover-agent .
docker run --rm -p 127.0.0.1:8000:8000 -e AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" zk-stark-fri-prover-agent
```

With Docker Compose, set `AUDIT_SECRET_KEY` before running `docker compose up --build`. By default Compose binds only to localhost. Do not publicly expose the unauthenticated parameter-audit API without implementing suitable authentication, request size limits and rate limiting.

## Privacy and security limitations

- The browser's FRI demonstration does not upload entered coefficients to the application server, but obtains runtime assets from an external CDN.
- The optional API sends entered fields to your configured server; the regex-based PHI guard is **not** complete de-identification and does not establish HIPAA compliance.
- The audit HMAC chain detects record modification while the signing key and chain head remain trusted, but persistence, key management, and external anchoring are not implemented.
- FRI randomness is not bound to a secure public transcript; do not use the implementation for real cryptographic attestations.
- Default audit inputs and agent responses are demonstrative; consult code for the actual thresholds.

## Technology

Python 3.9+, setuptools, optional FastAPI/Pydantic/Uvicorn, Pyodide for browser execution, vanilla HTML/CSS/JavaScript, pytest, GitHub Actions. Works in current browsers supporting WebAssembly and the Pyodide runtime (subject to CDN access). The browser demonstration may consume significant time or memory for larger inputs.

## License

MIT — see [LICENSE](LICENSE).
