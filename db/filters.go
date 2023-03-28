package db

import (
	"fmt"
	"time"
)

const (
	FilterParamOrderAscending  = "asc"
	FilterParamOrderDescending = "desc"
)

type PostFilters struct {
	BeforeId *uint64    `form:"before_id"`
	AfterId  *uint64    `form:"after_id"`
	Before   *time.Time `form:"before"`
	After    *time.Time `form:"after"`
	Order    *string    `form:"order"`
	Tags     []string   `form:"tag"`
	Authors  []uint     `form:"author_id"`
	Limit    *uint      `form:"limit"`
}

func (pf PostFilters) Validate() error {

	if pf.Before != nil && pf.BeforeId != nil {
		return fmt.Errorf("before and before_id must not be used together")
	}

	if pf.After != nil && pf.AfterId != nil {
		return fmt.Errorf("after and after_id must not be used together")
	}

	// This really grinds my gears...
	if pf.BeforeId != nil && pf.AfterId != nil && *pf.BeforeId < *pf.AfterId {
		return fmt.Errorf("before must be after after")
	}

	if pf.Before != nil && pf.After != nil && pf.Before.Before(*pf.After) {
		return fmt.Errorf("before must be after after")
	}

	if pf.Limit != nil && *pf.Limit == 0 {
		return fmt.Errorf("limit 0 makes no sense")
	}

	if (pf.Order != nil) && (*pf.Order != FilterParamOrderAscending && *pf.Order != FilterParamOrderDescending) {
		return fmt.Errorf("order must be either '" + FilterParamOrderAscending + "' or '" + FilterParamOrderDescending + "'")
	}

	return nil
}
