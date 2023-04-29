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
	Limit  *uint   `form:"limit"`
	Offset *uint   `form:"offset"`
	Order  *string `form:"order"`
}

type PostFilterParams struct {
	CommonPaginationParams
	BeforeId *uint64    `form:"before_id"`
	AfterId  *uint64    `form:"after_id"`
	Before   *time.Time `form:"before"`
	After    *time.Time `form:"after"`
	Tags     []string   `form:"tag"`
	Authors  []uint     `form:"author_id"`
}

type fillFilterParams struct {
	CommonPaginationParams
	Fill *bool `form:"fill"`
}

type TagFillFilterParams struct {
	fillFilterParams // having simply the type here does not work for some reason, Validate() will call common instead of associated
}

type AuthorFillFilterParams struct {
	fillFilterParams
}

// CommonPaginationParams

func (p CommonPaginationParams) Validate() error {

	if p.Limit != nil && *p.Limit == 0 {
		return fmt.Errorf("limit 0 makes no sense")
	}

	if (p.Order != nil) && (*p.Order != FilterParamOrderAscending && *p.Order != FilterParamOrderDescending) {
		return fmt.Errorf("order must be either '%s' or '%s'", FilterParamOrderAscending, FilterParamOrderDescending)
	}

	return nil
}

func (p CommonPaginationParams) Apply(chain *gorm.DB) *gorm.DB {

	if p.Order != nil {
		// Order is higher order than the implicit ordering
		switch *p.Order {
		case FilterParamOrderAscending:
			chain = chain.Order("id ASC")
		case FilterParamOrderDescending:
			chain = chain.Order("id DESC")
		}
	}

	// Apply offset if needed
	if p.Offset != nil {
		chain = chain.Offset(int(*p.Offset))
	}

	// Limit should be the last
	if p.Limit != nil {
		chain = chain.Limit(int(*p.Limit))
	}

	return chain
}

// PostFilterParams

func (p PostFilterParams) Validate() error {
	// Call parent validations first
	err := p.CommonPaginationParams.Validate()
	if err != nil {
		return err
	}

	if p.Before != nil && p.BeforeId != nil {
		return fmt.Errorf("before and before_id must not be used together")
	}

	if p.After != nil && p.AfterId != nil {
		return fmt.Errorf("after and after_id must not be used together")
	}

	// This really grinds my gears...
	if p.BeforeId != nil && p.AfterId != nil && *p.BeforeId <= *p.AfterId {
		return fmt.Errorf("before must be after after")
	}

	if p.Before != nil && p.After != nil && (p.Before.Before(*p.After) || p.Before.Equal(*p.After)) {
		return fmt.Errorf("before must be after after")
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

	// and then these filters
	var afterUsed bool
	if p.AfterId != nil {
		chain = chain.Where("posts.id > ?", *p.AfterId)
		afterUsed = true
	} else if p.After != nil {
		chain = chain.Where("posts.created_at > ?", *p.After)
		afterUsed = true
	}

	var beforeUsed bool
	if p.BeforeId != nil {
		chain = chain.Where("posts.id < ?", *p.BeforeId)
		beforeUsed = true
	} else if p.Before != nil {
		chain = chain.Where("posts.created_at < ?", *p.Before)
		beforeUsed = true
	}

	// implicit ordering

	if p.Order == nil {
		if afterUsed && !beforeUsed {
			chain = chain.Order("id ASC")
		} else if !afterUsed && beforeUsed {
			chain = chain.Order("id DESC")
		}
	}

	// and then these
	return p.CommonPaginationParams.Apply(chain)
}

// fillFilterParams

func (p fillFilterParams) Validate() error {

	if !p.IsFill() {
		// if fill is disabled no params should be allowed
		if p.Limit != nil || p.Offset != nil || p.Order != nil {
			return fmt.Errorf("using any pagination params while fill is disabled makes no sense")
		}
	}

	return p.CommonPaginationParams.Validate()
}

func (p fillFilterParams) IsFill() bool { // Default is true
	return p.Fill == nil || *p.Fill == true
}

// TagFillFilterParams

func (p TagFillFilterParams) Apply(chain *gorm.DB) *gorm.DB {
	if p.IsFill() {
		chain = chain.Preload("Posts", func(subChain *gorm.DB) *gorm.DB {
			return p.CommonPaginationParams.Apply(subChain)
		}).Preload("Posts.Author").Preload("Posts.Tags")
	}
	return chain
}

// AuthorFillFilterParams

func (p AuthorFillFilterParams) Apply(chain *gorm.DB) *gorm.DB {
	if p.IsFill() {
		chain = chain.Preload("Posts", func(subChain *gorm.DB) *gorm.DB {
			return p.CommonPaginationParams.Apply(subChain)
		}).Preload("Posts.Tags")
	}
	return chain
}
