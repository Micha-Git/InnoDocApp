package policy_rules.document

# Single source of truth for document access.
# Endpoints call this

# Inputs:
# - subject: AuthZEN subject object (with properties.secLevel and properties.sources)
# - doc:     document context/attributes (e.g., from PIP)

check(subject, doc, resource) := true if {
    subject.type == "partner"
    resource.type == "document"
    can_read(subject, doc)
}

can_read(subject, doc) := true if {
  doc.seclevel <= subject.properties.secLevel
  doc.source in subject.properties.sources
}