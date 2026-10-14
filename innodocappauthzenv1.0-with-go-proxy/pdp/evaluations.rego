package evaluations

import data.utils.pip
import data.policy_rules.document as doc_rules


# -----------------------------
# AuthZEN bulk response
# -----------------------------
response := {"evaluations": results} if {
  evals := object.get(input, "evaluations", [])
  n := count(evals)

  # No evaluations provided -> empty response
  n == 0
  results := []
} else := {"evaluations": results} if {
  evals := object.get(input, "evaluations", [])
  n := count(evals)
  n > 0

  semantic := lower(object.get(object.get(input, "options", {}), "evaluations_semantic", "execute_all"))

  results := results_for_semantic(semantic, evals)
}

results_for_semantic(semantic, evals) := results if {
  semantic == "execute_all"
  results := results_execute_all(evals)
} else := results if {
  semantic == "permit_on_first_permit"
  results := results_permit_on_first_permit(evals)
} else := results if {
  semantic == "deny_on_first_deny"
  results := results_deny_on_first_deny(evals)
} else := results if {
  # Fallback for unknown semantics
  results := results_execute_all(evals)
}

# -----------------------------
# Semantics implementations
# -----------------------------

# execute_all: return one decision per evaluation
results_execute_all(evals) := results if {
  n := count(evals)
  results := [decision_result(evals[i]) | i := numbers.range(0, n - 1)[_]]
}

# permit_on_first_permit:
# Return results in order up to the first permit.
# If no permit occurs, return all results.
results_permit_on_first_permit(evals) := results if {
  n := count(evals)
  permit_idx := first_permit_index(evals)
  results := [decision_result_short_circuit(evals, i, permit_idx, n, "permit_on_first_permit") | i := numbers.range(0, permit_idx)[_]]
} else := results if {
  results := results_execute_all(evals)
}

# deny_on_first_deny:
# Return results in order up to the first deny.
# If no deny occurs, return all results.
results_deny_on_first_deny(evals) := results if {
  n := count(evals)
  deny_idx := first_deny_index(evals)
  results := [decision_result_short_circuit(evals, i, deny_idx, n, "deny_on_first_deny") | i := numbers.range(0, deny_idx)[_]]
} else := results if {
  results := results_execute_all(evals)
}

first_permit_index(evals) := idx if {
  n := count(evals)
  permit_idxs := {i | i := numbers.range(0, n - 1)[_]; decision_for_eval(evals[i])}
  count(permit_idxs) > 0
  idx := min(permit_idxs)
}

first_deny_index(evals) := idx if {
  n := count(evals)
  deny_idxs := {i | i := numbers.range(0, n - 1)[_]; not decision_for_eval(evals[i])}
  count(deny_idxs) > 0
  idx := min(deny_idxs)
}

decision_result(e) := {"decision": decision_for_eval(e)}

decision_result_short_circuit(evals, i, cut_idx, n, reason) := result if {
  decision := decision_for_eval(evals[i])
  i == cut_idx
  cut_idx < n - 1
  reason != ""
  result := {"decision": decision, "context": {"reason": reason}}
} else := result if {
  decision := decision_for_eval(evals[i])
  result := {"decision": decision}
}

# -----------------------------
# Decision for a single evaluation
# -----------------------------
default decision_for_eval(e) := false

decision_for_eval(e) := true if {
  input.action.name == "can_read"

  rid := e.resource.id

  # PIP returns rows like:
  # [{"file_id":100,"seclevel":1,"source":"Project Horizon"}, ...]
  # Build a lookup keyed by string ids because AuthZEN uses string "id".
  pip_by_id := {sprintf("%v", [r.file_id]): r | r := pip.document_attributes[_]}

  d := pip_by_id[rid]
  doc_rules.check(input.subject, d, e.resource)
}
