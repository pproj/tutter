package main

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	_ = promauto.NewCounterFunc(prometheus.CounterOpts{
		Name: "tutter_posts_count",
		Help: "Count of posts",
	}, func() float64 {
		cnt, err := db.GetPostCount()
		if err != nil {
			// it may be that there is no record in the table
			return 0 // ?
		}
		return float64(cnt)
	})
	_ = promauto.NewCounterFunc(prometheus.CounterOpts{
		Name: "tutter_authors_count",
		Help: "Count of authors",
	}, func() float64 {
		cnt, err := db.GetAuthorCount()
		if err != nil {
			// it may be that there is no record in the table
			return 0 // ?
		}
		return float64(cnt)
	})
	_ = promauto.NewCounterFunc(prometheus.CounterOpts{
		Name: "tutter_tags_count",
		Help: "Count of tags",
	}, func() float64 {
		cnt, err := db.GetTagCount()
		if err != nil {
			// it may be that there is no record in the table
			return 0 // ?
		}
		return float64(cnt)
	})
)
