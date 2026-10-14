package evaluation

# AuthZEN access evaluation endpoint.
# Dispatches a request to the matching resource-type rules under policy_rules/
# and returns an AuthZEN decision response: {"decision": true|false}.

import data.policy_rules.document as document_rules
import data.policy_rules.route as route_rules

# Default deny: applied when no evaluate_decision rule matches
# (unknown resource type, missing data, or all policy rules failing).
default result := {"decision": false}

result := {"decision": true} if {
	evaluate_decision(input)
}

# Dispatch by resource type. Each branch delegates to the resource-specific
# rules module, keeping this file free of policy logic.
evaluate_decision(req) if {
	req.resource.type == "route"
	route_rules.evaluate(req)
}

evaluate_decision(req) if {
	req.resource.type == "document"
	document_rules.evaluate(req)
}

# To support an additional resource type:
# 1. Create policy_rules/<type>.rego exposing an evaluate(req) rule
# 2. Import it here, e.g. import data.policy_rules.<type> as <type>_rules
# 3. Add a new evaluate_decision:
#
# evaluate_decision(req) if {
#   req.resource.type == "<type>"
#   <type>_rules.evaluate(req)
# }
