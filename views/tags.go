package views

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func listTags(ctx *gin.Context) {
	tags, err := db.GetAllTags()
	if err != nil {
		handleInternalError(ctx, err)
	}

	ctx.JSON(200, tags)
}

func getTag(ctx *gin.Context) {
	tagStr := ctx.Param("tag")
	tag, err := db.GetTagByTag(tagStr)
	if err == gorm.ErrRecordNotFound {
		ctx.AbortWithStatus(404)
		return
	}

	// TODO: limiting

	ctx.JSON(200, tag)
}
