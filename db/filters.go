package db

import (
	"fmt"
	"time"
)

const (
	FilterParamOrderAscending  = "asc"
	FilterParamOrderDescending = "desc"
)

type CommonPagination struct {
	BeforeId *uint64    `form:"before_id"`
	AfterId  *uint64    `form:"after_id"`
	Before   *time.Time `form:"before"`
	After    *time.Time `form:"after"`
	Limit    *uint      `form:"limit"`
	Order    *string    `form:"order"`
}

type PostFilters struct {
	CommonPagination
	Tags    []string `form:"tag"`
	Authors []uint   `form:"author_id"`
}

func (cp CommonPagination) Validate() error {

	if cp.Before != nil && cp.BeforeId != nil {
		return fmt.Errorf("before and before_id must not be used together")
	}

	if cp.After != nil && cp.AfterId != nil {
		return fmt.Errorf("after and after_id must not be used together")
	}

	// This really grinds my gears...
	if cp.BeforeId != nil && cp.AfterId != nil && *cp.BeforeId < *cp.AfterId {
		return fmt.Errorf("before must be after after")
	}

	if cp.Before != nil && cp.After != nil && cp.Before.Before(*cp.After) {
		return fmt.Errorf("before must be after after")
	}

	if cp.Limit != nil && *cp.Limit == 0 {
		return fmt.Errorf("limit 0 makes no sense")
	}

	if (cp.Order != nil) && (*cp.Order != FilterParamOrderAscending && *cp.Order != FilterParamOrderDescending) {
		return fmt.Errorf("order must be either '" + FilterParamOrderAscending + "' or '" + FilterParamOrderDescending + "'")
	}

	return nil
}

func (pf PostFilters) Validate() error {
	// Call parent validations first
	err := pf.CommonPagination.Validate()
	if err != nil {
		return err
	}

	// Custom validation for this type
	if pf.Tags != nil && len(pf.Tags) > 0 {
		for _, tag := range pf.Tags {
			if tag == "" {
				return fmt.Errorf("tag can not be empty string")
			}
		}
	}

	return nil
}
