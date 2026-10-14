package policy_rules.route

# Endpoint authorization rules.
# These rules gate access to HTTP routes (not document content).

# To add a new subject and endpoint:
# 1) Add another evaluate rule and set subject.type to the new type
# 2) Add another subject.id_route_condition(route_id, action_name) for the route and action you want to allow.
# 3) Add this rule to the new evaluate function
# If conditions are reused, give them an appropriate name
#
# Example: allow project managers to access /manage.
#
# evaluate(subject, resource, action) if {
#     subject.type == "manager"
#     manager_route_condition(resource.id, action.name)
# }
#
# manager_route_condition(route_id, action_name) if {
#     action_name == "GET"
#     path := split(route_id, "?")[0]
#     path == "/manage"
# }

# Medium-grained endpoint authorization.
evaluate(subject, resource, action) if {
	subject.type == "partner"
	partner_route_condition(resource.id, action.name)
}

# Initial rule: only partners can access /docs and /docs/<file>.

# Match the docs collection endpoint: /docs
partner_route_condition(route_id, action_name) if {
	action_name == "GET"
	path := split(route_id, "?")[0]
	path == "/docs"
}

# Match a specific doc endpoint: /docs/<id>
partner_route_condition(route_id, action_name) if {
	action_name == "GET"
	path := split(route_id, "?")[0]
	startswith(path, "/docs/")
}

