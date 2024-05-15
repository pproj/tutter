package views

import (
	"github.com/gin-gonic/gin"
	"github.com/pproj/tutter/observer"
)

// handleError create a 500 response for error
func handleInternalError(ctx *gin.Context, err error) {
	ctx.AbortWithStatusJSON(500, gin.H{"error": err.Error()})
}

// handleUserError create a 4XX response for error
func handleUserError(ctx *gin.Context, err error) {
	ctx.AbortWithStatusJSON(400, gin.H{"reason": err.Error()})
}

var newPostObserver *observer.NewPostObserver = nil
