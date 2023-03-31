package db

import (
	"fmt"
	"gorm.io/gorm"
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

type associatedFilterParams struct {
	CommonPaginationParams
	Fill *bool `form:"fill"`
}

type TagFilterParams associatedFilterParams
type AuthorFilterParams associatedFilterParams

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

func (p CommonPaginationParams) Apply(chain *gorm.DB) *gorm.DB {

	var afterUsed bool
	if p.AfterId != nil {
		chain = chain.Where("id > ?", *p.AfterId)
		afterUsed = true
	} else if p.After != nil {
		chain = chain.Where("created_at > ?", *p.After)
		afterUsed = true
	}

	var beforeUsed bool
	if p.BeforeId != nil {
		chain = chain.Where("id < ?", *p.BeforeId)
	} else if p.Before != nil {
		chain = chain.Where("created_at < ?", *p.Before)
	}

	if p.Order != nil {
		// Order is higher order than the implicit ordering
		switch *p.Order {
		case FilterParamOrderAscending:
			chain = chain.Order("id ASC")
		case FilterParamOrderDescending:
			chain = chain.Order("id DESC")
		}

	} else if afterUsed && !beforeUsed { // implicit ordering
		chain = chain.Order("id ASC")
	} else if !afterUsed && beforeUsed { // implicit ordering
		chain = chain.Order("id DESC")
	}
	// Otherwise, don't care

	// Limit should be the last
	if p.Limit != nil {
		chain = chain.Limit(int(*p.Limit))
	}

	return chain
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

func (p PostFilterParams) Apply(chain *gorm.DB) *gorm.DB {
	chain = chain.Preload("Tags", func(subChain *gorm.DB) *gorm.DB {
		return subChain.Omit("FirstSeen") // These cols would be omitted by the json serializer anyway
		// note: ID can not be omitted otherwise the join would fail
	})

	// these must be the first ones
	if p.Tags != nil && len(p.Tags) != 0 {
		// https://github.com/go-gorm/gorm/issues/3287#issuecomment-908893840
		chain = chain.Joins("JOIN post_tags on post_tags.post_id = posts.id JOIN tags on post_tags.tag_id = tags.id AND tags.tag in ? ", p.Tags).Group("posts.id")
	}

	if p.Authors != nil && len(p.Authors) != 0 {
		chain = chain.Where("author_id IN (?)", p.Authors)
	}
	chain = chain.Preload("Author")

	// and then these
	return p.CommonPaginationParams.Apply(chain)
}

func (p associatedFilterParams) Validate() error {
	// Call parent validations first
	return p.CommonPaginationParams.Validate()
}
