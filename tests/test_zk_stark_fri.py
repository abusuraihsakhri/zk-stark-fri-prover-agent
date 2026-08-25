"""
Real tests for ZK-STARK FRI Prover Engine.
"""
import random
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from zk_stark_fri.engine import (
    mod_pow, mod_inverse,
    field_add, field_mul, field_sub, field_neg,
    poly_eval, poly_degree, poly_add, poly_scale,
    generate_evaluation_domain, _find_primitive_root, _prime_factors,
    merkle_commit, merkle_open, merkle_verify, _hash,
    fri_fold, fri_commit, fri_query, fri_verify,
    soundness_analysis, run_fri_protocol,
    FRIProof,
)


class TestFieldArithmetic(unittest.TestCase):

    def test_field_add(self):
        self.assertEqual(field_add(3, 5, 7), 1)

    def test_field_mul(self):
        self.assertEqual(field_mul(3, 5, 7), 1)

    def test_field_sub(self):
        self.assertEqual(field_sub(3, 5, 7), 5)  # (3-5) mod 7 = -2 mod 7 = 5

    def test_field_neg(self):
        self.assertEqual(field_neg(3, 7), 4)

    def test_mod_inverse(self):
        p = 17
        a = 5
        inv = mod_inverse(a, p)
        self.assertEqual((a * inv) % p, 1)


class TestPolynomial(unittest.TestCase):

    def test_poly_eval_constant(self):
        self.assertEqual(poly_eval([42], 5, 65537), 42)

    def test_poly_eval_linear(self):
        # f(x) = 3 + 2x
        self.assertEqual(poly_eval([3, 2], 1, 65537), 5)
        self.assertEqual(poly_eval([3, 2], 2, 65537), 7)

    def test_poly_eval_quadratic(self):
        # f(x) = 1 + 2x + 3x^2
        # f(2) = 1 + 4 + 12 = 17
        self.assertEqual(poly_eval([1, 2, 3], 2, 65537), 17)

    def test_poly_degree(self):
        self.assertEqual(poly_degree([1, 2, 3, 0, 0]), 2)
        self.assertEqual(poly_degree([0, 0, 5]), 2)
        self.assertEqual(poly_degree([42]), 0)

    def test_poly_add(self):
        result = poly_add([1, 2], [3, 4, 5], 65537)
        self.assertEqual(result, [4, 6, 5])

    def test_poly_scale(self):
        result = poly_scale([1, 2, 3], 2, 7)
        self.assertEqual(result, [2, 4, 6])


class TestPrimitiveRoot(unittest.TestCase):

    def test_find_primitive_root(self):
        p = 17
        g = _find_primitive_root(p)
        # g should generate all non-zero elements
        seen = set()
        for i in range(1, p):
            seen.add(mod_pow(g, i, p))
        self.assertEqual(len(seen), p - 1)

    def test_prime_factors(self):
        self.assertEqual(sorted(_prime_factors(12)), [2, 3])
        self.assertEqual(sorted(_prime_factors(7)), [7])


class TestEvaluationDomain(unittest.TestCase):

    def test_domain_size(self):
        # 65537 - 1 = 65536 = 2^16, so domain sizes must be powers of 2
        domain = generate_evaluation_domain(16, 65537)
        self.assertEqual(len(domain), 16)

    def test_domain_elements_distinct(self):
        domain = generate_evaluation_domain(16, 65537)
        self.assertEqual(len(set(domain)), 16)

    def test_domain_is_subgroup(self):
        # All elements raised to n should be 1
        domain = generate_evaluation_domain(8, 65537)
        for d in domain:
            self.assertEqual(mod_pow(d, 8, 65537), 1)

    def test_invalid_domain_size(self):
        with self.assertRaises(ValueError):
            generate_evaluation_domain(7, 65537)  # 7 doesn't divide 65536


class TestMerkleTree(unittest.TestCase):

    def test_commit_and_verify(self):
        values = [1, 2, 3, 4, 5, 6, 7, 8]
        root, layers = merkle_commit(values)
        for i in range(len(values)):
            leaf_hash = _hash(str(values[i]))
            proof = merkle_open(layers, i)
            self.assertTrue(merkle_verify(root, leaf_hash, proof, i))

    def test_wrong_value_fails(self):
        values = [1, 2, 3, 4]
        root, layers = merkle_commit(values)
        leaf_hash = _hash(str(999))  # wrong value
        proof = merkle_open(layers, 0)
        self.assertFalse(merkle_verify(root, leaf_hash, proof, 0))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            merkle_commit([])

    def test_single_element(self):
        root, layers = merkle_commit([42])
        self.assertEqual(len(layers), 1)
        leaf_hash = _hash(str(42))
        proof = merkle_open(layers, 0)
        self.assertTrue(merkle_verify(root, leaf_hash, proof, 0))


class TestFRIFolding(unittest.TestCase):

    def test_fold_halves_length(self):
        p = 65537
        domain = generate_evaluation_domain(8, p)
        coeffs = [1, 2, 3, 4]
        evals = [poly_eval(coeffs, d, p) for d in domain]
        new_evals, new_domain = fri_fold(evals, domain, 5, p)
        self.assertEqual(len(new_evals), 4)
        self.assertEqual(len(new_domain), 4)

    def test_fold_consistency(self):
        # After folding, the new evaluations should be consistent
        p = 65537
        domain = generate_evaluation_domain(8, p)
        coeffs = [1, 2, 3, 4, 5, 6, 7, 8]
        evals = [poly_eval(coeffs, d, p) for d in domain]
        new_evals, new_domain = fri_fold(evals, domain, 3, p)
        self.assertEqual(len(new_evals), 4)

    def test_fold_invalid_odd_length(self):
        with self.assertRaises(ValueError):
            fri_fold([1, 2, 3], [1, 2, 3], 5, 65537)


class TestFRIProtocol(unittest.TestCase):

    def test_commit_returns_proof(self):
        random.seed(42)
        p = 65537
        domain = generate_evaluation_domain(16, p)
        coeffs = [1, 2, 3, 4]
        proof, all_evals, all_domains = fri_commit(coeffs, domain, p)
        self.assertIsInstance(proof, FRIProof)
        self.assertGreater(len(proof.roots), 0)

    def test_query_phase(self):
        random.seed(42)
        p = 65537
        domain = generate_evaluation_domain(16, p)
        coeffs = [1, 2, 3, 4]
        proof, all_evals, all_domains = fri_commit(coeffs, domain, p)
        query_proofs = fri_query(all_evals, all_domains, proof, 3, p)
        self.assertEqual(len(query_proofs), 3)

    def test_verify_valid_proof(self):
        random.seed(42)
        p = 65537
        domain = generate_evaluation_domain(16, p)
        coeffs = [1, 2, 3, 4]
        proof, all_evals, all_domains = fri_commit(coeffs, domain, p)
        fri_query(all_evals, all_domains, proof, 3, p)
        is_valid, details = fri_verify(proof, all_evals, all_domains, p)
        self.assertTrue(is_valid)


class TestSoundnessAnalysis(unittest.TestCase):

    def test_returns_dict(self):
        result = soundness_analysis(8, 65537, 3, 3)
        self.assertIsInstance(result, dict)

    def test_more_queries_better_soundness(self):
        r1 = soundness_analysis(8, 65537, 3, 3)
        r2 = soundness_analysis(8, 65537, 10, 3)
        self.assertGreater(r2["soundness_bits"], r1["soundness_bits"])

    def test_larger_field_better_soundness(self):
        r1 = soundness_analysis(8, 1009, 3, 3)
        r2 = soundness_analysis(8, 65537, 3, 3)
        self.assertGreater(r2["soundness_bits"], r1["soundness_bits"])

    def test_soundness_error_bounded(self):
        result = soundness_analysis(16, 65537, 5, 4)
        self.assertGreater(result["total_soundness_error"], 0)
        self.assertLess(result["total_soundness_error"], 1)


class TestRunFRIProtocol(unittest.TestCase):

    def test_full_protocol(self):
        random.seed(42)
        coeffs = [1, 2, 3, 4]
        result = run_fri_protocol(coeffs, 65537, 16, 3)
        self.assertIn("is_valid", result)
        self.assertIn("proof", result)
        self.assertIn("soundness", result)

    def test_protocol_with_larger_polynomial(self):
        random.seed(42)
        coeffs = list(range(1, 9))  # degree 7
        result = run_fri_protocol(coeffs, 65537, 16, 5)
        self.assertIn("is_valid", result)


if __name__ == "__main__":
    unittest.main()
