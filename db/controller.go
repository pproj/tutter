package db

import (
	"fmt"
	"gorm.io/gorm"
)

var RandomGormError = fmt.Errorf("random gorm error")

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
	var posts []Post
	result := filter.Apply(db).Find(&posts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &posts, nil
}

func GetAllPostsAfterId(id uint64) (*[]Post, error) {
	var allPosts []Post
	result := db.Preload("Author").Preload("Tags").Where("id > ?", id).Find(&allPosts)
	if result.Error != nil {
		return nil, result.Error
	}
	return &allPosts, nil
}

func GetPostById(id uint64) (*Post, error) {
	var post Post
	result := db.Preload("Author").Preload("Tags").First(&post, id)
	if result.Error != nil {
		return nil, result.Error
	}
	if result.RowsAffected == 0 {
		return nil, gorm.ErrRecordNotFound
	}
	if post.ID != id {
		// I can't believe I have to do this...
		return nil, RandomGormError
	}
	return &post, nil
}

// GetLastPostId returns the id of the last post or 0 if no posts were published yet (post id starts with 1)
func GetLastPostId() (uint64, error) {
	var maxid *uint64
	result := db.Table("posts").Select("MAX(id)").Row()
	if result.Err() != nil {
		if result.Err() == gorm.ErrRecordNotFound {
			return 0, nil
		} else {
			return 0, result.Err()
		}
	}

	err := result.Scan(&maxid)
	if err != nil {
		return 0, err
	}
	if maxid == nil {
		return 0, nil
	}

	return *maxid, nil

}

// GetLastPost returns the last post or error gorm.ErrRecordNotFound if no posts were published yet
func GetLastPost() (*Post, error) {
	var post Post
	result := db.Order("id DESC").First(&post)
	if result.Error != nil {
		return nil, result.Error
	}
	if post.ID == 0 { // with GORM anything can happen...  (post ids should start with 1)
		return nil, gorm.ErrRecordNotFound
	}
	return &post, nil
}

func GetPostCount() (int64, error) {
	var count int64
	result := db.Model(&Post{}).Count(&count)
	if result.Error != nil {
		return 0, result.Error
	}
	return count, nil
}

// AUTHORS

func GetAuthors(filter *AuthorFilterParams) (*[]Author, error) {
	var authors []Author
	result := filter.Apply(db).Find(&authors)
	if result.Error != nil {
		return nil, result.Error
	}
	return &authors, nil
}

func GetAllAuthors() (*[]Author, error) {
	var authors []Author
	result := db.Find(&authors)
	if result.Error != nil {
		return nil, result.Error
	}
	return &authors, nil
}

func GetAuthorById(id uint, filter *AuthorFillFilterParams) (*Author, error) {
	var author Author
	result := filter.Apply(db).Find(&author, id)
	if result.Error != nil {
		return nil, result.Error
	}
	if result.RowsAffected == 0 {
		return nil, gorm.ErrRecordNotFound
	}
	if author.ID != id {
		// I can't believe I have to do this...
		return nil, RandomGormError
	}
	return &author, nil
}

func GetAuthorCount() (int64, error) {
	var count int64
	result := db.Model(&Author{}).Count(&count)
	if result.Error != nil {
		return 0, result.Error
	}
	return count, nil
}

// TAGS

func GetTags(filter *CommonPaginationParams) (*[]Tag, error) {
	var tags []Tag
	result := filter.Apply(db).Find(&tags)
	if result.Error != nil {
		return nil, result.Error
	}
	return &tags, nil
}

func GetAllTags() (*[]Tag, error) {
	var tags []Tag
	result := db.Find(&tags)
	if result.Error != nil {
		return nil, result.Error
	}
	return &tags, nil
}

func GetTagCount() (int64, error) {
	var count int64
	result := db.Model(&Tag{}).Count(&count)
	if result.Error != nil {
		return 0, result.Error
	}
	return count, nil
}

func GetTagByTag(tagStr string, filter *TagFillFilterParams) (*Tag, error) {
	var tag Tag
	result := filter.Apply(db.Where("tag = ?", tagStr)).First(&tag)
	if result.Error != nil {
		return nil, result.Error
	}
	if result.RowsAffected == 0 {
		return nil, gorm.ErrRecordNotFound
	}
	if tag.Tag != tagStr {
		// I can't believe I have to do this...
		return nil, RandomGormError
	}
	return &tag, nil
}

func GetTrendingTags() (*[]Tag, error) {
	var tags []Tag
	result := db.Where("trending = true").Find(&tags)
	if result.Error != nil {
		return nil, result.Error
	}
	return &tags, nil
}

// Debug

func CleanUpEverything() {
	db.Exec("TRUNCATE TABLE post_tags RESTART IDENTITY CASCADE;")
	db.Exec("TRUNCATE TABLE posts RESTART IDENTITY CASCADE;")
	db.Exec("TRUNCATE TABLE authors RESTART IDENTITY CASCADE;")
	db.Exec("TRUNCATE TABLE tags RESTART IDENTITY CASCADE;")
}

func SetTrendingTag(tag string, trending bool) error {
	result := db.Model(&Tag{}).Where("tag = ?", tag).Update("trending", trending)
	return result.Error
}
