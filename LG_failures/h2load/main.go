package main

import (
	"flag"
	"log"
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

type PhaseConfig struct {
	FastDur   time.Duration
	SlowDur   time.Duration
	FastDelay time.Duration
	SlowDelay time.Duration
}

type PhaseInfo struct {
	Name  string
	Delay time.Duration
}

var (
	// Number of workload requests that have entered the application handler.
	cumulativeArrivals atomic.Uint64

	// The experiment clock begins when the first workload request arrives.
	startOnce  sync.Once
	startTime  time.Time
	sutStarted = make(chan struct{})
)

// ensureSUTStart initializes the experiment clock on the first workload
// request and returns that start time.
//
// Closing sutStarted safely publishes startTime to the logger goroutine.
func ensureSUTStart() time.Time {
	startOnce.Do(func() {
		startTime = time.Now()
		close(sutStarted)
	})

	return startTime
}

// currentPhase determines the phase corresponding to an arrival's elapsed
// time. Each cycle begins with SLOW and then transitions to FAST.
func currentPhase(elapsed time.Duration, cfg PhaseConfig) PhaseInfo {
	cycle := cfg.SlowDur + cfg.FastDur

	if cycle <= 0 {
		return PhaseInfo{
			Name:  "FAST",
			Delay: cfg.FastDelay,
		}
	}

	position := elapsed % cycle

	if position < cfg.SlowDur {
		return PhaseInfo{
			Name:  "SLOW",
			Delay: cfg.SlowDelay,
		}
	}

	return PhaseInfo{
		Name:  "FAST",
		Delay: cfg.FastDelay,
	}
}

func main() {
	addr := flag.String(
		"addr",
		":8080",
		"listen address",
	)

	maxStreams := flag.Int(
		"max-streams",
		50000,
		"maximum concurrent HTTP/2 streams per connection",
	)

	cfg := PhaseConfig{}

	flag.DurationVar(
		&cfg.FastDelay,
		"fast-delay",
		0,
		"service delay for requests arriving during the fast phase",
	)

	flag.DurationVar(
		&cfg.SlowDelay,
		"slow-delay",
		10*time.Second,
		"service delay for requests arriving during the slow phase",
	)

	flag.DurationVar(
		&cfg.FastDur,
		"fast-dur",
		15*time.Second,
		"duration of each fast phase",
	)

	flag.DurationVar(
		&cfg.SlowDur,
		"slow-dur",
		10*time.Second,
		"duration of each slow phase",
	)

	flag.Parse()

	mux := http.NewServeMux()

	mux.HandleFunc("GET /{$}", func(w http.ResponseWriter, r *http.Request) {
		sutStart := ensureSUTStart()

		arrivalElapsed := time.Since(sutStart)
		phase := currentPhase(arrivalElapsed, cfg)

		cumulativeArrivals.Add(1)

		time.Sleep(phase.Delay)

		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok\n"))
	})

	// Log cumulative application-level arrivals approximately once per second.
	go func() {
		ticker := time.NewTicker(time.Second)
		defer ticker.Stop()

		for range ticker.C {
			select {
			case <-sutStarted:
				// startTime has been initialized and safely published.
			default:
				continue
			}

			elapsed := time.Since(startTime)
			phase := currentPhase(elapsed, cfg)
			total := cumulativeArrivals.Load()

			log.Printf(
				"t=%.3fs phase_now=%s cumulative_arrivals=%d",
				elapsed.Seconds(),
				phase.Name,
				total,
			)
		}
	}()

	// Enable unencrypted HTTP/2 prior knowledge and HTTP/1.1 on the same port.
	protocols := new(http.Protocols)
	protocols.SetUnencryptedHTTP2(true)
	protocols.SetHTTP1(true)

	server := &http.Server{
		Addr:      *addr,
		Handler:   mux,
		Protocols: protocols,
		HTTP2: &http.HTTP2Config{
			MaxConcurrentStreams: *maxStreams,
		},
	}

	log.Printf(
		"listening on %s using native h2c; "+
			"max_streams_per_connection=%d "+
			"phase_order=SLOW,FAST "+
			"slow_delay=%s fast_delay=%s "+
			"slow_dur=%s fast_dur=%s",
		*addr,
		*maxStreams,
		cfg.SlowDelay,
		cfg.FastDelay,
		cfg.SlowDur,
		cfg.FastDur,
	)

	log.Fatal(server.ListenAndServe())
}
