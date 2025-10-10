// Package main provides examples for Tree-sitter MCP testing
// Demonstrates Go features: structs, interfaces, goroutines, channels
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "sync"
    "time"
)

// User represents a user in the system
type User struct {
    ID        int       `json:"id"`
    Username  string    `json:"username"`
    Email     string    `json:"email"`
    CreatedAt time.Time `json:"created_at"`
    Active    bool      `json:"active"`
}

// Interface definitions
type Storage interface {
    Save(ctx context.Context, data interface{}) error
    Load(ctx context.Context, id string) (interface{}, error)
    Delete(ctx context.Context, id string) error
}

type Cache interface {
    Get(key string) (interface{}, bool)
    Set(key string, value interface{}, ttl time.Duration)
    Delete(key string)
}

// Repository pattern implementation
type UserRepository struct {
    storage Storage
    cache   Cache
    mu      sync.RWMutex
}

func NewUserRepository(storage Storage, cache Cache) *UserRepository {
    return &UserRepository{
        storage: storage,
        cache:   cache,
    }
}

func (r *UserRepository) GetUser(ctx context.Context, id int) (*User, error) {
    // Check cache first
    if cached, ok := r.cache.Get(fmt.Sprintf("user:%d", id)); ok {
        if user, ok := cached.(*User); ok {
            return user, nil
        }
    }
    
    // Load from storage
    data, err := r.storage.Load(ctx, fmt.Sprintf("%d", id))
    if err != nil {
        return nil, fmt.Errorf("failed to load user: %w", err)
    }
    
    user, ok := data.(*User)
    if !ok {
        return nil, fmt.Errorf("invalid user data type")
    }
    
    // Cache the result
    r.cache.Set(fmt.Sprintf("user:%d", id), user, 5*time.Minute)
    
    return user, nil
}

// Generic function (Go 1.18+)
func Map[T, U any](slice []T, fn func(T) U) []U {
    result := make([]U, len(slice))
    for i, v := range slice {
        result[i] = fn(v)
    }
    return result
}

// Concurrent worker pool
func WorkerPool(jobs <-chan int, results chan<- int, workerCount int) {
    var wg sync.WaitGroup
    
    worker := func(id int) {
        defer wg.Done()
        for job := range jobs {
            // Simulate work
            time.Sleep(100 * time.Millisecond)
            results <- job * 2
            fmt.Printf("Worker %d processed job %d\n", id, job)
        }
    }
    
    // Start workers
    for i := 0; i < workerCount; i++ {
        wg.Add(1)
        go worker(i)
    }
    
    // Wait for all workers to complete
    wg.Wait()
    close(results)
}

// Error handling with custom error type
type ValidationError struct {
    Field   string
    Message string
}

func (e ValidationError) Error() string {
    return fmt.Sprintf("validation error on field %s: %s", e.Field, e.Message)
}

func ValidateUser(user *User) error {
    if user.Username == "" {
        return ValidationError{Field: "username", Message: "cannot be empty"}
    }
    if len(user.Username) < 3 {
        return ValidationError{Field: "username", Message: "must be at least 3 characters"}
    }
    return nil
}

// Channel select example
func multiplex(ch1, ch2 <-chan string) <-chan string {
    out := make(chan string)
    go func() {
        defer close(out)
        for {
            select {
            case msg, ok := <-ch1:
                if !ok {
                    ch1 = nil
                    continue
                }
                out <- fmt.Sprintf("ch1: %s", msg)
            case msg, ok := <-ch2:
                if !ok {
                    ch2 = nil
                    continue
                }
                out <- fmt.Sprintf("ch2: %s", msg)
            }
            if ch1 == nil && ch2 == nil {
                return
            }
        }
    }()
    return out
}

// Defer and panic/recover
func SafeOperation() (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered from panic: %v", r)
        }
    }()
    
    // Potentially panicking operation
    riskyOperation()
    return nil
}

func riskyOperation() {
    panic("something went wrong")
}

func main() {
    // Create user
    user := &User{
        ID:        1,
        Username:  "john_doe",
        Email:     "john@example.com",
        CreatedAt: time.Now(),
        Active:    true,
    }
    
    // Validate user
    if err := ValidateUser(user); err != nil {
        fmt.Printf("Validation failed: %v\n", err)
    }
    
    // JSON marshaling
    data, _ := json.MarshalIndent(user, "", "  ")
    fmt.Printf("User JSON:\n%s\n", data)
    
    // Use generic function
    numbers := []int{1, 2, 3, 4, 5}
    squared := Map(numbers, func(n int) int { return n * n })
    fmt.Printf("Squared: %v\n", squared)
    
    // Worker pool example
    jobs := make(chan int, 100)
    results := make(chan int, 100)
    
    go func() {
        for i := 1; i <= 10; i++ {
            jobs <- i
        }
        close(jobs)
    }()
    
    go WorkerPool(jobs, results, 3)
    
    // Collect results
    for result := range results {
        fmt.Printf("Result: %d\n", result)
    }
}