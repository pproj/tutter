package views

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"git.sch.bme.hu/pp23/tutter/observer"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
	"time"
)

// dbIdPoller is used to give subscribers that missed an event a second chance of catching it.
// This is also useful when the application is running in multiple replicas and the shared sync thing does not work for some reason
func dbIdPoller(logger *zap.Logger) {
	for {
		time.Sleep(time.Second * 30)
		maxid, err := db.GetLastPostId()
		if err != nil {
			logger.Warn("Error during periodic query for the last post id", zap.Error(err))
			continue // ignore
		}
		if maxid > newPostObserver.LastId() { // <- this is not atomic, but post ids only expected to grow, so this should not be an issue
			err = newPostObserver.Notify(maxid)
			if err != nil {
				logger.Warn("Error while notifying observers of the result of a periodic query", zap.Error(err))
				continue // ignore
			}
		}
	}
}

func SetupEndpoints(routerGroup *gin.RouterGroup, logger *zap.Logger) error {

	// First, setup observer for the long polling thing
	id, err := db.GetLastPostId()
	if err != nil {
		return err
	}
	newPostObserver = observer.NewNewIdObserver(id)
	routerGroup.GET("/poll", longPoll)
	go dbIdPoller(logger)

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
