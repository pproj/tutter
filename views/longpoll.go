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
		last = newPostObserver.LastId()
		// TODO: Document somewhere that it's unlikely the best option
	}

	newIdChan, err := newPostObserver.Subscribe(ctx2)

BigWait:
	for { // This is a long, complex wait thing
		select {
		case newId := <-newIdChan:

			if newId <= last {
				continue BigWait
			}

			// We don't actually have to keep this value, as the query uses the last id anyways
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

	if posts == nil || len(*posts) == 0 {
		// This is a highly unlikely situation, but I like to tell myself that I have prepared for everything
		ctx.Status(204)
	} else {
		ctx.JSON(200, posts)
	}

}
