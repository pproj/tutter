package main

import (
	"crypto/rand"
	"fmt"
	ginzap "github.com/gin-contrib/zap"
	"github.com/gin-gonic/gin"
	"github.com/pproj/tutter/db"
	"github.com/pproj/tutter/views"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"gitlab.com/MikeTTh/env"
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
	"math/big"
	"net/http"
	"strings"
	"time"
)

// GenerateRandomString returns a securely generated random string.
// It will return an error if the system's secure random
// number generator fails to function correctly, in which
// case the caller should not continue.
// taken from here: https://gist.github.com/dopey/c69559607800d2f2f90b1b1ed4e550fb
func generateRandomString(n int) string {
	const letters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-"
	ret := make([]byte, n)
	for i := 0; i < n; i++ {
		num, err := rand.Int(rand.Reader, big.NewInt(int64(len(letters))))
		if err != nil {
			panic(err)
		}
		ret[i] = letters[num.Int64()]
	}

	return string(ret)
}

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

func validateAuthHeader(ctx *gin.Context, type_, key string) bool {
	authHeader := ctx.GetHeader("Authorization")

	if authHeader == "" {
		return false
	}

	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 {
		return false
	}

	if parts[0] != type_ {
		return false
	}

	if parts[1] != key {
		return false
	}

	return true
}

func createBearerAuth(token string) gin.HandlerFunc {
	return func(ctx *gin.Context) {

		if token == "" { // I'll leave this optional
			ctx.Next()
			return
		}

		if validateAuthHeader(ctx, "Bearer", token) {
			ctx.Next()
		} else {
			ctx.Status(http.StatusUnauthorized)
			ctx.Abort()
			return
		}

	}
}

func main() {
	debugMode := env.Bool("DEBUG", false)

	// Setup logger
	var err error
	var logger *zap.Logger
	if debugMode {
		gin.SetMode(gin.DebugMode)
		logger, err = zap.NewDevelopment()
	} else {
		gin.SetMode(gin.ReleaseMode)
		logger, err = zap.NewProduction()
	}
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
	if !debugMode {
		// proper panic logs are better when debugging
		router.Use(ginzap.RecoveryWithZap(logger, true))
	}

	// Serve SPA from dist/
	router.StaticFS("/assets", http.Dir("dist/assets"))
	router.StaticFile("/favicon.ico", "dist/favicon.ico")
	router.StaticFile("/site.webmanifest", "dist/site.webmanifest")

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
	debugPin := ""
	if debugMode {
		debugPin = env.StringOrDoSomething("DEBUG_PIN", func() string {
			generatedDebugPin := generateRandomString(24)
			logger.Info("DEBUG_PIN envvar undefined, random pin generated", zap.String("generatedDebugPin", generatedDebugPin))
			return generatedDebugPin
		})
		logger.Warn("Debug mode enabled", zap.String("DEBUG_PIN", debugPin))
	}

	api := router.Group("/api")
	err = views.SetupEndpoints(api, logger, debugMode, debugPin)
	if err != nil {
		panic(err)
	}

	// Add API documentation... it may be ugly, but it works well.
	api.StaticFile("/", "apidoc/apidoc.html")
	api.StaticFile("/spec.yaml", "apidoc/spec.yaml")

	// Add Prometheus metrics endpoint
	router.GET(
		"/metrics",
		createBearerAuth(env.String("METRICS_BEARER", "")),
		gin.WrapH(promhttp.Handler()),
	)

	srv := &http.Server{
		Addr:              env.String("BIND_ADDR", ":8080"),
		Handler:           router,
		ReadHeaderTimeout: 2 * time.Second,
		MaxHeaderBytes:    1 << 20,
	}

	tlsKey := env.String("TLS_KEY", "")
	tlsCert := env.String("TLS_CERT", "")

	if tlsKey != "" && tlsCert != "" {
		logger.Warn("Running in HTTPS", zap.String("tlsCert", tlsCert), zap.String("tlsKey", tlsKey), zap.String("listenAddr", srv.Addr))
		err = srv.ListenAndServeTLS(tlsCert, tlsKey)
	} else {
		logger.Warn("Running in HTTP mode without TLS", zap.String("listenAddr", srv.Addr))
		err = srv.ListenAndServe()
	}
	if err != nil {
		panic(err)
	}
}
