#!/usr/bin/env python3
"""P1-003-R2 Analysis reference-skill validation.

Static checks only. Runtime Skill behavior is NOT executed or claimed.
"""
import copy
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "analysis"
REQ_SKILL = ROOT / "skills" / "requirements-clarity"
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
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path):
    with path.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=UniqueKeyLoader)


def schema_errors(validator, obj):
    return list(validator.iter_errors(obj))


SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def valid_semver(value):
    return isinstance(value, str) and bool(SEMVER_RE.match(value))


def requirement_blocking(req):
    if not isinstance(req, dict):
        return False
    return (
        any(x.get("blocking") is True for x in req.get("open_questions", []) or [])
        or any(x.get("blocking") is True for x in req.get("unknowns", []) or [])
        or any(x.get("status") == "open" for x in req.get("conflicts", []) or [])
        or any(x.get("status") == "open" for x in req.get("ambiguities", []) or [])
    )


def validate_analysis_input(inp, label, input_validator, req_validator):
    errs = schema_errors(input_validator, inp)
    result = [f"{label}: input schema: {e.message}" for e in errs]
    ref = inp.get("requirements_ref") if isinstance(inp, dict) else None
    if isinstance(ref, dict) and ref.get("type") != "requirements":
        result.append(f"{label}: requirements_ref.type must be requirements")
    req = inp.get("requirements") if isinstance(inp, dict) else None
    if isinstance(req, dict):
        envelope = {
            "status": "ok",
            "data": {"requirements": req},
            "artifacts": [],
            "errors": [],
            "evidence": [],
        }
        for e in req_validator.iter_errors(envelope):
            result.append(f"{label}: requirements content invalid: {e.message}")
    return result


def validate_analysis_output(obj, label, input_obj=None):
    errs = []
    if not isinstance(obj, dict):
        return [f"{label}: output must be an object"]
    data = obj.get("data")
    if isinstance(data, dict):
        for forbidden in ("implementation_plan", "design_spec", "design_approved", "gate_approved", "confirmation_ref", "g2_approved"):
            if forbidden in data:
                errs.append(f"{label}: forbidden field {forbidden}")
    analysis = data.get("analysis") if isinstance(data, dict) else None
    if not isinstance(analysis, dict):
        return errs
    for forbidden in ("implementation_plan", "design_spec", "design_approved", "gate_approved", "confirmation_ref", "g2_approved"):
        if forbidden in analysis:
            errs.append(f"{label}: forbidden field {forbidden} in analysis")

    if obj.get("status") != "ok":
        return errs

    required = [
        "analysis_id", "analysis_version", "source_requirements_ref", "problem_statement",
        "technical_context", "candidate_solutions", "feasibility_assessment", "risk_assessment",
        "comparison_matrix", "recommendation", "next_steps",
    ]
    for key in required:
        if key not in analysis:
            errs.append(f"{label}: missing {key}")

    candidates = analysis.get("candidate_solutions", []) or []
    candidate_ids = [c.get("solution_id") for c in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        errs.append(f"{label}: duplicate candidate solution_id")
    if not candidates:
        errs.append(f"{label}: no candidate solutions")
    if len(candidates) == 1 and not analysis.get("single_solution_rationale"):
        errs.append(f"{label}: single candidate requires single_solution_rationale")

    risks = analysis.get("risk_assessment", []) or []
    risk_ids = [r.get("risk_id") for r in risks]
    if len(risk_ids) != len(set(risk_ids)):
        errs.append(f"{label}: duplicate risk_id")
    for risk in risks:
        if not risk.get("severity_basis"):
            errs.append(f"{label}: risk {risk.get('risk_id')} missing severity_basis")

    recommendation = analysis.get("recommendation") or {}
    rec_id = recommendation.get("recommended_solution_id")
    if rec_id not in candidate_ids:
        errs.append(f"{label}: recommended_solution_id {rec_id} not in candidate_solutions")
    for risk_id in recommendation.get("unresolved_risks", []) or []:
        if risk_id not in risk_ids:
            errs.append(f"{label}: unresolved risk {risk_id} not in risk_assessment")
    if recommendation.get("recommendation_status") not in {"recommended", "conditionally_recommended", "no_recommendation"}:
        errs.append(f"{label}: recommendation_status must not be design_approved")

    feasibility = analysis.get("feasibility_assessment", []) or []
    areas = {x.get("area") for x in feasibility}
    core_areas = {"technical", "compatibility", "performance", "security", "operations"}
    missing_areas = core_areas - areas
    if missing_areas:
        errs.append(f"{label}: feasibility missing core areas {sorted(missing_areas)}")

    comparison = analysis.get("comparison_matrix") or {}
    dimensions = comparison.get("dimensions", []) or []
    if comparison.get("weighted") is True:
        if not comparison.get("method"):
            errs.append(f"{label}: weighted comparison missing method")
        if not comparison.get("weight_basis"):
            errs.append(f"{label}: weighted comparison missing weight_basis")
        weights = [d.get("weight") for d in dimensions]
        if any(not isinstance(w, (int, float)) for w in weights):
            errs.append(f"{label}: weighted comparison dimension missing weight")
        elif abs(sum(weights) - 1.0) > 0.01:
            errs.append(f"{label}: comparison weights must sum to 1.0")
    for dim in dimensions:
        for score in dim.get("scores", []) or []:
            if score.get("solution_id") not in candidate_ids:
                errs.append(f"{label}: comparison score references unknown solution_id")
            if score.get("not_applicable") is True and score.get("score") is not None:
                errs.append(f"{label}: not_applicable score must be null")
            if score.get("not_applicable") is False and score.get("score") is None:
                errs.append(f"{label}: applicable score must be numeric")

    for fact in analysis.get("facts", []) or []:
        if fact.get("source_type") == "evidence_backed" and not fact.get("evidence_refs"):
            errs.append(f"{label}: evidence_backed fact missing evidence_refs")
    for assumption in analysis.get("assumptions", []) or []:
        if assumption.get("status") != "unconfirmed":
            errs.append(f"{label}: assumption must remain unconfirmed")
    for unknown in analysis.get("unknowns", []) or []:
        if unknown.get("status") != "unknown":
            errs.append(f"{label}: unknown must have status=unknown")
        if unknown.get("blocking") is True:
            errs.append(f"{label}: blocking unknown prevents status=ok")
    next_steps = analysis.get("next_steps") or {}
    if next_steps.get("blocking_questions"):
        errs.append(f"{label}: blocking_questions present with status=ok")

    source_ref = analysis.get("source_requirements_ref")
    if isinstance(input_obj, dict):
        input_ref = input_obj.get("requirements_ref")
        if isinstance(input_ref, dict) and source_ref != input_ref:
            errs.append(f"{label}: source_requirements_ref does not match input requirements_ref")
        req = input_obj.get("requirements")
        if isinstance(req, dict):
            if requirement_blocking(req):
                errs.append(f"{label}: blocking upstream requirements cannot produce status=ok")
            input_constraints = set(req.get("constraints", []) or [])
            output_constraints = set((analysis.get("problem_statement") or {}).get("constraints", []) or [])
            missing = input_constraints - output_constraints
            if missing:
                errs.append(f"{label}: upstream constraints dropped: {sorted(missing)}")
    return errs


# 1. Structural checks
text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
check(bool(m), "SKILL.md: missing frontmatter")
meta = yaml.safe_load(m.group(1)) if m else {}
check(meta.get("name") == "analysis", "SKILL.md: name mismatch")
check(bool(meta.get("description")), "SKILL.md: missing description")
check(set(meta) <= {"name", "description", "requires"}, "SKILL.md: platform/unknown fields in core frontmatter")
check(set(meta.get("requires", {})) <= {"runtime", "tools", "permissions"}, "SKILL.md: unknown requires keys")

manifest = load_yaml(SKILL / "skill.yaml")
check(manifest.get("name") == "analysis", "skill.yaml: name mismatch")
check(manifest.get("schema_version") == 1, "skill.yaml: schema_version must be 1")
check(manifest.get("version") == "0.1.0", "skill.yaml: version must be 0.1.0")
check(valid_semver(str(manifest.get("version", ""))), "skill.yaml: invalid SemVer")
check(manifest.get("status") in {"draft", "review", "tested", "published", "deprecated", "retired", "archived"}, "skill.yaml: invalid status")
check(manifest.get("dependencies", {}).get("skills", [{}])[0].get("name") == "requirements-clarity",
      "skill.yaml: must depend on requirements-clarity")
check(manifest.get("dependencies", {}).get("tools") == ["file-read"], "skill.yaml: tool dependency must be file-read")
check(manifest.get("compatibility", {}).get("requires_capabilities") ==
      ["skill-discovery", "skill-metadata", "tool-invocation", "context-port", "artifact-port", "result-port"],
      "skill.yaml: capability registry mismatch")

input_schema = load_json(SKILL / "schemas" / "input.schema.json")
output_schema = load_json(SKILL / "schemas" / "output.schema.json")
req_output_schema = load_json(REQ_SKILL / "schemas" / "output.schema.json")
for name, schema in (("input", input_schema), ("output", output_schema)):
    check(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{name} schema: wrong $schema")
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as e:
        errors.append(f"{name} schema: invalid Draft 2020-12 schema: {e}")
in_validator = Draft202012Validator(input_schema)
out_validator = Draft202012Validator(output_schema)
req_validator = Draft202012Validator(req_output_schema)

# 2. Examples
input_files = sorted((SKILL / "examples").glob("example-input*.json"))
output_files = sorted((SKILL / "examples").glob("example-output*.json"))
input_positive = 0
output_positive = 0
input_objects = {}
for path in input_files:
    obj = load_json(path)
    input_objects[path.name] = obj
    errs = validate_analysis_input(obj, path.name, in_validator, req_validator)
    check(not errs, f"{path.name}: invalid: {errs[:3]}")
    if not errs:
        input_positive += 1
for path in output_files:
    obj = load_json(path)
    errs = schema_errors(out_validator, obj)
    check(not errs, f"{path.name}: schema invalid: {[e.message for e in errs[:3]]}")
    sem = validate_analysis_output(obj, path.name)
    check(not sem, f"{path.name}: semantic error: {sem[:3]}")
    if not errs and not sem:
        output_positive += 1

# 3. Cases
cases = load_yaml(SKILL / "tests" / "cases.yaml")
check(cases.get("skill") == "analysis", "cases: skill mismatch")
check(cases.get("version") == "0.1.0", "cases: version must be 0.1.0")
case_list = cases.get("cases", [])
check(isinstance(case_list, list) and len(case_list) >= 3, "cases: need at least 3 cases")
for case in case_list:
    name = case.get("name", "case")
    input_rel = case.get("input_example")
    input_path = SKILL / input_rel if input_rel else None
    check(bool(input_path and input_path.exists()), f"cases[{name}]: input example missing")
    if not input_path or not input_path.exists():
        continue
    inp = load_json(input_path)
    in_errs = validate_analysis_input(inp, f"cases[{name}]", in_validator, req_validator)
    check(not in_errs, f"cases[{name}]: input invalid: {in_errs[:3]}")
    expect = case.get("expect", {})
    status = expect.get("status")
    check(status in {"ok", "needs_input", "needs_approval", "blocked", "failed"}, f"cases[{name}]: invalid status")
    out_rel = expect.get("output_example")
    out_path = SKILL / out_rel if out_rel else None
    check(bool(out_path and out_path.exists()), f"cases[{name}]: output example missing")
    if out_path and out_path.exists():
        out = load_json(out_path)
        out_errs = schema_errors(out_validator, out)
        check(not out_errs, f"cases[{name}]: output schema invalid: {[e.message for e in out_errs[:2]]}")
        sem = validate_analysis_output(out, f"cases[{name}]", inp)
        check(not sem, f"cases[{name}]: semantic error: {sem[:3]}")
        check(out.get("status") == status, f"cases[{name}]: output status mismatch")

# 4. Invalid inputs
invalid = load_yaml(SKILL / "tests" / "invalid-cases.yaml")
invalid_list = invalid.get("invalid_cases", [])
for i, case in enumerate(invalid_list):
    errs = schema_errors(in_validator, case.get("input"))
    check(bool(errs), f"invalid-cases[{i}]: expected schema rejection, got valid input")

# 5. Negative schema/semantic cases
base = load_json(SKILL / "examples" / "example-output.json")
schema_negative = [0]
semantic_negative = [0]


def expect_schema_invalid(label, mutate):
    obj = copy.deepcopy(base)
    mutate(obj["data"]["analysis"])
    errs = schema_errors(out_validator, obj)
    check(bool(errs), f"{label}: expected schema rejection, got valid input")
    if errs:
        schema_negative[0] += 1


def expect_semantic_failure(label, mutate, inp=None):
    obj = copy.deepcopy(base)
    mutate(obj["data"]["analysis"])
    errs = validate_analysis_output(obj, label, inp)
    check(bool(errs), f"{label}: expected semantic failure, got pass")
    if errs:
        semantic_negative[0] += 1


expect_schema_invalid("analysis-missing-source-ref", lambda a: a.pop("source_requirements_ref"))
expect_schema_invalid("analysis-bad-version", lambda a: a.update({"analysis_version": "1.0"}))
expect_schema_invalid("analysis-candidate-missing-approach", lambda a: a["candidate_solutions"][0].pop("approach"))
expect_schema_invalid("analysis-recommendation-missing-rationale", lambda a: a["recommendation"].pop("rationale"))
expect_schema_invalid("analysis-fact-evidence-missing", lambda a: next(f for f in a["facts"] if f["source_type"] == "evidence_backed").update({"evidence_refs": []}))
expect_schema_invalid("analysis-assumption-confirmed", lambda a: a["assumptions"][0].update({"status": "confirmed"}))
expect_schema_invalid("analysis-unknown-verified", lambda a: a["unknowns"][0].update({"status": "verified"}))
expect_schema_invalid("analysis-risk-missing-basis", lambda a: a["risk_assessment"][0].pop("severity_basis"))
expect_schema_invalid("analysis-design-approved", lambda a: a["recommendation"].update({"recommendation_status": "design_approved"}))
expect_schema_invalid("analysis-implementation-plan", lambda a: a.update({"implementation_plan": {}}))
expect_schema_invalid("analysis-cost-missing-basis", lambda a: a["candidate_solutions"][0]["implementation_cost_estimate"].pop("basis"))

input_bad_ref = copy.deepcopy(load_json(SKILL / "examples" / "example-input.json"))
input_bad_ref["requirements_ref"]["type"] = "analysis"
in_errs = validate_analysis_input(input_bad_ref, "input-bad-ref-type", in_validator, req_validator)
check(bool(in_errs), "input-bad-ref-type: expected rejection")
if in_errs:
    semantic_negative[0] += 1

expect_semantic_failure(
    "analysis-recommendation-unknown-solution",
    lambda a: a["recommendation"].update({"recommended_solution_id": "SOL-MISSING"}))
expect_semantic_failure(
    "analysis-weighted-no-weights",
    lambda a: a["comparison_matrix"].update({"weighted": True, "weight_basis": ""}) and
    [d.pop("weight", None) for d in a["comparison_matrix"]["dimensions"]])
expect_semantic_failure(
    "analysis-single-without-rationale",
    lambda a: a.update({"candidate_solutions": [a["candidate_solutions"][0]], "single_solution_rationale": ""}))
expect_semantic_failure(
    "analysis-blocking-input-with-ok",
    lambda a: None,
    load_json(SKILL / "examples" / "example-input-partial.json"))
expect_semantic_failure(
    "analysis-dropped-upstream-constraint",
    lambda a: a["problem_statement"].update({"constraints": []}),
    input_objects.get("example-input.json"))
expect_semantic_failure(
    "analysis-blocking-unknown",
    lambda a: a["unknowns"][0].update({"blocking": True}))
expect_semantic_failure(
    "analysis-unresolved-risk-missing",
    lambda a: a["recommendation"].update({"unresolved_risks": ["RISK-MISSING"]}))

if errors:
    print("ANALYSIS VALIDATION FAILED")
    for e in errors:
        print("-", e)
    raise SystemExit(1)

print("ANALYSIS VALIDATION PASSED")
print(f"schemas=2 input_examples={len(input_files)} output_examples={len(output_files)}")
print(f"input_positive={input_positive} output_positive={output_positive} cases={len(case_list)} invalid_cases={len(invalid_list)}")
print(f"schema_negative={schema_negative[0]} semantic_negative={semantic_negative[0]}")
print("runtime_behavior=NOT_EXECUTED")
