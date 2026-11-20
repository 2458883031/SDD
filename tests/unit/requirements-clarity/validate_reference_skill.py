#!/usr/bin/env python3
"""P1-001 reference-skill validation.

Three separate layers are reported:
1. Structural/metadata checks.
2. JSON Schema Draft 2020-12 checks for every example and every case input.
3. SemVer 2.0.0 positive/negative checks.
Runtime Skill behavior is NOT executed or claimed as tested.
"""
import copy
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "requirements-clarity"
errors = []

REGISTRY = {
    "skill-discovery",
    "skill-metadata",
    "tool-invocation",
    "context-port",
    "artifact-port",
    "approval-port",
    "result-port",
}
REQUIRED_CAPS = (
    "skill-discovery",
    "skill-metadata",
    "tool-invocation",
    "context-port",
    "artifact-port",
    "result-port",
)
OPTIONAL_CAPS = {"approval-port"}


class UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys."""

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


def validate_optional_caps(value):
    """Validate an optional_capabilities list and return error strings."""
    if not isinstance(value, list):
        return ["optional_capabilities must be a list"]
    if not all(isinstance(cap, str) for cap in value):
        return ["optional_capabilities must contain only strings"]
    errs = []
    seen = set()
    duplicates = []
    for cap in value:
        if cap in seen and cap not in duplicates:
            duplicates.append(cap)
        seen.add(cap)
    if duplicates:
        errs.append(f"optional_capabilities contains duplicate IDs: {sorted(duplicates)}")
    unknown = seen - REGISTRY
    if unknown:
        errs.append(f"optional_capabilities contains unknown IDs: {sorted(unknown)}")
    required_declared = seen & set(REQUIRED_CAPS)
    if required_declared:
        errs.append(f"optional_capabilities must not contain required capabilities: {sorted(required_declared)}")
    non_optional = seen - OPTIONAL_CAPS
    if non_optional:
        errs.append(f"optional_capabilities must only contain registered optional IDs: {sorted(non_optional)}")
    return errs


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path):
    with path.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=UniqueKeyLoader)


VAGUE_ACCEPTANCE_RE = re.compile(r"尽快|友好|高性能|尽可能|适当|良好|优秀|快速")


def validate_requirements_output(obj, label):
    """Semantic checks for Requirements output beyond JSON Schema."""
    errs = []
    if not isinstance(obj, dict):
        return [f"{label}: output must be an object"]
    data = obj.get("data")
    if isinstance(data, dict):
        for forbidden in ("confirmation_ref", "gate_approved", "confirmed_by"):
            if forbidden in data:
                errs.append(f"{label}: forbidden confirmation field {forbidden}")
    req = data.get("requirements") if isinstance(data, dict) else None
    if not isinstance(req, dict):
        return errs
    for forbidden in ("confirmation_ref", "gate_approved", "confirmed_by"):
        if forbidden in req:
            errs.append(f"{label}: forbidden confirmation field {forbidden} in requirements")

    for fr in req.get("functional_requirements", []) or []:
        if fr.get("source_type") == "evidence_backed" and not fr.get("evidence_refs"):
            errs.append(f"{label}: evidence-backed FR {fr.get('id')} missing evidence_refs")
    for nfr in req.get("non_functional_requirements", []) or []:
        if nfr.get("source_type") == "evidence_backed" and not nfr.get("evidence_refs"):
            errs.append(f"{label}: evidence-backed NFR {nfr.get('id')} missing evidence_refs")
        target = nfr.get("measurable_target", "")
        if isinstance(target, str) and VAGUE_ACCEPTANCE_RE.search(target):
            errs.append(f"{label}: NFR {nfr.get('id')} has vague measurable_target")
    for assumption in req.get("assumptions", []) or []:
        if assumption.get("status") != "unconfirmed":
            errs.append(f"{label}: assumption {assumption.get('id')} must remain unconfirmed")
        if not assumption.get("basis"):
            errs.append(f"{label}: assumption {assumption.get('id')} missing basis")

    if obj.get("status") == "ok":
        for item in req.get("unknowns", []) or []:
            if item.get("blocking") is True:
                errs.append(f"{label}: blocking unknown prevents status=ok")
        for item in req.get("open_questions", []) or []:
            if item.get("blocking") is True:
                errs.append(f"{label}: blocking open question prevents status=ok")
        for item in req.get("conflicts", []) or []:
            if item.get("status") == "open":
                errs.append(f"{label}: open conflict prevents status=ok")
        for item in req.get("ambiguities", []) or []:
            if item.get("status") == "open":
                errs.append(f"{label}: open ambiguity prevents status=ok")

    for criterion in req.get("acceptance_criteria", []) or []:
        if isinstance(criterion, str):
            text = criterion
            verification = None
        elif isinstance(criterion, dict):
            text = criterion.get("criterion", "")
            verification = criterion.get("verification")
            if not verification:
                errs.append(f"{label}: acceptance criterion {criterion.get('id')} missing verification")
        else:
            errs.append(f"{label}: acceptance criterion must be string or object")
            continue
        if not text:
            errs.append(f"{label}: empty acceptance criterion")
        elif VAGUE_ACCEPTANCE_RE.search(text):
            errs.append(f"{label}: vague acceptance criterion {text!r}")

    change = req.get("change_impact")
    if isinstance(change, dict):
        if not change.get("previous_ref"):
            errs.append(f"{label}: change_impact missing previous_ref")
        downstream = change.get("downstream_impact", {})
        if isinstance(downstream, dict) and any(downstream.values()) and not change.get("gate_invalidation"):
            errs.append(f"{label}: change_impact affects downstream but has no gate_invalidation")
    return errs


def expect_schema_invalid(validator, instance, label, counter):
    errs = list(validator.iter_errors(instance))
    check(bool(errs), f"{label}: expected schema rejection, got valid instance")
    if errs:
        counter[0] += 1


def validate_metadata_doc(doc, label):
    """Return semantic errors for a platform metadata document.

    Non-metadata YAML documents (frontmatter, snippets) return [].
    """
    if not isinstance(doc, dict) or "skills" not in doc or "platform" not in doc:
        return []
    errs = []
    skills = doc.get("skills")
    if not isinstance(skills, dict):
        return [f"{label}: skills must be a mapping"]
    for skill_name, entry in skills.items():
        if not isinstance(entry, dict):
            errs.append(f"{label}/{skill_name}: entry must be a mapping")
            continue
        caps = entry.get("capabilities")
        if not isinstance(caps, dict):
            errs.append(f"{label}/{skill_name}: missing capabilities")
        else:
            unknown = set(caps) - REGISTRY
            if unknown:
                errs.append(f"{label}/{skill_name}: unknown capability IDs {sorted(unknown)}")
            for cap in REQUIRED_CAPS:
                if caps.get(cap) is not True:
                    errs.append(f"{label}/{skill_name}: required capability {cap} missing/false")
            for cap, value in caps.items():
                if cap not in REGISTRY:
                    continue
                if not isinstance(value, bool):
                    errs.append(f"{label}/{skill_name}: capability {cap} must be boolean")
            if "approval-port" in caps and not isinstance(caps["approval-port"], bool):
                errs.append(f"{label}/{skill_name}: approval-port must be boolean")
        tools = entry.get("invocation", {}).get("tools") if isinstance(entry.get("invocation"), dict) else None
        if skill_name == "requirements-clarity" and tools != ["read"]:
            errs.append(f"{label}/{skill_name}: invocation.tools must be ['read']; got {tools!r}")
        if skill_name == "requirements-clarity" and isinstance(tools, list) and "write" in tools:
            errs.append(f"{label}/{skill_name}: write must not be exposed as a Skill Tool")
    return errs


def check_yaml_blocks(path):
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)```", text, re.S)
    metadata_examples = 0
    for i, block in enumerate(blocks):
        try:
            docs = list(yaml.load_all(block, Loader=UniqueKeyLoader))
        except Exception as e:
            errors.append(f"{path.name} yaml block {i + 1}: {e}")
            continue
        for doc in docs:
            errs = validate_metadata_doc(doc, f"{path.name} yaml block {i + 1}")
            if errs:
                errors.extend(errs)
            if isinstance(doc, dict) and "platform" in doc and "skills" in doc:
                metadata_examples += 1
    return len(blocks), metadata_examples


SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def valid_semver(v):
    return isinstance(v, str) and bool(SEMVER_RE.match(v))


# 1. Structural checks
text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
check(bool(m), "SKILL.md: missing frontmatter")
meta = yaml.safe_load(m.group(1)) if m else {}
check(meta.get("name") == "requirements-clarity", "SKILL.md: name mismatch")
check(bool(meta.get("description")), "SKILL.md: missing description")
check(set(meta) <= {"name", "description", "requires"}, "SKILL.md: platform/unknown fields in core frontmatter")
check(set(meta.get("requires", {})) <= {"runtime", "tools", "permissions"}, "SKILL.md: unknown requires keys")

manifest = load_yaml(SKILL / "skill.yaml")
check(manifest.get("name") == "requirements-clarity", "skill.yaml: name mismatch")
check(manifest.get("schema_version") == 1, "skill.yaml: schema_version must be 1")
check(manifest.get("version") == "0.2.0", "skill.yaml: version must be 0.2.0")
check(valid_semver(str(manifest.get("version", ""))), "skill.yaml: invalid SemVer")
check(manifest.get("status") in {"draft", "review", "tested", "published", "deprecated", "retired", "archived"}, "skill.yaml: invalid status")
check(manifest.get("compatibility", {}).get("requires_capabilities") == ["skill-discovery", "skill-metadata", "tool-invocation", "context-port", "artifact-port", "result-port"], "skill.yaml: capability registry mismatch")
req_caps = manifest.get("compatibility", {}).get("requires_capabilities", [])
opt_caps = manifest.get("compatibility", {}).get("optional_capabilities", [])
check(isinstance(req_caps, list), "skill.yaml: requires_capabilities must be a list")
if isinstance(req_caps, list):
    check(set(req_caps) <= REGISTRY, "skill.yaml: unknown required capability")
opt_errors = validate_optional_caps(opt_caps)
check(not opt_errors, "skill.yaml: invalid optional_capabilities: " + "; ".join(opt_errors))
check(manifest.get("dependencies", {}).get("tools") == ["file-read"], "skill.yaml: tool mapping must be file-read")

# 2. JSON Schema checks
input_schema = load_json(SKILL / "schemas" / "input.schema.json")
output_schema = load_json(SKILL / "schemas" / "output.schema.json")
in_validator = Draft202012Validator(input_schema)
out_validator = Draft202012Validator(output_schema)
for name, schema in (("input", input_schema), ("output", output_schema)):
    check(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{name} schema: wrong $schema")
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as e:
        errors.append(f"{name} schema: invalid Draft 2020-12 schema: {e}")

example_inputs = sorted((SKILL / "examples").glob("example-input*.json"))
example_outputs = sorted((SKILL / "examples").glob("example-output*.json"))
requirements_semantic_positive = 0
for path in example_inputs:
    errs = list(in_validator.iter_errors(load_json(path)))
    check(not errs, f"{path.name}: input example invalid: {errs[:2]}")
for path in example_outputs:
    obj = load_json(path)
    errs = list(out_validator.iter_errors(obj))
    check(not errs, f"{path.name}: output example invalid: {errs[:2]}")
    sem_errs = validate_requirements_output(obj, path.name)
    check(not sem_errs, f"{path.name}: semantic error: {sem_errs[:3]}")
    if not errs and not sem_errs:
        requirements_semantic_positive += 1

cases = load_yaml(SKILL / "tests" / "cases.yaml")
check(cases.get("skill") == "requirements-clarity", "tests: skill mismatch")
check(cases.get("version") == "0.2.0", "tests: version must be 0.2.0")
case_list = cases.get("cases", [])
check(isinstance(case_list, list) and len(case_list) >= 6, "tests: need at least 6 cases")
executed_cases = 0
for i, case in enumerate(case_list):
    name = case.get("name", f"case-{i}")
    inp = case.get("input")
    errs = list(in_validator.iter_errors(inp))
    check(not errs, f"tests[{name}]: input does not match input.schema.json: {errs[:2]}")
    expect = case.get("expect", {})
    status = expect.get("status")
    check(status in {"ok", "needs_input", "needs_approval", "blocked", "failed"}, f"tests[{name}]: invalid expected status")
    example_rel = expect.get("output_example")
    check(bool(example_rel), f"tests[{name}]: missing output_example")
    if example_rel:
        example_path = SKILL / example_rel
        check(example_path.exists(), f"tests[{name}]: output example missing: {example_rel}")
        if example_path.exists():
            out_obj = load_json(example_path)
            out_errs = list(out_validator.iter_errors(out_obj))
            check(not out_errs, f"tests[{name}]: output example invalid: {out_errs[:2]}")
            sem_errs = validate_requirements_output(out_obj, f"tests[{name}]")
            check(not sem_errs, f"tests[{name}]: output semantic error: {sem_errs[:3]}")
            check(out_obj.get("status") == status, f"tests[{name}]: output example status mismatch")
    executed_cases += 1

invalid = load_yaml(SKILL / "tests" / "invalid-cases.yaml")
invalid_list = invalid.get("invalid_cases", [])
for i, case in enumerate(invalid_list):
    errs = list(in_validator.iter_errors(case.get("input")))
    check(bool(errs), f"invalid-cases[{i}]: expected schema rejection, got valid input")

# 2b. Requirements-specific negative tests
structured_output = load_json(SKILL / "examples" / "example-output-structured.json")
change_output = load_json(SKILL / "examples" / "example-output-change.json")
negative_schema = [0]
negative_semantic = [0]


def expect_requirements_schema_invalid(label, mutate):
    obj = copy.deepcopy(structured_output)
    mutate(obj["data"]["requirements"])
    expect_schema_invalid(out_validator, obj, label, negative_schema)


def expect_requirements_semantic_failure(label, mutate):
    obj = copy.deepcopy(structured_output)
    mutate(obj["data"]["requirements"])
    errs = validate_requirements_output(obj, label)
    check(bool(errs), f"{label}: expected semantic failure, got pass")
    if errs:
        negative_semantic[0] += 1


expect_requirements_schema_invalid(
    "requirements-fr-missing-statement",
    lambda req: req["functional_requirements"][0].pop("statement"))
expect_requirements_schema_invalid(
    "requirements-fr-evidence-without-refs",
    lambda req: next(
        (fr for fr in req["functional_requirements"] if fr["source_type"] == "evidence_backed")
    ).update({"evidence_refs": []}))
expect_requirements_schema_invalid(
    "requirements-nfr-missing-target",
    lambda req: req["non_functional_requirements"][0].pop("measurable_target"))
expect_requirements_schema_invalid(
    "requirements-assumption-missing-basis",
    lambda req: req["assumptions"][0].pop("basis"))
expect_requirements_schema_invalid(
    "requirements-assumption-confirmed",
    lambda req: req["assumptions"][0].update({"status": "confirmed"}))
expect_requirements_schema_invalid(
    "requirements-open-question-missing-blocking",
    lambda req: req["open_questions"][0].pop("blocking"))
expect_requirements_schema_invalid(
    "requirements-dependency-missing-type",
    lambda req: req["dependencies"][0].pop("type"))
expect_requirements_schema_invalid(
    "requirements-source-ref-bad-sha",
    lambda req: req["source_refs"][0].update({"sha256": "not-a-sha"}))
expect_requirements_schema_invalid(
    "requirements-acceptance-missing-verification",
    lambda req: req["acceptance_criteria"][0].pop("verification"))
change_missing_previous = copy.deepcopy(change_output)
change_missing_previous["data"]["requirements"]["change_impact"].pop("previous_ref", None)
expect_schema_invalid(out_validator, change_missing_previous,
                      "requirements-change-missing-previous-ref", negative_schema)
expect_requirements_schema_invalid(
    "requirements-confirmation-ref-forbidden",
    lambda req: req.update({"confirmation_ref": "fake"}))
expect_requirements_schema_invalid(
    "requirements-unknown-field",
    lambda req: req.update({"unexpected_field": True}))
expect_requirements_schema_invalid(
    "requirements-version-invalid",
    lambda req: req.update({"requirements_version": "1.0"}))

expect_requirements_semantic_failure(
    "requirements-blocking-open-question",
    lambda req: req["open_questions"][0].update({"blocking": True}))
expect_requirements_semantic_failure(
    "requirements-blocking-unknown",
    lambda req: req["unknowns"][0].update({"blocking": True}))
expect_requirements_semantic_failure(
    "requirements-open-conflict",
    lambda req: req["conflicts"][0].update({"status": "open"}))
expect_requirements_semantic_failure(
    "requirements-open-ambiguity",
    lambda req: req["ambiguities"][0].update({"status": "open"}))
expect_requirements_semantic_failure(
    "requirements-vague-acceptance",
    lambda req: req["acceptance_criteria"].append("尽快完成"))
change_semantic = copy.deepcopy(change_output)

def mutate_change_gate(req):
    req["change_impact"]["gate_invalidation"] = []

change_semantic_req = change_semantic["data"]["requirements"]
mutate_change_gate(change_semantic_req)
errs = validate_requirements_output(change_semantic, "requirements-change-no-gate-invalidation")
check(bool(errs), "requirements-change-no-gate-invalidation: expected semantic failure")
if errs:
    negative_semantic[0] += 1

# Ensure the unfailed structured/change examples pass semantic validation.
check(not validate_requirements_output(structured_output, "structured-output"),
      "structured output should pass semantic validation")
check(not validate_requirements_output(change_output, "change-output"),
      "change output should pass semantic validation")


# 3. SemVer 2.0.0 positive/negative checks
semver_valid = ["0.1.0", "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-0.3.7", "1.0.0+build.1", "1.0.0-rc.1+build.5"]
semver_invalid = ["01.0.0", "1.0", "1.0.0-alpha..1", "1.0.0-01", "v1.0.0", "1.0.0+"]
for v in semver_valid:
    check(valid_semver(v), f"SemVer: should accept {v}")
for v in semver_invalid:
    check(not valid_semver(v), f"SemVer: should reject {v}")

# 4. Platform metadata
platform = load_yaml(ROOT / "platforms" / "openclaw" / "skill-metadata.yaml")
errors.extend(validate_metadata_doc(platform, "platforms/openclaw/skill-metadata.yaml"))
check(platform.get("platform") == "openclaw", "platform metadata: platform mismatch")
entry = platform.get("skills", {}).get("requirements-clarity", {})
for key in ("discovery", "trigger", "requirements", "invocation", "approval", "capabilities"):
    check(key in entry, f"platform metadata: missing {key}")
caps = entry.get("capabilities", {})
check(set(caps) <= REGISTRY, "platform metadata: unknown capability ID")
for cap in ("skill-discovery", "skill-metadata", "tool-invocation", "context-port", "artifact-port", "result-port"):
    check(caps.get(cap) is True, f"platform metadata: required capability {cap} not declared")
check(caps.get("approval-port") is False, "platform metadata: approval-port should be optional/false")
check(entry.get("invocation", {}).get("tools") == ["read"], "platform metadata: invocation.tools must expose only read (artifact writes via ContextPort)")

# 4b. Deprecated IDs in current normative files (historical reports excluded)
deprecated_files = [
    ROOT / "docs" / "standards" / "skill-standard.md",
    ROOT / "docs" / "standards" / "skill-metadata-standard.md",
    ROOT / "docs" / "standards" / "skill-io-contract.md",
    ROOT / "docs" / "standards" / "skill-security-standard.md",
    ROOT / "docs" / "standards" / "skill-versioning-standard.md",
    ROOT / "docs" / "architecture" / "platform-adapter-architecture.md",
    ROOT / "docs" / "architecture" / "platform-compatibility-matrix.md",
    ROOT / "docs" / "architecture" / "skill-architecture.md",
    SKILL / "skill.yaml",
    ROOT / "platforms" / "openclaw" / "skill-metadata.yaml",
]
for path in deprecated_files:
    txt = path.read_text(encoding="utf-8")
    check("tool-port" not in txt, f"{path.name}: deprecated capability ID tool-port found")

# 4c. YAML examples in standards must parse, have no duplicate keys,
# and metadata examples must pass semantic validation.
yaml_blocks = 0
metadata_examples = 0
for path in (ROOT / "docs" / "standards").glob("*.md"):
    count, examples = check_yaml_blocks(path)
    yaml_blocks += count
    metadata_examples += examples

# 4d. Negative metadata cases (must fail semantic validation)
negative_metadata_cases = 0
base_meta = copy.deepcopy(platform)

def expect_metadata_failure(case_name, mutate, label):
    global negative_metadata_cases
    doc = copy.deepcopy(base_meta)
    mutate(doc)
    errs = validate_metadata_doc(doc, label + "/" + case_name)
    check(bool(errs), f"negative metadata case '{case_name}' should fail but passed")
    if errs:
        negative_metadata_cases += 1

def entry(doc):
    return doc["skills"]["requirements-clarity"]

expect_metadata_failure("unknown-capability", lambda d: entry(d)["capabilities"].update({"unknown-cap": True}), "negative")
expect_metadata_failure("deprecated-tool-port", lambda d: entry(d)["capabilities"].update({"tool-port": True}), "negative")
expect_metadata_failure("missing-required-capability", lambda d: entry(d)["capabilities"].pop("result-port", None), "negative")
expect_metadata_failure("write-exposed-as-tool", lambda d: entry(d)["invocation"].update({"tools": ["read", "write"]}), "negative")

# duplicate YAML key must fail the loader
try:
    yaml.load("schema_version: 1\nplatform: openclaw\nplatform: openclaw\n", Loader=UniqueKeyLoader)
    check(False, "negative metadata case 'duplicate-key' should fail but passed")
except Exception:
    negative_metadata_cases += 1

# 4e. Optional capability classification (skill.yaml)
optional_positive_cases = 0
for value, case_name in (([], "empty"), (["approval-port"], "approval-port")):
    errs = validate_optional_caps(value)
    check(not errs, f"positive optional case '{case_name}' should pass: {errs}")
    if not errs:
        optional_positive_cases += 1

optional_negative_cases = 0

def expect_optional_failure(case_name, value, needle):
    global optional_negative_cases
    errs = validate_optional_caps(value)
    check(bool(errs), f"negative optional case '{case_name}' should fail but passed")
    check(any(needle in e for e in errs), f"negative optional case '{case_name}' missing error '{needle}': {errs}")
    if errs and any(needle in e for e in errs):
        optional_negative_cases += 1

for cap in REQUIRED_CAPS:
    expect_optional_failure(f"required-as-optional-{cap}", [cap], "required capabilities")
expect_optional_failure("unknown-id", ["unknown-cap"], "unknown IDs")
expect_optional_failure("wrong-type", "approval-port", "must be a list")
expect_optional_failure("duplicate-id", ["approval-port", "approval-port"], "duplicate IDs")

if errors:
    print("REFERENCE SKILL VALIDATION FAILED")
    for e in errors:
        print("-", e)
    raise SystemExit(1)

print("REFERENCE SKILL VALIDATION PASSED")
print(f"structure=passed schema=Draft202012 examples_in={len(example_inputs)} examples_out={len(example_outputs)}")
print(f"cases_input_validated={len(case_list)} invalid_cases_rejected={len(invalid_list)}")
print(f"semver_valid={len(semver_valid)} semver_invalid={len(semver_invalid)}")
print(f"yaml_blocks_checked={yaml_blocks} metadata_examples={metadata_examples} registry_ids={len(REGISTRY)}")
print(f"negative_metadata_cases_passed={negative_metadata_cases}")
print(f"optional_positive_cases_passed={optional_positive_cases} optional_negative_cases_passed={optional_negative_cases}")
print(f"requirements_semantic_positive={requirements_semantic_positive} requirements_schema_negative={negative_schema[0]} requirements_semantic_negative={negative_semantic[0]}")
print(f"runtime_behavior=NOT_EXECUTED platform_entries={len(platform.get('skills', {}))}")
