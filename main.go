package main

import (
	"fmt"
	"git.sch.bme.hu/pp23/tutter/db"
	"git.sch.bme.hu/pp23/tutter/views"
	ginzap "github.com/gin-contrib/zap"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"net/http"
	"strings"
	"time"
)

func goodLoggerMiddleware(logger *zap.Logger) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		start := time.Now()
		// some evil middlewares modify this values
		path := ctx.Request.URL.Path
		query := ctx.Request.URL.RawQuery

		fields := []zapcore.Field{
			zap.String("method", ctx.Request.Method),
			zap.String("path", path),
			zap.String("query", query),
			zap.String("ip", ctx.ClientIP()),
			zap.String("user-agent", ctx.Request.UserAgent()),
		}
		subLogger := logger.With(fields...)

		ctx.Set("l", subLogger)

		ctx.Next() // <- execute next thing in the chain
		end := time.Now()

		latency := end.Sub(start)
		completedRequestFields := []zapcore.Field{
			zap.Int("status", ctx.Writer.Status()),
			zap.Duration("latency", latency),
		}
		if len(ctx.Errors) > 0 {
			// Append error field if this is an erroneous request.
			for _, e := range ctx.Errors.Errors() {
				subLogger.Error(e, completedRequestFields...)
			}
		}

		subLogger.Info(fmt.Sprintf("%s %s served: %d", ctx.Request.Method, path, ctx.Writer.Status()), completedRequestFields...) // <- always print this

	}
}

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

	router.Use(goodLoggerMiddleware(logger))
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
	err = views.SetupEndpoints(api, logger)
	if err != nil {
		panic(err)
	}

	// Add API documentation... it may be ugly, but it works well.
	api.StaticFile("/", "apidoc/apidoc.html")
	api.StaticFile("/spec.yaml", "apidoc/spec.yaml")

	// Listen and serve on 0.0.0.0:8080
	err = router.Run(":8080")
	if err != nil {
		panic(err)
	}
}
