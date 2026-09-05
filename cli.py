"""
CLI for ZK-STARK FRI Prover Agent.
Supports: commit, query, verify, soundness, demo.
"""
import argparse
import json
import sys

from zk_stark_fri.engine import (
    poly_eval, poly_degree, generate_evaluation_domain,
    merkle_commit, merkle_open, merkle_verify,
    fri_fold, fri_commit, fri_query, fri_verify,
    soundness_analysis, run_fri_protocol,
    FRIProof,
)


def cmd_eval(args):
    """Evaluate polynomial at a point."""
    coeffs = json.loads(args.coefficients)
    result = poly_eval(coeffs, args.x, args.prime)
    print(json.dumps({"x": args.x, "value": result, "prime": args.prime}, indent=2))
    return 0


def cmd_domain(args):
    """Generate evaluation domain."""
    domain = generate_evaluation_domain(args.size, args.prime)
    print(json.dumps({"size": args.size, "prime": args.prime,
                       "domain": domain[:20],  # show first 20
                       "domain_length": len(domain)}, indent=2))
    return 0


def cmd_merkle(args):
    """Build Merkle tree and generate proof."""
    values = json.loads(args.values)
    root, layers = merkle_commit(values)
    proof = merkle_open(layers, args.index)
    from zk_stark_fri.engine import _hash
    leaf_hash = _hash(str(values[args.index]))
    valid = merkle_verify(root, leaf_hash, proof, args.index)
    print(json.dumps({
        "root": root,
        "index": args.index,
        "leaf_value": values[args.index],
        "proof_length": len(proof),
        "verified": valid,
    }, indent=2))
    return 0


def cmd_fold(args):
    """Run one FRI folding step."""
    evals = json.loads(args.evaluations)
    domain = json.loads(args.domain)
    new_evals, new_domain = fri_fold(evals, domain, args.alpha, args.prime)
    print(json.dumps({
        "alpha": args.alpha,
        "input_length": len(evals),
        "output_length": len(new_evals),
        "new_evaluations": new_evals,
        "new_domain": new_domain,
    }, indent=2))
    return 0


def cmd_commit(args):
    """Run FRI commitment phase."""
    coeffs = json.loads(args.coefficients)
    domain = generate_evaluation_domain(args.domain_size, args.prime)
    proof, all_evals, all_domains = fri_commit(coeffs, domain, args.prime)
    print(json.dumps({
        "proof": proof.to_dict(),
        "num_rounds": proof.rounds,
        "evaluations_per_round": [len(e) for e in all_evals],
    }, indent=2))
    return 0


def cmd_soundness(args):
    """Analyze FRI soundness."""
    result = soundness_analysis(args.degree, args.field_size,
                                 args.num_queries, args.num_rounds)
    print(json.dumps(result, indent=2))
    return 0


def cmd_demo(args):
    """Run full FRI protocol demo."""
    coeffs = json.loads(args.coefficients) if args.coefficients else [1, 2, 3, 4]
    result = run_fri_protocol(coeffs, args.prime, args.domain_size, args.num_queries)
    print(json.dumps(result, indent=2))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="zk-stark-fri-prover-agent",
        description="ZK-STARK FRI Prover: polynomial commitment via Fast Reed-Solomon IOP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Eval
    p_eval = subparsers.add_parser("eval", help="Evaluate polynomial")
    p_eval.add_argument("--coefficients", type=str, required=True, help="JSON array of coefficients")
    p_eval.add_argument("--x", type=int, required=True, help="Evaluation point")
    p_eval.add_argument("--prime", type=int, default=65537)

    # Domain
    p_domain = subparsers.add_parser("domain", help="Generate evaluation domain")
    p_domain.add_argument("--size", type=int, required=True, help="Domain size (must divide p-1)")
    p_domain.add_argument("--prime", type=int, default=65537)

    # Merkle
    p_merkle = subparsers.add_parser("merkle", help="Merkle tree operations")
    p_merkle.add_argument("--values", type=str, required=True, help="JSON array of values")
    p_merkle.add_argument("--index", type=int, required=True, help="Leaf index for proof")

    # Fold
    p_fold = subparsers.add_parser("fold", help="FRI folding step")
    p_fold.add_argument("--evaluations", type=str, required=True, help="JSON evaluations array")
    p_fold.add_argument("--domain", type=str, required=True, help="JSON domain array")
    p_fold.add_argument("--alpha", type=int, required=True, help="Folding challenge")
    p_fold.add_argument("--prime", type=int, default=65537)

    # Commit
    p_commit = subparsers.add_parser("commit", help="FRI commitment phase")
    p_commit.add_argument("--coefficients", type=str, required=True, help="JSON polynomial coefficients")
    p_commit.add_argument("--domain-size", type=int, required=True)
    p_commit.add_argument("--prime", type=int, default=65537)

    # Soundness
    p_sound = subparsers.add_parser("soundness", help="Soundness analysis")
    p_sound.add_argument("--degree", type=int, required=True, help="Polynomial degree")
    p_sound.add_argument("--field-size", type=int, required=True, help="Field size")
    p_sound.add_argument("--num-queries", type=int, required=True)
    p_sound.add_argument("--num-rounds", type=int, required=True)

    # Demo
    p_demo = subparsers.add_parser("demo", help="Full FRI protocol demo")
    p_demo.add_argument("--coefficients", type=str, default=None, help="JSON coefficients")
    p_demo.add_argument("--domain-size", type=int, default=16)
    p_demo.add_argument("--prime", type=int, default=65537)
    p_demo.add_argument("--num-queries", type=int, default=3)

    args = parser.parse_args(argv)

    cmd_map = {
        "eval": cmd_eval,
        "domain": cmd_domain,
        "merkle": cmd_merkle,
        "fold": cmd_fold,
        "commit": cmd_commit,
        "soundness": cmd_soundness,
        "demo": cmd_demo,
    }
    return cmd_map[args.command](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
