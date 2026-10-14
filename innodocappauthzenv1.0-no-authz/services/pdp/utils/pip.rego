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

document_by_id(id) := doc if {
	# Build a lookup keyed by string ids because AuthZEN uses string "id".
	document_by_id := {sprintf("%v", [r.file_id]): r | r := document_attributes[_]}
	doc := document_by_id[id]
}

