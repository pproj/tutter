package db

import (
	"fmt"
	"time"
)

const (
	FilterParamOrderAscending  = "asc"
	FilterParamOrderDescending = "desc"
)

type CommonPaginationParams struct {
	BeforeId *uint64    `form:"before_id"`
	AfterId  *uint64    `form:"after_id"`
	Before   *time.Time `form:"before"`
	After    *time.Time `form:"after"`
	Limit    *uint      `form:"limit"`
	Order    *string    `form:"order"`
}

type PostFilterParams struct {
	CommonPaginationParams
	Tags    []string `form:"tag"`
	Authors []uint   `form:"author_id"`
}

func (p CommonPaginationParams) Validate() error {

	if p.Before != nil && p.BeforeId != nil {
		return fmt.Errorf("before and before_id must not be used together")
	}

	if p.After != nil && p.AfterId != nil {
		return fmt.Errorf("after and after_id must not be used together")
	}

	// This really grinds my gears...
	if p.BeforeId != nil && p.AfterId != nil && *p.BeforeId < *p.AfterId {
		return fmt.Errorf("before must be after after")
	}

	if p.Before != nil && p.After != nil && p.Before.Before(*p.After) {
		return fmt.Errorf("before must be after after")
	}

	if p.Limit != nil && *p.Limit == 0 {
		return fmt.Errorf("limit 0 makes no sense")
	}

	if (p.Order != nil) && (*p.Order != FilterParamOrderAscending && *p.Order != FilterParamOrderDescending) {
		return fmt.Errorf("order must be either '" + FilterParamOrderAscending + "' or '" + FilterParamOrderDescending + "'")
	}

	return nil
}

func (p PostFilterParams) Validate() error {
	// Call parent validations first
	err := p.CommonPaginationParams.Validate()
	if err != nil {
		return err
	}

	// Custom validation for this type
	if p.Tags != nil && len(p.Tags) > 0 {
		for _, tag := range p.Tags {
			if tag == "" {
				return fmt.Errorf("tag can not be empty string")
			}
		}
	}

	return nil
}
