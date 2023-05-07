package views

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
)

func createDebugAuth(debugPin string) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		gotPin := ctx.GetHeader("X-Debug-Pin") // this isn't really standards compliant, but I don't care
		if gotPin == debugPin {
			ctx.Next()
		} else {
			ctx.Status(403)
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
