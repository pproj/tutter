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
	ID        uint      `gorm:"primarykey"`
	FirstSeen time.Time `gorm:"default:now()"`
	Tag       string    `gorm:"not null; uniqueIndex, varchar(280)"`
	Trending  bool      `json:"-" gorm:"not null; default:false"`

	JSONIncludePosts bool    `json:"-" gorm:"-" sql:"-"` // Default false
	Posts            []*Post `gorm:"many2many:post_tags;"`
}

func (t Tag) MarshalJSON() ([]byte, error) {
	if t.JSONIncludePosts {
		return json.Marshal(struct {
			FirstSeen time.Time `json:"first_seen"`
			Tag       string    `json:"tag"`
			Posts     []*Post   `json:"posts"`
		}{
			FirstSeen: t.FirstSeen,
			Tag:       t.Tag,
			Posts:     t.Posts,
		})
	} else {
		return json.Marshal(struct {
			FirstSeen time.Time `json:"first_seen"`
			Tag       string    `json:"tag"`
		}{
			FirstSeen: t.FirstSeen,
			Tag:       t.Tag,
		})
	}
}

type Author struct {
	ID        uint      `gorm:"primarykey"`
	FirstSeen time.Time `gorm:"default:now()"`
	Name      string    `gorm:"uniqueIndex;varchar(32)"`

	JSONIncludePosts bool    `json:"-" gorm:"-" sql:"-"` // Default false
	Posts            []*Post `gorm:""`
}

func (a Author) MarshalJSON() ([]byte, error) {
	if a.JSONIncludePosts {
		return json.Marshal(struct {
			ID        uint      `json:"id"`
			FirstSeen time.Time `json:"first_seen"`
			Name      string    `json:"name"`
			Posts     []*Post   `json:"posts"`
		}{
			ID:        a.ID,
			FirstSeen: a.FirstSeen,
			Name:      a.Name,
			Posts:     a.Posts,
		})
	} else {
		return json.Marshal(struct {
			ID        uint      `json:"id"`
			FirstSeen time.Time `json:"first_seen"`
			Name      string    `json:"name"`
		}{
			ID:        a.ID,
			FirstSeen: a.FirstSeen,
			Name:      a.Name,
		})
	}
}
