package views

import "github.com/gin-gonic/gin"

func RegisterEndpoints(routerGroup *gin.RouterGroup) {

	routerGroup.POST("/post", createPost)
	routerGroup.GET("/post", listPosts)
	routerGroup.GET("/post/:id", getPost)

	routerGroup.GET("/poll", longPoll)

	routerGroup.GET("/tag", listTags)
	routerGroup.GET("/tag/:tag", getTag)

	routerGroup.GET("/author", listAuthors)
	routerGroup.GET("/author/:id", getAuthor)

}
