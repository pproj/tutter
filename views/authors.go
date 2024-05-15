package views

import (
	"github.com/gin-gonic/gin"
	"github.com/pproj/tutter/db"
	"gorm.io/gorm"
	"strconv"
)

func listAuthors(ctx *gin.Context) {
	var queryParams db.AuthorFilterParams
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

	var queryParams db.AuthorFillFilterParams
	err = ctx.ShouldBindQuery(&queryParams)
	if err != nil {
		handleUserError(ctx, err)
		return
	}

	err = queryParams.Validate()
	if err != nil {
		handleUserError(ctx, err)
		return
	}

	author, err := db.GetAuthorById(uint(id), &queryParams)
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			ctx.AbortWithStatus(404)
			return
		}
		handleInternalError(ctx, err)
		return
	}

	author.JSONIncludePosts = queryParams.IsFill()

	ctx.JSON(200, author)

}
