package utils.pip

# PIP (Policy Information Point) integration.
# Fetches document attributes from an external service via HTTP.

# -----------------------------
# PIP call
# -----------------------------
document_attributes := resp.body if {
	# PIP endpoint is configured via OPA runtime env.
	pip_url := opa.runtime().env.PIP_DOCUMENT_ATTRIBUTES_URL

	resp := http.send({
		"method": "GET",
		"url": pip_url,
	})
}

# Look up a single document by its id.
# resource ids are strings, while the PIP's file_id may be numeric;
# sprintf("%v", ...) normalises both sides to strings before indexing.
# If id is not present, the rule yields no value (caller sees an undefined
# result, which propagates to default-deny in the evaluation endpoint).
document_by_id(id) := doc if {
	# Build a lookup keyed by string ids because AuthZEN uses string "id".
	by_id := {sprintf("%v", [r.file_id]): r | r := document_attributes[_]}
	doc := by_id[id]
}

