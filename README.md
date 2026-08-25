# ZK-STARK FRI Prover Agent

A pure-Python implementation of the FRI (Fast Reed-Solomon Interactive Oracle Proof) commitment scheme used in ZK-STARKs. Uses only the Python standard library.

## Features

- **FRI Commitment Scheme**: Polynomial evaluation on multiplicative subgroup domains
- **Folding**: `p(x) → p_even(x²) + α × p_odd(x²)`, halving degree each round
- **Merkle Tree Commitment**: SHA-256 based Merkle trees for evaluation commitments
- **Query Phase**: Random point selection with Merkle proof verification
- **Soundness Analysis**: Compute soundness error based on queries, field size, and rounds
- **Finite Field Arithmetic**: Operations over GF(p) with primitive root computation

## CLI Usage

```bash
# Full FRI protocol demo
python cli.py demo --coefficients '[1,2,3,4]' --domain-size 16 --prime 65537 --num-queries 3

# Evaluate polynomial
python cli.py eval --coefficients '[1,2,3]' --x 5 --prime 65537

# Generate evaluation domain
python cli.py domain --size 16 --prime 65537

# Merkle tree operations
python cli.py merkle --values '[1,2,3,4,5,6,7,8]' --index 3

# FRI folding step
python cli.py fold --evaluations '[1,2,3,4]' --domain '[1,10,100,1000]' --alpha 5 --prime 65537

# FRI commitment phase
python cli.py commit --coefficients '[1,2,3,4]' --domain-size 16 --prime 65537

# Soundness analysis
python cli.py soundness --degree 8 --field-size 65537 --num-queries 5 --num-rounds 3
```

## Python API

```python
from zk_stark_fri.engine import run_fri_protocol, soundness_analysis

# Run complete FRI protocol
result = run_fri_protocol(
    coefficients=[1, 2, 3, 4],
    p=65537,
    domain_size=16,
    num_queries=3
)
print(result["is_valid"])
print(result["soundness"]["soundness_bits"])
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## License

MIT License.
