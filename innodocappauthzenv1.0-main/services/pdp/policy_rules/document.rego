package policy_rules.document

import data.utils.pip

# Document authorization rules.
# This module is the single source of truth for document access decisions.
# It is used by the endpoints evaluation, evaluations, and resource_search.

# Inputs:
# - req.subject: AuthZEN subject object (with properties.secLevel and properties.sources)
# - req.resource: AuthZEN resource object (type document)
# - req.action:  AuthZEN action object (e.g., name == "can_read")

# Entry point for single-decision evaluation.
# If the document id is unknown to the PIP, `document_by_id` yields no value,
# this rule fails, and the caller's default-deny applies.
evaluate(req) if {
	doc := pip.document_by_id(req.resource.id)
	check_document(req.subject, doc, req.action)
}

# Subject-type dispatch. Add a sibling rule with a different subject.type
# guard to support further subject types.
check_document(subject, doc, action) if {
	subject.type == "partner"
	partner_document_condition(subject, doc, action)
}

# Action dispatch for partner subjects.
# Add a sibling rule with a different action.name guard for further actions.
partner_document_condition(partner, doc, action) if {
	action.name == "can_read"
	partner_document_can_read(partner, doc)
}

# Authorization Policy 10
partner_document_can_read(partner, doc) if {
	doc.seclevel <= partner.properties.secLevel
	doc.source in partner.properties.sources
}

