package evaluations

# Batch evaluation policy (AuthZEN bulk endpoint).
# Supports different evaluation semantics (execute_all, permit_on_first_permit,
# deny_on_first_deny) and returns a list of decisions.

import data.evaluation

# -----------------------------
# AuthZEN bulk result
# -----------------------------
default result := {"evaluations": []}

result := {"evaluations": results} if {
	evals := object.get(input, "evaluations", [])
	n := count(evals)

	# No evaluations provided -> empty result
	n == 0
	results := []
} else := {"evaluations": results} if {
	evals := object.get(input, "evaluations", [])
	n := count(evals)
	n > 0

	# Allow caller to select how many evaluations to execute.
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
	not semantic
	results := results_execute_all(evals)
}

# -----------------------------
# Semantics implementations
# -----------------------------

# execute_all: return one decision per evaluation
results_execute_all(evals) := results if {
	n := count(evals)
	results := [decision_result(e) | e := evals[_]]
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

# When we short-circuit, include a context reason on the final evaluated item.
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

decision_for_eval(e) if {
	evaluation.evaluate_decision({"subject": input.subject, "resource": e.resource, "action": input.action})
}

