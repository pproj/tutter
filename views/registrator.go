package views

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"git.sch.bme.hu/pp23/tutter/observer"
	"github.com/gin-gonic/gin"
)

func RegisterEndpoints(routerGroup *gin.RouterGroup) error {

	// First, setup observer for the long polling thing
	id, err := db.GetLastPostId()
	if err != nil {
		return err
	}
	newPostObserver = observer.NewNewIdObserver(id)
	routerGroup.GET("/poll", longPoll)

	// Then the REST
	routerGroup.POST("/post", createPost)
	routerGroup.GET("/post", listPosts)
	routerGroup.GET("/post/:id", getPost)

	routerGroup.GET("/tag", listTags)
	routerGroup.GET("/tag/:tag", getTag)

	routerGroup.GET("/author", listAuthors)
	routerGroup.GET("/author/:id", getAuthor)

	return nil
}
