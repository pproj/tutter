package views

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"git.sch.bme.hu/pp23/tutter/observer"
	"github.com/gin-gonic/gin"
	"time"
)

// dbIdPoller is used to give subscribers that missed an event a second chance of catching it.
// This is also useful when the application is running in multiple replicas and the shared sync thing does not work for some reason
func dbIdPoller() {
	for {
		time.Sleep(time.Second * 30)
		maxid, err := db.GetLastPostId()
		if err != nil {
			continue // ignore
		}
		if maxid > newPostObserver.LastId() {
			err = newPostObserver.Notify(maxid)
			if err != nil {
				continue // ignore
			}
		}
	}
}

func SetupEndpoints(routerGroup *gin.RouterGroup) error {

	// First, setup observer for the long polling thing
	id, err := db.GetLastPostId()
	if err != nil {
		return err
	}
	newPostObserver = observer.NewNewIdObserver(id)
	routerGroup.GET("/poll", longPoll)
	go dbIdPoller()

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
