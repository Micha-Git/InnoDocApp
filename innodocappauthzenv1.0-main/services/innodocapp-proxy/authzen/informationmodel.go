package authzen

import (
	"encoding/json"
	"fmt"
)

type Subject struct {
	ID         string                 `json:"id,omitempty"`
	Type       string                 `json:"type,omitempty"`
	Properties map[string]interface{} `json:"properties,omitempty"`
}

type Resource struct {
	ID         string                 `json:"id,omitempty"`
	Type       string                 `json:"type,omitempty"`
	Properties map[string]interface{} `json:"properties,omitempty"`
}

type Action struct {
	Name       string                 `json:"name,omitempty"`
	Properties map[string]interface{} `json:"properties,omitempty"`
}

type Decision struct {
	Decision bool                   `json:"decision,omitempty"`
	Context  map[string]interface{} `json:"context,omitempty"`
}

func (s *Subject) UnmarshalJSON(data []byte) error {
	type Alias Subject
	aux := &struct{ *Alias }{Alias: (*Alias)(s)}
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}
	if s.ID == "" {
		return fmt.Errorf("subject.id is required")
	}
	if s.Type == "" {
		return fmt.Errorf("subject.type is required")
	}
	return nil
}

func (r *Resource) UnmarshalJSON(data []byte) error {
	type Alias Resource
	aux := &struct{ *Alias }{Alias: (*Alias)(r)}
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}
	if r.ID == "" {
		return fmt.Errorf("resource.id is required")
	}
	if r.Type == "" {
		return fmt.Errorf("resource.type is required")
	}
	return nil
}

func (a *Action) UnmarshalJSON(data []byte) error {
	type Alias Action
	aux := &struct{ *Alias }{Alias: (*Alias)(a)}
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}
	if a.Name == "" {
		return fmt.Errorf("action.name is required")
	}
	return nil
}

func (d *Decision) UnmarshalJSON(data []byte) error {
	type Alias Decision
	aux := &struct{ *Alias }{Alias: (*Alias)(d)}
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}
	return nil
}
