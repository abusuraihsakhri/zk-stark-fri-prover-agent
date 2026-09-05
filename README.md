# ZK STARK FRI Prover Agent

> **Domain:** Post-Quantum Cryptography & Zero-Knowledge Architecture
> **Reference Guidelines & Standards:** `NIST FIPS 203/204/205, NIST SP 800-90B & ISO/IEC Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**ZK STARK FRI Prover Agent** is an advanced analytical and computational platform implementing Transparent ZK-STARK Fast Reed-Solomon Interactive Oracle Proof (FRI) verification. It provides:

- A **pure-Python FRI engine** (no external crypto dependencies) implementing polynomial evaluation, Merkle commitments, FRI folding, and soundness analysis.
- A **multi-agent evaluation system** with PHI outbound guarding and HMAC-SHA256 tamper-evident audit trails.
- A **FastAPI REST server** with Prometheus-compatible metrics.
- A **batch simulator** for high-throughput stress testing.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### FRI Engine (`zk_stark_fri/engine.py`)
- **Finite field arithmetic** — prime-field operations in GF(p).
- **Polynomial operations** — evaluation (Horner), degree, add, scale.
- **Evaluation domains** — multiplicative subgroups via primitive nth roots of unity.
- **Merkle trees** — commit, open, verify over polynomial evaluations.
- **FRI folding** — reduce-degree folding with random challenges.
- **FRI protocol** — full commit → query → verify pipeline.
- **Soundness analysis** — per-round error and total soundness bits.
- **FrontierDomainEngine** — parameter evaluation for agent auditing.

### Agent System (`agents/`)
- **Workers** — `InvariantQCWorker`, `SafetyEscalationWorker`, `ProtocolConformanceWorker`.
- **Supervisor** — `SystemSupervisor` orchestrates multi-worker consensus.
- **PHI Guard** — regex + AST inspection blocking SSNs, MRNs, emails, phone numbers.
- **Audit Trail** — chained HMAC-SHA256 tamper-evident logging.
- **Metrics Collector** — Prometheus-format operational telemetry.
- **LLM Factory** — pluggable Ollama / Claude / OpenAI / mock adapters.

### Enrichment Suite (`enrichment.py`)
- Performance benchmarking, side-channel analysis, interoperability testing, ZK proof aggregation, formal security documentation, NIST compliance, FRI profiling, AIR constraint analysis.

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/zk-stark-fri-prover-agent.git
cd zk-stark-fri-prover-agent

# (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install core dependencies (stdlib-only engine needs nothing)
pip install fastapi uvicorn pydantic pytest
```

---

## 🧪 CLI Usage

### FRI Engine CLI (`cli.py`)

```bash
# Evaluate a polynomial f(x) = 1 + 2x + 3x² + 4x³ at x = 2 (mod 65537)
python cli.py eval --coefficients "[1, 2, 3, 4]" --x 2 --prime 65537

# Generate an evaluation domain of size 16
python cli.py domain --size 16 --prime 65537

# Run a full FRI protocol demo
python cli.py demo --coefficients "[1, 2, 3, 4]" --domain-size 16 --num-queries 3

# Analyze soundness for given parameters
python cli.py soundness --degree 8 --field-size 65537 --num-queries 5 --num-rounds 4
```

### Agent System CLI (`zk_stark_fri/cli.py`)

```bash
# Run a single audit evaluation
python -m zk_stark_fri.cli audit --task-id "TASK-001" --target "TARGET-01" --primary 28.4 --secondary 14.2 --critical --status "DISCORDANT"

# Batch process a CSV file
python -m zk_stark_fri.cli batch -i sample.csv -o results.csv

# Interactive chat with the supervisor
python -m zk_stark_fri.cli chat "What is the system status?"

# Verify audit trail integrity
python -m zk_stark_fri.cli verify-audit

# Launch FastAPI server
python -m zk_stark_fri.cli serve --host 127.0.0.1 --port 8000
```

---

## 🧪 Testing & Verification

```bash
# Run the full test suite (38 tests)
pytest -v

# Run a specific test module
pytest tests/test_zk_stark_fri.py -v

# Execute high-throughput batch simulation
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t zk-stark-fri-prover-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$(openssl rand -hex 32) zk-stark-fri-prover-agent
```

Or with Docker Compose:

```bash
docker compose up --build
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOB, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Secure defaults:** `AUDIT_SECRET_KEY` must be set in production; a random ephemeral key is generated at runtime otherwise (with a warning).
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and `/metrics`.

---

## 📁 Project Structure

```
zk-stark-fri-prover-agent/
├── agents/                  # Enterprise agent system (PHI guard, audit, workers, supervisor)
│   ├── api.py               # FastAPI REST endpoints
│   ├── base.py              # PHIGuard, AuditTrail, SecurityException
│   ├── models.py            # Pydantic schemas (SystemTaskPayload, ConsensusDossier)
│   ├── workers.py           # Specialized domain workers
│   ├── supervisor.py        # Master orchestrator
│   ├── metrics.py           # Prometheus-format collector
│   ├── llm_factory.py       # Pluggable LLM provider
│   └── streamer.py          # WebSocket telemetry broadcaster
├── zk_stark_fri/            # Core FRI engine package
│   ├── engine.py            # FRI protocol + FrontierDomainEngine
│   ├── agents.py            # ZK-STARK coordinator sub-agents
│   ├── models.py            # FrontierPayload, AgentTelemetryAlert
│   ├── cli.py               # Agent CLI (audit, chat, batch, serve)
│   └── server.py            # FastAPI app factory
├── tests/                   # Pytest test suite
│   ├── test_zk_stark_fri.py # FRI engine tests (field, poly, merkle, FRI)
│   ├── test_enrichment.py   # Enrichment suite tests
│   └── test_zk_stark_fri_prover_agent.py  # Agent system tests
├── web/index.html           # Operations console UI
├── cli.py                   # FRI engine CLI entry point
├── simulator.py             # High-throughput batch simulator
├── enrichment.py            # Enrichment feature implementations
├── sample.csv               # Sample batch input
├── sample_payload.json      # Sample API payload
├── benchmark_dataset.json   # Golden benchmark test vectors
├── Dockerfile               # Container build
├── docker-compose.yml       # Compose orchestration
└── pyproject.toml           # Project metadata & build config
```

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
