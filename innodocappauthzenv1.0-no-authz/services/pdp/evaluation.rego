package evaluation

import data.policy_rules.document as document_rules
import data.policy_rules.route as route_rules

# Single evaluation policy (AuthZEN-compliant).

# Default deny with 401 (unauthorized) when no rule matches.
default result := {"decision": false, "context": {"httpStatus": 401}}

result := {"decision": true} if {
	input.resource.type == "route"
	route_rules.evaluate(input.subject, input.resource, input.action)
}

result := {"decision": true} if {
	input.resource.type == "document"
	document_rules.evaluate(input.subject, input.resource, input.action)
}
