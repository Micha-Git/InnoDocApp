package utils.pip

# -----------------------------
# PIP call
# -----------------------------
document_attributes := resp.body if {
  pip_url := opa.runtime().env.PIP_DOCUMENT_ATTRIBUTES_URL

  resp := http.send({
    "method": "GET",
    "url": pip_url,
  })
}
