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


def ref_key(ref):
    if not isinstance(ref, dict):
        return ""
    return f"{ref.get('path')}@{ref.get('version')}#{ref.get('sha256')}"


def upstream_items(req):
    if not isinstance(req, dict):
        return set()
    items = set()
    for fr in req.get("functional_requirements", []) or []:
        if fr.get("id"):
            items.add(("functional_requirement", fr["id"]))
    for nfr in req.get("non_functional_requirements", []) or []:
        if nfr.get("id"):
            items.add(("non_functional_requirement", nfr["id"]))
    for value in req.get("constraints", []) or []:
        if isinstance(value, str) and value:
            items.add(("constraint", value))
    for dep in req.get("dependencies", []) or []:
        if dep.get("id"):
            items.add(("dependency", dep["id"]))
    for assumption in req.get("assumptions", []) or []:
        if assumption.get("id"):
            items.add(("assumption", assumption["id"]))
    for unknown in req.get("unknowns", []) or []:
        if unknown.get("id"):
            items.add(("unknown", unknown["id"]))
    for question in req.get("open_questions", []) or []:
        if question.get("id"):
            items.add(("open_question", question["id"]))
    for criterion in req.get("acceptance_criteria", []) or []:
        if isinstance(criterion, dict) and criterion.get("id"):
            items.add(("acceptance_criterion", criterion["id"]))
        elif isinstance(criterion, str) and criterion:
            items.add(("acceptance_criterion", criterion))
    for non_goal in req.get("non_goals", []) or []:
        if isinstance(non_goal, str) and non_goal:
            items.add(("non_goal", non_goal))
    for source_ref in req.get("source_refs", []) or []:
        key = ref_key(source_ref)
        if key:
            items.add(("source_ref", key))
    return items


def analysis_ref_exists(ref, analysis, candidate_ids, risk_ids, design_considerations):
    if ref.startswith("solution:"):
        return ref.split(":", 1)[1] in candidate_ids
    if ref.startswith("risk:"):
        return ref.split(":", 1)[1] in risk_ids
    if ref.startswith("design:"):
        return ref.split(":", 1)[1] in design_considerations
    if ref.startswith("technical:"):
        field = ref.split(":", 1)[1]
        return field in (analysis.get("technical_context") or {})
    if ref.startswith("problem:"):
        field = ref.split(":", 1)[1]
        return field in (analysis.get("problem_statement") or {})
    if ref.startswith("feasibility:"):
        area = ref.split(":", 1)[1]
        return area in {x.get("area") for x in analysis.get("feasibility_assessment", []) or []}
    if ref.startswith("comparison:"):
        dim_id = ref.split(":", 1)[1]
        return dim_id in {d.get("id") for d in (analysis.get("comparison_matrix") or {}).get("dimensions", []) or []}
    return ref in candidate_ids or ref in risk_ids or ref in design_considerations


BARE_SHA_RE = re.compile(r"[a-f0-9]{64}")
VERSIONED_REF_RE = re.compile(
    r"(?!.*(?:^|/)\.\.?(?:/|@))"
    r"(?!(?:.*[a-f0-9]{64}){2})"
    r"(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+"
    r"@(?:0|[1-9][0-9]*)"
    r"#(?P<sha>[a-f0-9]{64})"
)


def artifact_sha(ref):
    """Return SHA-256 only for a full canonical bare or path@version#sha reference."""
    if not isinstance(ref, str):
        return None
    if BARE_SHA_RE.fullmatch(ref):
        return ref
    match = VERSIONED_REF_RE.fullmatch(ref)
    if match:
        # The full structure was validated before extracting the terminal digest.
        return match.group("sha")
    return None


def is_requirements_ref(ref, analysis):
    req = analysis.get("source_requirements_ref")
    if not isinstance(req, dict) or not isinstance(ref, str):
        return False
    if ref in {req.get("path"), ref_key(req)}:
        return True
    sha = artifact_sha(ref)
    req_sha = req.get("sha256")
    return bool(sha and req_sha and sha == req_sha)


def resolved_evidence_exists(ref, analysis):
    # Resolution evidence must carry an immutable SHA-256 identity.
    if not artifact_sha(ref):
        return False
    if is_requirements_ref(ref, analysis):
        return False
    evidence = set()
    # Statements and ordinary source registrations are not resolution evidence.
    for fact in analysis.get("facts", []) or []:
        evidence.update(fact.get("evidence_refs", []) or [])
    for candidate in analysis.get("candidate_solutions", []) or []:
        evidence.update(candidate.get("evidence_refs", []) or [])
    for risk in analysis.get("risk_assessment", []) or []:
        evidence.update(risk.get("evidence_refs", []) or [])
    return bool(ref) and ref in evidence


def retained_actual(item, analysis, input_req):
    source_type = item.get("source_type")
    source_id = item.get("source_id")
    problem = analysis.get("problem_statement") or {}
    technical = analysis.get("technical_context") or {}
    next_steps = analysis.get("next_steps") or {}
    candidates = analysis.get("candidate_solutions", []) or []
    if source_type == "unknown":
        return source_id in {x.get("id") for x in analysis.get("unknowns", []) or []}
    if source_type == "assumption":
        return source_id in {x.get("id") for x in analysis.get("assumptions", []) or []}
    if source_type == "non_goal":
        return source_id in (problem.get("non_goals", []) or [])
    if source_type == "open_question":
        questions = []
        questions.extend(next_steps.get("blocking_questions", []) or [])
        questions.extend(next_steps.get("non_blocking_questions", []) or [])
        upstream_question = None
        if isinstance(input_req, dict):
            for q in input_req.get("open_questions", []) or []:
                if q.get("id") == source_id:
                    upstream_question = q.get("question")
                    break
        return (upstream_question in questions if upstream_question else False) or source_id in questions
    if source_type == "constraint":
        return source_id in (problem.get("constraints", []) or []) or source_id in (technical.get("known_limitations", []) or [])
    if source_type == "dependency":
        if source_id in (technical.get("technical_dependencies", []) or []):
            return True
        return any(source_id in (c.get("dependencies", []) or []) for c in candidates)
    if source_type == "acceptance_criterion":
        considerations = next_steps.get("design_considerations", []) or []
        prefix = source_id + ":"
        return any(
            isinstance(value, str)
            and value.startswith(prefix)
            and bool(value[len(prefix):].strip())
            for value in considerations
        )
    if source_type in {"functional_requirement", "non_functional_requirement"}:
        return any(source_id in (c.get("applicable_requirements", []) or []) for c in candidates) or \
            source_id in (next_steps.get("design_considerations", []) or [])
    if source_type == "source_ref":
        return source_id in {ref_key(x) for x in analysis.get("source_refs", []) or []}
    return False


def traceability_errors(analysis, input_obj):
    if not isinstance(analysis, dict):
        return []
    trace = analysis.get("requirements_traceability")
    if not isinstance(trace, dict) or not isinstance(trace.get("items"), list):
        return ["requirements_traceability missing"]
    errs = []
    trace_items = trace.get("items") or []
    seen = set()
    candidate_ids = {c.get("solution_id") for c in analysis.get("candidate_solutions", []) or []}
    risk_ids = {r.get("risk_id") for r in analysis.get("risk_assessment", []) or []}
    design_considerations = set((analysis.get("next_steps") or {}).get("design_considerations", []) or [])
    input_req = input_obj.get("requirements") if isinstance(input_obj, dict) else None
    required = upstream_items(input_req) if isinstance(input_req, dict) else set()
    for item in trace_items:
        key = (item.get("source_type"), item.get("source_id"))
        if key in seen:
            errs.append(f"duplicate trace item {key}")
        seen.add(key)
        if required and key not in required:
            errs.append(f"trace item {key} is not an upstream item")
        disposition = item.get("disposition")
        refs = item.get("analysis_refs", []) or []
        if disposition in {"analyzed", "mapped"}:
            if not refs:
                errs.append(f"{disposition} trace item {key} requires analysis_refs")
            for ref in refs:
                if not analysis_ref_exists(ref, analysis, candidate_ids, risk_ids, design_considerations):
                    errs.append(f"trace item {key} references unknown analysis object {ref}")
        if disposition == "mapped":
            # Mapped must point at a concrete analysis object, not a free string.
            if not any(ref.startswith(("solution:", "risk:", "design:")) or ref in candidate_ids or ref in risk_ids or ref in design_considerations for ref in refs):
                errs.append(f"mapped trace item {key} needs candidate/risk/design reference")
        if disposition == "retained" and not retained_actual(item, analysis, input_req):
            errs.append(f"retained trace item {key} has no actual retained content")
        if disposition == "resolved":
            evidence_refs = item.get("resolution_evidence_refs", []) or []
            if not evidence_refs:
                errs.append(f"resolved trace item {key} requires resolution_evidence_refs")
            for ref in evidence_refs:
                if not resolved_evidence_exists(ref, analysis):
                    errs.append(f"resolved trace item {key} has unverifiable evidence {ref}")
        if disposition in {"not_applicable", "deferred"}:
            if not item.get("rationale"):
                errs.append(f"trace item {key} requires rationale for {disposition}")
    if isinstance(input_req, dict):
        missing = required - seen
        if missing:
            errs.append(f"upstream items not traced: {sorted(missing)}")
    return errs


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

    # F2: apply the same source binding rule to every status that carries analysis.
    source_ref = analysis.get("source_requirements_ref")
    if isinstance(input_obj, dict):
        input_ref = input_obj.get("requirements_ref")
        if isinstance(input_ref, dict) and source_ref != input_ref:
            errs.append(f"{label}: source_requirements_ref does not match input requirements_ref")

    trace = analysis.get("requirements_traceability")
    if obj.get("status") == "ok":
        artifacts = obj.get("artifacts", []) or []
        if not any(a.get("type") == "analysis" for a in artifacts):
            errs.append(f"{label}: ok output requires an analysis artifact")
        errs.extend(traceability_errors(analysis, input_obj))
    elif isinstance(trace, dict):
        errs.extend(traceability_errors(analysis, input_obj))

    if obj.get("status") != "ok":
        return errs

    required = [
        "analysis_id", "analysis_version", "source_requirements_ref", "problem_statement",
        "technical_context", "candidate_solutions", "feasibility_assessment", "risk_assessment",
        "comparison_matrix", "recommendation", "next_steps", "requirements_traceability",
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

    if isinstance(input_obj, dict):
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
ref_item_schema = output_schema["$defs"]["traceItem"]["properties"]["resolution_evidence_refs"]["items"]
ref_validator = Draft202012Validator(ref_item_schema)

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
    out_ref = (obj.get("data", {}).get("analysis", {}) or {}).get("source_requirements_ref")
    matching_input = next(
        (x for x in input_objects.values() if ref_key(x.get("requirements_ref")) == ref_key(out_ref)),
        None,
    )
    sem = validate_analysis_output(obj, path.name, matching_input)
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
expect_schema_invalid("analysis-missing-traceability", lambda a: a.pop("requirements_traceability"))
expect_schema_invalid(
    "analysis-trace-not-applicable-no-rationale",
    lambda a: a["requirements_traceability"]["items"][0].update({"disposition": "not_applicable"}))
expect_schema_invalid(
    "analysis-trace-analyzed-no-refs",
    lambda a: next(i for i in a["requirements_traceability"]["items"] if i.get("disposition") == "analyzed").update({"analysis_refs": []}))
expect_schema_invalid(
    "analysis-trace-resolved-no-evidence",
    lambda a: a["requirements_traceability"]["items"][0].update({"disposition": "resolved", "resolution_evidence_refs": []}))
expect_schema_invalid(
    "analysis-trace-deferred-no-rationale",
    lambda a: a["requirements_traceability"]["items"][0].update({"disposition": "deferred"}))
expect_schema_invalid(
    "analysis-trace-resolved-suffix",
    lambda a: a["requirements_traceability"]["items"][0].update({
        "disposition": "resolved",
        "resolution_evidence_refs": ["path@1#" + "1" * 64 + "x"],
    }))
expect_schema_invalid(
    "analysis-trace-resolved-uppercase",
    lambda a: a["requirements_traceability"]["items"][0].update({
        "disposition": "resolved",
        "resolution_evidence_refs": ["path@1#" + "A" * 64],
    }))
expect_schema_invalid(
    "analysis-trace-resolved-fake-prefix",
    lambda a: a["requirements_traceability"]["items"][0].update({
        "disposition": "resolved",
        "resolution_evidence_refs": ["a" * 64 + "/fake@1#" + "1" * 64],
    }))

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

# F1: upstream Requirements traceability for every key category.
f1_negative_cases = 0
f1_positive_cases = 0
full_input = input_objects.get("example-input.json")
for source_type, label in (
    ("dependency", "analysis-trace-drop-dependency"),
    ("unknown", "analysis-trace-drop-nonblocking-unknown"),
    ("acceptance_criterion", "analysis-trace-drop-acceptance"),
    ("functional_requirement", "analysis-trace-drop-fr"),
    ("non_functional_requirement", "analysis-trace-drop-nfr"),
    ("non_goal", "analysis-trace-drop-non-goal"),
    ("constraint", "analysis-trace-drop-constraint"),
):
    def remove_trace(a, st=source_type):
        a["requirements_traceability"]["items"] = [
            item for item in a["requirements_traceability"]["items"]
            if item.get("source_type") != st
        ]
    expect_semantic_failure(label, remove_trace, full_input)
    f1_negative_cases += 1

def mapped_without_refs(a):
    for item in a["requirements_traceability"]["items"]:
        if item.get("disposition") == "mapped":
            item["analysis_refs"] = []
            return

expect_semantic_failure("analysis-trace-mapped-without-refs", mapped_without_refs, full_input)
f1_negative_cases += 1

trace_positive = copy.deepcopy(base)
for item in trace_positive["data"]["analysis"]["requirements_traceability"]["items"]:
    if item.get("source_type") == "non_goal":
        item.update({"disposition": "not_applicable", "rationale": "该非目标不影响本次分析"})
        break
trace_positive_errs = validate_analysis_output(trace_positive, "analysis-trace-positive-not-applicable", full_input)
check(not trace_positive_errs, f"analysis-trace-positive-not-applicable: {trace_positive_errs[:3]}")
if not trace_positive_errs:
    f1_positive_cases += 1

# F2: disposition semantics must close the loop to actual analysis content.
trace_negative_cases = 0
trace_positive_cases = 0


def expect_trace_failure(label, mutate):
    global trace_negative_cases
    expect_semantic_failure(label, mutate, full_input)
    trace_negative_cases += 1


expect_trace_failure("trace-retained-unknown-missing", lambda a: a.update({"unknowns": []}))
expect_trace_failure("trace-retained-assumption-missing", lambda a: a.update({"assumptions": []}))
expect_trace_failure(
    "trace-retained-non-goal-missing",
    lambda a: a["problem_statement"].update({"non_goals": []}))
expect_trace_failure(
    "trace-retained-open-question-missing",
    lambda a: a["next_steps"].update({"blocking_questions": [], "non_blocking_questions": []}))


def retained_dependency_without_content(a):
    for item in a["requirements_traceability"]["items"]:
        if item.get("source_type") == "dependency":
            item["disposition"] = "retained"
            item.pop("analysis_refs", None)
    a["technical_context"]["technical_dependencies"] = []
    for candidate in a["candidate_solutions"]:
        candidate["dependencies"] = []


expect_trace_failure("trace-retained-dependency-missing", retained_dependency_without_content)


def mapped_acceptance_missing_ref(a):
    for item in a["requirements_traceability"]["items"]:
        if item.get("source_type") == "acceptance_criterion":
            item["analysis_refs"] = ["SOL-MISSING"]


expect_trace_failure("trace-mapped-acceptance-missing-ref", mapped_acceptance_missing_ref)

resolved_positive = copy.deepcopy(base)
resolved_independent_ref = "docs/evidence/independent-facts.md@1#" + "d" * 64
resolved_positive["data"]["analysis"]["facts"][0]["evidence_refs"].append(resolved_independent_ref)
for item in resolved_positive["data"]["analysis"]["requirements_traceability"]["items"]:
    if item.get("source_type") == "non_goal":
        item.update({
            "disposition": "resolved",
            "resolution_evidence_refs": [resolved_independent_ref],
        })
        break
resolved_errs = validate_analysis_output(resolved_positive, "trace-resolved-with-evidence", full_input)
check(not resolved_errs, f"trace-resolved-with-evidence: {resolved_errs[:3]}")
if not resolved_errs:
    trace_positive_cases += 1

deferred_positive = copy.deepcopy(base)
for item in deferred_positive["data"]["analysis"]["requirements_traceability"]["items"]:
    if item.get("source_type") == "non_goal":
        item.update({"disposition": "deferred", "rationale": "该非目标在后续迭代处理"})
        break
deferred_errs = validate_analysis_output(deferred_positive, "trace-deferred-with-rationale", full_input)
check(not deferred_errs, f"trace-deferred-with-rationale: {deferred_errs[:3]}")
if not deferred_errs:
    trace_positive_cases += 1

# F3-A: resolved evidence must be an explicit reference, never a statement.
resolved_negative_cases = 0
resolved_positive_cases = 0


def resolved_output(ref):
    obj = copy.deepcopy(base)
    for item in obj["data"]["analysis"]["requirements_traceability"]["items"]:
        if item.get("source_type") == "non_goal":
            item.update({"disposition": "resolved", "resolution_evidence_refs": [ref]})
            break
    return obj


def expect_resolved_failure(label, ref):
    global resolved_negative_cases
    errs = validate_analysis_output(resolved_output(ref), label, full_input)
    check(bool(errs), f"{label}: expected unresolved/invalid evidence rejection")
    if errs:
        resolved_negative_cases += 1


def resolved_with_evidence(kind, ref):
    obj = resolved_output(ref)
    a = obj["data"]["analysis"]
    if kind == "facts":
        a["facts"][0]["evidence_refs"].append(ref)
    elif kind == "candidate":
        a["candidate_solutions"][0]["evidence_refs"].append(ref)
    elif kind == "risk":
        a["risk_assessment"][0]["evidence_refs"].append(ref)
    return obj


expect_resolved_failure("resolved-user-stated-statement", "需求要求组合筛选。")
expect_resolved_failure("resolved-assumption-statement", "现有查询接口可以安全增加过滤参数。")
expect_resolved_failure("resolved-missing-ref", "missing-evidence-ref")
only_statement = resolved_output("only a statement")
only_statement["data"]["analysis"]["facts"] = [
    {"statement": "only a statement", "source_type": "user_stated", "evidence_refs": []}
]
only_statement_errs = validate_analysis_output(only_statement, "resolved-only-statement", full_input)
check(bool(only_statement_errs), "resolved-only-statement: expected rejection")
if only_statement_errs:
    resolved_negative_cases += 1

fact_ref = "docs/evidence/independent-facts.md@1#" + "d" * 64
candidate_ref = "docs/evidence/independent-candidate.md@1#" + "e" * 64
risk_ref = "docs/evidence/independent-risk.md@1#" + "f" * 64
bare_ref = "c" * 64
for label, kind, ref in (
    ("resolved-bare-sha-evidence", "facts", bare_ref),
    ("resolved-fact-evidence", "facts", fact_ref),
    ("resolved-candidate-evidence", "candidate", candidate_ref),
    ("resolved-risk-evidence", "risk", risk_ref),
):
    errs = validate_analysis_output(resolved_with_evidence(kind, ref), label, full_input)
    check(not errs, f"{label}: expected valid independent evidence: {errs[:3]}")
    if not errs:
        resolved_positive_cases += 1

# Requirements/source registrations cannot prove resolution.
req_ref = base["data"]["analysis"]["source_requirements_ref"]
req_sha = req_ref["sha256"]
req_path = req_ref["path"]
expect_resolved_failure("resolved-requirements-path", req_path)
expect_resolved_failure("resolved-requirements-ref-key", ref_key(req_ref))
expect_resolved_failure("resolved-requirements-hash", req_sha)
expect_resolved_failure(
    "resolved-requirements-same-sha-different-path",
    "other/path/requirements-copy.md@1#" + req_sha,
)
expect_resolved_failure(
    "resolved-requirements-same-sha-different-dir",
    "different/dir/file.md@1#" + req_sha,
)
expect_resolved_failure(
    "resolved-requirements-normalized-alias",
    req_path + "#" + req_sha,
)

alias_ref = "docs/copies/requirements-copy.md@1#" + req_sha
for label, kind in (
    ("resolved-requirements-alias-in-facts", "facts"),
    ("resolved-requirements-alias-in-candidate", "candidate"),
    ("resolved-requirements-alias-in-risk", "risk"),
):
    errs = validate_analysis_output(resolved_with_evidence(kind, alias_ref), label, full_input)
    check(bool(errs), f"{label}: expected Requirements alias rejection")
    if errs:
        resolved_negative_cases += 1

# F6-A: only canonical bare SHA-256 or path@version#sha256 is accepted.
# A 64-hex substring before the terminal digest must not be selected as the SHA.
expect_resolved_failure(
    "resolved-fake-sha-prefix",
    "a" * 64 + "/fake@1#" + req_sha,
)
expect_resolved_failure(
    "resolved-two-digests",
    "docs/copies/requirements-copy.md@1#" + "b" * 64 + "#" + req_sha,
)
expect_resolved_failure(
    "resolved-sha-not-terminal",
    "docs/copies/requirements-copy.md@1#" + req_sha + "/tail",
)
expect_resolved_failure(
    "resolved-digest-before-reference",
    "b" * 64 + "/docs/copies/requirements-copy.md@1#" + req_sha,
)
expect_resolved_failure(
    "resolved-sha-extra-suffix",
    "docs/copies/requirements-copy.md@1#" + req_sha + "x",
)
expect_resolved_failure(
    "resolved-missing-digest",
    "docs/copies/requirements-copy.md@1#",
)
expect_resolved_failure(
    "resolved-repeated-digest",
    "docs/copies/requirements-copy.md@1#" + req_sha + "#" + req_sha,
)
expect_resolved_failure(
    "resolved-mixed-case-digest",
    "docs/copies/requirements-copy.md@1#" + "A" * 32 + "b" * 32,
)

# F7: strict reference grammar, shared Schema/parser vectors, and fail-closed checks.
ind_sha = "b" * 64
f7_valid_ref = "docs/evidence.md@1#" + ind_sha
f7_required_negatives = (
    ("resolved-extra-hash-in-path", "docs/evidence.md#extra@1#" + ind_sha),
    ("resolved-extra-at-sign", "docs/evidence@extra.md@1#" + ind_sha),
    ("resolved-empty-path", "@1#" + ind_sha),
    ("resolved-path-trailing-slash", "docs/evidence/@1#" + ind_sha),
    ("resolved-version-leading-zero", "docs/evidence.md@01#" + ind_sha),
    ("resolved-valid-ref-with-LF", f7_valid_ref + "\n"),
    ("resolved-valid-ref-with-CR", f7_valid_ref + "\r"),
    ("resolved-valid-ref-with-space", f7_valid_ref + " "),
    ("resolved-valid-ref-with-Tab", f7_valid_ref + "\t"),
    ("resolved-extra-char-before-sha", "docs/evidence.md@1#x" + ind_sha),
    ("resolved-extra-char-after-sha", f7_valid_ref + "x"),
    ("resolved-second-digest-in-path", "a" * 64 + "/docs/evidence.md@1#" + ind_sha),
)
f7_additional_negatives = (
    ("resolved-leading-slash-path", "/docs/evidence.md@1#" + ind_sha),
    ("resolved-double-slash-path", "docs//evidence.md@1#" + ind_sha),
    ("resolved-dot-segment", "docs/./evidence.md@1#" + ind_sha),
    ("resolved-dotdot-segment", "docs/../evidence.md@1#" + ind_sha),
)
f7_negative_cases = 0
f7_negative_passed = 0
for label, ref in f7_required_negatives + f7_additional_negatives:
    expect_resolved_failure(label, ref)
    schema_ok = ref_validator.is_valid(ref)
    parser_sha = artifact_sha(ref)
    evidence_ok = resolved_evidence_exists(
        ref, resolved_with_evidence("facts", ref)["data"]["analysis"]
    )
    identity_ok = is_requirements_ref(ref, base["data"]["analysis"])
    check(not schema_ok, f"{label}: Schema must reject non-canonical ref")
    check(parser_sha is None, f"{label}: artifact_sha must return None")
    check(not evidence_ok, f"{label}: resolved_evidence_exists must fail closed")
    check(not identity_ok, f"{label}: non-canonical ref must not match Requirements identity")
    f7_negative_cases += 1
    if not schema_ok and parser_sha is None and not evidence_ok and not identity_ok:
        f7_negative_passed += 1

f7_vectors = (
    ("bare-sha", ind_sha, True),
    ("versioned-simple", f7_valid_ref, True),
    ("versioned-zero", "docs/evidence/facts.md@0#" + ind_sha, True),
    ("versioned-multi-segment", "a/b_c-d.e/f@12#" + ind_sha, True),
    ("versioned-hidden-file", "docs/.evidence@1#" + ind_sha, True),
    ("extra-hash-in-path", "docs/evidence.md#extra@1#" + ind_sha, False),
    ("extra-at-in-path", "docs/evidence@extra.md@1#" + ind_sha, False),
    ("empty-path", "@1#" + ind_sha, False),
    ("leading-slash-path", "/docs/evidence.md@1#" + ind_sha, False),
    ("trailing-slash-path", "docs/evidence/@1#" + ind_sha, False),
    ("double-slash-path", "docs//evidence.md@1#" + ind_sha, False),
    ("dot-segment", "docs/./evidence.md@1#" + ind_sha, False),
    ("dotdot-segment", "docs/../evidence.md@1#" + ind_sha, False),
    ("dot-terminal-segment", "docs/.@1#" + ind_sha, False),
    ("dotdot-terminal-segment", "docs/..@1#" + ind_sha, False),
    ("leading-zero-version", "docs/evidence.md@01#" + ind_sha, False),
    ("empty-version", "docs/evidence.md@#" + ind_sha, False),
    ("signed-version", "docs/evidence.md@+1#" + ind_sha, False),
    ("missing-at-version", "docs/evidence.md#" + ind_sha, False),
    ("trailing-LF", f7_valid_ref + "\n", False),
    ("trailing-CR", f7_valid_ref + "\r", False),
    ("trailing-space", f7_valid_ref + " ", False),
    ("trailing-Tab", f7_valid_ref + "\t", False),
    ("extra-before-sha", "docs/evidence.md@1#x" + ind_sha, False),
    ("extra-after-sha", f7_valid_ref + "x", False),
    ("second-digest-in-path", "a" * 64 + "/docs/evidence.md@1#" + ind_sha, False),
    ("missing-sha", "docs/evidence.md@1#", False),
    ("uppercase-sha", "docs/evidence.md@1#" + ind_sha.upper(), False),
    ("mixed-case-sha", "docs/evidence.md@1#" + "A" * 32 + "b" * 32, False),
    ("non-string", None, False),
)
f7_vector_count = len(f7_vectors)
f7_vector_passed = 0
for label, ref, expected in f7_vectors:
    schema_ok = ref_validator.is_valid(ref)
    parser_ok = artifact_sha(ref) is not None
    check(schema_ok == expected, f"F7 vector {label}: Schema expected {expected}, got {schema_ok}")
    check(parser_ok == expected, f"F7 vector {label}: parser expected {expected}, got {parser_ok}")
    check(schema_ok == parser_ok, f"F7 vector {label}: Schema/parser disagree")
    if schema_ok == parser_ok == expected:
        f7_vector_passed += 1

f7_identity_positive = 0
for label, ref in (
    ("requirements-path", req_path),
    ("requirements-ref-key", ref_key(req_ref)),
    ("requirements-bare-sha", req_sha),
    ("requirements-same-sha-different-path", "other/path/requirements-copy.md@7#" + req_sha),
):
    ok = is_requirements_ref(ref, base["data"]["analysis"])
    check(ok, f"F7 identity {label}: expected Requirements identity match")
    if ok:
        f7_identity_positive += 1

multi_sha_alias = "a" * 64 + "/docs/copies/requirements-copy.md@1#" + req_sha
for label, kind in (
    ("resolved-multi-sha-alias-in-facts", "facts"),
    ("resolved-multi-sha-alias-in-candidate", "candidate"),
    ("resolved-multi-sha-alias-in-risk", "risk"),
):
    errs = validate_analysis_output(resolved_with_evidence(kind, multi_sha_alias), label, full_input)
    check(bool(errs), f"{label}: expected multi-SHA alias rejection")
    if errs:
        resolved_negative_cases += 1

ordinary_ref = {
    "path": "docs/notes/background.md",
    "version": 1,
    "sha256": "9" * 64,
    "type": "report",
}
background = resolved_output("docs/notes/background.md")
background["data"]["analysis"]["source_refs"].append(ordinary_ref)
background_errs = validate_analysis_output(background, "resolved-ordinary-source-ref", full_input)
check(bool(background_errs), "resolved-ordinary-source-ref: expected rejection")
if background_errs:
    resolved_negative_cases += 1

source_only = resolved_output(ref_key(ordinary_ref))
source_only["data"]["analysis"]["source_refs"].append(ordinary_ref)
source_only_errs = validate_analysis_output(source_only, "resolved-source-registration-only", full_input)
check(bool(source_only_errs), "resolved-source-registration-only: expected rejection")
if source_only_errs:
    resolved_negative_cases += 1

# F3-B: Acceptance Criterion retained must map to a concrete design consideration.
acceptance_negative_cases = 0
acceptance_positive_cases = 0


def acceptance_retained_output(design_considerations):
    obj = copy.deepcopy(base)
    for item in obj["data"]["analysis"]["requirements_traceability"]["items"]:
        if item.get("source_type") == "acceptance_criterion":
            item["disposition"] = "retained"
            item.pop("analysis_refs", None)
            break
    obj["data"]["analysis"]["next_steps"]["design_considerations"] = design_considerations
    return obj


acceptance_ok = acceptance_retained_output(["AC-1: 组合筛选验收标准需映射到测试设计"])
acceptance_errs = validate_analysis_output(acceptance_ok, "acceptance-retained-design-consideration", full_input)
check(not acceptance_errs, f"acceptance-retained-design-consideration: {acceptance_errs[:3]}")
if not acceptance_errs:
    acceptance_positive_cases += 1

for label, considerations in (
    ("acceptance-retained-exact-id-only", ["AC-1"]),
    ("acceptance-retained-empty-consideration", ["AC-1:"]),
    ("acceptance-retained-whitespace-consideration", ["AC-1:   "]),
    ("acceptance-retained-other-ac", ["AC-2: 无关考虑"]),
    ("acceptance-retained-missing-consideration", []),
    ("acceptance-retained-unrelated-consideration", ["其他设计考虑"]),
):
    errs = validate_analysis_output(acceptance_retained_output(considerations), label, full_input)
    check(bool(errs), f"{label}: expected missing/unrelated consideration rejection")
    if errs:
        acceptance_negative_cases += 1

# F2: source binding on all statuses, not only ok.
partial_input = load_json(SKILL / "examples" / "example-input-partial.json")
partial_output = load_json(SKILL / "examples" / "example-output-partial.json")
f2_cases = 0

def expect_no_semantic_errors(label, obj, inp=None):
    global f2_cases
    errs = validate_analysis_output(obj, label, inp)
    check(not errs, f"{label}: unexpected semantic errors: {errs[:3]}")
    if not errs:
        f2_cases += 1


def expect_semantic_errors(label, obj, inp=None):
    global f2_cases
    errs = validate_analysis_output(obj, label, inp)
    check(bool(errs), f"{label}: expected semantic failure")
    if errs:
        f2_cases += 1


expect_no_semantic_errors("needs-input-source-consistent", partial_output, partial_input)
bad_partial = copy.deepcopy(partial_output)
bad_partial["data"]["analysis"]["source_requirements_ref"]["path"] = "artifacts/wrong/requirements.md"
expect_semantic_errors("needs-input-source-inconsistent", bad_partial, partial_input)
blocked = copy.deepcopy(partial_output)
blocked["status"] = "blocked"
blocked["data"] = {"blocked_reason": "上游存在阻塞问题", "analysis": copy.deepcopy(partial_output["data"]["analysis"])}
expect_no_semantic_errors("blocked-source-consistent", blocked, partial_input)
blocked_bad = copy.deepcopy(blocked)
blocked_bad["data"]["analysis"]["source_requirements_ref"]["sha256"] = "f" * 64
expect_semantic_errors("blocked-source-inconsistent", blocked_bad, partial_input)
approval = copy.deepcopy(partial_output)
approval["status"] = "needs_approval"
approval["data"] = {
    "approval_request": {"gate_or_sa": "G2", "reason": "需要审批", "impact": "范围", "rollback": "回退"},
    "analysis": copy.deepcopy(partial_output["data"]["analysis"]),
}
approval["data"]["analysis"]["source_requirements_ref"]["version"] = 99
expect_semantic_errors("needs-approval-source-inconsistent", approval, partial_input)
ok_bad = copy.deepcopy(base)
ok_bad["data"]["analysis"]["source_requirements_ref"]["sha256"] = "e" * 64
expect_semantic_errors("ok-source-inconsistent", ok_bad, full_input)
failed_with_analysis = {
    "status": "failed",
    "data": {"analysis": copy.deepcopy(partial_output["data"]["analysis"])},
    "artifacts": [],
    "errors": [{"code": "internal_error", "message": "分析失败"}],
    "evidence": [],
}
expect_no_semantic_errors("failed-source-consistent", failed_with_analysis, partial_input)
expect_no_semantic_errors("partial-without-artifact", partial_output, partial_input)

# F3: ok status requires a real analysis artifact.
f3_cases = 0
for label, mutate in (
    ("analysis-ok-no-artifact", lambda o: o.update({"artifacts": []})),
    ("analysis-ok-wrong-artifact-type", lambda o: o["artifacts"][0].update({"type": "report"})),
):
    obj = copy.deepcopy(base)
    mutate(obj)
    errs = validate_analysis_output(obj, label, full_input)
    check(bool(errs), f"{label}: expected semantic failure")
    if errs:
        f3_cases += 1

if errors:
    print("ANALYSIS VALIDATION FAILED")
    for e in errors:
        print("-", e)
    raise SystemExit(1)

print("ANALYSIS VALIDATION PASSED")
print(f"schemas=2 input_examples={len(input_files)} output_examples={len(output_files)}")
print(f"input_positive={input_positive} output_positive={output_positive} cases={len(case_list)} invalid_cases={len(invalid_list)}")
print(f"schema_negative={schema_negative[0]} semantic_negative={semantic_negative[0]}")
print(f"f1_negative={f1_negative_cases} f1_positive={f1_positive_cases} f2_cases={f2_cases} f3_cases={f3_cases}")
print(f"trace_negative={trace_negative_cases} trace_positive={trace_positive_cases}")
print(f"resolved_negative={resolved_negative_cases} resolved_positive={resolved_positive_cases}")
print(f"f7_negative={f7_negative_cases} f7_negative_passed={f7_negative_passed}")
print(f"f7_vectors={f7_vector_count} f7_vectors_passed={f7_vector_passed} f7_identity_positive={f7_identity_positive}")
print(f"acceptance_retained_negative={acceptance_negative_cases} acceptance_retained_positive={acceptance_positive_cases}")
print("runtime_behavior=NOT_EXECUTED")
