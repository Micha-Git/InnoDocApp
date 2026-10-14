package policy_rules.document

import data.utils.pip

# Document authorization rules.
# This module is the single source of truth for document access decisions.
# It is used by evaluation endpoints and the resource search endpoint.

# Single source of truth for document access.
# Endpoints call this

# Inputs:
# - subject: AuthZEN subject object (with properties.secLevel and properties.sources)
# - resource: AuthZEN resource object (type document)
# - action:  AuthZEN action object (e.g., name == "can_read")

evaluate(subject, resource, action) if {
	doc := pip.document_by_id(resource.id)
	check_document(subject, doc, resource, action)
}

check_document(subject, doc, resource, action) if {
	# Only partners can read documents for now.
	subject.type == "partner"
	partner_document_condition(subject, doc, action)
}

partner_document_condition(subject, doc, action) if {
	action.name == "can_read"

	# Enforce security level and source-based access for reading documents
	doc.seclevel <= subject.properties.secLevel
	doc.source in subject.properties.sources
}

