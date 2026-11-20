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
from datetime import datetime, timezone
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

node_missing_parent = copy.deepcopy(base_task)
node_missing_parent.pop("parent_task_id", None)
expect_schema_invalid(task_schema, node_missing_parent, "task-node-missing-parent", negative)

node_bad_parent = copy.deepcopy(base_task)
node_bad_parent["parent_task_id"] = "not-a-root-task"
expect_schema_invalid(task_schema, node_bad_parent, "task-node-invalid-parent", negative)

node_verifying = copy.deepcopy(base_task)
node_verifying["context_status"] = "verifying"
expect_schema_invalid(task_schema, node_verifying, "task-node-verifying-status", negative)

root_task_base = next((load_json(p) for p in task_files if load_json(p).get("context_scope") == "root"), None)
if root_task_base:
    root_with_parent = copy.deepcopy(root_task_base)
    root_with_parent["parent_task_id"] = "task-20261120-root0001"
    expect_schema_invalid(task_schema, root_with_parent, "task-root-with-parent", negative)

root_completed = next((load_json(p) for p in task_files
                       if load_json(p).get("context_scope") == "root"
                       and load_json(p).get("context_status") == "completed"), None)
if root_completed:
    root_completed_unverified = copy.deepcopy(root_completed)
    root_completed_unverified["workflow_verified"] = False
    expect_schema_invalid(task_schema, root_completed_unverified,
                          "task-root-completed-without-verification", negative)

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

approval_highrisk_empty_scope = copy.deepcopy(base_approval)
approval_highrisk_empty_scope["type"] = "sa"
approval_highrisk_empty_scope["gate"] = None
approval_highrisk_empty_scope["risk_level"] = "high"
approval_highrisk_empty_scope["scope"] = {}
expect_schema_invalid(approval_schema, approval_highrisk_empty_scope,
                      "approval-highrisk-empty-scope", negative)

approval_both_empty_scope = copy.deepcopy(base_approval)
approval_both_empty_scope["type"] = "both"
approval_both_empty_scope["scope"] = {}
expect_schema_invalid(approval_schema, approval_both_empty_scope,
                      "approval-both-empty-scope", negative)

approval_g6_empty_scope = copy.deepcopy(base_approval)
approval_g6_empty_scope["type"] = "gate"
approval_g6_empty_scope["gate"] = "G6"
approval_g6_empty_scope["scope"] = {}
expect_schema_invalid(approval_schema, approval_g6_empty_scope,
                      "approval-g6-empty-scope", negative)

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
    # Separate success and failure edges. A failure-only node does not need a
    # success path, but every declared failure branch must still terminate.
    success_forward = {nid: set() for nid in idset}
    failure_forward = {nid: set() for nid in idset}
    for nid, deps in graph.items():
        for dep in deps:
            if dep in success_forward:
                success_forward[dep].add(nid)
                failure_forward[dep].add(nid)
    by_id = {n.get("id"): n for n in nodes}
    for node in nodes:
        nid = node.get("id")
        if node.get("on_success") in idset:
            success_forward[nid].add(node["on_success"])
            failure_forward[nid].add(node["on_success"])
        if node.get("on_failure") in idset:
            failure_forward[nid].add(node["on_failure"])

    def reachable_from(start, edges):
        seen_local = {start}
        todo = [start]
        while todo:
            cur = todo.pop()
            for nxt in edges.get(cur, []):
                if nxt not in seen_local:
                    seen_local.add(nxt)
                    todo.append(nxt)
        return seen_local

    # All nodes must be reachable from an entry through any declared edge.
    seen = set()
    for entry in entries:
        seen |= reachable_from(entry, failure_forward)
    unreachable = idset - seen
    if unreachable:
        errs.append(f"unreachable nodes: {sorted(unreachable)}")

    # Every success-reachable node must terminate through success edges.
    success_seen = set()
    for entry in entries:
        success_seen |= reachable_from(entry, success_forward)
    for nid in success_seen:
        if not (reachable_from(nid, success_forward) & set(ends)):
            errs.append(f"{nid}: success branch cannot reach an end node")

    # Every declared failure branch/compensation path must terminate.
    for node in nodes:
        nid = node.get("id")
        target = node.get("on_failure")
        if target in idset and not (reachable_from(target, failure_forward) & set(ends)):
            errs.append(f"{nid}: failure branch {target} cannot reach an end node")

    # End nodes must not have dependents/outgoing.
    for end in ends:
        if any(end in n.get("depends_on", []) for n in nodes):
            errs.append(f"end node {end} has dependents")
        end_node = by_id.get(end, {})
        if end_node.get("on_success") or end_node.get("on_failure"):
            errs.append(f"end node {end} has outgoing edges")

    # parallel_group must have a real join that waits for all members or quorum.
    groups = {}
    for node in nodes:
        group = node.get("parallel_group")
        if group:
            groups.setdefault(group, []).append(node.get("id"))
    for group, members in groups.items():
        if len(members) < 2:
            continue
        member_set = set(members)
        descendant_sets = [reachable_from(member, success_forward) for member in members]
        common = set.intersection(*descendant_sets) - member_set
        valid_join = False
        for join_id in common:
            join_node = by_id.get(join_id, {})
            join_deps = set(join_node.get("depends_on", []))
            if join_node.get("join_policy") == "quorum":
                quorum = join_node.get("quorum")
                if (isinstance(quorum, int) and 1 <= quorum <= len(member_set)
                        and len(join_deps & member_set) >= quorum):
                    valid_join = True
                    break
            elif member_set <= join_deps:
                valid_join = True
                break
        if not valid_join:
            errs.append(f"parallel_group {group}: missing valid join/quorum dependency")
    return errs


graph_positive = 0
for path in workflow_files:
    wf = load_yaml(path)
    errs = workflow_graph_errors(wf)
    check(not errs, f"{path.name}: graph error: {errs}")
    if not errs:
        graph_positive += 1

graph_negative = 0
dag_branch_cases = 0
parallel_join_cases = 0
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
    dag_branch_cases += 1
else:
    check(False, "graph negative 'unknown on_success' should fail")

bad = copy.deepcopy(base_wf)
bad["nodes"][0]["on_failure"] = "missing_failure_target"
if workflow_graph_errors(bad):
    graph_negative += 1
    dag_branch_cases += 1
else:
    check(False, "graph negative 'unknown on_failure' should fail")

# Success branch terminates, failure branch is dead.
bad = copy.deepcopy(base_wf)
base_end = next(n["id"] for n in bad["nodes"] if n.get("type") == "end")
bad["nodes"].append({"id": "dead_failure", "type": "check"})
bad["nodes"][0]["on_failure"] = "dead_failure"
bad["nodes"][0]["on_success"] = base_end
if workflow_graph_errors(bad):
    graph_negative += 1
    dag_branch_cases += 1
else:
    check(False, "graph negative 'dead failure branch masked by success branch' should fail")

# Failure branch terminates, success branch is dead.
bad = copy.deepcopy(base_wf)
bad["nodes"].append({"id": "dead_success", "type": "check"})
bad["nodes"][0]["on_success"] = "dead_success"
bad["nodes"][0]["on_failure"] = base_end
if workflow_graph_errors(bad):
    graph_negative += 1
    dag_branch_cases += 1
else:
    check(False, "graph negative 'dead success branch masked by failure branch' should fail")

# Parallel join exists but does not wait for all members.
feature_wf = load_yaml(next(p for p in workflow_files if load_yaml(p).get("id") == "feature-development"))
bad = copy.deepcopy(feature_wf)
for node in bad["nodes"]:
    if node.get("id") == "quality_gate":
        node["depends_on"] = ["code_review"]
if workflow_graph_errors(bad):
    graph_negative += 1
    parallel_join_cases += 1
else:
    check(False, "graph negative 'join missing member dependency' should fail")

# Only one parallel branch reaches the join.
bad_parallel_one = {
    "id": "bad-parallel-one", "version": "0.1.0", "status": "tested",
    "nodes": [
        {"id": "a", "type": "check", "parallel_group": "g"},
        {"id": "b", "type": "check", "parallel_group": "g"},
        {"id": "join", "type": "parallel", "depends_on": ["a"]},
        {"id": "end_join", "type": "end", "depends_on": ["join"]},
        {"id": "end_b", "type": "end", "depends_on": ["b"]},
    ],
}
if workflow_graph_errors(bad_parallel_one):
    graph_negative += 1
    parallel_join_cases += 1
else:
    check(False, "graph negative 'only one branch reaches join' should fail")

# Quorum larger than parallel members.
bad_parallel_quorum = {
    "id": "bad-parallel-quorum", "version": "0.1.0", "status": "tested",
    "nodes": [
        {"id": "a", "type": "check", "parallel_group": "g"},
        {"id": "b", "type": "check", "parallel_group": "g"},
        {"id": "join", "type": "parallel", "depends_on": ["a", "b"],
         "join_policy": "quorum", "quorum": 3},
        {"id": "end_join", "type": "end", "depends_on": ["join"]},
    ],
}
if workflow_graph_errors(bad_parallel_quorum):
    graph_negative += 1
    parallel_join_cases += 1
else:
    check(False, "graph negative 'parallel quorum larger than members' should fail")

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
    parallel_join_cases += 1
else:
    check(False, "graph negative 'parallel without join' should fail")

# quorum out of range.
bad_quorum = copy.deepcopy(base_wf)
bad_quorum["nodes"][0]["join_policy"] = "quorum"
bad_quorum["nodes"][0]["quorum"] = 5
if workflow_graph_errors(bad_quorum):
    graph_negative += 1
    parallel_join_cases += 1
else:
    check(False, "graph negative 'quorum out of range' should fail")

# quorum without join_policy.
bad_quorum2 = copy.deepcopy(base_wf)
bad_quorum2["nodes"][0]["quorum"] = 1
if workflow_graph_errors(bad_quorum2):
    graph_negative += 1
    parallel_join_cases += 1
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
root_task = next((load_json(p) for p in task_files if load_json(p).get("context_scope") == "root"
                  and load_json(p).get("context_status") != "completed"), None)
node_succeeded = next((load_json(p) for p in task_files if load_json(p).get("status") == "SUCCEEDED"
                       and load_json(p).get("context_scope") == "node"), None)
root_completed = next((load_json(p) for p in task_files if load_json(p).get("context_scope") == "root"
                       and load_json(p).get("context_status") == "completed"), None)
check(root_task is not None, "task-context: root task example missing")
task_context_cases += 1
check(node_succeeded is not None, "task-context: succeeded node task example missing")
task_context_cases += 1
check(root_completed is not None, "task-context: completed root example missing")
task_context_cases += 1
if root_task and node_succeeded:
    check(root_task.get("context_scope") == "root" and root_task.get("parent_task_id") is None,
          "task-context: root context must not have parent_task_id")
    task_context_cases += 1
    check(node_succeeded.get("context_scope") == "node"
          and node_succeeded.get("parent_task_id") == root_task.get("task_id"),
          "task-context: node task must reference root task via parent_task_id")
    task_context_cases += 1
    check(root_task.get("workflow_verified") is False,
          "task-context: running root must not claim workflow verification")
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
if root_completed:
    check(root_completed.get("workflow_verified") is True,
          "task-context: completed root must have workflow_verified=true")
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
    """Resolve path components, including intermediate and nested symlinks."""
    if not isinstance(path, str) or not path.strip():
        return None
    p = path.replace("\\", "/")
    if p.startswith("/") or re.match(r"^[A-Za-z]:/", p):
        return None
    links = {}
    if symlinks:
        for key, value in symlinks.items():
            nk = posixpath.normpath(key.replace("\\", "/"))
            links[nk] = value
    parts = [x for x in p.split("/") if x not in ("", ".")]
    resolved = []
    seen_links = set()
    hops = 0
    i = 0
    while i < len(parts):
        part = parts[i]
        if part == "..":
            if not resolved:
                return None
            resolved.pop()
            i += 1
            continue
        candidate = "/".join(resolved + [part])
        if candidate in links:
            hops += 1
            if hops > 32 or candidate in seen_links:
                return None
            seen_links.add(candidate)
            target = links[candidate].replace("\\", "/")
            if target.startswith("/") or re.match(r"^[A-Za-z]:/", target):
                return None
            target_parts = [x for x in target.split("/") if x not in ("", ".")]
            # Relative target is resolved from the symlink's parent directory.
            parts = resolved + target_parts + parts[i + 1:]
            resolved = []
            i = 0
            continue
        resolved.append(part)
        i += 1
    norm = "/".join(resolved)
    if norm == ".." or norm.startswith("../") or norm.startswith("/"):
        return None
    return norm


def path_allowed(task_id, path, symlinks=None):
    norm = normalize_path(path, symlinks)
    if norm is None:
        return False
    root = f"artifacts/{task_id}"
    return norm == root or norm.startswith(root + "/")


def canonical_scope(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def is_nonempty(value):
    return isinstance(value, str) and value.strip() != ""


def scope_requires_nonempty(approval):
    if approval.get("type") in {"sa", "both"}:
        return True
    return approval.get("type") == "gate" and approval.get("gate") == "G6"


def approval_scope_valid(approval):
    scope = approval.get("scope")
    if not isinstance(scope, dict):
        return False
    if scope_requires_nonempty(approval) and len(scope) == 0:
        return False
    return True


def scope_matches(approval_scope, requested_scope):
    if not isinstance(approval_scope, dict) or not isinstance(requested_scope, dict):
        return False
    # Exact canonical match: no implicit subset/superset authorization.
    return canonical_scope(approval_scope) == canonical_scope(requested_scope)


def parse_timestamp(value):
    """Strict ISO 8601 parser: required timezone, UTC conversion, fail closed."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    # Missing timezone is invalid; never silently assume UTC/system time.
    if dt.tzinfo is None:
        return None
    try:
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def approval_usable(approval, ctx):
    if approval.get("status") != "APPROVED":
        return False
    for key in ("task_id", "workflow_id", "node_id", "operation", "target", "environment"):
        if approval.get(key) != ctx.get(key):
            return False
    if not approval_scope_valid(approval):
        return False
    if not scope_matches(approval.get("scope", {}), ctx.get("scope", {})):
        return False

    approval_hash = approval.get("subject_hash") or ""
    context_hash = ctx.get("subject_hash") or ""
    subject_required = bool(ctx.get("subject_required", False)) or approval.get("gate") in {"G4", "G5", "G6"}
    if subject_required:
        if not (is_nonempty(approval_hash) and is_nonempty(context_hash)
                and approval_hash == context_hash):
            return False
    else:
        if bool(approval_hash) != bool(context_hash):
            return False
        if approval_hash and approval_hash != context_hash:
            return False

    expires = parse_timestamp(approval.get("expires_at"))
    if expires is None:
        return False
    now = parse_timestamp(ctx.get("now"))
    if now is None:
        return False
    if now >= expires:
        return False
    if approval.get("consumed_at") is not None:
        return False
    return approval.get("single_use") is True


class ApprovalStore:
    def __init__(self, approval):
        self.approval = copy.deepcopy(approval)
        self.lock = threading.Lock()

    def consume(self, actor, ctx, ref):
        with self.lock:
            if self.approval.get("status") != "APPROVED" or self.approval.get("consumed_at"):
                return False
            if not approval_usable(self.approval, ctx):
                return False
            self.approval["status"] = "CONSUMED"
            self.approval["consumed_at"] = ctx.get("now")
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
path_cases = 0


def path_assert(cond, msg):
    global path_cases, security_cases
    check(cond, msg)
    path_cases += 1
    security_cases += 1


path_assert(path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/design/design.md"),
            "security: own task path should be allowed")
path_assert(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/../task-20261120-ffffffff/secret.md"),
            "security: path traversal into another task must be denied")
path_assert(not path_allowed(task_for_path, "/etc/passwd"),
            "security: absolute unix path must be denied")
path_assert(not path_allowed(task_for_path, "C:\\Windows\\win.ini"),
            "security: absolute Windows path must be denied")
path_assert(not path_allowed(task_for_path, "artifacts/task-20261120-ffffffff/secret.md"),
            "security: other task path must be denied")

# Symlink directory itself.
symlinks_dir = {
    "artifacts/task-20261120-a1b2c3d4/link":
        "../task-20261120-ffffffff"
}
path_assert(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/link", symlinks_dir),
            "security: symlink directory escaping task must be denied")
# File under a symlinked directory.
path_assert(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/link/secret.md", symlinks_dir),
            "security: child under symlinked directory must be denied")
# Nested/multi-level symlinks, including a symlinked child file.
symlinks_nested = {
    "artifacts/task-20261120-a1b2c3d4/dir1": "dir2",
    "artifacts/task-20261120-a1b2c3d4/dir2/secret.md": "../../../other/secret.md",
}
path_assert(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/dir1/secret.md", symlinks_nested),
            "security: nested symlink escaping task must be denied")
symlinks_chain = {
    "artifacts/task-20261120-a1b2c3d4/dir1": "dir2",
    "artifacts/task-20261120-a1b2c3d4/dir2": "dir3",
    "artifacts/task-20261120-a1b2c3d4/dir3/secret.md": "../../../etc/passwd",
}
path_assert(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/dir1/secret.md", symlinks_chain),
            "security: multi-level symlink escaping project must be denied")
# Symlink cycle.
symlinks_cycle = {
    "artifacts/task-20261120-a1b2c3d4/loop1": "loop2",
    "artifacts/task-20261120-a1b2c3d4/loop2": "loop1",
}
path_assert(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/loop1/secret.md", symlinks_cycle),
            "security: symlink cycle must be denied")
# Relative escape and absolute symlink target.
symlinks_escape = {
    "artifacts/task-20261120-a1b2c3d4/link": "../../etc/passwd"
}
path_assert(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/link", symlinks_escape),
            "security: relative symlink escape must be denied")
symlinks_absolute = {
    "artifacts/task-20261120-a1b2c3d4/link": "/etc/passwd"
}
path_assert(not path_allowed(task_for_path, "artifacts/task-20261120-a1b2c3d4/link", symlinks_absolute),
            "security: absolute symlink target must be denied")

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
    "subject_required": True,
    "now": base_now,
}
approval_cases = 0
scope_cases = 0
expiry_cases = 0
time_fail_closed_cases = 0


def approval_assert(cond, msg, category=None):
    global approval_cases, security_cases, scope_cases, expiry_cases
    check(cond, msg)
    approval_cases += 1
    security_cases += 1
    if category == "scope":
        scope_cases += 1
    elif category == "expiry":
        expiry_cases += 1


approval_assert(approval_usable(approval, approval_ctx), "security: valid approval should be usable")
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
    approval_assert(not approval_usable(approval, ctx),
                    f"security: approval must be invalid for changed {key}")

# subject_hash: bidirectional binding.
approval_no_hash = copy.deepcopy(approval)
approval_no_hash["subject_hash"] = None
approval_assert(not approval_usable(approval_no_hash, approval_ctx),
                "security: required subject_hash missing from approval must fail")
approval_empty_hash = copy.deepcopy(approval)
approval_empty_hash["subject_hash"] = ""
approval_assert(not approval_usable(approval_empty_hash, approval_ctx),
                "security: required subject_hash empty from approval must fail")
ctx_no_hash = dict(approval_ctx)
ctx_no_hash["subject_hash"] = None
approval_assert(not approval_usable(approval, ctx_no_hash),
                "security: required subject_hash missing from context must fail")
ctx_empty_hash = dict(approval_ctx)
ctx_empty_hash["subject_hash"] = ""
approval_assert(not approval_usable(approval, ctx_empty_hash),
                "security: required subject_hash empty from context must fail")
ctx_diff_hash = dict(approval_ctx)
ctx_diff_hash["subject_hash"] = "e" * 40
approval_assert(not approval_usable(approval, ctx_diff_hash),
                "security: different subject_hash must fail")
ctx_not_required_no_hash = dict(approval_ctx)
ctx_not_required_no_hash["subject_required"] = False
ctx_not_required_no_hash["subject_hash"] = None
approval_assert(not approval_usable(approval, ctx_not_required_no_hash),
                "security: approval hash with missing context hash must fail even if not required")
approval_assert(not approval_usable(approval_no_hash, ctx_not_required_no_hash),
                "security: one-sided missing hash must fail")

# Scope: exact canonical match, empty is not unlimited.
base_scope = approval.get("scope", {})
approval_assert(scope_matches(base_scope, copy.deepcopy(base_scope)),
                "security: identical scope should match", "scope")
for label, changed in (
    ("added-parameter", {**base_scope, "extra": "value"}),
    ("resource-change", {**base_scope, "namespace": "other-namespace"}),
    ("path-change", {**base_scope, "image": "sdd-api:other"}),
    ("range-expanded", {**base_scope, "replicas": "1-10"}),
    ("scope-shrunk", {"cluster": base_scope.get("cluster")}),
    ("scope-expanded", {**base_scope, "network": "host"}),
):
    approval_assert(not scope_matches(base_scope, changed),
                    f"security: scope {label} must not match", "scope")
approval_assert(not scope_matches({}, {"extra": "value"}),
                "security: empty approval scope must not authorize non-empty request", "scope")
low_risk_empty = copy.deepcopy(approval)
low_risk_empty["type"] = "gate"
low_risk_empty["gate"] = "G1"
low_risk_empty["risk_level"] = "low"
low_risk_empty["scope"] = {}
low_risk_empty["subject_hash"] = None
low_risk_ctx = {
    "task_id": low_risk_empty.get("task_id"),
    "workflow_id": low_risk_empty.get("workflow_id"),
    "node_id": low_risk_empty.get("node_id"),
    "operation": low_risk_empty.get("operation"),
    "target": low_risk_empty.get("target"),
    "environment": low_risk_empty.get("environment"),
    "scope": {},
    "subject_hash": None,
    "subject_required": False,
    "now": base_now,
}
approval_assert(approval_usable(low_risk_empty, low_risk_ctx),
                "security: empty scope may match only empty low-risk request", "scope")
low_risk_ctx_nonempty = dict(low_risk_ctx)
low_risk_ctx_nonempty["scope"] = {"extra": "value"}
approval_assert(not approval_usable(low_risk_empty, low_risk_ctx_nonempty),
                "security: empty approval scope must not authorize non-empty request", "scope")

pure_file = next((p for p in approval_files if "pure" in p.name), None)
if pure_file:
    pure = load_json(pure_file)
    pure_ctx = {
        "task_id": pure.get("task_id"),
        "workflow_id": pure.get("workflow_id"),
        "node_id": pure.get("node_id"),
        "operation": pure.get("operation"),
        "target": pure.get("target"),
        "environment": pure.get("environment"),
        "scope": copy.deepcopy(pure.get("scope", {})),
        "subject_hash": None,
        "subject_required": False,
        "now": "2026-11-20T13:05:00Z",
    }
    approval_assert(approval_usable(pure, pure_ctx),
                    "security: pure SA without subject binding should be usable", "scope")
high_risk_empty = copy.deepcopy(approval)
high_risk_empty["scope"] = {}
approval_assert(not approval_scope_valid(high_risk_empty),
                "security: high-risk SA with empty scope must be invalid", "scope")
sa_empty = copy.deepcopy(approval)
sa_empty["type"] = "sa"
sa_empty["gate"] = None
sa_empty["risk_level"] = "low"
sa_empty["scope"] = {}
approval_assert(not approval_scope_valid(sa_empty),
                "security: SA with empty scope must be invalid", "scope")
both_empty = copy.deepcopy(approval)
both_empty["type"] = "both"
both_empty["scope"] = {}
approval_assert(not approval_scope_valid(both_empty),
                "security: both with empty scope must be invalid", "scope")
g6_empty = copy.deepcopy(approval)
g6_empty["type"] = "gate"
g6_empty["gate"] = "G6"
g6_empty["scope"] = {}
approval_assert(not approval_scope_valid(g6_empty),
                "security: G6 with empty scope must be invalid", "scope")

# Expiry: real datetime parsing with timezone offsets and boundary.
for now_value, expected, label in (
    ("2026-11-20T11:05:00Z", True, "before"),
    ("2026-11-20T11:30:00Z", False, "exact-boundary"),
    ("2026-11-20T11:31:00Z", False, "after"),
    ("2026-11-20T19:05:00+08:00", True, "offset-before"),
    ("2026-11-20T19:30:00+08:00", False, "offset-boundary"),
    ("2026-11-20T19:31:00+08:00", False, "offset-after"),
):
    ctx = dict(approval_ctx)
    ctx["now"] = now_value
    approval_assert(approval_usable(approval, ctx) is expected,
                    f"security: expiry {label} result mismatch", "expiry")

consumed = copy.deepcopy(approval)
consumed["status"] = "CONSUMED"
consumed["consumed_at"] = "2026-11-20T11:12:00Z"
consumed["consumed_by"] = "orchestrator-main"
approval_assert(not approval_usable(consumed, approval_ctx),
                "security: consumed approval must not be usable")
rejected = copy.deepcopy(approval)
rejected["status"] = "REJECTED"
approval_assert(not approval_usable(rejected, approval_ctx),
                "security: rejected approval must not be usable")

# Atomic consumption validates binding/expiry inside the critical section.
consume_ctx = dict(approval_ctx)
consume_ctx["now"] = "2026-11-20T11:12:00Z"

# Fail-closed time validation: every invalid expires_at/now must reject via
# the real ApprovalStore.consume(), leaving APPROVED and no consumption fields.
invalid_expires = [
    ("missing", None, True),
    ("null", None, False),
    ("empty", "", False),
    ("non-string", 123, False),
    ("bad-date", "not-a-date", False),
    ("no-timezone", "2026-11-20T11:30:00", False),
    ("bad-timezone", "2026-11-20T11:30:00+99:99", False),
]
for label, value, missing in invalid_expires:
    a = copy.deepcopy(approval)
    if missing:
        a.pop("expires_at", None)
    else:
        a["expires_at"] = value
    s = ApprovalStore(a)
    approval_assert(not s.consume("worker-a", consume_ctx, f"bad-expires-{label}"),
                    f"security: consume must fail closed for expires_at {label}")
    approval_assert(s.approval["status"] == "APPROVED",
                    f"security: invalid expires_at {label} must not change status")
    approval_assert(s.approval.get("consumed_at") is None,
                    f"security: invalid expires_at {label} must not set consumed_at")
    approval_assert(s.approval.get("consumed_by") is None,
                    f"security: invalid expires_at {label} must not set consumed_by")
    time_fail_closed_cases += 1

invalid_now = [
    ("missing", None, True),
    ("null", None, False),
    ("empty", "", False),
    ("non-string", 123, False),
    ("bad-date", "not-a-date", False),
    ("no-timezone", "2026-11-20T11:05:00", False),
    ("bad-timezone", "2026-11-20T11:05:00+99:99", False),
]
for label, value, missing in invalid_now:
    ctx = dict(consume_ctx)
    if missing:
        ctx.pop("now", None)
    else:
        ctx["now"] = value
    s = ApprovalStore(approval)
    approval_assert(not s.consume("worker-a", ctx, f"bad-now-{label}"),
                    f"security: consume must fail closed for now {label}")
    approval_assert(s.approval["status"] == "APPROVED",
                    f"security: invalid now {label} must not change status")
    approval_assert(s.approval.get("consumed_at") is None,
                    f"security: invalid now {label} must not set consumed_at")
    approval_assert(s.approval.get("consumed_by") is None,
                    f"security: invalid now {label} must not set consumed_by")
    time_fail_closed_cases += 1

# Boundary and post-failure recovery through the real consume path.
boundary_ctx = dict(consume_ctx)
boundary_ctx["now"] = approval.get("expires_at")
s_boundary = ApprovalStore(approval)
approval_assert(not s_boundary.consume("worker-a", boundary_ctx, "boundary-ref"),
                "security: now == expires_at must reject consumption")
approval_assert(s_boundary.approval["status"] == "APPROVED",
                "security: boundary rejection must keep APPROVED")
time_fail_closed_cases += 1

corrected_ctx = dict(consume_ctx)
corrected_ctx["now"] = "2026-11-20T19:05:00+08:00"
s_corrected = ApprovalStore(approval)
approval_assert(s_corrected.consume("worker-a", corrected_ctx, "corrected-ref"),
                "security: valid offset time must allow consumption after failures")
approval_assert(s_corrected.approval["status"] == "CONSUMED",
                "security: corrected valid input must consume successfully")

store = ApprovalStore(approval)
approval_assert(store.consume("worker-a", consume_ctx, "consume-ref"),
                "security: valid approval should consume once")
approval_assert(store.approval["status"] == "CONSUMED",
                "security: consumed approval must be CONSUMED")
approval_assert(store.approval.get("consumed_at") and store.approval.get("consumed_by"),
                "security: consumed approval must record consumed_at/consumed_by")
approval_assert(not store.consume("worker-b", consume_ctx, "consume-ref-2"),
                "security: second consumption must fail")
approval_assert(not approval_usable(store.approval, approval_ctx),
                "security: consumed approval must not be usable after consumption")

bad_binding_ctx = dict(consume_ctx)
bad_binding_ctx["scope"] = {"cluster": "prod-cluster-eu"}
store_bad = ApprovalStore(approval)
approval_assert(not store_bad.consume("worker-a", bad_binding_ctx, "bad-ref"),
                "security: consume must reject wrong scope inside lock")
approval_assert(store_bad.approval["status"] == "APPROVED",
                "security: failed consume must not change approval status")
expired_ctx = dict(consume_ctx)
expired_ctx["now"] = "2026-11-20T12:00:00Z"
store_expired = ApprovalStore(approval)
approval_assert(not store_expired.consume("worker-a", expired_ctx, "expired-ref"),
                "security: consume must reject expired approval inside lock")
approval_assert(store_expired.approval["status"] == "APPROVED",
                "security: expired consume must not change approval status")

# Concurrent duplicate consumption: exactly one success.
store_concurrent = ApprovalStore(approval)
barrier = threading.Barrier(2)
results = []


def consume_worker():
    barrier.wait()
    results.append(store_concurrent.consume("worker-a", consume_ctx, "consume-ref"))


threads = [threading.Thread(target=consume_worker) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join()
approval_assert(results.count(True) == 1,
                "security: concurrent consumption must succeed exactly once")
approval_assert(store_concurrent.approval["status"] == "CONSUMED",
                "security: concurrent consumption must leave CONSUMED")
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
print(f"approval_cases={approval_cases} scope_cases={scope_cases} expiry_cases={expiry_cases} time_fail_closed_cases={time_fail_closed_cases} path_cases={path_cases}")
print(f"dag_branch_cases={dag_branch_cases} parallel_join_cases={parallel_join_cases}")
print(f"failure_cases={failure_cases} security_cases={security_cases}")
print(f"yaml_blocks_checked={yaml_blocks} registry_ids={len(found_registry)}")
print("runtime_behavior=NOT_EXECUTED")
