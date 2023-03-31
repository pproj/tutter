package db

import (
	"gorm.io/gorm"
	"time"
)

// POSTS

func CreatePost(post *Post) error {

	return db.Transaction(func(tx *gorm.DB) error {

		result := tx.Where(post.Author).First(post.Author) // This looks cursed

		if result.Error == gorm.ErrRecordNotFound {
			innerResult := tx.Create(post.Author)

			if innerResult.Error != nil {
				return innerResult.Error
			}

		} else if result.Error != nil {
			return result.Error
		}

		for _, tag := range post.Tags {
			result = tx.Where(tag).First(tag) // the cursedness increases
			if result.Error == gorm.ErrRecordNotFound {
				innerResult := tx.Create(tag)
				if innerResult.Error != nil {
					return innerResult.Error
				}
			} else if result.Error != nil {
				return result.Error
			}
		}

		result = tx.Create(post)
		return result.Error
	})

}

func GetPosts(filter *PostFilterParams) (*[]Post, error) {
	chain := db.Preload("Tags", func(subChain *gorm.DB) *gorm.DB {
		return subChain.Omit("FirstSeen") // These cols would be omitted by the json serializer anyway
		// note: ID can not be omitted otherwise the join would fail
	})

	// these must be the first ones
	if filter.Tags != nil && len(filter.Tags) != 0 {
		// https://github.com/go-gorm/gorm/issues/3287#issuecomment-908893840
		chain = chain.Joins("JOIN post_tags on post_tags.post_id = posts.id JOIN tags on post_tags.tag_id = tags.id AND tags.tag in ? ", filter.Tags).Group("posts.id")
	}

	if filter.Authors != nil && len(filter.Authors) != 0 {
		chain = chain.Where("author_id IN (?)", filter.Authors)
	}
	chain = chain.Preload("Author")

	// and then these
	var afterUsed bool
	if filter.AfterId != nil {
		chain = chain.Where("id > ?", *filter.AfterId)
		afterUsed = true
	} else if filter.After != nil {
		chain = chain.Where("created_at > ?", *filter.After)
		afterUsed = true
	}

	var beforeUsed bool
	if filter.BeforeId != nil {
		chain = chain.Where("id < ?", *filter.BeforeId)
	} else if filter.Before != nil {
		chain = chain.Where("created_at < ?", *filter.Before)
	}

	if filter.Order != nil {
		// Order is higher order than the implicit ordering
		switch *filter.Order {
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
	if filter.Limit != nil {
		chain = chain.Limit(int(*filter.Limit))
	}

	var allPosts []Post
	result := chain.Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetAllPosts() (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Preload("Tags").Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetLastNPosts(n int) (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Preload("Tags").Order("created_at DESC").Limit(n).Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetAllPostsAfterId(id uint) (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Preload("Tags").Where("id > ?", id).Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetNPostsBeforeId(n int, id uint) (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Preload("Tags").Where("id < ?", id).Order("created_at DESC").Limit(n).Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetAllPostsAfterTimestamp(ts time.Time) (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Preload("Tags").Where("created_at > ?", ts).Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetPostById(id uint) (*Post, error) {
	var post Post
	result := db.Preload("Author").Preload("Tags").First(&post, id)
	if result.Error != nil {
		return nil, result.Error
	}
	return &post, nil
}

// AUTHORS

func GetAllAuthors() (*[]Author, error) {
	var authors []Author
	result := db.Find(&authors)
	if result.Error != nil {
		return nil, result.Error
	}
	return &authors, nil
}

func GetAuthorById(id uint) (*Author, error) {
	var author Author
	result := db.Preload("Posts").Find(&author, id)
	if result.Error != nil {
		return nil, result.Error
	}
	return &author, nil
}

// TAGS

func GetAllTags() (*[]Tag, error) {
	var tags []Tag
	result := db.Find(&tags)
	if result.Error != nil {
		return nil, result.Error
	}
	return &tags, nil
}

func GetTagByTag(tagStr string) (*Tag, error) {
	var tag Tag
	result := db.Preload("Posts").Where("tag = ?", tagStr).Preload("Posts.Author").Preload("Posts.Tags").First(&tag)
	if result.Error != nil {
		return nil, result.Error
	}
	return &tag, nil
}

// TODO: limits
