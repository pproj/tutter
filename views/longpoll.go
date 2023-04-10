package views

import (
	"context"
	"git.sch.bme.hu/pp23/tutter/db"
	"github.com/gin-gonic/gin"
	"strconv"
	"time"
)

func longPoll(ctx *gin.Context) {
	ctx2, cancel := context.WithTimeout(ctx, time.Minute*2)
	defer cancel() // <- This will cause ctx2.Done() channel to return

	var last uint64
	lastStr, ok := ctx.GetQuery("last")
	if ok {
		var err error
		last, err = strconv.ParseUint(lastStr, 10, 64)
		if err != nil {
			handleUserError(ctx, err)
			return
		}
	} else {
		last = 0 // TODO: Get current max id, and document that it is not a good idea to use it
	}

	newMsgChan := make(chan uint64)
	go func() {
		time.Sleep(time.Second * 30)
		newMsgChan <- 2
	}()

BigWait:
	for { // This is a long, complex wait thing
		select {
		case newId := <-newMsgChan:

			if newId <= last {
				continue BigWait
			}

			break BigWait

		case <-ctx2.Done():
			ctx.Status(204)
			// Deadline exceeded, no new post were created
			return
		case <-ctx.Writer.CloseNotify():
			// Connection closed
			// Since the context's close is deferred, the context will be canceled
			return
		}
	}

	// We got a new ID, the context or the connection is not (yet) closed, we can run the query and return the results now
	posts, err := db.GetAllPostsAfterId(last)
	if err != nil {
		handleInternalError(ctx, err)
		return
	}
	ctx.JSON(200, posts)

}
