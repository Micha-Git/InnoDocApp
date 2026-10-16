wrk.method = "POST"
wrk.body = '{"input":{"subject":{"type":"partner","id":"john@innocomp.com","properties":{"secLevel":5,"sources":["Project Horizon"]}},"action":{"name":"can_read"},"options":{"evaluations_semantic":"execute_all"},"evaluations":[{"resource":{"type":"document","id":"4"}},{"resource":{"type":"document","id":"101"}},{"resource":{"type":"document","id":"102"}},{"resource":{"type":"document","id":"103"}},{"resource":{"type":"document","id":"104"}}]}}'
wrk.headers["Content-Type"] = "application/json"
