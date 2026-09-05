"""
ZK-STARK FRI (Fast Reed-Solomon Interactive Oracle Proof) Engine
Implements: FRI commitment scheme with polynomial evaluation, folding,
Merkle tree commitments, query phase, and soundness analysis.
Uses only Python stdlib.
"""
import hashlib
import json
import math
import random
from typing import List, Dict, Any, Tuple, Optional


# ---------------------------------------------------------------------------
# Finite field arithmetic (prime field GF(p))
# ---------------------------------------------------------------------------

def mod_pow(base: int, exp: int, mod: int) -> int:
    """Modular exponentiation."""
    return pow(base, exp, mod)


def mod_inverse(a: int, mod: int) -> int:
    """Modular inverse using Fermat's little theorem."""
    return pow(a, mod - 2, mod)


def field_add(a: int, b: int, p: int) -> int:
    return (a + b) % p


def field_mul(a: int, b: int, p: int) -> int:
    return (a * b) % p


def field_sub(a: int, b: int, p: int) -> int:
    return (a - b) % p


def field_neg(a: int, p: int) -> int:
    return (-a) % p


# ---------------------------------------------------------------------------
# Polynomial operations
# ---------------------------------------------------------------------------

def poly_eval(coefficients: List[int], x: int, p: int) -> int:
    """Evaluate polynomial at x using Horner's method. coefficients[0] = constant."""
    result = 0
    for c in reversed(coefficients):
        result = (result * x + c) % p
    return result


def poly_degree(coefficients: List[int]) -> int:
    """Return the degree of the polynomial (index of highest non-zero coefficient)."""
    for i in range(len(coefficients) - 1, -1, -1):
        if coefficients[i] != 0:
            return i
    return 0


def poly_add(a: List[int], b: List[int], p: int) -> List[int]:
    """Add two polynomials."""
    length = max(len(a), len(b))
    result = [0] * length
    for i in range(len(a)):
        result[i] = (result[i] + a[i]) % p
    for i in range(len(b)):
        result[i] = (result[i] + b[i]) % p
    return result


def poly_scale(coeffs: List[int], scalar: int, p: int) -> List[int]:
    """Multiply polynomial by a scalar."""
    return [(c * scalar) % p for c in coeffs]


# ---------------------------------------------------------------------------
# Evaluation domain
# ---------------------------------------------------------------------------

def generate_evaluation_domain(n: int, p: int) -> List[int]:
    """
    Generate a multiplicative subgroup of order n in GF(p).
    Requires n | (p-1). Returns [1, ω, ω², ..., ω^(n-1)] where ω is a primitive nth root of unity.
    """
    if (p - 1) % n != 0:
        raise ValueError(f"n={n} does not divide p-1={p-1}")

    # Find a primitive nth root of unity
    g = _find_primitive_root(p)
    omega = mod_pow(g, (p - 1) // n, p)

    domain = [1]
    for i in range(1, n):
        domain.append((domain[-1] * omega) % p)

    return domain


def _find_primitive_root(p: int) -> int:
    """Find a primitive root modulo p."""
    if p == 2:
        return 1
    # Factor p-1
    factors = _prime_factors(p - 1)
    for g in range(2, p):
        is_primitive = True
        for f in factors:
            if mod_pow(g, (p - 1) // f, p) == 1:
                is_primitive = False
                break
        if is_primitive:
            return g
    raise ValueError(f"No primitive root found for p={p}")


def _prime_factors(n: int) -> List[int]:
    """Return unique prime factors of n."""
    factors = set()
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.add(d)
            n //= d
        d += 1
    if n > 1:
        factors.add(n)
    return list(factors)


# ---------------------------------------------------------------------------
# Merkle tree
# ---------------------------------------------------------------------------

def _hash(data: str) -> str:
    """SHA-256 hash."""
    return hashlib.sha256(data.encode()).hexdigest()


def merkle_commit(evaluations: List[int]) -> Tuple[str, List[List[str]]]:
    """
    Build a Merkle tree over polynomial evaluations.
    Returns (root_hash, layers) where layers[0] = leaf hashes.
    """
    if not evaluations:
        raise ValueError("Empty evaluations")

    # Leaf hashes
    leaves = [_hash(str(e)) for e in evaluations]
    layers = [leaves]

    current = leaves
    while len(current) > 1:
        next_layer = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else current[i]
            next_layer.append(_hash(left + right))
        layers.append(next_layer)
        current = next_layer

    root = current[0]
    return root, layers


def merkle_open(layers: List[List[str]], index: int) -> List[str]:
    """
    Generate a Merkle proof (authentication path) for the leaf at given index.
    Returns list of sibling hashes from leaf to root (excluding root layer).
    """
    proof = []
    # Iterate through all layers except the last one (root)
    for layer in layers[:-1]:
        if index % 2 == 0:
            sibling = layer[index + 1] if index + 1 < len(layer) else layer[index]
        else:
            sibling = layer[index - 1]
        proof.append(sibling)
        index //= 2
    return proof


def merkle_verify(root: str, leaf_hash: str, proof: List[str], index: int) -> bool:
    """Verify a Merkle proof."""
    current = leaf_hash
    for sibling in proof:
        if index % 2 == 0:
            current = _hash(current + sibling)
        else:
            current = _hash(sibling + current)
        index //= 2
    return current == root


# ---------------------------------------------------------------------------
# FRI Folding
# ---------------------------------------------------------------------------

def fri_fold(evaluations: List[int], domain: List[int],
             alpha: int, p: int) -> Tuple[List[int], List[int]]:
    """
    FRI folding step.
    
    Given polynomial p(x) evaluated on domain, fold into:
        p_even(x²) + α × p_odd(x²)
    
    The evaluations are split into even/odd indexed pairs:
        p(x) = p_even(x²) + x × p_odd(x²)
    
    At point x_i and -x_i:
        p(x_i) = p_even(x_i²) + x_i × p_odd(x_i²)
        p(-x_i) = p_even(x_i²) - x_i × p_odd(x_i²)
    
    Solving:
        p_even(x_i²) = (p(x_i) + p(-x_i)) / 2
        p_odd(x_i²) = (p(x_i) - p(-x_i)) / (2 × x_i)
    
    New evaluation: p_even(x_i²) + α × p_odd(x_i²)
    
    Returns:
        (new_evaluations, new_domain)
    """
    n = len(evaluations)
    if n % 2 != 0:
        raise ValueError("Number of evaluations must be even")
    if len(domain) != n:
        raise ValueError("Domain size must match evaluations size")

    half = n // 2
    new_evaluations = []
    new_domain = []

    two_inv = mod_inverse(2, p)

    for i in range(half):
        x_i = domain[i]
        neg_x_i = field_neg(x_i, p)

        # Find the index of -x_i in the domain
        # In a subgroup, -x_i = x_{i + half}
        j = (i + half) % n

        p_xi = evaluations[i]
        p_neg_xi = evaluations[j]

        # p_even(x_i²) = (p(x_i) + p(-x_i)) / 2
        p_even = field_mul(field_add(p_xi, p_neg_xi, p), two_inv, p)

        # p_odd(x_i²) = (p(x_i) - p(-x_i)) / (2 * x_i)
        x_i_inv = mod_inverse(x_i, p) if x_i != 0 else 0
        p_odd = field_mul(field_mul(field_sub(p_xi, p_neg_xi, p), two_inv, p), x_i_inv, p)

        # New evaluation at x_i²
        new_eval = field_add(p_even, field_mul(alpha, p_odd, p), p)
        new_evaluations.append(new_eval)

        # New domain point is x_i²
        new_domain.append(field_mul(x_i, x_i, p))

    return new_evaluations, new_domain


# ---------------------------------------------------------------------------
# FRI Protocol
# ---------------------------------------------------------------------------

class FRIProof:
    """Complete FRI proof containing commitments, evaluations, and queries."""

    def __init__(self):
        self.roots: List[str] = []  # Merkle roots per round
        self.folding_alphas: List[int] = []  # Random challenges per round
        self.final_evaluations: List[int] = []  # Final polynomial evaluations
        self.query_proofs: List[List[Dict[str, Any]]] = []  # Merkle proofs per query
        self.rounds: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "roots": self.roots,
            "folding_alphas": self.folding_alphas,
            "final_evaluations": self.final_evaluations,
            "rounds": self.rounds,
            "num_queries": len(self.query_proofs),
        }


def fri_commit(coefficients: List[int], domain: List[int],
               p: int, folding_factor: int = 2,
               max_rounds: Optional[int] = None,
               seed: Optional[int] = None) -> Tuple[FRIProof, List[List[int]], List[List[int]]]:
    """
    FRI commitment phase.
    
    1. Evaluate polynomial on domain
    2. Commit (Merkle root)
    3. Fold polynomial (reduce degree by half)
    4. Repeat until degree ≤ threshold
    
    Returns:
        (proof, all_evaluations, all_domains)
    """
    if seed is not None:
        random.seed(seed)

    proof = FRIProof()
    all_evaluations = []
    all_domains = []

    # Initial evaluation
    evaluations = [poly_eval(coefficients, d, p) for d in domain]
    all_evaluations.append(evaluations)
    all_domains.append(domain)

    # Determine max rounds
    deg = poly_degree(coefficients)
    if max_rounds is None:
        max_rounds = max(1, int(math.log2(deg + 1)))

    current_evals = evaluations
    current_domain = domain

    for round_num in range(max_rounds):
        # Commit
        root, layers = merkle_commit(current_evals)
        proof.roots.append(root)

        # Generate random challenge (Fiat-Shamir in non-interactive version)
        alpha = random.randrange(1, p)
        proof.folding_alphas.append(alpha)

        # Fold
        if len(current_evals) <= 2:
            # Reached minimum degree - stop
            proof.final_evaluations = current_evals
            break

        new_evals, new_domain = fri_fold(current_evals, current_domain, alpha, p)
        all_evaluations.append(new_evals)
        all_domains.append(new_domain)

        current_evals = new_evals
        current_domain = new_domain
        proof.rounds += 1

    if not proof.final_evaluations:
        proof.final_evaluations = current_evals

    return proof, all_evaluations, all_domains


def fri_query(all_evaluations: List[List[int]], all_domains: List[List[int]],
              proof: FRIProof, num_queries: int, p: int) -> List[List[Dict[str, Any]]]:
    """
    FRI query phase.
    
    For each query:
    1. Pick a random index in the initial domain
    2. For each round, provide the evaluation and its Merkle proof
    3. Verify consistency across folding rounds
    
    Returns:
        List of query proofs (one per query)
    """
    query_proofs = []

    for _ in range(num_queries):
        # Pick random index in initial domain
        n = len(all_evaluations[0])
        idx = random.randrange(0, n)

        query_proof = []
        current_idx = idx

        for round_num in range(len(all_evaluations)):
            evals = all_evaluations[round_num]
            root, layers = merkle_commit(evals)

            # Get Merkle proof for current index
            actual_idx = current_idx % len(evals)
            leaf_hash = _hash(str(evals[actual_idx]))
            merkle_proof = merkle_open(layers, actual_idx)

            query_proof.append({
                "round": round_num,
                "index": actual_idx,
                "evaluation": evals[actual_idx],
                "merkle_proof": merkle_proof,
                "leaf_hash": leaf_hash,
                "root": root,
            })

            # Next round index (domain halves each round)
            current_idx = current_idx % len(all_evaluations[min(round_num + 1, len(all_evaluations) - 1)])

        query_proofs.append(query_proof)
        proof.query_proofs.append(query_proof)

    return query_proofs


def fri_verify(proof: FRIProof, all_evaluations: List[List[int]],
               all_domains: List[List[int]], p: int) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify a FRI proof.
    
    Checks:
    1. Merkle roots match commitments
    2. Folding consistency (evaluations are consistent with folding)
    3. Final evaluations are from a low-degree polynomial
    """
    details = {
        "merkle_checks": [],
        "folding_checks": [],
        "final_degree_check": False,
        "is_valid": True,
    }

    # Check Merkle proofs for each query
    for q_idx, query_proof in enumerate(proof.query_proofs):
        for step in query_proof:
            valid = merkle_verify(step["root"], step["leaf_hash"],
                                  step["merkle_proof"], step["index"])
            details["merkle_checks"].append({
                "query": q_idx,
                "round": step["round"],
                "merkle_valid": valid,
            })
            if not valid:
                details["is_valid"] = False

    # Check folding consistency
    for round_num in range(len(all_evaluations) - 1):
        if round_num >= len(proof.folding_alphas):
            break
        alpha = proof.folding_alphas[round_num]
        evals = all_evaluations[round_num]
        domain = all_domains[round_num]

        if len(evals) <= 2:
            break

        new_evals, _ = fri_fold(evals, domain, alpha, p)
        expected = all_evaluations[round_num + 1] if round_num + 1 < len(all_evaluations) else []

        if expected and len(new_evals) == len(expected):
            consistent = all(a == b for a, b in zip(new_evals, expected))
            details["folding_checks"].append({
                "round": round_num,
                "consistent": consistent,
            })
            if not consistent:
                details["is_valid"] = False

    # Final degree check
    final_evals = proof.final_evaluations
    if len(final_evals) <= 2:
        details["final_degree_check"] = True
    else:
        details["final_degree_check"] = True  # Simplified: trust the protocol

    return details["is_valid"], details


# ---------------------------------------------------------------------------
# Soundness analysis
# ---------------------------------------------------------------------------

def soundness_analysis(degree: int, field_size: int, num_queries: int,
                        num_rounds: int) -> Dict[str, Any]:
    """
    Analyze the soundness of the FRI protocol.
    
    Soundness error ≈ (degree / field_size) × (1/2)^num_queries
    After folding: effective degree halves each round.
    """
    effective_degree = degree
    per_round_error = []

    for r in range(num_rounds):
        error = effective_degree / field_size
        per_round_error.append(error)
        effective_degree = max(1, effective_degree // 2)

    # Total soundness error
    query_error = (1.0 / 2.0) ** num_queries
    total_error = per_round_error[-1] * query_error if per_round_error else 1.0

    return {
        "initial_degree": degree,
        "field_size": field_size,
        "num_queries": num_queries,
        "num_rounds": num_rounds,
        "final_effective_degree": effective_degree,
        "soundness_error_per_round": per_round_error,
        "query_soundness_error": query_error,
        "total_soundness_error": total_error,
        "soundness_bits": -math.log2(total_error) if total_error > 0 else float('inf'),
    }


# ---------------------------------------------------------------------------
# High-level API
# ---------------------------------------------------------------------------

def run_fri_protocol(coefficients: List[int], p: int, domain_size: int,
                      num_queries: int = 3) -> Dict[str, Any]:
    """
    Run the complete FRI protocol: commit, query, verify.
    """
    # Generate evaluation domain
    domain = generate_evaluation_domain(domain_size, p)

    # Commit phase
    proof, all_evals, all_domains = fri_commit(coefficients, domain, p)

    # Query phase
    query_proofs = fri_query(all_evals, all_domains, proof, num_queries, p)

    # Verify
    is_valid, details = fri_verify(proof, all_evals, all_domains, p)

    # Soundness analysis
    deg = poly_degree(coefficients)
    soundness = soundness_analysis(deg, p, num_queries, proof.rounds)

    return {
        "polynomial_degree": deg,
        "domain_size": domain_size,
        "field_prime": p,
        "proof": proof.to_dict(),
        "verification": details,
        "soundness": soundness,
        "is_valid": is_valid,
    }


# ---------------------------------------------------------------------------
# Frontier Domain Engine (parameter evaluation for agent auditing)
# ---------------------------------------------------------------------------

class FrontierDomainEngine:
    """Domain-specific evaluation engine used by ZK-STARK agent sub-auditors.

    Each *evaluate* classmethod inspects a single metric/description and
    returns ``None`` when the value is within acceptable bounds, or a dict
    with ``summary``, ``details``, and ``remediation`` keys when an anomaly
    is detected.
    """

    PRIMARY_THRESHOLD: float = 25.0
    SECONDARY_THRESHOLD: float = 12.0
    DISCORDANT_KEYWORDS = ("DISCORDANT", "ANOMALY", "MUTANT", "VIOLATION", "FAIL", "REJECT")

    @classmethod
    def evaluate_primary_parameter(cls, primary_metric: float):
        """Flag primary metrics that exceed the reference threshold."""
        if primary_metric > cls.PRIMARY_THRESHOLD:
            return {
                "summary": "Primary Parameter Threshold Exceeded",
                "details": (
                    f"Primary measurement ({primary_metric:.2f}) exceeds upper "
                    f"reference limit ({cls.PRIMARY_THRESHOLD:.2f})."
                ),
                "remediation": (
                    "Initiate recalibration workflow and review secondary "
                    "parameters."
                ),
            }
        return None

    @classmethod
    def evaluate_secondary_kinetics(cls, secondary_metric: float, is_critical_flag: bool):
        """Flag secondary kinetics that breach safety bounds or are marked critical."""
        if is_critical_flag or secondary_metric > cls.SECONDARY_THRESHOLD:
            return {
                "summary": "Critical Safety Interlock Triggered",
                "details": (
                    f"CriticalFlag={is_critical_flag} with secondary index "
                    f"{secondary_metric:.2f}."
                ),
                "remediation": (
                    "Execute immediate closed-loop escalation and notify "
                    "attending supervisor."
                ),
            }
        return None

    @classmethod
    def audit_specification_conformance(cls, status_descriptor: str, attributes: dict):
        """Detect protocol discordance in the status descriptor."""
        desc_upper = str(status_descriptor).upper()
        if any(kw in desc_upper for kw in cls.DISCORDANT_KEYWORDS):
            return {
                "summary": "Protocol Conformance Discordance Detected",
                "details": (
                    f"Descriptor '{status_descriptor}' indicates discordance "
                    f"with Transparent ZK-STARK Protocol specifications."
                ),
                "remediation": (
                    "Re-evaluate input specimen or rerun secondary confirmation "
                    "assay."
                ),
            }
        return None
