package views

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/pproj/tutter/db"
	"gorm.io/gorm"
)

func listTags(ctx *gin.Context) {
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

	tags, err := db.GetTags(&queryParams)
	if err != nil {
		handleInternalError(ctx, err)
		return
	}

	ctx.JSON(200, tags)
}

func getTag(ctx *gin.Context) {
	tagStr := ctx.Param("tag")
	if tagStr == "" {
		handleUserError(ctx, fmt.Errorf("tag should not be empty"))
		return
	}

	var queryParams db.TagFillFilterParams
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

	tag, err := db.GetTagByTag(tagStr, &queryParams)
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			ctx.AbortWithStatus(404)
			return
		}
		handleInternalError(ctx, err)
		return
	}

	tag.JSONIncludePosts = queryParams.IsFill()

	ctx.JSON(200, tag)
}

func getTrendingTags(ctx *gin.Context) {
	tags, err := db.GetTrendingTags()

	if err != nil {
		handleInternalError(ctx, err)
		return
	}

	trendingTags := make([]string, len(*tags))
	for idx, tag := range *tags {
		trendingTags[idx] = tag.Tag
	}

	ctx.JSON(200, trendingTags)
}
