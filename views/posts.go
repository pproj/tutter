package views

import (
	"fmt"
	"git.sch.bme.hu/pp23/tutter/db"
	"github.com/gin-gonic/gin"
	"github.com/microcosm-cc/bluemonday"
	"go.uber.org/zap"
	"gorm.io/gorm"
	"regexp"
	"strconv"
	"strings"
	"unicode/utf8"
)

var (
	authorRegex      *regexp.Regexp
	tagRegex         *regexp.Regexp
	blueMondayPolicy *bluemonday.Policy
)

func init() {
	authorRegex = regexp.MustCompile(`^[a-z0-9_]+$`)
	tagRegex = regexp.MustCompile(`#[a-zA-Z0-9]+`)
	blueMondayPolicy = bluemonday.StrictPolicy()
}

func createPost(ctx *gin.Context) {

	// First, parse json

	type newPostParamsType struct {
		Author string `json:"author" binding:"required"` // length binding requirement removed, as it was not working
		Text   string `json:"text" binding:"required"`
	}
	var newPostParams newPostParamsType
	err := ctx.ShouldBindJSON(&newPostParams)
	if err != nil {
		handleUserError(ctx, err)
		return
	}

	if utf8.RuneCountInString(newPostParams.Text) > 260 || utf8.RuneCountInString(newPostParams.Author) > 32 {
		// This is double-checked after sanitization
		handleUserError(ctx, fmt.Errorf("text or author too long"))
		return
	}

	// Then sanitize all fields
	sanitizedText := strings.TrimSpace(blueMondayPolicy.Sanitize(newPostParams.Text))
	sanitizedAuthor := strings.TrimSpace(blueMondayPolicy.Sanitize(newPostParams.Author))

	if utf8.RuneCountInString(sanitizedText) == 0 || utf8.RuneCountInString(sanitizedAuthor) == 0 || len(sanitizedText) == 0 || len(sanitizedAuthor) == 0 {
		// rune count and len should both be zero if the other one is zero, as a zero length string can not contain any rune
		// But I'm too stupid for unicode, so I make sure... if this really is unnecessary the compiler will optimize it out anyway
		handleUserError(ctx, fmt.Errorf("text or author empty"))
		return
	}

	if utf8.RuneCountInString(sanitizedText) > 260 || utf8.RuneCountInString(sanitizedAuthor) > 32 {
		// This should not happen either, but whatever
		handleUserError(ctx, fmt.Errorf("text or author too long"))
		return
	}

	if !authorRegex.MatchString(sanitizedAuthor) { // only lowercase and numbers
		handleUserError(ctx, fmt.Errorf("author invalid"))
		return
	}

	// Then extract tags from sanitized data

	match := tagRegex.FindAllStringSubmatch(sanitizedText, 260/3)

	tagSet := make(map[string]interface{})
	for _, tagMatch := range match {
		if len(tagMatch) == 0 {
			break
		}
		tagText := tagMatch[0][1:]
		tagText = blueMondayPolicy.Sanitize(tagText) // <- this...
		tagText = strings.TrimSpace(tagText)         // <- ... this...
		tagText = strings.ToLower(tagText)

		if len(tagText) == 0 || len(tagText) > 259 { // <- using len instead of rune count, as unicode characters are not allowed in tags
			// ... and this should never happen... but you never know either
			continue
		}

		tagSet[tagText] = nil // This is a "hack" to have sets in golang, we need it to de-duplicate tags

	}

	// And now turn the set into a list of tags
	var tags []*db.Tag
	for tag := range tagSet {
		tags = append(tags, &db.Tag{
			Tag: tag,
		})
	}

	// Compile new post object
	newPost := db.Post{
		Text: sanitizedText,
		Author: &db.Author{
			Name: sanitizedAuthor,
		},
		Tags: tags,
	}

	// Submit to db
	err = db.CreatePost(&newPost)
	if err != nil {
		handleInternalError(ctx, err)
		return
	}

	// Broadcast to all long polling fellas
	err = newPostObserver.Notify(newPost.ID)
	if err != nil {
		l, ok := ctx.Get("l")
		if !ok {
			panic("could not access logger")
		}
		logger := l.(*zap.Logger)
		logger.Error("Error while notifying observers", zap.Error(err))
	}

	// return 201
	ctx.JSON(201, newPost)

}

func listPosts(ctx *gin.Context) {

	var queryParams db.PostFilterParams
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

	posts, err := db.GetPosts(&queryParams)
	if err != nil {
		handleInternalError(ctx, err)
		return
	}

	ctx.JSON(200, posts)

}

func getPost(ctx *gin.Context) { // This one does not take any query params
	id, err := strconv.ParseUint(ctx.Param("id"), 10, 64)
	if err != nil {
		handleUserError(ctx, err)
		return
	}

	post, err := db.GetPostById(id)

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
