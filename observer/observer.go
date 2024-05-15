package observer

import (
	"context"
	"fmt"
	"github.com/pproj/tutter/db"
	"sync"
	"sync/atomic"
)

type NewPostObserver struct {
	lastPost  atomic.Pointer[db.Post] // This is only updated in the run function.
	inputChan chan *db.Post

	// Using a mutex isn't really efficient, but it is what it is
	outputChanMutex sync.Mutex // RWLock would not make much sense as notify is the only read, and it's called from a single gorutine only
	outputChans     map[chan *db.Post]interface{}

	allowDebug bool
}

func NewNewPostObserver(lastPost *db.Post, allowDebug bool) *NewPostObserver {
	if lastPost == nil {
		// TODO: log Warning!
	}

	o := NewPostObserver{
		inputChan:   make(chan *db.Post, 10),
		outputChans: make(map[chan *db.Post]interface{}),
		allowDebug:  allowDebug,
	}
	o.lastPost.Store(lastPost) // THIS MAY BE NIL!!
	go o.run()
	return &o
}

// Subscribe is a complex function, but it basically just returns with a channel that will pump out ids of new posts
// the ids may not be in sequence!
// The ID of the last post is always put on the channel upon subscribing, so the race condition with check-before-subscribe can be eliminated
// If the context is cancelled along the way, the channel will be closed, and un-subscribed automagically
func (o *NewPostObserver) Subscribe(ctx context.Context) (<-chan *db.Post, error) {
	subscriberChan := make(chan *db.Post, 3)
	lastPost := o.lastPost.Load()
	if lastPost != nil { // only send if there's something to send
		subscriberChan <- lastPost
	}
	o.outputChanMutex.Lock()
	o.outputChans[subscriberChan] = nil
	o.outputChanMutex.Unlock()

	go func() { // Yes, this allocates an extra goroutine for each subscriber... but it won't be easy to wait on this many contexts
		<-ctx.Done()
		o.outputChanMutex.Lock()
		delete(o.outputChans, subscriberChan)
		o.outputChanMutex.Unlock()
		close(subscriberChan)
	}()

	return subscriberChan, nil
}

func (o *NewPostObserver) Notify(post *db.Post) error {
	if post == nil {
		return fmt.Errorf("can not use Notify() with nil")
	}
	o.inputChan <- post
	return nil
}

// LastPost returns the last post or nil if there weren't any posts posted yet
func (o *NewPostObserver) LastPost() *db.Post {
	return o.lastPost.Load()
}

func (o *NewPostObserver) DebugCleanup() {
	if !o.allowDebug {
		return
	}
	o.lastPost.Store(nil)
}

func (o *NewPostObserver) run() {

	for {
		select {
		case inputPost := <-o.inputChan:

			if inputPost == nil {
				continue // should not happen, but ignore it anyway
				// TODO: log warning?
			}

			currentLastPost := o.lastPost.Load()
			if currentLastPost == nil || inputPost.ID > currentLastPost.ID {
				if !o.lastPost.CompareAndSwap(currentLastPost, inputPost) {
					panic("race condition while storing last id (should not be updated outside this goroutine)")
				}
				o.outputChanMutex.Lock()
				for ch := range o.outputChans {
					select { // This is a non-blocking send in golang
					case ch <- inputPost: // This would panic if any of the channels were closed, but the subscriber should make sure that no closed channels are in this list
					default:
						// TODO: log warning
					}
				}
				o.outputChanMutex.Unlock()

			}

		}
	}

}
