#!/usr/bin/env python3
"""P1-001 reference-skill validation.

Three separate layers are reported:
1. Structural/metadata checks.
2. JSON Schema Draft 2020-12 checks for every example and every case input.
3. SemVer 2.0.0 positive/negative checks.
Runtime Skill behavior is NOT executed or claimed as tested.
"""
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


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path):
    with path.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=UniqueKeyLoader)


def check_yaml_blocks(path):
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)```", text, re.S)
    for i, block in enumerate(blocks):
        try:
            list(yaml.load_all(block, Loader=UniqueKeyLoader))
        except Exception as e:
            errors.append(f"{path.name} yaml block {i + 1}: {e}")
    return len(blocks)


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
check(valid_semver(str(manifest.get("version", ""))), "skill.yaml: invalid SemVer")
check(manifest.get("status") in {"draft", "review", "tested", "published", "deprecated", "retired", "archived"}, "skill.yaml: invalid status")
check(manifest.get("compatibility", {}).get("requires_capabilities") == ["skill-discovery", "skill-metadata", "tool-invocation", "context-port", "artifact-port", "result-port"], "skill.yaml: capability registry mismatch")
req_caps = manifest.get("compatibility", {}).get("requires_capabilities", [])
opt_caps = manifest.get("compatibility", {}).get("optional_capabilities", [])
check(set(req_caps) <= REGISTRY, "skill.yaml: unknown required capability")
check(set(opt_caps) <= REGISTRY, "skill.yaml: unknown optional capability")
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
for path in example_inputs:
    errs = list(in_validator.iter_errors(load_json(path)))
    check(not errs, f"{path.name}: input example invalid: {errs[:2]}")
for path in example_outputs:
    errs = list(out_validator.iter_errors(load_json(path)))
    check(not errs, f"{path.name}: output example invalid: {errs[:2]}")

cases = load_yaml(SKILL / "tests" / "cases.yaml")
check(cases.get("skill") == "requirements-clarity", "tests: skill mismatch")
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
            check(out_obj.get("status") == status, f"tests[{name}]: output example status mismatch")
    executed_cases += 1

invalid = load_yaml(SKILL / "tests" / "invalid-cases.yaml")
invalid_list = invalid.get("invalid_cases", [])
for i, case in enumerate(invalid_list):
    errs = list(in_validator.iter_errors(case.get("input")))
    check(bool(errs), f"invalid-cases[{i}]: expected schema rejection, got valid input")

# 3. SemVer 2.0.0 positive/negative checks
semver_valid = ["0.1.0", "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-0.3.7", "1.0.0+build.1", "1.0.0-rc.1+build.5"]
semver_invalid = ["01.0.0", "1.0", "1.0.0-alpha..1", "1.0.0-01", "v1.0.0", "1.0.0+"]
for v in semver_valid:
    check(valid_semver(v), f"SemVer: should accept {v}")
for v in semver_invalid:
    check(not valid_semver(v), f"SemVer: should reject {v}")

# 4. Platform metadata
platform = load_yaml(ROOT / "platforms" / "openclaw" / "skill-metadata.yaml")
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

# 4c. YAML examples in standards must parse and have no duplicate keys
yaml_blocks = 0
for path in (ROOT / "docs" / "standards").glob("*.md"):
    yaml_blocks += check_yaml_blocks(path)

if errors:
    print("REFERENCE SKILL VALIDATION FAILED")
    for e in errors:
        print("-", e)
    raise SystemExit(1)

print("REFERENCE SKILL VALIDATION PASSED")
print(f"structure=passed schema=Draft202012 examples_in={len(example_inputs)} examples_out={len(example_outputs)}")
print(f"cases_input_validated={len(case_list)} invalid_cases_rejected={len(invalid_list)}")
print(f"semver_valid={len(semver_valid)} semver_invalid={len(semver_invalid)}")
print(f"yaml_blocks_checked={yaml_blocks} registry_ids={len(REGISTRY)}")
print(f"runtime_behavior=NOT_EXECUTED platform_entries={len(platform.get('skills', {}))}")
