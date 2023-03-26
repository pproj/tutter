package db

import (
	"encoding/json"
	"time"
)

type Post struct {
	ID        uint64    `gorm:"primarykey"`
	CreatedAt time.Time `gorm:"default:now()"`
	Text      string

	AuthorID uint
	Author   *Author `gorm:"belongsTo:Author"`

	Tags []*Tag `gorm:"many2many:post_tags;"`
}

func (p Post) MarshalJSON() ([]byte, error) {

	type MarshaledPost struct {
		ID        uint64    `json:"id"`
		CreatedAt time.Time `json:"created_at"`
		Text      string    `json:"text"`
		Author    *Author   `json:"author,omitempty"`
		Tags      []string  `json:"tags"`
	}

	tags := make([]string, len(p.Tags))
	for i, tag := range p.Tags {
		tags[i] = tag.Tag
	}

	mp := MarshaledPost{
		ID:        p.ID,
		CreatedAt: p.CreatedAt,
		Text:      p.Text,
		Author:    p.Author,
		Tags:      tags,
	}

	return json.Marshal(mp)

}

type Tag struct {
	ID        uint      `json:"-" gorm:"primarykey"`
	FirstSeen time.Time `json:"first_seen" gorm:"default:now()"`
	Tag       string    `json:"tag" gorm:"uniqueIndex, varchar(280)"`

	Posts []*Post `json:"posts,omitempty" gorm:"many2many:post_tags;"`
}

type Author struct {
	ID        uint      `json:"id" gorm:"primarykey"`
	FirstSeen time.Time `json:"first_seen" gorm:"default:now()"`
	Name      string    `json:"name" gorm:"uniqueIndex;varchar(32)"`

	Posts []*Post `json:"posts,omitempty" gorm:""`
}
