package db

import (
	"gitlab.com/MikeTTh/env"
	"go.uber.org/zap"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	gormlogger "gorm.io/gorm/logger"
	"moul.io/zapgorm2"
	"time"
)

var db *gorm.DB

func Connect(lgr *zap.Logger) (err error) {
	dsn := env.String("POSTGRESQL_DSN", "postgresql://localhost/postgres")
	db, err = gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: zapgorm2.Logger{
			ZapLogger:                 lgr,
			LogLevel:                  gormlogger.Info,
			SlowThreshold:             100 * time.Millisecond,
			SkipCallerLookup:          false,
			IgnoreRecordNotFoundError: true,
			Context:                   nil,
		},
		SkipDefaultTransaction: true, // Epic performance improvement
	})
	if err != nil {
		return
	}

	err = db.AutoMigrate(Post{}, Tag{}, Author{})
	if err != nil {
		return
	}

	return
}
