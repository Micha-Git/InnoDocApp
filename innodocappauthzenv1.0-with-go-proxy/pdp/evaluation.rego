package evaluation

import data.policy_rules.document as doc_rules
import data.utils.pip

default decision := false


decision if {
    allow(input.subject, input.resource)
}

allow(subject, resource) if {
    # Build a lookup keyed by string ids because AuthZEN uses string "id".
    pip_by_id := {sprintf("%v", [r.file_id]): r | r := pip.document_attributes[_]}
    doc := pip_by_id[resource.id]
    doc_rules.check(subject, doc, resource)
}
