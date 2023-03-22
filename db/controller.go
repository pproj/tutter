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

func GetAllPosts() (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetLastNPosts(n int) (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Order("created_at DESC").Limit(n).Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetAllPostsAfterId(id uint) (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Where("id > ?", id).Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetNPostsBeforeId(n int, id uint) (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Where("id < ?", id).Order("created_at DESC").Limit(n).Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetAllPostsAfterTimestamp(ts time.Time) (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Where("created_at > ?", ts).Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetPostById(id uint) (*Post, error) {
	var post Post
	result := db.Preload("Author").First(&post, id)
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
	result := db.Preload("Posts").Where("tag = ?", tagStr).Preload("Posts.Author").First(&tag)
	if result.Error != nil {
		return nil, result.Error
	}
	return &tag, nil
}

// TODO: limits
