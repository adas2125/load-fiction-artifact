package main

import (
	"encoding/csv"
	"encoding/json"
	"flag"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync/atomic"
	"time"
)

type response struct {
	Now          time.Time     `json:"now"`           // when the request arrived
	Phase        string        `json:"phase"`         // current phase of the server (fast or slow)
	AppliedDelay time.Duration `json:"applied_delay"` // delay applied to the request
	TotalCount   uint64        `json:"total_count"`   // total number of requests arrived
}

func main() {
	// command-line flags to configure the server behavior
	addr := flag.String("addr", ":8080", "listen address")
	fastDelay := flag.Duration("fast-delay", 10*time.Millisecond, "delay outside the spike window")
	slowDelay := flag.Duration("slow-delay", 200*time.Millisecond, "delay inside the spike window")
	cycle := flag.Duration("cycle", 4*time.Second, "full duration of the repeating latency pattern")
	spike := flag.Duration("spike", 1500*time.Millisecond, "time spent in the slow phase within each cycle")
	arrivalLog := flag.String("arrival-log", "arrival_counts.csv", "CSV file for periodic arrival counts; empty disables")
	arrivalInterval := flag.Duration("arrival-interval", time.Second, "arrival count sampling interval")
	flag.Parse()

	if *cycle <= 0 {
		log.Fatal("cycle must be > 0")
	}
	if *spike < 0 || *spike > *cycle {
		log.Fatal("spike must be between 0 and cycle")
	}
	if *arrivalInterval <= 0 {
		log.Fatal("arrival-interval must be > 0")
	}

	var total uint64 // total number of requests arrived, updated atomically
	var firstRequestUnixNano int64
	var arrivalWriter *csv.Writer
	var arrivalFile *os.File
	if *arrivalLog != "" {
		var err error
		arrivalFile, err = os.Create(*arrivalLog)
		if err != nil {
			log.Fatalf("create arrival log: %v", err)
		}
		defer arrivalFile.Close()
		arrivalWriter = csv.NewWriter(arrivalFile)
		defer arrivalWriter.Flush()
		if err := arrivalWriter.Write([]string{"timestamp", "elapsed_ms", "arrivals_total", "arrivals_interval"}); err != nil {
			log.Fatalf("write arrival log header: %v", err)
		}
		arrivalWriter.Flush()
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		now := time.Now()
		firstRequest := atomic.LoadInt64(&firstRequestUnixNano)

		// check if this is the first request
		if firstRequest == 0 {

			// assign current timestamp to firstRequest
			firstRequest = now.UnixNano()

			// swap in the first request timestamp if it's still 0, otherwise use the existing value
			// handles race conditions where multiple requests arrive at the same time when the server is starting up
			if !atomic.CompareAndSwapInt64(&firstRequestUnixNano, 0, firstRequest) {
				firstRequest = atomic.LoadInt64(&firstRequestUnixNano)
			}
		}

		// calculate how much time has elapsed since the first request
		elapsed := now.Sub(time.Unix(0, firstRequest))
		// position within the current cycle determines the delay applied to this request
		offset := elapsed % *cycle

		// start with fast delay
		delay := *fastDelay
		phase := "fast"

		// if we're within the spike window, switch to slow delay
		if offset < *spike {
			delay = *slowDelay
			phase = "slow"
		}

		// increment the total count of arrivals
		count := atomic.AddUint64(&total, 1)

		time.Sleep(delay)
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(response{
			Now:          now,
			Phase:        phase,
			AppliedDelay: delay,
			TotalCount:   count,
		})
	})

	// background goroutine to log periodic arrival counts
	go func() {
		ticker := time.NewTicker(*arrivalInterval)
		defer ticker.Stop()

		var last uint64
		for range ticker.C {
			// total is incremented before sleeping, so this records arrivals, not completions.
			now := time.Now()
			totalNow := atomic.LoadUint64(&total)
			intervalArrivals := totalNow - last
			elapsedMs := int64(0)
			if firstRequest := atomic.LoadInt64(&firstRequestUnixNano); firstRequest != 0 {
				elapsedMs = now.Sub(time.Unix(0, firstRequest)).Milliseconds()
			}
			log.Printf("arrivals=%d last_interval=%d\n", totalNow, intervalArrivals)
			if arrivalWriter != nil {
				if err := arrivalWriter.Write([]string{
					now.Format(time.RFC3339Nano),
					strconv.FormatInt(elapsedMs, 10),
					formatUint(totalNow),
					formatUint(intervalArrivals),
				}); err != nil {
					log.Printf("write arrival log: %v", err)
				}
				arrivalWriter.Flush()
			}
			last = totalNow
		}
	}()

	log.Printf("listening on %s fast=%s slow=%s cycle=%s spike=%s\n", *addr, *fastDelay, *slowDelay, *cycle, *spike)
	log.Fatal(http.ListenAndServe(*addr, mux))
}

func formatUint(v uint64) string {
	return strconv.FormatUint(v, 10)
}
