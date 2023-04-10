package observer

import (
	"context"
	"sync"
	"sync/atomic"
)

type NewIdObserver struct {
	lastId    atomic.Uint64 // This is only updated in the run function.
	inputChan chan uint64

	// Using a mutex isn't really efficient, but it is what it is
	outputChanMutex sync.Mutex // RWLock would not make much sense as notify is the only read, and it's called from a single gorutine only
	outputChans     map[chan uint64]interface{}
}

func NewNewIdObserver(lastId uint64) *NewIdObserver {
	o := NewIdObserver{
		inputChan:   make(chan uint64, 10),
		outputChans: make(map[chan uint64]interface{}),
	}
	o.lastId.Store(lastId)
	go o.run()
	return &o
}

// Subscribe is a complex function, but it basically just returns with a channel that will pump out ids of new posts
// the ids may not be in sequence!
// The ID of the last post is always put on the channel upon subscribing, so the race condition with check-before-subscribe can be eliminated
// If the context is cancelled along the way, the channel will be closed, and un-subscribed automagically
func (o *NewIdObserver) Subscribe(ctx context.Context) (<-chan uint64, error) {
	subscriberChan := make(chan uint64, 3)
	subscriberChan <- o.lastId.Load()
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

func (o *NewIdObserver) Notify(id uint64) error {
	o.inputChan <- id
	return nil
}

func (o *NewIdObserver) LastId() uint64 {
	return o.lastId.Load()
}

func (o *NewIdObserver) run() {

	for {
		select {
		case inputId := <-o.inputChan:
			currentLastId := o.lastId.Load()
			if inputId > currentLastId {
				if !o.lastId.CompareAndSwap(currentLastId, inputId) {
					panic("race condition while storing last id (should not be updated outside this goroutine)")
				}
				o.outputChanMutex.Lock()
				for ch := range o.outputChans {
					select { // This is a non-blocking send in golang
					case ch <- inputId: // This would panic if any of the channels were closed, but the subscriber should make sure that no closed channels are in this list
					default:
						// TODO: log warning
					}
				}
				o.outputChanMutex.Unlock()

			}

		}
	}

}
