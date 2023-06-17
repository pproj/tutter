package views

import (
	"git.sch.bme.hu/pp23/tutter/db"
	"git.sch.bme.hu/pp23/tutter/observer"
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
	"gorm.io/gorm"
	"time"
)

// dbIdPoller is used to give subscribers that missed an event a second chance of catching it.
// This is also useful when the application is running in multiple replicas and the shared sync thing does not work for some reason
func dbIdPoller(logger *zap.Logger) {
	for {
		time.Sleep(time.Second * 30)
		lastPostInDB, err := db.GetLastPost()
		if err != nil {

			if err == gorm.ErrRecordNotFound {
				continue // ignore without warning
			}

			logger.Warn("Error during periodic query for the last post id", zap.Error(err))
			continue // ignore
		}

		lastPostInMemory := newPostObserver.LastPost()
		if lastPostInMemory == nil || lastPostInDB.ID > lastPostInMemory.ID { // <- this is not atomic, but post ids only expected to grow, so this should not be an issue
			err = newPostObserver.Notify(lastPostInDB)
			if err != nil {
				logger.Warn("Error while notifying observers of the result of a periodic query", zap.Error(err))
				continue // ignore
			}
		}
	}
}

func SetupEndpoints(routerGroup *gin.RouterGroup, logger *zap.Logger, debug bool, debugPin string) error {

	// First, setup observer for the long polling thing
	lastPost, err := db.GetLastPost()
	if err == gorm.ErrRecordNotFound {
		lastPost = nil
	} else if err != nil {
		return err
	}
	newPostObserver = observer.NewNewPostObserver(lastPost, debug)
	routerGroup.GET("/poll", longPoll)
	go dbIdPoller(logger)

	// Then the REST
	routerGroup.POST("/post", createPost)
	routerGroup.GET("/post", listPosts)
	routerGroup.GET("/post/:id", getPost)

	routerGroup.GET("/tag", listTags)
	routerGroup.GET("/tag/:tag", getTag)
	routerGroup.GET("/trending", getTrendingTags)

	routerGroup.GET("/author", listAuthors)
	routerGroup.GET("/author/:id", getAuthor)

	if debug { // only register these in debug mode!!
		logger.Warn("REGISTERING DEBUG ENDPOINTS! THIS IS SUPER UNSAFE AND NOT SOMETHING YOU WANT IN PRODUCTION!")
		debugGroup := routerGroup.Group("/debug")
		debugGroup.Use(createDebugAuth(debugPin))
		debugGroup.POST("/cleanup", debugCleanup)
		debugGroup.PUT("/setTrending/:tag", debugSetTrending)
		debugGroup.DELETE("/setTrending/:tag", debugSetTrending)
	}

	return nil
}
