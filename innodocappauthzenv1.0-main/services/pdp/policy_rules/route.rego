package policy_rules.route

# Endpoint authorization rules.
# These rules gate access to HTTP routes (not document content).

# To add a new subject type and its endpoints:
# 1) Add an evaluate rule and set req.subject.type to the new subject type
# 2) Add a <subject>_route_condition rule that dispatches by action.name
# 3) Add one <subject>_route_<action> rule per allowed path pattern
#
# Example: allow project managers to POST to /manage.
#
# evaluate(req) if {
#     req.subject.type == "project manager"
#     project_manager_route_condition(req.resource, req.action)
# }
#
# project_manager_route_condition(route, action) if {
#     action.name == "POST"
#     project_manager_route_post(route)
# }
#
# project_manager_route_post(route) if {
#     path := split(route.id, "?")[0]
#     path == "/manage"
# }

# Entry point. Dispatches by subject type to the corresponding route condition.
evaluate(req) if {
	req.subject.type == "partner"
	partner_route_condition(req.resource, req.action)
}

# Action dispatch for partner subjects.
partner_route_condition(route, action) if {
    action.name == "GET"
    partner_route_get(route)
}

# Match the docs collection endpoint: /docs
partner_route_get(route) if {
	path := split(route.id, "?")[0]
	path == "/docs"
}

# Match a specific doc endpoint: /docs/<id>
partner_route_get(route) if {
	path := split(route.id, "?")[0]
	startswith(path, "/docs/")
}

