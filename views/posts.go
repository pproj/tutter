package views

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
	"strconv"
)

func createPost(ctx *gin.Context) {
	type newPostParamsType struct {
		Author string `json:"author" binding:"required,max=32"`
		Text   string `json:"text" binding:"required,max=260"`
	}
	var newPostParams newPostParamsType
	err := ctx.ShouldBindJSON(&newPostParams)
	if err != nil {
		handleUserError(ctx, err)
		return
	}

	// TODO: Parse tags

	newPost := db.Post{
		Text: newPostParams.Text,
		Author: &db.Author{
			Name: newPostParams.Author,
		},
		Tags: []*db.Tag{},
	}

	err = db.CreatePost(&newPost)
	if err != nil {
		handleInternalError(ctx, err)
		return
	}

	ctx.JSON(201, newPost)

}

func listPosts(ctx *gin.Context) {

	// TODO: various filtering based on params

	posts, err := db.GetAllPosts()
	if err != nil {
		handleInternalError(ctx, err)
	}

	ctx.JSON(200, posts)

}

func getPost(ctx *gin.Context) {
	id, err := strconv.ParseUint(ctx.Param("id"), 10, 0)
	if err != nil {
		handleUserError(ctx, err)
		return
	}

	post, err := db.GetPostById(uint(id))

	if err != nil {

		if err == gorm.ErrRecordNotFound {
			ctx.AbortWithStatus(404)
			return
		}

		handleInternalError(ctx, err)
		return

	}

	ctx.JSON(200, post)

}
