package db

import (
	"database/sql"
	"fmt"
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

	var sqlDB *sql.DB
	sqlDB, err = db.DB()
	if err != nil {
		return
	}

	// hopefully this sets stuff globally
	sqlDB.SetConnMaxLifetime(time.Minute * 15)
	maxConn := env.Int("POSTGRESQL_MAX_CONNECTIONS", 50)
	if maxConn <= 0 {
		err = fmt.Errorf("max connections must be a positive number")
		return
	}
	var maxIdle int
	if maxConn < 10 {
		maxIdle = maxConn
	} else {
		maxIdle = 10
	}
	sqlDB.SetMaxIdleConns(maxIdle)
	sqlDB.SetMaxOpenConns(maxConn)

	if err != nil {
		return
	}

	err = db.AutoMigrate(Post{}, Tag{}, Author{})
	if err != nil {
		return
	}

	return
}
