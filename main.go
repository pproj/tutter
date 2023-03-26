package main

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"git.sch.bme.hu/pp23/tutter/views"
	ginzap "github.com/gin-contrib/zap"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
	"net/http"
	"strings"
	"time"
)

func main() {

	// Setup logger
	logger, err := zap.NewProduction()
	if err != nil {
		panic(err)
	}

	defer logger.Sync()

	// Setup DB connection
	err = db.Connect(logger)
	if err != nil {
		panic(err)
	}

	// Setup Gin
	router := gin.New()

	router.Use(ginzap.Ginzap(logger, time.RFC3339, true))
	router.Use(ginzap.RecoveryWithZap(logger, true))

	// Serve SPA from dist/
	router.StaticFS("/assets", http.Dir("dist/assets"))
	router.StaticFile("/favicon.ico", "dist/favicon.ico")

	router.NoRoute(func(c *gin.Context) {
		path := c.Request.URL.Path // seems like this is already normalized
		if strings.HasPrefix(path, "/api") || strings.HasPrefix(path, "/assets") {
			c.AbortWithStatus(404)
			return
		}
		if c.Request.Method != "GET" {
			c.AbortWithStatus(405)
			return
		}
		c.File("dist/index.html")
	})

	// Serve api
	api := router.Group("/api")
	views.RegisterEndpoints(api)

	// Add API documentation... it may be ugly, but it works well.
	api.StaticFile("/", "apidoc/apidoc.html")
	api.StaticFile("/spec.yaml", "apidoc/spec.yaml")

	// Listen and serve on 0.0.0.0:8080
	err = router.Run(":8080")
	if err != nil {
		panic(err)
	}
}
