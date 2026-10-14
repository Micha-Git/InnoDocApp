package resource_search

# AuthZEN resource search endpoint.
# Returns every resource of the requested type that the subject is allowed
# to access for the given action. The access decision itself is delegated
# to the resource-specific rules module, so this file stays only a filter.

import data.policy_rules.document as document_rules
import data.utils.pip

# Default to an empty result list so the response shape stays stable
# even when no rule matches (unknown resource type, no permitted items).
default result := {"results": []}

# Document search: iterate over all documents known to the PIP and keep those the subject may access.
result := {"results": results} if {
	input.resource.type == "document"
	results := [
	{
		"id": d.file_id,
		"type": "document",
	} |
		d := pip.document_attributes[_]

		# Delegate access decisions to document policy rules.
		document_rules.check_document(input.subject, d, input.action)
	]
}

# To support an additional resource type, add another result rule
# guarded by input.resource.type == "<type>" that delegates to the
# corresponding rules module (e.g. route_rules.check_route).
