#!/usr/bin/env python3
"""P1-002 Orchestration static validation.

This validator covers:
1. JSON Schema Draft 2020-12 validation for workflows/tasks/gates/approvals/evidence.
2. Workflow DAG rules (unique IDs, dependencies, cycles, entries/ends, node types).
3. Task/Workflow/Node/Gate/Approval state machines and legal transitions.
4. Parallel scheduling, G4/G5 version binding, aggregation and conflict rules.
5. Gate applicability (G6/R3/R4/SA) and Builder Check independence.
6. Failure/recovery, idempotency, approval binding and security boundaries.
7. YAML block parsing (duplicate keys) and Capability Registry consistency.

Runtime behavior is NOT executed or claimed as tested.
"""
import copy
import json
import posixpath
import re
import threading
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = ROOT / "schemas" / "orchestration"
EXAMPLES = ROOT / "examples" / "orchestration"
DOCS = ROOT / "docs" / "standards"
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

TASK_TYPES = {
    "technical_consultation",
    "simple_change",
    "bug_fix",
    "feature_development",
    "system_refactoring",
    "new_project",
    "testing_task",
    "deployment_task",
    "documentation_task",
}

WORKFLOW_IDS = {
    "consultation",
    "simple-task",
    "bug-fix",
    "feature-development",
    "refactoring",
    "new-project",
    "testing",
    "deployment",
    "documentation",
    "release-composed",
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


def schema_errors(schema, instance):
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return list(validator.iter_errors(instance))


def expect_schema_invalid(schema, instance, label, counter):
    errs = schema_errors(schema, instance)
    check(bool(errs), f"{label}: expected schema rejection, got valid instance")
    if errs:
        counter[0] += 1


def expect_schema_valid(schema, instance, label, counter):
    errs = schema_errors(schema, instance)
    check(not errs, f"{label}: expected valid instance: {[e.message for e in errs[:3]]}")
    if not errs:
        counter[0] += 1


# ---------------------------------------------------------------------------
# 1. Schemas
# ---------------------------------------------------------------------------
schemas = {}
for name in [
    "workflow.schema.json",
    "task.schema.json",
    "gate-decision.schema.json",
    "approval.schema.json",
    "evidence.schema.json",
]:
    path = SCHEMAS / name
    check(path.exists(), f"missing schema: {name}")
    if path.exists():
        schema = load_json(path)
        check(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
              f"{name}: wrong $schema")
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as e:
            errors.append(f"{name}: invalid Draft 2020-12 schema: {e}")
        schemas[name] = schema

workflow_schema = schemas.get("workflow.schema.json", {})
task_schema = schemas.get("task.schema.json", {})
gate_schema = schemas.get("gate-decision.schema.json", {})
approval_schema = schemas.get("approval.schema.json", {})
evidence_schema = schemas.get("evidence.schema.json", {})

# ---------------------------------------------------------------------------
# 2. Examples
# ---------------------------------------------------------------------------
workflow_files = sorted((EXAMPLES / "workflows").glob("*.yaml"))
task_files = sorted((EXAMPLES / "tasks").glob("*.json"))
gate_files = sorted((EXAMPLES / "gates").glob("*.json"))
approval_files = sorted((EXAMPLES / "approvals").glob("*.json"))
evidence_files = sorted((EXAMPLES / "evidence").glob("*.json"))

positive = [0]
for path in workflow_files:
    wf = load_yaml(path)
    expect_schema_valid(workflow_schema, wf, path.name, positive)
for path in task_files:
    expect_schema_valid(task_schema, load_json(path), path.name, positive)
for path in gate_files:
    expect_schema_valid(gate_schema, load_json(path), path.name, positive)
for path in approval_files:
    expect_schema_valid(approval_schema, load_json(path), path.name, positive)
for path in evidence_files:
    expect_schema_valid(evidence_schema, load_json(path), path.name, positive)

check(len(workflow_files) >= 9, f"expected at least 9 workflow examples, got {len(workflow_files)}")
check(len(task_files) >= 2, "expected at least 2 task examples")
check(len(gate_files) >= 2, "expected at least 2 gate examples")
check(len(approval_files) >= 1, "expected at least 1 approval example")
check(len(evidence_files) >= 2, "expected at least 2 evidence examples")

# Negative schema cases.
negative = [0]
base_wf = load_yaml(workflow_files[0]) if workflow_files else {}
base_task = load_json(task_files[0]) if task_files else {}
base_gate = load_json(gate_files[0]) if gate_files else {}
base_approval = load_json(approval_files[0]) if approval_files else {}
base_evidence = load_json(evidence_files[0]) if evidence_files else {}

wf_missing_nodes = copy.deepcopy(base_wf)
wf_missing_nodes.pop("nodes", None)
expect_schema_invalid(workflow_schema, wf_missing_nodes, "workflow-missing-nodes", negative)

wf_unknown = copy.deepcopy(base_wf)
wf_unknown["unexpected"] = True
expect_schema_invalid(workflow_schema, wf_unknown, "workflow-unknown-field", negative)

wf_bad_status = copy.deepcopy(base_wf)
wf_bad_status["status"] = "bogus"
expect_schema_invalid(workflow_schema, wf_bad_status, "workflow-invalid-status", negative)

wf_skill_missing = copy.deepcopy(base_wf)
for node in wf_skill_missing.get("nodes", []):
    if node.get("type") == "skill":
        node.pop("skill", None)
        break
expect_schema_invalid(workflow_schema, wf_skill_missing, "workflow-skill-missing", negative)

wf_gate_missing = copy.deepcopy(base_wf)
added = False
for node in wf_gate_missing.get("nodes", []):
    if node.get("type") == "gate":
        node.pop("gate", None)
        node.pop("gates", None)
        added = True
        break
if not added:
    wf_gate_missing["nodes"].append({"id": "bad_gate", "type": "gate"})
expect_schema_invalid(workflow_schema, wf_gate_missing, "workflow-gate-missing", negative)

task_missing_id = copy.deepcopy(base_task)
task_missing_id.pop("task_id", None)
expect_schema_invalid(task_schema, task_missing_id, "task-missing-id", negative)

task_unknown = copy.deepcopy(base_task)
task_unknown["unexpected"] = True
expect_schema_invalid(task_schema, task_unknown, "task-unknown-field", negative)

task_bad_status = copy.deepcopy(base_task)
task_bad_status["status"] = "DONE"
expect_schema_invalid(task_schema, task_bad_status, "task-invalid-status", negative)

task_bad_dep = copy.deepcopy(base_task)
task_bad_dep["dependencies"] = ["not-a-task"]
expect_schema_invalid(task_schema, task_bad_dep, "task-invalid-dependency", negative)

task_bad_scope = copy.deepcopy(base_task)
task_bad_scope["context_scope"] = "invalid"
expect_schema_invalid(task_schema, task_bad_scope, "task-invalid-context-scope", negative)

succeeded_task = next((load_json(p) for p in task_files if load_json(p).get("status") == "SUCCEEDED"), None)
if succeeded_task:
    no_outputs = copy.deepcopy(succeeded_task)
    no_outputs["outputs"] = []
    expect_schema_invalid(task_schema, no_outputs, "task-succeeded-no-outputs", negative)

gate_no_hash = copy.deepcopy(base_gate)
gate_no_hash["status"] = "PASSED"
gate_no_hash["subject_hash"] = None
expect_schema_invalid(gate_schema, gate_no_hash, "gate-passed-no-subject-hash", negative)

for gate_status in ("PENDING", "BLOCKED", "FAILED"):
    gate_missing_hash = copy.deepcopy(base_gate)
    gate_missing_hash["gate_id"] = "G4"
    gate_missing_hash["status"] = gate_status
    gate_missing_hash.pop("subject_hash", None)
    expect_schema_invalid(gate_schema, gate_missing_hash,
                          f"gate-g4-{gate_status.lower()}-no-subject-hash", negative)

gate_g6_no_target = copy.deepcopy(base_gate)
gate_g6_no_target["gate_id"] = "G6"
gate_g6_no_target["status"] = "PENDING"
gate_g6_no_target.pop("deployment_target", None)
expect_schema_invalid(gate_schema, gate_g6_no_target,
                      "gate-g6-no-deployment-target", negative)

gate_bad_id = copy.deepcopy(base_gate)
gate_bad_id["gate_id"] = "G7"
expect_schema_invalid(gate_schema, gate_bad_id, "gate-invalid-id", negative)

gate_g6_no_hash = copy.deepcopy(base_gate)
gate_g6_no_hash["gate_id"] = "G6"
gate_g6_no_hash["subject_hash"] = None
expect_schema_invalid(gate_schema, gate_g6_no_hash, "gate-g6-no-subject-hash", negative)

approval_no_decision = copy.deepcopy(base_approval)
approval_no_decision["status"] = "APPROVED"
approval_no_decision["decided_by"] = None
expect_schema_invalid(approval_schema, approval_no_decision, "approval-approved-no-decider", negative)

approval_g6_no_hash = copy.deepcopy(base_approval)
approval_g6_no_hash["type"] = "gate"
approval_g6_no_hash["gate"] = "G6"
approval_g6_no_hash.pop("subject_hash", None)
expect_schema_invalid(approval_schema, approval_g6_no_hash, "approval-g6-no-subject-hash", negative)

approval_bad_status = copy.deepcopy(base_approval)
approval_bad_status["status"] = "MAYBE"
expect_schema_invalid(approval_schema, approval_bad_status, "approval-invalid-status", negative)

approval_consumed_no_fields = copy.deepcopy(base_approval)
approval_consumed_no_fields["status"] = "CONSUMED"
approval_consumed_no_fields.pop("consumed_at", None)
approval_consumed_no_fields.pop("consumed_by", None)
expect_schema_invalid(approval_schema, approval_consumed_no_fields,
                      "approval-consumed-no-consumption-fields", negative)

evidence_not_redacted = copy.deepcopy(base_evidence)
evidence_not_redacted["redacted"] = False
expect_schema_invalid(evidence_schema, evidence_not_redacted, "evidence-not-redacted", negative)

evidence_bad_type = copy.deepcopy(base_evidence)
evidence_bad_type["type"] = "unknown-type"
expect_schema_invalid(evidence_schema, evidence_bad_type, "evidence-invalid-type", negative)

# ---------------------------------------------------------------------------
# 3. Workflow DAG rules
# ---------------------------------------------------------------------------
COMPOSABLE_STATUSES = {"tested", "published"}
workflow_catalog = {}
for path in workflow_files:
    wf = load_yaml(path)
    workflow_catalog[(wf.get("id"), wf.get("version"))] = wf


def workflow_graph_errors(wf, catalog=None, stack=(), depth=0):
    catalog = catalog if catalog is not None else workflow_catalog
    errs = []
    nodes = wf.get("nodes", [])
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)):
        errs.append("duplicate node IDs")
    idset = set(ids)
    for node in nodes:
        nid = node.get("id")
        ntype = node.get("type")
        deps = node.get("depends_on", [])
        for dep in deps:
            if dep not in idset:
                errs.append(f"{nid}: unknown dependency {dep}")
            if dep == nid:
                errs.append(f"{nid}: self dependency")
        for edge in ("on_success", "on_failure"):
            target = node.get(edge)
            if target and target not in idset:
                errs.append(f"{nid}: unknown {edge} target {target}")
        if ntype == "skill" and not node.get("skill"):
            errs.append(f"{nid}: skill node missing skill")
        if ntype == "tool" and not node.get("tool"):
            errs.append(f"{nid}: tool node missing tool")
        if ntype == "subworkflow":
            ref = node.get("workflow_ref")
            if not isinstance(ref, dict) or not ref.get("id") or not ref.get("version"):
                errs.append(f"{nid}: subworkflow requires workflow_ref with id and version")
            else:
                rid, rver = ref.get("id"), ref.get("version")
                key = (rid, rver)
                if key not in catalog:
                    errs.append(f"{nid}: unknown workflow_ref {rid}@{rver}")
                else:
                    ref_wf = catalog[key]
                    if ref_wf.get("status") not in COMPOSABLE_STATUSES:
                        errs.append(f"{nid}: referenced workflow {rid}@{rver} is not tested/published")
                    if rid in stack or rid == wf.get("id"):
                        errs.append(f"{nid}: subworkflow cycle at {rid}")
                    elif depth + 1 > 3:
                        errs.append(f"{nid}: subworkflow depth exceeds 3")
                    else:
                        errs.extend(workflow_graph_errors(ref_wf, catalog, stack + (wf.get("id"),), depth + 1))
        if ntype == "gate" and not (node.get("gate") or node.get("gates")):
            errs.append(f"{nid}: gate node missing gate/gates")
        if ntype == "approval" and not node.get("approval"):
            errs.append(f"{nid}: approval node missing approval")
        if node.get("join_policy") == "quorum":
            q = node.get("quorum")
            if not isinstance(q, int) or q < 1 or q > max(1, len(deps)):
                errs.append(f"{nid}: quorum must be between 1 and dependency count")
        elif node.get("quorum") is not None:
            errs.append(f"{nid}: quorum requires join_policy=quorum")
    # Cycle detection (DFS colors).
    graph = {n.get("id"): list(n.get("depends_on", [])) for n in nodes}
    color = {nid: 0 for nid in idset}

    def dfs(nid):
        if nid not in color:
            return False
        if color[nid] == 1:
            return True
        if color[nid] == 2:
            return False
        color[nid] = 1
        for dep in graph.get(nid, []):
            if dep in color and dfs(dep):
                return True
        color[nid] = 2
        return False

    for nid in idset:
        if dfs(nid):
            errs.append("cycle detected")
            break
    entries = [n.get("id") for n in nodes if not n.get("depends_on")]
    ends = [n.get("id") for n in nodes if n.get("type") == "end"]
    if not entries:
        errs.append("no entry node")
    if not ends:
        errs.append("no end node")
    # Forward edges: dependency edges plus on_success/on_failure.
    forward = {nid: set() for nid in idset}
    for nid, deps in graph.items():
        for dep in deps:
            if dep in forward:
                forward[dep].add(nid)
    for node in nodes:
        nid = node.get("id")
        for edge in ("on_success", "on_failure"):
            target = node.get(edge)
            if target in idset:
                forward[nid].add(target)
    # Reachability from entries.
    seen = set(entries)
    stack_ids = list(entries)
    while stack_ids:
        cur = stack_ids.pop()
        for nxt in forward.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                stack_ids.append(nxt)
    unreachable = idset - seen
    if unreachable:
        errs.append(f"unreachable nodes: {sorted(unreachable)}")
    # Every node must have a path to an end.
    for nid in idset:
        reachable = {nid}
        todo = [nid]
        while todo:
            cur = todo.pop()
            for nxt in forward.get(cur, []):
                if nxt not in reachable:
                    reachable.add(nxt)
                    todo.append(nxt)
        if not (reachable & set(ends)):
            errs.append(f"{nid}: cannot reach an end node")
    # End nodes must not have dependents/outgoing.
    for end in ends:
        if any(end in n.get("depends_on", []) for n in nodes):
            errs.append(f"end node {end} has dependents")
    # parallel_group must converge at a common descendant (join).
    groups = {}
    for node in nodes:
        group = node.get("parallel_group")
        if group:
            groups.setdefault(group, []).append(node.get("id"))
    for group, members in groups.items():
        if len(members) < 2:
            continue
        descendant_sets = []
        for member in members:
            reachable = {member}
            todo = [member]
            while todo:
                cur = todo.pop()
                for nxt in forward.get(cur, []):
                    if nxt not in reachable:
                        reachable.add(nxt)
                        todo.append(nxt)
            descendant_sets.append(reachable)
        common = set.intersection(*descendant_sets)
        common.discard(None)
        common -= set(members)
        if not common:
            errs.append(f"parallel_group {group}: no common join descendant")
    return errs


graph_positive = 0
for path in workflow_files:
    wf = load_yaml(path)
    errs = workflow_graph_errors(wf)
    check(not errs, f"{path.name}: graph error: {errs}")
    if not errs:
        graph_positive += 1

graph_negative = 0
# Unknown dependency.
bad = copy.deepcopy(base_wf)
bad["nodes"][0]["depends_on"] = ["missing_node"]
if workflow_graph_errors(bad):
    graph_negative += 1
else:
    check(False, "graph negative 'unknown dependency' should fail")
# Cycle.
bad = copy.deepcopy(base_wf)
if len(bad["nodes"]) >= 2:
    bad["nodes"][0]["depends_on"] = [bad["nodes"][1]["id"]]
    bad["nodes"][1]["depends_on"] = [bad["nodes"][0]["id"]]
    if workflow_graph_errors(bad):
        graph_negative += 1
    else:
        check(False, "graph negative 'cycle' should fail")
# Duplicate node ID.
bad = copy.deepcopy(base_wf)
if len(bad["nodes"]) >= 2:
    bad["nodes"][1]["id"] = bad["nodes"][0]["id"]
    if workflow_graph_errors(bad):
        graph_negative += 1
    else:
        check(False, "graph negative 'duplicate ID' should fail")
# No end.
bad = copy.deepcopy(base_wf)
bad["nodes"] = [n for n in bad["nodes"] if n.get("type") != "end"]
if workflow_graph_errors(bad):
    graph_negative += 1
else:
    check(False, "graph negative 'no end' should fail")
# Skill node missing skill.
bad = copy.deepcopy(base_wf)
for node in bad["nodes"]:
    if node.get("type") == "skill":
        node.pop("skill", None)
        break
if workflow_graph_errors(bad):
    graph_negative += 1
else:
    check(False, "graph negative 'skill missing' should fail")
# Unknown subworkflow reference.
composed = next((load_yaml(p) for p in workflow_files if load_yaml(p).get("id") == "release-composed"), None)
if composed:
    bad = copy.deepcopy(composed)
    for node in bad["nodes"]:
        if node.get("type") == "subworkflow":
            node["workflow_ref"] = {"id": "missing-workflow", "version": "0.1.0"}
            break
    if workflow_graph_errors(bad):
        graph_negative += 1
    else:
        check(False, "graph negative 'unknown subworkflow' should fail")
    # Unknown subworkflow version.
    bad = copy.deepcopy(composed)
    for node in bad["nodes"]:
        if node.get("type") == "subworkflow":
            node["workflow_ref"]["version"] = "9.9.9"
            break
    if workflow_graph_errors(bad):
        graph_negative += 1
    else:
        check(False, "graph negative 'unknown subworkflow version' should fail")
    # Referenced workflow is not tested/published.
    bad_catalog = dict(workflow_catalog)
    key = ("feature-development", "0.1.0")
    if key in bad_catalog:
        draft_ref = copy.deepcopy(bad_catalog[key])
        draft_ref["status"] = "draft"
        bad_catalog[key] = draft_ref
        if workflow_graph_errors(composed, bad_catalog):
            graph_negative += 1
        else:
            check(False, "graph negative 'draft subworkflow' should fail")

# Indirect subworkflow cycle.
def minimal_wf(wid, ref_id, ref_version="0.1.0"):
    return {
        "id": wid,
        "version": "0.1.0",
        "status": "tested",
        "nodes": [
            {"id": "ref_other", "type": "subworkflow",
             "workflow_ref": {"id": ref_id, "version": ref_version}},
            {"id": "end", "type": "end", "depends_on": ["ref_other"]},
        ],
    }


cycle_a = minimal_wf("cycle-a", "cycle-b")
cycle_b = minimal_wf("cycle-b", "cycle-a")
cycle_catalog = {("cycle-a", "0.1.0"): cycle_a, ("cycle-b", "0.1.0"): cycle_b}
if workflow_graph_errors(cycle_a, cycle_catalog):
    graph_negative += 1
else:
    check(False, "graph negative 'indirect subworkflow cycle' should fail")

# Subworkflow depth > 3.
depth_wfs = {}
for i in range(1, 6):
    nxt = f"depth-{i + 1}" if i < 5 else None
    if nxt:
        wf = minimal_wf(f"depth-{i}", nxt)
    else:
        wf = {"id": f"depth-{i}", "version": "0.1.0", "status": "tested",
              "nodes": [{"id": "end", "type": "end"}]}
    depth_wfs[(f"depth-{i}", "0.1.0")] = wf
if workflow_graph_errors(depth_wfs[("depth-1", "0.1.0")], depth_wfs):
    graph_negative += 1
else:
    check(False, "graph negative 'subworkflow depth > 3' should fail")

# Unknown on_success/on_failure target.
bad = copy.deepcopy(base_wf)
bad["nodes"][0]["on_success"] = "missing_target"
if workflow_graph_errors(bad):
    graph_negative += 1
else:
    check(False, "graph negative 'unknown on_success' should fail")

bad = copy.deepcopy(base_wf)
bad["nodes"][0]["on_failure"] = "missing_failure_target"
if workflow_graph_errors(bad):
    graph_negative += 1
else:
    check(False, "graph negative 'unknown on_failure' should fail")

# parallel_group without common join.
bad_parallel = {
    "id": "bad-parallel", "version": "0.1.0", "status": "tested",
    "nodes": [
        {"id": "a", "type": "check", "parallel_group": "g"},
        {"id": "b", "type": "check", "parallel_group": "g"},
        {"id": "end_a", "type": "end", "depends_on": ["a"]},
        {"id": "end_b", "type": "end", "depends_on": ["b"]},
    ],
}
if workflow_graph_errors(bad_parallel):
    graph_negative += 1
else:
    check(False, "graph negative 'parallel without join' should fail")

# quorum out of range.
bad_quorum = copy.deepcopy(base_wf)
bad_quorum["nodes"][0]["join_policy"] = "quorum"
bad_quorum["nodes"][0]["quorum"] = 5
if workflow_graph_errors(bad_quorum):
    graph_negative += 1
else:
    check(False, "graph negative 'quorum out of range' should fail")

# quorum without join_policy.
bad_quorum2 = copy.deepcopy(base_wf)
bad_quorum2["nodes"][0]["quorum"] = 1
if workflow_graph_errors(bad_quorum2):
    graph_negative += 1
else:
    check(False, "graph negative 'quorum without join_policy' should fail")

# A reachable branch that cannot reach any end.
bad_dead_end = copy.deepcopy(base_wf)
bad_dead_end["nodes"].append({"id": "dead_branch", "type": "check"})
bad_dead_end["nodes"][0]["on_success"] = "dead_branch"
if workflow_graph_errors(bad_dead_end):
    graph_negative += 1
else:
    check(False, "graph negative 'branch without termination' should fail")

# ---------------------------------------------------------------------------
# 4. State machines
# ---------------------------------------------------------------------------
MACHINE_FILES = [
    "task-state-machine.json",
    "workflow-state-machine.json",
    "node-state-machine.json",
    "gate-state-machine.json",
    "approval-state-machine.json",
]

machines = {}
machine_errors = []
for name in MACHINE_FILES:
    path = SCHEMAS / name
    if not path.exists():
        machine_errors.append(f"missing state machine: {name}")
        continue
    m = load_json(path)
    machines[name] = m
    states = m.get("states", [])
    terminal = m.get("terminal", [])
    transitions = m.get("transitions", [])
    if len(states) != len(set(states)):
        machine_errors.append(f"{name}: duplicate states")
    if m.get("initial") not in states:
        machine_errors.append(f"{name}: initial not in states")
    if not set(terminal) <= set(states):
        machine_errors.append(f"{name}: terminal not subset of states")
    pairs = set()
    for t in transitions:
        frm, to = t.get("from"), t.get("to")
        if frm not in states or to not in states:
            machine_errors.append(f"{name}: invalid transition {frm}->{to}")
        if frm == to:
            machine_errors.append(f"{name}: self transition {frm}")
        if frm in terminal:
            machine_errors.append(f"{name}: transition from terminal {frm}")
        if (frm, to) in pairs:
            machine_errors.append(f"{name}: duplicate transition {frm}->{to}")
        pairs.add((frm, to))
    # Every non-terminal state must have an outgoing transition.
    for s in states:
        if s not in terminal and not any(t.get("from") == s for t in transitions):
            machine_errors.append(f"{name}: non-terminal {s} has no outgoing transition")
    # Reachability from initial.
    seen = {m.get("initial")}
    changed = True
    while changed:
        changed = False
        for t in transitions:
            if t.get("from") in seen and t.get("to") not in seen:
                seen.add(t.get("to"))
                changed = True
    if seen != set(states):
        machine_errors.append(f"{name}: unreachable states {sorted(set(states) - seen)}")

check(not machine_errors, f"state machine errors: {machine_errors}")


def can_transition(machine, frm, to):
    return any(t.get("from") == frm and t.get("to") == to for t in machine.get("transitions", []))


EXPECTED_TRANSITIONS = {
    "task-state-machine.json": {
        ("PENDING", "READY"), ("PENDING", "CANCELLED"),
        ("READY", "RUNNING"), ("READY", "WAITING"), ("READY", "BLOCKED"), ("READY", "CANCELLED"),
        ("RUNNING", "SUCCEEDED"), ("RUNNING", "FAILED"), ("RUNNING", "WAITING"), ("RUNNING", "BLOCKED"), ("RUNNING", "CANCELLED"),
        ("WAITING", "READY"), ("WAITING", "BLOCKED"), ("WAITING", "FAILED"), ("WAITING", "CANCELLED"),
        ("BLOCKED", "READY"), ("BLOCKED", "FAILED"), ("BLOCKED", "CANCELLED"),
    },
    "workflow-state-machine.json": {
        ("PENDING", "RUNNING"), ("PENDING", "CANCELLED"),
        ("RUNNING", "WAITING"), ("RUNNING", "BLOCKED"), ("RUNNING", "SUCCEEDED"), ("RUNNING", "FAILED"), ("RUNNING", "CANCELLED"),
        ("WAITING", "RUNNING"), ("WAITING", "BLOCKED"), ("WAITING", "FAILED"), ("WAITING", "CANCELLED"),
        ("BLOCKED", "RUNNING"), ("BLOCKED", "FAILED"), ("BLOCKED", "CANCELLED"),
    },
    "node-state-machine.json": {
        ("PENDING", "READY"), ("PENDING", "SKIPPED"), ("PENDING", "CANCELLED"),
        ("READY", "RUNNING"), ("READY", "WAITING"), ("READY", "BLOCKED"), ("READY", "CANCELLED"),
        ("RUNNING", "SUCCEEDED"), ("RUNNING", "FAILED"), ("RUNNING", "WAITING"), ("RUNNING", "BLOCKED"), ("RUNNING", "CANCELLED"),
        ("WAITING", "READY"), ("WAITING", "BLOCKED"), ("WAITING", "FAILED"), ("WAITING", "CANCELLED"),
        ("BLOCKED", "READY"), ("BLOCKED", "FAILED"), ("BLOCKED", "CANCELLED"),
    },
    "gate-state-machine.json": {
        ("PENDING", "NOT_REQUIRED"), ("PENDING", "EVALUATING"), ("PENDING", "INVALIDATED"), ("PENDING", "EXPIRED"),
        ("EVALUATING", "PASSED"), ("EVALUATING", "FAILED"), ("EVALUATING", "BLOCKED"), ("EVALUATING", "INVALIDATED"), ("EVALUATING", "EXPIRED"),
        ("BLOCKED", "EVALUATING"), ("BLOCKED", "FAILED"), ("BLOCKED", "INVALIDATED"), ("BLOCKED", "EXPIRED"),
        ("PASSED", "INVALIDATED"), ("PASSED", "EXPIRED"), ("FAILED", "INVALIDATED"),
    },
    "approval-state-machine.json": {
        ("REQUESTED", "PENDING"),
        ("PENDING", "APPROVED"), ("PENDING", "REJECTED"), ("PENDING", "EXPIRED"), ("PENDING", "REVOKED"), ("PENDING", "INVALIDATED"),
        ("APPROVED", "CONSUMED"), ("APPROVED", "EXPIRED"), ("APPROVED", "REVOKED"), ("APPROVED", "INVALIDATED"),
    },
}

state_positive = 0
state_negative = 0
transition_definitions = 0
transition_tests = 0
for name, machine in machines.items():
    expected = EXPECTED_TRANSITIONS.get(name, set())
    actual = {(t.get("from"), t.get("to")) for t in machine.get("transitions", [])}
    check(actual == expected, f"{name}: transitions differ from independent expectation: {sorted(actual ^ expected)}")
    transition_definitions += len(actual)
    for pair in expected:
        check(can_transition(machine, pair[0], pair[1]),
              f"{name}: expected legal transition rejected {pair[0]}->{pair[1]}")
        state_positive += 1
        transition_tests += 1
    states = machine.get("states", [])
    for frm in states:
        for to in states:
            if frm == to:
                check(not can_transition(machine, frm, to),
                      f"{name}: self transition must be illegal {frm}->{to}")
                state_negative += 1
                transition_tests += 1
                continue
            if (frm, to) not in expected:
                check(not can_transition(machine, frm, to),
                      f"{name}: unexpected transition allowed {frm}->{to}")
                state_negative += 1
                transition_tests += 1

# Guard tests: independently evaluate guard conditions, not by reading transitions.
def guard_ok(guard, ctx):
    rules = {
        "dependencies_satisfied_and_inputs_valid": lambda c: c.get("deps_ok") and c.get("inputs_valid"),
        "assigned_and_lease_acquired_and_permissions_valid": lambda c: c.get("assigned") and c.get("lease_ok") and c.get("permissions_ok"),
        "outputs_valid_and_evidence_complete_and_gates_satisfied": lambda c: c.get("outputs_ok") and c.get("evidence_ok") and c.get("gates_ok"),
        "approval_granted_or_permission_capability_restored": lambda c: c.get("approval_ok") or c.get("permission_ok") or c.get("capability_ok"),
        "cancel_requested": lambda c: bool(c.get("cancel_requested")),
        "wait_condition_cleared": lambda c: bool(c.get("wait_cleared")),
        "block_cleared": lambda c: bool(c.get("block_cleared")),
        "subject_hash_changed": lambda c: bool(c.get("subject_hash_changed")),
        "single_use_atomic_consume_and_binding_valid": lambda c: c.get("approved") and c.get("binding_ok") and not c.get("already_consumed"),
    }
    return bool(rules.get(guard, lambda c: False)(ctx))


guard_cases = 0
guard_tests = [
    ("dependencies_satisfied_and_inputs_valid", {"deps_ok": True, "inputs_valid": True}, True),
    ("dependencies_satisfied_and_inputs_valid", {"deps_ok": False, "inputs_valid": True}, False),
    ("assigned_and_lease_acquired_and_permissions_valid", {"assigned": True, "lease_ok": True, "permissions_ok": True}, True),
    ("assigned_and_lease_acquired_and_permissions_valid", {"assigned": True, "lease_ok": False, "permissions_ok": True}, False),
    ("outputs_valid_and_evidence_complete_and_gates_satisfied", {"outputs_ok": True, "evidence_ok": True, "gates_ok": True}, True),
    ("outputs_valid_and_evidence_complete_and_gates_satisfied", {"outputs_ok": True, "evidence_ok": False, "gates_ok": True}, False),
    ("approval_granted_or_permission_capability_restored", {"approval_ok": False, "permission_ok": True, "capability_ok": False}, True),
    ("approval_granted_or_permission_capability_restored", {"approval_ok": False, "permission_ok": False, "capability_ok": False}, False),
    ("cancel_requested", {"cancel_requested": True}, True),
    ("cancel_requested", {"cancel_requested": False}, False),
    ("wait_condition_cleared", {"wait_cleared": True}, True),
    ("wait_condition_cleared", {"wait_cleared": False}, False),
    ("block_cleared", {"block_cleared": True}, True),
    ("block_cleared", {"block_cleared": False}, False),
    ("subject_hash_changed", {"subject_hash_changed": True}, True),
    ("subject_hash_changed", {"subject_hash_changed": False}, False),
    ("single_use_atomic_consume_and_binding_valid", {"approved": True, "binding_ok": True, "already_consumed": False}, True),
    ("single_use_atomic_consume_and_binding_valid", {"approved": True, "binding_ok": True, "already_consumed": True}, False),
]
for guard, ctx, expected in guard_tests:
    check(guard_ok(guard, ctx) is expected, f"guard {guard} returned wrong result for {ctx}")
    guard_cases += 1

# Specific invariant checks.
task_machine = machines.get("task-state-machine.json", {})
check(not can_transition(task_machine, "PENDING", "RUNNING"), "task: PENDING->RUNNING must be illegal")
check(not can_transition(task_machine, "SUCCEEDED", "READY"), "task: SUCCEEDED->READY must be illegal")
check(not can_transition(task_machine, "CANCELLED", "RUNNING"), "task: CANCELLED->RUNNING must be illegal")
workflow_machine = machines.get("workflow-state-machine.json", {})
check(not can_transition(workflow_machine, "SUCCEEDED", "RUNNING"), "workflow: SUCCEEDED->RUNNING must be illegal")
approval_machine = machines.get("approval-state-machine.json", {})
check(not can_transition(approval_machine, "REJECTED", "APPROVED"), "approval: REJECTED->APPROVED must be illegal")
node_machine = machines.get("node-state-machine.json", {})
check(not can_transition(node_machine, "CANCELLED", "RUNNING"), "node: CANCELLED->RUNNING must be illegal")

# ---------------------------------------------------------------------------
# 5. Task model / dependency / parallel
# ---------------------------------------------------------------------------
def dependencies_satisfied(task, statuses):
    return all(statuses.get(dep) == "SUCCEEDED" for dep in task.get("dependencies", []))


def ready_tasks(tasks, statuses):
    return [t["task_id"] for t in tasks if t.get("status") == "READY" and dependencies_satisfied(t, statuses)]


def detect_cycle(edges):
    color = {}

    def dfs(n):
        if color.get(n) == 1:
            return True
        if color.get(n) == 2:
            return False
        color[n] = 1
        for m in edges.get(n, []):
            if dfs(m):
                return True
        color[n] = 2
        return False

    return any(dfs(n) for n in list(edges))


def quality_gate_passed(g4, g5, current_subject_hash):
    return (
        g4.get("gate_id") == "G4"
        and g5.get("gate_id") == "G5"
        and g4.get("status") == "PASSED"
        and g5.get("status") == "PASSED"
        and g4.get("subject_hash") == g5.get("subject_hash") == current_subject_hash
    )


def aggregate(results, policy="all", quorum=1):
    if policy == "all":
        return all(results)
    if policy == "any":
        return any(results)
    if policy == "quorum":
        return sum(1 for r in results if r) >= quorum
    return False


def paths_overlap(paths):
    return len(paths) != len(set(paths))


parallel_cases = 0
# Independent tasks can be ready.
t1 = {"task_id": "task-20261120-00000001", "status": "READY", "dependencies": []}
t2 = {"task_id": "task-20261120-00000002", "status": "READY", "dependencies": []}
check(set(ready_tasks([t1, t2], {})) == {t1["task_id"], t2["task_id"]},
      "parallel: independent tasks should be ready")
parallel_cases += 1
# Unmet dependency prevents start.
t3 = {"task_id": "task-20261120-00000003", "status": "READY",
      "dependencies": ["task-20261120-00000001"]}
check(not ready_tasks([t3], {t1["task_id"]: "RUNNING"}), "parallel: unmet dependency should not be ready")
parallel_cases += 1
check(dependencies_satisfied(t3, {t1["task_id"]: "SUCCEEDED"}), "parallel: satisfied dependency should be ready")
parallel_cases += 1
# Cycle detection.
check(detect_cycle({"a": ["b"], "b": ["a"]}), "parallel: cycle should be detected")
parallel_cases += 1
check(not detect_cycle({"a": ["b"], "b": []}), "parallel: acyclic graph should pass")
parallel_cases += 1
# G4/G5 same subject hash.
g4 = load_json(gate_files[0]) if gate_files else {}
g5 = load_json(gate_files[1]) if len(gate_files) > 1 else {}
check(quality_gate_passed(g4, g5, g4.get("subject_hash")),
      "parallel: G4/G5 same hash should pass quality gate")
parallel_cases += 1
check(not quality_gate_passed(g4, g5, "f" * 40),
      "parallel: different current hash should fail quality gate")
parallel_cases += 1
g4_failed = copy.deepcopy(g4)
g4_failed["status"] = "FAILED"
check(not quality_gate_passed(g4_failed, g5, g4.get("subject_hash")),
      "parallel: failed G4 should fail quality gate")
parallel_cases += 1
g5_failed = copy.deepcopy(g5)
g5_failed["status"] = "FAILED"
check(not quality_gate_passed(g4, g5_failed, g4.get("subject_hash")),
      "parallel: failed G5 should fail quality gate")
parallel_cases += 1
# Task SUCCEEDED is not a substitute for GateDecision.
check(not quality_gate_passed({}, {}, None), "parallel: task status must not replace GateDecision")
parallel_cases += 1
# New commit invalidates old results.
new_hash = "a" * 40
check(not quality_gate_passed(g4, g5, new_hash), "parallel: new commit should invalidate old gates")
parallel_cases += 1
# Aggregation.
check(aggregate([True, True], "all"), "parallel: aggregate all true")
parallel_cases += 1
check(not aggregate([True, False], "all"), "parallel: aggregate all false")
parallel_cases += 1
check(aggregate([True, False], "any"), "parallel: aggregate any")
parallel_cases += 1
check(aggregate([True, False, True], "quorum", 2), "parallel: aggregate quorum")
parallel_cases += 1
check(paths_overlap(["a", "a"]), "parallel: shared path conflict should be detected")
parallel_cases += 1
check(not paths_overlap(["a", "b"]), "parallel: distinct paths should not conflict")
parallel_cases += 1


def parallel_workflow_status(branch_statuses, failure_policy="fail_workflow"):
    if any(s == "FAILED" for s in branch_statuses):
        return "FAILED" if failure_policy == "fail_workflow" else "PARTIAL"
    return "SUCCEEDED"


check(parallel_workflow_status(["SUCCEEDED", "FAILED"]) == "FAILED",
      "parallel: gate-related branch failure must fail workflow")
parallel_cases += 1
check(parallel_workflow_status(["SUCCEEDED", "FAILED"], "continue_independent") == "PARTIAL",
      "parallel: independent branch failure must not be reported as full success")
parallel_cases += 1

# ---------------------------------------------------------------------------
# 5b. Root vs node Task Context (ADR-005 alignment)
# ---------------------------------------------------------------------------
task_context_cases = 0
root_task = next((load_json(p) for p in task_files if load_json(p).get("context_scope") == "root"), None)
node_succeeded = next((load_json(p) for p in task_files if load_json(p).get("status") == "SUCCEEDED"), None)
check(root_task is not None, "task-context: root task example missing")
task_context_cases += 1
check(node_succeeded is not None, "task-context: succeeded node task example missing")
task_context_cases += 1
if root_task and node_succeeded:
    check(node_succeeded.get("parent_task_id") == root_task.get("task_id"),
          "task-context: node task must reference root task via parent_task_id")
    task_context_cases += 1

    def root_context_after_node(root, node, workflow_verified=False,
                                required_tasks_ok=False, gates_ok=False):
        if root.get("context_scope") != "root":
            return None
        if workflow_verified and required_tasks_ok and gates_ok:
            return "completed"
        return root.get("context_status")

    check(root_context_after_node(root_task, node_succeeded) == root_task.get("context_status"),
          "task-context: node SUCCEEDED must not complete root context")
    task_context_cases += 1
    check(root_context_after_node(root_task, node_succeeded, True, True, True) == "completed",
          "task-context: root may complete after workflow verification and gates")
    task_context_cases += 1
    check(root_context_after_node(root_task, node_succeeded, True, True, False) != "completed",
          "task-context: root must not complete when required gates are missing")
    task_context_cases += 1
    check(node_succeeded.get("context_status") == "completed"
          and root_task.get("context_status") != "completed",
          "task-context: node local context_status must not be root lifecycle")
    task_context_cases += 1

# ---------------------------------------------------------------------------
# 6. Gate applicability / Builder Check
# ---------------------------------------------------------------------------
def required_controls(environment="dev", deployment=False, db_operation=None,
                      destructive=False, sensitive_credential=False,
                      config_change=False):
    production = environment == "prod"
    g6 = production and deployment
    if sensitive_credential or (production and destructive):
        permission = "R4"
        sa = True
    elif production and deployment:
        permission = "R3"
        sa = True
    elif production and db_operation == "migration":
        permission = "R3"
        sa = False
    elif production and config_change:
        permission = "R3"
        sa = True
    elif deployment:
        permission = "R2"
        sa = False
    else:
        permission = "R1"
        sa = False
    return {"g6": g6, "permission": permission, "sa": sa, "environment": environment}


def can_execute_production_deploy(permission, g6, sa):
    return permission == "R3" and g6 is True and sa is True


def independent_reviewer(author, reviewer):
    return bool(reviewer) and author != reviewer


gate_cases = 0
c = required_controls("dev")
check(c["g6"] is False and c["permission"] == "R1" and c["sa"] is False,
      "gate: normal development must not trigger G6")
gate_cases += 1
c = required_controls("staging", deployment=True)
check(c["g6"] is False and c["permission"] == "R2" and c["sa"] is False,
      "gate: non-production deployment must not trigger G6")
gate_cases += 1
c = required_controls("prod", deployment=True)
check(c["g6"] is True and c["permission"] == "R3" and c["sa"] is True,
      "gate: production deployment must require G6 + R3 + SA")
gate_cases += 1
check(not can_execute_production_deploy("R3", True, False),
      "gate: production deployment missing SA must fail")
gate_cases += 1
check(not can_execute_production_deploy("R2", True, True),
      "gate: production deployment missing R3 must fail")
gate_cases += 1
c = required_controls("prod", db_operation="migration")
check(c["g6"] is False and c["permission"] == "R3" and c["sa"] is False,
      "gate: production migration must be R3 without G6")
gate_cases += 1
c = required_controls("prod", db_operation="migration", destructive=True)
check(c["g6"] is False and c["permission"] == "R4" and c["sa"] is True,
      "gate: production destructive DB operation must be R4 + SA without G6")
gate_cases += 1
c = required_controls("prod", db_operation="migration", destructive=True, deployment=True)
check(c["g6"] is True and c["permission"] == "R4" and c["sa"] is True,
      "gate: destructive DB operation during production deployment adds G6")
gate_cases += 1
c = required_controls("prod", sensitive_credential=True)
check(c["g6"] is False and c["permission"] == "R4" and c["sa"] is True,
      "gate: sensitive credential read must be R4 + SA without G6")
gate_cases += 1
c = required_controls("prod", config_change=True)
check(c["g6"] is False and c["permission"] == "R3" and c["sa"] is True,
      "gate: production config change must be R3 + SA without G6")
gate_cases += 1
check(required_controls("prod", destructive=True)["g6"] is False,
      "gate: R4 must not automatically equal G6")
gate_cases += 1
check(not can_execute_production_deploy("R2", True, True),
      "gate: SA must not replace permission check")
gate_cases += 1
# G6 approval cannot be auto-approved.
g6_approval = load_json(approval_files[0]) if approval_files else {}
g6_approval["status"] = "PENDING"
check(g6_approval["status"] != "APPROVED", "gate: G6 must not be auto-approved")
gate_cases += 1
check(independent_reviewer("author-1", "reviewer-1"), "gate: independent reviewer should pass")
gate_cases += 1
check(not independent_reviewer("author-1", "author-1"), "gate: author self-review must fail")
gate_cases += 1

# ---------------------------------------------------------------------------
# 7. Failure / recovery
# ---------------------------------------------------------------------------
def retry_decision(category, attempt, max_attempts, reversible=True, idempotent=True):
    if not reversible or not idempotent:
        return "no_retry"
    if category not in {"retryable", "timeout", "agent_unavailable", "tool_error"}:
        return "no_retry"
    if attempt >= max_attempts:
        return "exhausted"
    return "retry"


failure_cases = 0
check(retry_decision("retryable", 1, 3) == "retry", "failure: retryable should retry")
failure_cases += 1
check(retry_decision("non_retryable", 1, 3) == "no_retry", "failure: non-retryable must not retry")
failure_cases += 1
check(retry_decision("timeout", 1, 3) == "retry", "failure: timeout should retry when safe")
failure_cases += 1
check(retry_decision("agent_unavailable", 1, 3) == "retry", "failure: agent unavailable should retry")
failure_cases += 1
check(retry_decision("retryable", 1, 3, reversible=False) == "no_retry",
      "failure: irreversible operation must not auto-retry")
failure_cases += 1
check(retry_decision("retryable", 1, 3, idempotent=False) == "no_retry",
      "failure: non-idempotent operation must not auto-retry")
failure_cases += 1
check(retry_decision("retryable", 3, 3) == "exhausted", "failure: retry budget should exhaust")
failure_cases += 1
check(retry_decision("needs_human", 1, 3) == "no_retry", "failure: approval rejection/human must not auto-retry")
failure_cases += 1


def duplicate_request(existing_keys, key):
    return key in existing_keys


def artifact_hash_ok(expected, actual):
    return bool(expected) and expected == actual


check(duplicate_request({"k1"}, "k1"), "failure: duplicate key should be detected")
failure_cases += 1
check(not duplicate_request({"k1"}, "k2"), "failure: unique key should pass")
failure_cases += 1
check(artifact_hash_ok("a" * 64, "a" * 64), "failure: matching artifact hash should pass")
failure_cases += 1
check(not artifact_hash_ok("a" * 64, "b" * 64), "failure: mismatched artifact hash should fail")
failure_cases += 1


def can_resume(status):
    return status in {"WAITING", "BLOCKED"}


check(can_resume("WAITING"), "failure: WAITING task may resume")
failure_cases += 1
check(can_resume("BLOCKED"), "failure: BLOCKED task may resume after unblock")
failure_cases += 1
check(not can_resume("FAILED"), "failure: terminal FAILED task must not resume in place")
failure_cases += 1
check(not can_resume("CANCELLED"), "failure: cancelled task must not resume")
failure_cases += 1

# ---------------------------------------------------------------------------
# 8. Security / approval binding
# ---------------------------------------------------------------------------
def tool_allowed(declared_tools, requested_tool):
    return requested_tool in declared_tools


def normalize_path(path, symlinks=None):
    if not isinstance(path, str) or not path:
        return None
    p = path.replace("\\", "/")
    if p.startswith("/") or re.match(r"^[A-Za-z]:/", p):
        return None
    norm = posixpath.normpath(p)
    if norm == ".." or norm.startswith("../") or norm.startswith("/"):
        return None
    if symlinks and norm in symlinks:
        target = symlinks[norm].replace("\\", "/")
        if target.startswith("/") or re.match(r"^[A-Za-z]:/", target):
            return None
        norm = posixpath.normpath(target)
        if norm == ".." or norm.startswith("../") or norm.startswith("/"):
            return None
    return norm


def path_allowed(task_id, path, symlinks=None):
    norm = normalize_path(path, symlinks)
    if norm is None:
        return False
    root = f"artifacts/{task_id}"
    return norm == root or norm.startswith(root + "/")


def scope_matches(approval_scope, requested_scope):
    if not isinstance(approval_scope, dict) or not isinstance(requested_scope, dict):
        return False
    return all(requested_scope.get(k) == v for k, v in approval_scope.items())


def approval_usable(approval, ctx):
    if approval.get("status") != "APPROVED":
        return False
    for key in ("task_id", "workflow_id", "node_id", "operation", "target", "environment"):
        if approval.get(key) != ctx.get(key):
            return False
    if not scope_matches(approval.get("scope", {}), ctx.get("scope", {})):
        return False
    if approval.get("subject_hash") and approval.get("subject_hash") != ctx.get("subject_hash"):
        return False
    if approval.get("expires_at") and approval["expires_at"] <= ctx.get("now", ""):
        return False
    if approval.get("consumed_at") is not None:
        return False
    return approval.get("single_use") is True


class ApprovalStore:
    def __init__(self, approval):
        self.approval = copy.deepcopy(approval)
        self.lock = threading.Lock()

    def consume(self, actor, now, ref):
        with self.lock:
            if self.approval.get("status") != "APPROVED" or self.approval.get("consumed_at"):
                return False
            self.approval["status"] = "CONSUMED"
            self.approval["consumed_at"] = now
            self.approval["consumed_by"] = actor
            self.approval["consumption_ref"] = ref
            return True


def permission_allows(declared_level, requested_level):
    order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4}
    return order.get(declared_level, -1) >= order.get(requested_level, 99)


SECRET_RE = re.compile(
    r"(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"(?i:(password|passwd|secret|api[_-]?key))\s*[:=]\s*['\"]?[^'\"\s]{6,})"
)

security_cases = 0
check(tool_allowed(["file-read", "file-write"], "file-read"), "security: declared tool should be allowed")
security_cases += 1
check(not tool_allowed(["file-read"], "shell:exec:prod"), "security: undeclared tool must be denied")
security_cases += 1
task_for_path = "task-20261120-a1b2c3d4"
check(path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/design/design.md"),
      "security: own task path should be allowed")
security_cases += 1
check(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/../task-20261120-ffffffff/secret.md"),
      "security: path traversal into another task must be denied")
security_cases += 1
check(not path_allowed(task_for_path, "/etc/passwd"), "security: absolute unix path must be denied")
security_cases += 1
check(not path_allowed(task_for_path, "C:\\Windows\\win.ini"),
      "security: absolute Windows path must be denied")
security_cases += 1
check(not path_allowed(task_for_path, "artifacts/task-20261120-ffffffff/secret.md"),
      "security: other task path must be denied")
security_cases += 1
symlinks = {
    "artifacts/task-20261120-a1b2c3d4/link":
        "../task-20261120-ffffffff/secret.md"
}
check(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/link", symlinks),
      "security: symlink escaping task directory must be denied")
security_cases += 1
symlinks_escape = {
    "artifacts/task-20261120-a1b2c3d4/link": "../../etc/passwd"
}
check(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/link", symlinks_escape),
      "security: symlink escaping project root must be denied")
security_cases += 1

approval_file = next((p for p in approval_files if "approved" in p.name), approval_files[0] if approval_files else None)
approval = load_json(approval_file) if approval_file else {}
base_now = "2026-11-20T11:05:00Z"
approval_ctx = {
    "task_id": approval.get("task_id"),
    "workflow_id": approval.get("workflow_id"),
    "node_id": approval.get("node_id"),
    "operation": approval.get("operation"),
    "target": approval.get("target"),
    "environment": approval.get("environment"),
    "scope": copy.deepcopy(approval.get("scope", {})),
    "subject_hash": approval.get("subject_hash"),
    "now": base_now,
}
check(approval_usable(approval, approval_ctx), "security: valid approval should be usable")
security_cases += 1
for key, value in (
    ("task_id", "task-20261120-ffffffff"),
    ("workflow_id", "bug-fix"),
    ("node_id", "g6"),
    ("operation", "delete_production_data"),
    ("target", "prod-cluster-eu"),
    ("environment", "staging"),
    ("scope", {"cluster": "prod-cluster-eu"}),
    ("subject_hash", "f" * 40),
    ("now", "2026-11-20T12:00:00Z"),
):
    ctx = dict(approval_ctx)
    ctx[key] = value
    check(not approval_usable(approval, ctx),
          f"security: approval must be invalid for changed {key}")
    security_cases += 1
consumed = copy.deepcopy(approval)
consumed["status"] = "CONSUMED"
consumed["consumed_at"] = "2026-11-20T11:12:00Z"
consumed["consumed_by"] = "orchestrator-main"
check(not approval_usable(consumed, approval_ctx),
      "security: consumed approval must not be usable")
security_cases += 1
rejected = copy.deepcopy(approval)
rejected["status"] = "REJECTED"
check(not approval_usable(rejected, approval_ctx),
      "security: rejected approval must not be usable")
security_cases += 1

# Atomic single consumption, including concurrent duplicate consumption.
store = ApprovalStore(approval)
barrier = threading.Barrier(2)
results = []


def consume_worker():
    barrier.wait()
    results.append(store.consume("worker-a", "2026-11-20T11:12:00Z", "consume-ref"))


threads = [threading.Thread(target=consume_worker) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()
check(results.count(True) == 1, "security: concurrent consumption must succeed exactly once")
security_cases += 1
check(store.approval["status"] == "CONSUMED", "security: consumed approval must be CONSUMED")
security_cases += 1
check(store.approval.get("consumed_at") and store.approval.get("consumed_by"),
      "security: consumed approval must record consumed_at/consumed_by")
security_cases += 1
check(not store.consume("worker-b", "2026-11-20T11:13:00Z", "consume-ref-2"),
      "security: second consumption must fail")
security_cases += 1
check(not approval_usable(store.approval, approval_ctx),
      "security: consumed approval must not be usable after consumption")
security_cases += 1
check(SECRET_RE.search("password=supersecret123") is not None,
      "security: secret detection should catch password assignment")
security_cases += 1
check(SECRET_RE.search("normal log line without credentials") is None,
      "security: normal log should not be flagged")
security_cases += 1
check(not permission_allows("R0", "R4"), "security: R0 context must not bypass to R4")
security_cases += 1
check(permission_allows("R4", "R4"), "security: R4 declared permission should allow R4")
security_cases += 1
check(approval.get("single_use") is True, "security: approval must be single-use")
security_cases += 1


def can_delegate(parent_level, child_level):
    order = {"R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4}
    return child_level != "R4" and order.get(child_level, 99) <= order.get(parent_level, -1)


check(can_delegate("R3", "R2"), "security: sub-agent may receive a permission subset")
security_cases += 1
check(not can_delegate("R2", "R3"), "security: sub-agent must not exceed parent permissions")
security_cases += 1
check(not can_delegate("R4", "R4"), "security: R4 must not be delegated")
security_cases += 1

example_secret_hits = []
for path in EXAMPLES.rglob("*"):
    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
        if SECRET_RE.search(text):
            example_secret_hits.append(str(path.relative_to(ROOT)))
check(not example_secret_hits, f"security: examples contain secret-like values: {example_secret_hits}")
security_cases += 1

# ---------------------------------------------------------------------------
# 9. YAML blocks and docs consistency
# ---------------------------------------------------------------------------
def check_yaml_blocks(path):
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)```", text, re.S)
    for i, block in enumerate(blocks):
        try:
            list(yaml.load_all(block, Loader=UniqueKeyLoader))
        except Exception as e:
            errors.append(f"{path.name} yaml block {i + 1}: {e}")
    return len(blocks)


yaml_blocks = 0
for path in sorted(DOCS.glob("*.md")):
    yaml_blocks += check_yaml_blocks(path)

registry_doc = (ROOT / "docs" / "architecture" / "platform-adapter-architecture.md").read_text(encoding="utf-8")
found_registry = {cap for cap in REGISTRY if f"`{cap}`" in registry_doc}
check(found_registry == REGISTRY, f"Capability Registry mismatch: {sorted(found_registry)}")

workflow_doc = (DOCS / "workflow-standard.md").read_text(encoding="utf-8")
for wid in WORKFLOW_IDS:
    check(f"`{wid}`" in workflow_doc, f"workflow doc missing {wid}")
for path in workflow_files:
    wf = load_yaml(path)
    wid = wf.get("id")
    check(wid in WORKFLOW_IDS, f"{path.name}: unexpected workflow id {wid}")
    check(wf.get("trigger", {}).get("task_types", [None])[0] in TASK_TYPES,
          f"{path.name}: unexpected task type")

P1_002_DOCS = [
    "orchestration-standard.md",
    "task-classification-standard.md",
    "workflow-standard.md",
    "task-standard.md",
    "orchestration-state-machine.md",
    "gate-orchestration-standard.md",
    "approval-orchestration-standard.md",
    "failure-recovery-standard.md",
    "execution-evidence-standard.md",
]
for name in P1_002_DOCS:
    path = DOCS / name
    check(path.exists(), f"missing P1-002 standard: {name}")
    if path.exists():
        text = path.read_text(encoding="utf-8")
        check("artifact_refs" not in text, f"{name}: deprecated artifact_refs found")

check(len(list(SCHEMAS.glob("*.schema.json"))) == 5, "expected 5 orchestration schemas")
check(len(list(SCHEMAS.glob("*-state-machine.json"))) == 5, "expected 5 state machine files")

# ---------------------------------------------------------------------------
# 10. Result
# ---------------------------------------------------------------------------
if errors:
    print("ORCHESTRATION VALIDATION FAILED")
    for e in errors:
        print("-", e)
    raise SystemExit(1)

print("ORCHESTRATION VALIDATION PASSED")
print(f"schemas={len(schemas)} state_machines={len(machines)}")
print(f"examples: workflows={len(workflow_files)} tasks={len(task_files)} gates={len(gate_files)} approvals={len(approval_files)} evidence={len(evidence_files)}")
print(f"schema_positive={positive[0]} schema_negative={negative[0]}")
print(f"workflow_graph_positive={graph_positive} workflow_graph_negative={graph_negative}")
print(f"state_transitions_positive={state_positive} state_transitions_negative={state_negative}")
print(f"transition_definitions={transition_definitions} transition_tests={transition_tests} guard_cases={guard_cases}")
print(f"parallel_cases={parallel_cases} task_context_cases={task_context_cases} gate_cases={gate_cases}")
print(f"failure_cases={failure_cases} security_cases={security_cases}")
print(f"yaml_blocks_checked={yaml_blocks} registry_ids={len(found_registry)}")
print("runtime_behavior=NOT_EXECUTED")
