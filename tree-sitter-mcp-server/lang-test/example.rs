// Rust example for Tree-sitter MCP testing
// Demonstrates ownership, traits, generics, error handling, and async

use std::collections::HashMap;
use std::error::Error;
use std::fmt;
use std::sync::{Arc, Mutex};
use async_trait::async_trait;

// Custom error type
#[derive(Debug)]
enum AppError {
    NotFound(String),
    InvalidInput(String),
    DatabaseError(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::NotFound(msg) => write!(f, "Not found: {}", msg),
            AppError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            AppError::DatabaseError(msg) => write!(f, "Database error: {}", msg),
        }
    }
}

impl Error for AppError {}

// Generic struct with lifetime parameter
#[derive(Debug, Clone)]
struct User<'a> {
    id: u64,
    username: &'a str,
    email: String,
    metadata: HashMap<String, String>,
}

impl<'a> User<'a> {
    fn new(id: u64, username: &'a str, email: String) -> Self {
        Self {
            id,
            username,
            email,
            metadata: HashMap::new(),
        }
    }
    
    fn add_metadata(&mut self, key: String, value: String) {
        self.metadata.insert(key, value);
    }
}

// Trait definition
trait Repository<T> {
    fn save(&mut self, item: T) -> Result<(), AppError>;
    fn find(&self, id: u64) -> Result<Option<T>, AppError>;
    fn delete(&mut self, id: u64) -> Result<(), AppError>;
}

// Async trait
#[async_trait]
trait AsyncService {
    async fn process(&self, data: Vec<u8>) -> Result<String, Box<dyn Error>>;
    async fn validate(&self, input: &str) -> bool;
}

// Generic implementation with trait bounds
struct InMemoryRepository<T: Clone> {
    storage: Arc<Mutex<HashMap<u64, T>>>,
}

impl<T: Clone> InMemoryRepository<T> {
    fn new() -> Self {
        Self {
            storage: Arc::new(Mutex::new(HashMap::new())),
        }
    }
}

impl<T: Clone> Repository<T> for InMemoryRepository<T> {
    fn save(&mut self, item: T) -> Result<(), AppError> {
        let mut storage = self.storage.lock()
            .map_err(|e| AppError::DatabaseError(e.to_string()))?;
        
        // Simulating ID generation
        let id = storage.len() as u64 + 1;
        storage.insert(id, item);
        Ok(())
    }
    
    fn find(&self, id: u64) -> Result<Option<T>, AppError> {
        let storage = self.storage.lock()
            .map_err(|e| AppError::DatabaseError(e.to_string()))?;
        Ok(storage.get(&id).cloned())
    }
    
    fn delete(&mut self, id: u64) -> Result<(), AppError> {
        let mut storage = self.storage.lock()
            .map_err(|e| AppError::DatabaseError(e.to_string()))?;
        
        storage.remove(&id)
            .ok_or_else(|| AppError::NotFound(format!("Item with id {} not found", id)))?;
        Ok(())
    }
}

// Enum with pattern matching
#[derive(Debug)]
enum Command {
    Create { name: String, value: i32 },
    Update { id: u64, value: i32 },
    Delete { id: u64 },
    Query { filter: String },
}

impl Command {
    fn execute(&self) -> Result<String, AppError> {
        match self {
            Command::Create { name, value } => {
                Ok(format!("Created {} with value {}", name, value))
            }
            Command::Update { id, value } => {
                Ok(format!("Updated item {} to value {}", id, value))
            }
            Command::Delete { id } => {
                Ok(format!("Deleted item {}", id))
            }
            Command::Query { filter } => {
                if filter.is_empty() {
                    Err(AppError::InvalidInput("Filter cannot be empty".to_string()))
                } else {
                    Ok(format!("Querying with filter: {}", filter))
                }
            }
        }
    }
}

// Iterator implementation
struct FibonacciIterator {
    curr: u64,
    next: u64,
}

impl FibonacciIterator {
    fn new() -> Self {
        Self { curr: 0, next: 1 }
    }
}

impl Iterator for FibonacciIterator {
    type Item = u64;
    
    fn next(&mut self) -> Option<Self::Item> {
        let current = self.curr;
        self.curr = self.next;
        self.next = current + self.next;
        Some(current)
    }
}

// Closure and higher-order functions
fn apply_operation<F>(values: Vec<i32>, operation: F) -> Vec<i32>
where
    F: Fn(i32) -> i32,
{
    values.into_iter().map(operation).collect()
}

// Macro definition
macro_rules! create_function {
    ($func_name:ident, $op:tt) => {
        fn $func_name(a: i32, b: i32) -> i32 {
            a $op b
        }
    };
}

create_function!(add, +);
create_function!(subtract, -);
create_function!(multiply, *);

// Async function
async fn fetch_data(url: &str) -> Result<String, Box<dyn Error>> {
    // Simulating async operation
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    Ok(format!("Data from {}", url))
}

// Pattern matching with guards
fn categorize_number(n: i32) -> &'static str {
    match n {
        n if n < 0 => "negative",
        0 => "zero",
        1..=10 => "small positive",
        11..=100 => "medium positive",
        _ => "large positive",
    }
}

// Main function demonstrating usage
#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    // Create user
    let mut user = User::new(1, "alice", "alice@example.com".to_string());
    user.add_metadata("role".to_string(), "admin".to_string());
    
    // Use repository
    let mut repo: InMemoryRepository<String> = InMemoryRepository::new();
    repo.save("test_data".to_string())?;
    
    // Execute command
    let cmd = Command::Create {
        name: "item".to_string(),
        value: 42,
    };
    println!("Command result: {}", cmd.execute()?);
    
    // Use iterator
    let fib: Vec<u64> = FibonacciIterator::new().take(10).collect();
    println!("Fibonacci: {:?}", fib);
    
    // Use closure
    let numbers = vec![1, 2, 3, 4, 5];
    let doubled = apply_operation(numbers, |x| x * 2);
    println!("Doubled: {:?}", doubled);
    
    // Use async function
    let data = fetch_data("https://api.example.com").await?;
    println!("Fetched: {}", data);
    
    // Pattern matching
    println!("Number category: {}", categorize_number(42));
    
    Ok(())
}