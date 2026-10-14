package authzen

import (
	"encoding/json"
	"fmt"
)

type AuthZResponse struct {
	Decision bool                   `json:"decision,omitempty"`
	Context  map[string]interface{} `json:"context,omitempty"`
}

func (r *AuthZResponse) UnmarshalJSON(data []byte) error {
	type Alias AuthZResponse
	aux := &struct{ *Alias }{Alias: (*Alias)(r)}
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}

	var raw map[string]json.RawMessage
	if err := json.Unmarshal(data, &raw); err != nil {
		return err
	}
	if _, ok := raw["decision"]; !ok {
		return fmt.Errorf("authzresponse.decision is required")
	}
	return nil
}
