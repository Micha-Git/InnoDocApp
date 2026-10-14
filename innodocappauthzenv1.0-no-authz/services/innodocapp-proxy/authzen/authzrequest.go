package authzen

import (
	"encoding/json"
	"fmt"
)

type AuthZRequest struct {
	Subject  *Subject               `json:"subject,omitempty"`
	Action   *Action                `json:"action,omitempty"`
	Resource *Resource              `json:"resource,omitempty"`
	Context  map[string]interface{} `json:"context,omitempty"`
}

func (a *AuthZRequest) UnmarshalJSON(data []byte) error {
	type Alias AuthZRequest
	aux := &struct{ *Alias }{Alias: (*Alias)(a)}
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}
	if a.Subject == nil {
		return fmt.Errorf("authzrequest.subject is required")
	}
	if a.Resource == nil {
		return fmt.Errorf("authzrequest.resource is required")
	}
	if a.Action == nil {
		return fmt.Errorf("authzrequest.action is required")
	}
	return nil
}
