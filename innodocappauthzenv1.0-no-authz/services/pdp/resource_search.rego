package resource_search

# Resource search policy.
# Returns a list of documents the subject is allowed to see.
import data.policy_rules.document as document_rules
import data.utils.pip

# Default to empty list to keep response shape stable.
default result := {"results": []}

# Duplicate method to support another resource type
result := {"results": results} if {
	input.resource.type == "document"
	results := [
	{
		"id": d.file_id,
		"type": "document",
		"context": d,
	} |
		d := pip.document_attributes[_]

		# Delegate access decisions to document policy rules.
		document_rules.check_document(input.subject, d, input.resource, input.action)
	]
}

