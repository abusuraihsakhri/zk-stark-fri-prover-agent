"""Regression tests for field, FRI trace and audit-chain correctness."""
import copy

import pytest

from agents.base import AuditTrail
from zk_stark_fri.engine import (
    fri_commit, fri_query, fri_verify, generate_evaluation_domain,
    mod_inverse, run_fri_protocol, _degree_at_most,
)


def make_trace(coefficients=(1, 2, 3, 4)):
    p = 65537
    domain = generate_evaluation_domain(16, p)
    proof, evaluations, domains = fri_commit(list(coefficients), domain, p, seed=7)
    fri_query(evaluations, domains, proof, 3, p)
    return proof, evaluations, domains, p


def test_valid_trace_and_public_degree_bound():
    proof, evaluations, domains, p = make_trace()
    assert fri_verify(proof, evaluations, domains, p, max_degree=3)[0] is True
    assert fri_verify(proof, evaluations, domains, p, max_degree=0)[0] is False


@pytest.mark.parametrize("mutation", ["root", "opening", "fold", "domain", "final", "query"])
def test_tampering_is_rejected(mutation):
    proof, evaluations, domains, p = make_trace()
    proof = copy.deepcopy(proof)
    evaluations, domains = copy.deepcopy(evaluations), copy.deepcopy(domains)
    if mutation == "root":
        proof.roots[0] = "0" * 64
    elif mutation == "opening":
        proof.query_proofs[0][0]["evaluation"] += 1
    elif mutation == "fold":
        evaluations[1][0] += 1
    elif mutation == "domain":
        domains[1][0] = 123
    elif mutation == "final":
        proof.final_evaluations[0] += 1
    elif mutation == "query":
        proof.query_proofs[0][0]["index"] = -1
    assert not fri_verify(proof, evaluations, domains, p)[0]


@pytest.mark.parametrize("size,prime", [(0, 65537), (-2, 65537), (3, 65537), (4, 15), (4, 2)])
def test_reject_invalid_domains(size, prime):
    with pytest.raises(ValueError):
        generate_evaluation_domain(size, prime)


def test_inverse_zero_fails():
    with pytest.raises(ValueError):
        mod_inverse(0, 65537)


def test_trace_final_degree_polynomial_validation():
    d = generate_evaluation_domain(8, 65537)
    assert _degree_at_most([9] * 8, d, 0, 65537)
    assert not _degree_at_most([9, 9, 9, 9, 9, 9, 9, 10], d, 0, 65537)
    assert _degree_at_most([(3 + 2*x) % 65537 for x in d], d, 1, 65537)


def test_audit_signature_detects_mutation():
    audit = AuditTrail(secret_key="local-testing-only")
    entry = audit.log("test", "unit", "event", {"task_id": "T-1"})
    assert audit.verify_integrity()
    audit.logs[0]["payload_hash"] = "0" * 64
    assert not audit.verify_integrity()


def test_audit_get_trail_is_snapshot():
    audit = AuditTrail(secret_key="local-testing-only")
    audit.log("test", "unit", "event", {"task_id": "T-1"})
    audit.get_trail()[0]["event_type"] = "MODIFIED"
    assert audit.verify_integrity()


def test_demo_result_is_explicitly_educational():
    output = run_fri_protocol([1, 2, 3, 4], 65537, 16, 3)
    assert output["is_valid"] is True
    assert "not a" in output["verification"]["security_note"].lower()
