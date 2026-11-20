#!/usr/bin/env python3
"""Structural validation for the P1-001 reference skill.

This is not a Skill runtime. It validates metadata, manifests, schemas,
examples and test-case declarations against the P1 standards.
"""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "requirements-clarity"
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(instance, schema, path="$"):
    t = schema.get("type")
    if t == "object":
        check(isinstance(instance, dict), f"{path}: expected object")
        if not isinstance(instance, dict):
            return
        for key in schema.get("required", []):
            check(key in instance, f"{path}: missing required '{key}'")
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, value in instance.items():
            if key in props:
                validate(value, props[key], f"{path}.{key}")
            elif extra is False:
                check(False, f"{path}: unexpected '{key}'")
    elif t == "array":
        check(isinstance(instance, list), f"{path}: expected array")
        if not isinstance(instance, list):
            return
        if "minItems" in schema:
            check(len(instance) >= schema["minItems"], f"{path}: minItems")
        if "items" in schema:
            for i, item in enumerate(instance):
                validate(item, schema["items"], f"{path}[{i}]")
    elif t == "string":
        check(isinstance(instance, str), f"{path}: expected string")
        if isinstance(instance, str):
            if "minLength" in schema:
                check(len(instance) >= schema["minLength"], f"{path}: minLength")
            if "pattern" in schema:
                check(re.search(schema["pattern"], instance), f"{path}: pattern")
            if "enum" in schema:
                check(instance in schema["enum"], f"{path}: enum")
    elif t == "integer":
        check(isinstance(instance, int) and not isinstance(instance, bool), f"{path}: expected integer")
        if isinstance(instance, int):
            if "minimum" in schema:
                check(instance >= schema["minimum"], f"{path}: minimum")
    elif t == "boolean":
        check(isinstance(instance, bool), f"{path}: expected boolean")


# 1. SKILL.md frontmatter
text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
check(bool(m), "SKILL.md: missing frontmatter")
meta = yaml.safe_load(m.group(1)) if m else {}
check(meta.get("name") == "requirements-clarity", "SKILL.md: name mismatch")
check(bool(meta.get("description")), "SKILL.md: missing description")
allowed = {"name", "description", "requires"}
check(set(meta) <= allowed, f"SKILL.md: platform/unknown fields in core frontmatter: {set(meta) - allowed}")
requires = meta.get("requires", {})
check(set(requires) <= {"runtime", "tools", "permissions"}, "SKILL.md: unknown requires keys")

# 2. skill.yaml
manifest = load_yaml(SKILL / "skill.yaml")
check(manifest.get("name") == "requirements-clarity", "skill.yaml: name mismatch")
check(re.match(r"^\d+\.\d+\.\d+([-.+].*)?$", str(manifest.get("version", ""))), "skill.yaml: invalid SemVer")
check(manifest.get("status") in {"draft", "review", "tested", "published", "deprecated", "retired", "archived"}, "skill.yaml: invalid status")
check(manifest.get("schema_version") == 1, "skill.yaml: schema_version must be 1")

# 3. Schemas and examples
input_schema = load_json(SKILL / "schemas" / "input.schema.json")
output_schema = load_json(SKILL / "schemas" / "output.schema.json")
for name, schema in (("input", input_schema), ("output", output_schema)):
    check(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{name} schema: wrong $schema")
    check(schema.get("type") == "object", f"{name} schema: must be object")
    check(bool(schema.get("properties")), f"{name} schema: no properties")

example_input = load_json(SKILL / "examples" / "example-input.json")
example_output = load_json(SKILL / "examples" / "example-output.json")
validate(example_input, input_schema, "example-input")
validate(example_output, output_schema, "example-output")

# 4. Test cases
cases = load_yaml(SKILL / "tests" / "cases.yaml")
check(cases.get("skill") == "requirements-clarity", "tests: skill mismatch")
check(isinstance(cases.get("cases"), list) and len(cases["cases"]) >= 5, "tests: need at least 5 cases")
for i, case in enumerate(cases.get("cases", [])):
    check("name" in case and "input" in case and "expect" in case, f"tests[{i}]: missing fields")
    status = case.get("expect", {}).get("status")
    check(status in {"ok", "needs_input", "needs_approval", "blocked", "failed"}, f"tests[{i}]: invalid expected status")

# 5. Platform metadata
platform = load_yaml(ROOT / "platforms" / "openclaw" / "skill-metadata.yaml")
check(platform.get("platform") == "openclaw", "platform metadata: platform mismatch")
check("requirements-clarity" in platform.get("skills", {}), "platform metadata: missing reference skill")
entry = platform.get("skills", {}).get("requirements-clarity", {})
for key in ("discovery", "trigger", "requirements", "invocation", "approval"):
    check(key in entry, f"platform metadata: missing {key}")

if errors:
    print("REFERENCE SKILL VALIDATION FAILED")
    for e in errors:
        print("-", e)
    raise SystemExit(1)

print("REFERENCE SKILL VALIDATION PASSED")
print(f"cases={len(cases['cases'])} schemas=2 examples=2 platform_entries={len(platform['skills'])}")
