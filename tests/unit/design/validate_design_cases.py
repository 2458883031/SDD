#!/usr/bin/env python3
"""P1-003-R3-R3 Design case fixture validator.

Static fixture checks only. This is NOT a Design Semantic Validator and does
not execute the Design Skill or any Runtime behavior.

It validates:
  - positive example inputs/outputs against the current schemas;
  - cases.yaml structure, IDs, references and expected statuses;
  - schema-input / schema-output negative cases against the schemas;
  - the documented missing-input contract decision table;
  - semantic cases are explicitly reported as unexecuted.

runtime_behavior = NOT_EXECUTED
"""
import copy
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "design"
errors = []


class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError(f"duplicate YAML key: {key!r}")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def check(cond, msg):
    if not cond:
        errors.append(msg)


def load_json(path):
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path):
    with Path(path).open(encoding="utf-8") as f:
        return yaml.load(f, Loader=UniqueKeyLoader)


def schema_errors(validator, obj):
    return list(validator.iter_errors(obj))


def apply_mutation(obj, path, mutation):
    """Apply a narrow fixture mutation and return the mutated object."""
    target = obj
    for key in path[:-1]:
        if isinstance(target, dict):
            target = target[key]
        elif isinstance(target, list):
            target = target[int(key)]
        else:
            raise ValueError(f"cannot traverse {key!r} in mutation path")

    last = path[-1]
    if mutation == "remove":
        if isinstance(target, dict):
            target.pop(last, None)
        elif isinstance(target, list):
            target.pop(int(last), None)
    elif mutation == "set_empty_array":
        target[last] = []
    elif mutation == "set_true":
        target[last] = True
    elif mutation == "set_to_report":
        target[last] = "report"
    elif mutation.startswith("add_forbidden_field_"):
        field = mutation[len("add_forbidden_field_"):]
        target[field] = {}
    else:
        raise ValueError(f"unsupported mutation: {mutation}")
    return obj


def contract_status(inp):
    """Documented missing-input decision table; not a semantic validator."""
    if not in_validator.is_valid(inp):
        return "failed/input_invalid"
    missing_refs = [k for k in ("requirements_ref", "analysis_ref") if k not in inp]
    if missing_refs:
        return "needs_input"
    if "complexity" not in inp:
        return "blocked"
    return "proceed"


# Schemas
input_schema = load_json(SKILL / "schemas" / "input.schema.json")
output_schema = load_json(SKILL / "schemas" / "output.schema.json")
Draft202012Validator.check_schema(input_schema)
Draft202012Validator.check_schema(output_schema)
in_validator = Draft202012Validator(input_schema)
out_validator = Draft202012Validator(output_schema)

# Examples
ex_dir = SKILL / "examples"
input_files = sorted(ex_dir.glob("example-input-*.json"))
output_files = sorted(ex_dir.glob("example-output-*.json"))
input_map = {p.name: load_json(p) for p in input_files}
output_map = {p.name: load_json(p) for p in output_files}

# cases.yaml
cases_doc = load_yaml(SKILL / "tests" / "cases.yaml")
check(cases_doc.get("skill") == "design", "cases: skill mismatch")
check(cases_doc.get("version") == "0.1.0", "cases: version must be 0.1.0")
case_list = cases_doc.get("cases", [])
check(len(case_list) >= 11, f"cases: need at least 11 cases, got {len(case_list)}")
case_ids = [c.get("id") for c in case_list]
check(len(case_ids) == len(set(case_ids)), "cases: duplicate IDs detected")

input_positive = 0
output_positive = 0
case_schema_pass = 0
seen_input_positive = set()
seen_output_positive = set()

for case in case_list:
    cid = case.get("id", "unknown")
    inp_rel = case.get("input_example")
    out_rel = case.get("output_example")
    expect = case.get("expect") or {}
    check(bool(case.get("scenario")), f"{cid}: missing scenario")
    check(bool(case.get("standard_refs")), f"{cid}: missing standard_refs")
    check(bool(case.get("schema_refs")), f"{cid}: missing schema_refs")
    check(bool(inp_rel and (SKILL / inp_rel).exists()), f"{cid}: input_example missing: {inp_rel}")
    check(bool(out_rel and (SKILL / out_rel).exists()), f"{cid}: output_example missing: {out_rel}")
    if not inp_rel or not out_rel:
        continue

    inp = input_map.get(Path(inp_rel).name)
    out = output_map.get(Path(out_rel).name)
    if inp is None or out is None:
        check(False, f"{cid}: referenced example not loaded")
        continue

    input_schema_ok = not schema_errors(in_validator, inp)
    expected_input_ok = expect.get("input_schema_valid")
    if expected_input_ok is not None:
        check(input_schema_ok == expected_input_ok,
              f"{cid}: input schema expected valid={expected_input_ok}, got={input_schema_ok}")
    if input_schema_ok:
        if Path(inp_rel).name not in seen_input_positive:
            seen_input_positive.add(Path(inp_rel).name)
            input_positive += 1

    out_errs = schema_errors(out_validator, out)
    check(not out_errs, f"{cid}: output schema error: {[e.message for e in out_errs[:2]]}")
    if not out_errs:
        if Path(out_rel).name not in seen_output_positive:
            seen_output_positive.add(Path(out_rel).name)
            output_positive += 1

    expected_status = expect.get("status")
    actual_status = out.get("status")
    check(expected_status == actual_status,
          f"{cid}: expected status={expected_status}, got={actual_status}")

    if expected_status == "ok":
        design = out.get("data", {}).get("design", {}) or {}
        for field in expect.get("required_design_fields", []):
            check(field in design, f"{cid}: missing required design field: {field}")
        coverage_statuses = {c.get("status") for c in design.get("coverage", []) or []}
        for status in expect.get("coverage_statuses", []):
            check(status in coverage_statuses,
                  f"{cid}: coverage status {status!r} not present")
        if expect.get("require_deviation"):
            decisions = design.get("decisions", []) or []
            check(any(isinstance(d.get("deviation_from_recommendation"), dict)
                      for d in decisions),
                  f"{cid}: expected deviation_from_recommendation")
        if expect.get("require_ac_mapping"):
            mapping = (design.get("test_strategy") or {}).get("acceptance_criteria_mapping", [])
            check(bool(mapping) and all(m.get("design_refs") for m in mapping),
                  f"{cid}: expected non-empty AC design_refs")
        if expect.get("require_change_impact"):
            check(isinstance(design.get("design_change_impact"), dict),
                  f"{cid}: expected design_change_impact")
        check(any(a.get("type") == "design" for a in out.get("artifacts", [])),
              f"{cid}: ok output missing type=design artifact")
    elif expected_status == "needs_input":
        qs = (out.get("data") or {}).get("questions", [])
        check(isinstance(qs, list) and len(qs) >= 1, f"{cid}: needs_input missing questions")
    elif expected_status == "blocked":
        check(bool((out.get("data") or {}).get("blocked_reason")),
              f"{cid}: blocked missing blocked_reason")
    elif expected_status == "failed":
        check(len(out.get("errors", [])) >= 1, f"{cid}: failed missing errors")

    if not out_errs and expected_status == actual_status:
        case_schema_pass += 1

# invalid-cases.yaml
invalid_doc = load_yaml(SKILL / "tests" / "invalid-cases.yaml")
check(invalid_doc.get("skill") == "design", "invalid-cases: skill mismatch")
inv_list = invalid_doc.get("invalid_cases", [])
check(len(inv_list) >= 22, f"invalid-cases: need at least 22 cases, got {len(inv_list)}")
inv_ids = [c.get("id") for c in inv_list]
check(len(inv_ids) == len(set(inv_ids)), "invalid-cases: duplicate IDs detected")

schema_input_rejected = 0
schema_output_rejected = 0
contract_status_passed = 0
semantic_unexecuted = 0

for inv in inv_list:
    cid = inv.get("id", "unknown")
    layer = inv.get("layer")
    check(layer in {"schema-input", "schema-output", "contract-input-status", "contract-semantic"},
          f"{cid}: invalid layer {layer!r}")
    check(bool(inv.get("why_invalid")), f"{cid}: missing why_invalid")
    check(bool(inv.get("rule_source")), f"{cid}: missing rule_source")
    check(bool(inv.get("expected_result")), f"{cid}: missing expected_result")

    if layer == "schema-input":
        inp = inv.get("input")
        check(inp is not None, f"{cid}: schema-input missing input")
        if inp is not None:
            rejected = bool(schema_errors(in_validator, inp))
            check(rejected, f"{cid}: schema-input should reject but passed")
            if rejected:
                schema_input_rejected += 1
    elif layer == "schema-output":
        base_name = inv.get("base_output_example")
        path = inv.get("mutation_path")
        mutation = inv.get("mutation")
        check(bool(base_name and path and mutation), f"{cid}: incomplete schema-output mutation")
        base = output_map.get(Path(base_name).name) if base_name else None
        check(base is not None, f"{cid}: base_output_example missing: {base_name}")
        if base is not None and path and mutation:
            try:
                obj = apply_mutation(copy.deepcopy(base), path, mutation)
                rejected = bool(schema_errors(out_validator, obj))
                check(rejected, f"{cid}: schema-output should reject but passed")
                if rejected:
                    schema_output_rejected += 1
            except Exception as exc:
                check(False, f"{cid}: mutation failed: {exc}")
    elif layer == "contract-input-status":
        inp = inv.get("input")
        expected = inv.get("expected_status")
        check(inp is not None, f"{cid}: contract-input-status missing input")
        check(expected in {"needs_input", "blocked"},
              f"{cid}: expected_status must be needs_input or blocked")
        if inp is not None:
            actual = contract_status(inp)
            check(actual == expected, f"{cid}: contract status expected={expected}, got={actual}")
            if actual == expected:
                contract_status_passed += 1
    elif layer == "contract-semantic":
        check(inv.get("requires_semantic_validator") is True,
              f"{cid}: semantic case must set requires_semantic_validator=true")
        check(inv.get("validator_executed") is False,
              f"{cid}: semantic case must set validator_executed=false")
        semantic_unexecuted += 1

print("DESIGN CASE VALIDATION")
print(f"  examples: input_positive={input_positive}/{len(input_files)} "
      f"output_schema_valid={output_positive}/{len(output_files)}")
print(f"  cases: total={len(case_list)} schema_pass={case_schema_pass}")
print(f"  invalid-cases: total={len(inv_list)} "
      f"schema_input_rejected={schema_input_rejected} "
      f"schema_output_rejected={schema_output_rejected} "
      f"contract_status_passed={contract_status_passed} "
      f"semantic_unexecuted={semantic_unexecuted}")

if errors:
    print("\nVALIDATION FAILED")
    for e in errors:
        print(f"  - {e}")
    raise SystemExit(1)

print("\nDESIGN CASE VALIDATION PASSED")
print("runtime_behavior=NOT_EXECUTED")
