package views

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
	"strconv"
)

func listAuthors(ctx *gin.Context) {
	var queryParams db.CommonPaginationParams
	err := ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		handleUserError(ctx, err)
		return
	}

	err = queryParams.Validate()
	if err != nil {
		handleUserError(ctx, err)
		return
	}

	authors, err := db.GetAuthors(&queryParams)
	if err != nil {
		handleInternalError(ctx, err)
		return
	}
	ctx.JSON(200, authors)

}

func getAuthor(ctx *gin.Context) {
	id, err := strconv.ParseUint(ctx.Param("id"), 10, 0)
	if err != nil {
		handleUserError(ctx, err)
		return
	}
	author, err := db.GetAuthorById(uint(id))
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			ctx.AbortWithStatus(404)
			return
		}
		handleInternalError(ctx, err)
		return
	}

	// TODO: limits

	ctx.JSON(200, author)

}
