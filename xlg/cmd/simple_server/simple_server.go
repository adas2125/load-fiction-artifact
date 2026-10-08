package main

import (
	"flag"
	"fmt"
	"math/rand/v2"
	"net/http"
	"time"
)

func main() {
	addr := flag.String("addr", ":8080", "listen address")

	// Delay mode: fixed, uniform, exp
	delayMode := flag.String("delay-mode", "fixed", "delay mode: fixed, uniform, exp")

	// Fixed delay
	delay := flag.Duration("delay", 0, "fixed response delay (e.g. 50ms, 200ms)")

	// Uniform delay parameters
	minDelay := flag.Duration("min-delay", 0, "minimum delay for uniform mode")
	maxDelay := flag.Duration("max-delay", 0, "maximum delay for uniform mode")

	// Exponential delay parameter
	meanDelay := flag.Duration("mean-delay", 0, "mean delay for exp mode")

	flag.Parse()

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		// Call without rng
		d := sampleDelay(*delayMode, *delay, *minDelay, *maxDelay, *meanDelay)
		if d > 0 {
			time.Sleep(d)
		}

		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	fmt.Println("server listening on", *addr)
	fmt.Println("delay mode:", *delayMode)
	_ = http.ListenAndServe(*addr, nil)
}

func sampleDelay(
	mode string,
	fixed time.Duration,
	minDelay time.Duration,
	maxDelay time.Duration,
	meanDelay time.Duration,
) time.Duration {
	switch mode {
	case "fixed":
		return fixed

	case "uniform":
		if maxDelay < minDelay {
			minDelay, maxDelay = maxDelay, minDelay
		}
		if maxDelay == minDelay {
			return minDelay
		}
		span := maxDelay - minDelay
		// v2 uses Int64N instead of Int63n
		return minDelay + time.Duration(rand.Int64N(int64(span)+1))

	case "exp":
		if meanDelay <= 0 {
			return 0
		}
		// ExpFloat64 remains exactly the same in v2
		return time.Duration(rand.ExpFloat64() * float64(meanDelay))

	default:
		fmt.Printf("unknown delay mode %q, defaulting to fixed\n", mode)
		return fixed
	}
}
