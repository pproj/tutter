package views

import (
	"context"
	"fmt"
	"git.sch.bme.hu/pp23/tutter/db"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
	"time"
)

type longPollQueryParams struct {
	Last     *uint64 `form:"last"`
	Tag      *string `form:"tag"`
	AuthorId *uint   `form:"author_id"`
}

func (l longPollQueryParams) Validate() error {
	if (l.Tag != nil) && (*l.Tag == "") {
		return fmt.Errorf("tag can not be empty")
	}

	if (l.Tag != nil) && (l.AuthorId != nil) {
		return fmt.Errorf("tag and author_id can not be used together")
	}

	return nil
}

func (l longPollQueryParams) Evaluate(p *db.Post) bool {
	if p == nil { // Would this ever happen?
		return false
	}

	if l.AuthorId != nil { // filtering for author_id
		if p.AuthorID != *l.AuthorId {
			return false
		}
	} else if l.Tag != nil { // filtering for tag (should not filter for both, so else-if is fine

		found := false
		for _, tag := range p.Tags { // very lame linear search
			if tag.Tag == *l.Tag {
				found = true
				break
			}
		}
		if !found {
			return false
		}

	}

	return true
}

func (l longPollQueryParams) ConvertToStandard() db.PostFilterParams { // oh Lord forgive me...
	p := db.PostFilterParams{
		AfterId: l.Last, // this would be updated probably
	}
	if l.Tag != nil {
		p.Tags = []string{*l.Tag}
	}
	if l.AuthorId != nil {
		p.Authors = []uint{*l.AuthorId}
	}
	return p
}

func longPoll(ctx *gin.Context) {
	ctx2, cancel := context.WithTimeout(ctx, time.Minute*2)
	defer cancel() // <- This will cause ctx2.Done() channel to return

	var queryParams longPollQueryParams
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

	var lastID uint64
	if queryParams.Last != nil {
		lastID = *queryParams.Last
	} else {
		lastPost := newPostObserver.LastPost()

		if lastPost != nil {
			lastID = lastPost.ID
		} else {
			lastID = 0 // no posts yet
		}

		// TODO: Document somewhere that it's unlikely the best option
	}

	newPostChan, err := newPostObserver.Subscribe(ctx2)

	var posts *[]db.Post

BigWait:
	for { // This is looped if we received something interesting on the channel, but after querying the DB we conclude that it wasn't interesting

		var lastPostIdReceivedOnTheChannel uint64

	SmallWait:
		for { // This is looped if we receive something on the channel, but it's not what we are looking for...
			select {
			case newPost := <-newPostChan: // The last post is always put in the channel when it's created

				if newPost == nil || newPost.ID <= lastID {
					continue SmallWait
				}

				// The user does not know about this post...

				// quick optimization: if the user have not missed any post, (this new post is what we should return) we may quietly shift their last expected ID since we know that this post would not match anyway
				// Sadly we can not do this, it the user is behind with more than one post, because we can only check the latest one here...
				// We can only do this because IDs are expected to be monotonically incrementing!
				if newPost.ID == lastID+1 {
					match := queryParams.Evaluate(newPost)
					if !match {
						lastID = newPost.ID // wait for the next post, since this one did not match
						continue SmallWait
					}
				}

				// The user is more than one post behind OR the latest post matched

				lastPostIdReceivedOnTheChannel = newPost.ID // this will be used to reduce queries later if the db query does not return anything useful
				break SmallWait                             // we may respond now...

			case <-ctx2.Done():
				ctx.Status(204)
				// Deadline exceeded, no new post were created
				return
			case <-ctx.Writer.CloseNotify():
				// Connection closed
				// Since the context's close is deferred, the context will be canceled
				return
			}
		} // end of SmallWait

		// We MIGHT have something in the DB for the user...
		magicQueryParams := queryParams.ConvertToStandard()
		magicQueryParams.AfterId = &lastID // update the last id that we optimized (it isn't actually needed*)
		/*
			Incrementing the lastID only causes the SmallWait to break less, because every new message received on the channel would
			cause SmallWait to break normally, just to query the db and return nothing every time

			if we keep te lastID up to date with the last post, we can keep the optimization (local filtering) kicking in
			thus checking post locally instead of going for the DB every time.

			But (if everything works correctly) incrementing the ID should not change the result returned from the DB,
			so there is no point of incrementing it, other than maybe having the DB do less work we already did locally
		*/
		posts, err = db.GetPosts(&magicQueryParams)
		if err != nil {

			if err == gorm.ErrRecordNotFound {
				if lastPostIdReceivedOnTheChannel != 0 {
					lastID = lastPostIdReceivedOnTheChannel // wait for the next post, since this one did not match
				}
				continue BigWait // actually, nevermind...
			}

			handleInternalError(ctx, err)
			return
		}

		if posts == nil || len(*posts) == 0 {
			if lastPostIdReceivedOnTheChannel != 0 {
				lastID = lastPostIdReceivedOnTheChannel // wait for the next post, since this one did not match
			}
			continue BigWait // actually, nevermind...
		}

		// The posts var is filled up, now break out of this loop, and return the result
		break BigWait

	}

	ctx.JSON(200, posts)

}
