package views

import (
	"fmt"
	"git.sch.bme.hu/pp23/tutter/db"
	"github.com/gin-gonic/gin"
	"github.com/microcosm-cc/bluemonday"
	"gorm.io/gorm"
	"regexp"
	"strconv"
	"strings"
)

var (
	tagRegex         *regexp.Regexp
	blueMondayPolicy *bluemonday.Policy
)

func init() {
	tagRegex = regexp.MustCompile(`#[a-zA-Z0-9]+`)
	blueMondayPolicy = bluemonday.StrictPolicy()
}

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

	match := tagRegex.FindAllStringSubmatch(newPostParams.Text, 260/2)

	var tags []*db.Tag
	for _, tagMatch := range match {
		if len(tagMatch) == 0 {
			break
		}
		tagText := tagMatch[0][1:]
		tagText = blueMondayPolicy.Sanitize(tagText) // <- this...
		tagText = strings.TrimSpace(tagText)         // <- ... this...
		tagText = strings.ToLower(tagText)

		if len(tagText) == 0 || len(tagText) > 259 {
			// ... and this should never happen... but you never know either
			continue
		}

		tags = append(tags, &db.Tag{
			Tag: tagText,
		})
	}

	sanitizedText := strings.TrimSpace(blueMondayPolicy.Sanitize(newPostParams.Text))
	sanitizedAuthor := strings.TrimSpace(blueMondayPolicy.Sanitize(newPostParams.Author))

	if len(sanitizedText) == 0 || len(sanitizedAuthor) == 0 {
		handleUserError(ctx, fmt.Errorf("text or author empty"))
		return
	}

	if len(sanitizedText) > 260 || len(sanitizedAuthor) > 32 {
		// This should not happen either, but whatever
		handleUserError(ctx, fmt.Errorf("text or author too long"))
		return
	}

	newPost := db.Post{
		Text: sanitizedText,
		Author: &db.Author{
			Name: sanitizedAuthor,
		},
		Tags: tags,
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
