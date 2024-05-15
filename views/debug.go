package views

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/pproj/tutter/db"
	"go.uber.org/zap"
)

func createDebugAuth(debugPin string) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		gotPin := ctx.GetHeader("X-Debug-Pin") // this isn't really standards compliant, but I don't care
		if gotPin == debugPin {
			ctx.Next()
		} else {
			ctx.Status(401)
			ctx.Abort()
			return
		}
	}
}

func debugCleanup(ctx *gin.Context) {

	l, ok := ctx.Get("l")
	if !ok {
		panic("could not access logger")
	}
	logger := l.(*zap.Logger)
	logger.Info("DEBUG CLEANUP ENDPOINT IS USED!")

	db.CleanUpEverything()
	newPostObserver.DebugCleanup()

	ctx.Status(200)

}

func debugSetTrending(ctx *gin.Context) {
	l, ok := ctx.Get("l")
	if !ok {
		panic("could not access logger")
	}
	logger := l.(*zap.Logger)
	logger.Info("DEBUG TRENDING TAG UPDATE IS USED!")

	tagStr := ctx.Param("tag")
	if tagStr == "" {
		handleUserError(ctx, fmt.Errorf("tag should not be empty"))
		return
	}

	trending := ctx.Request.Method == "PUT"

	err := db.SetTrendingTag(tagStr, trending)
	if err != nil {
		handleInternalError(ctx, err)
		return
	}

	ctx.Status(200)

}
