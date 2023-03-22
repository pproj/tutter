package db

import "time"

type Post struct {
	ID        uint      `json:"id" gorm:"primarykey"`
	CreatedAt time.Time `json:"created_at" gorm:"default:now()"`
	Text      string    `json:"text"`

	AuthorID uint    `json:"-"`
	Author   *Author `json:"author" gorm:"belongsTo:Author"`

	Tags []*Tag `json:"-" gorm:"many2many:post_tags;"`
}

type Tag struct {
	ID        uint      `json:"id" gorm:"primarykey"`
	FirstSeen time.Time `json:"first_seen" gorm:"default:now()"`
	Tag       string    `json:"tag" gorm:"uniqueIndex, varchar(280)"`
}

type Author struct {
	ID        uint      `json:"id" gorm:"primarykey"`
	FirstSeen time.Time `json:"first_seen" gorm:"default:now()"`
	Name      string    `json:"name" gorm:"uniqueIndex;varchar(32)"`
}
