package resource_search
import data.utils.pip
import data.policy_rules.document as doc_rules


results = allowed_docs if {
    allowed_docs := [
        {
            "id": d.file_id,
            "type": "document",
            "context": d,
        } | d := pip.document_attributes[_]
            doc_rules.check(input.subject, d, input.resource)
    ]
} else = []
