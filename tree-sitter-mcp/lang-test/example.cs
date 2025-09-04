// C# (.NET) example for Tree-sitter MCP testing
// Demonstrates modern C# features: records, pattern matching, LINQ, async/await, nullable references

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Text.Json;
using System.Net.Http;
using System.Collections.Concurrent;

namespace TreeSitterExample
{
    // Record types (C# 9+)
    public record Person(string FirstName, string LastName, DateTime BirthDate)
    {
        public int Age => DateTime.Now.Year - BirthDate.Year;
        public string FullName => $"{FirstName} {LastName}";
    }

    // Interface with default implementation
    public interface IRepository<T> where T : class
    {
        Task<T?> GetByIdAsync(int id);
        Task<IEnumerable<T>> GetAllAsync();
        Task<T> CreateAsync(T entity);
        Task UpdateAsync(T entity);
        Task DeleteAsync(int id);
        
        // Default interface method
        async Task<bool> ExistsAsync(int id)
        {
            var entity = await GetByIdAsync(id);
            return entity != null;
        }
    }

    // Generic repository with constraints
    public class InMemoryRepository<T> : IRepository<T> where T : class, IEntity
    {
        private readonly ConcurrentDictionary<int, T> _storage = new();
        private int _nextId = 1;

        public async Task<T?> GetByIdAsync(int id)
        {
            await Task.Delay(10); // Simulate async operation
            return _storage.TryGetValue(id, out var entity) ? entity : null;
        }

        public async Task<IEnumerable<T>> GetAllAsync()
        {
            await Task.Delay(10);
            return _storage.Values.ToList();
        }

        public async Task<T> CreateAsync(T entity)
        {
            entity.Id = _nextId++;
            _storage[entity.Id] = entity;
            await Task.Delay(10);
            return entity;
        }

        public async Task UpdateAsync(T entity)
        {
            if (!_storage.ContainsKey(entity.Id))
                throw new InvalidOperationException($"Entity with ID {entity.Id} not found");
            
            _storage[entity.Id] = entity;
            await Task.Delay(10);
        }

        public async Task DeleteAsync(int id)
        {
            _storage.TryRemove(id, out _);
            await Task.Delay(10);
        }
    }

    // Interface for entities
    public interface IEntity
    {
        int Id { get; set; }
    }

    // Class with nullable reference types (C# 8+)
    public class Customer : IEntity
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string? Email { get; set; }
        public decimal CreditLimit { get; set; }
        public CustomerType Type { get; set; }
        public List<Order> Orders { get; set; } = new();

        // Computed property
        public decimal TotalOrderValue => Orders.Sum(o => o.Total);

        // Method with nullable return
        public Order? GetLatestOrder()
        {
            return Orders.OrderByDescending(o => o.OrderDate).FirstOrDefault();
        }
    }

    // Enum
    public enum CustomerType
    {
        Regular,
        Premium,
        VIP
    }

    // Class with init-only properties (C# 9+)
    public class Order : IEntity
    {
        public int Id { get; set; }
        public DateTime OrderDate { get; init; }
        public decimal Total { get; init; }
        public OrderStatus Status { get; set; }
        public List<OrderItem> Items { get; init; } = new();
    }

    public record OrderItem(string ProductName, int Quantity, decimal UnitPrice)
    {
        public decimal Subtotal => Quantity * UnitPrice;
    }

    public enum OrderStatus
    {
        Pending,
        Processing,
        Shipped,
        Delivered,
        Cancelled
    }

    // Service class with dependency injection
    public class CustomerService
    {
        private readonly IRepository<Customer> _customerRepository;
        private readonly HttpClient _httpClient;

        public CustomerService(IRepository<Customer> customerRepository, HttpClient httpClient)
        {
            _customerRepository = customerRepository ?? throw new ArgumentNullException(nameof(customerRepository));
            _httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));
        }

        // Async method with cancellation token
        public async Task<Customer?> GetCustomerWithOrdersAsync(int customerId, CancellationToken cancellationToken = default)
        {
            var customer = await _customerRepository.GetByIdAsync(customerId);
            
            if (customer != null)
            {
                // Simulate loading orders
                await Task.Delay(100, cancellationToken);
                customer.Orders = GenerateSampleOrders();
            }
            
            return customer;
        }

        // LINQ operations
        public async Task<IEnumerable<Customer>> GetPremiumCustomersAsync()
        {
            var allCustomers = await _customerRepository.GetAllAsync();
            
            return allCustomers
                .Where(c => c.Type == CustomerType.Premium || c.Type == CustomerType.VIP)
                .Where(c => c.CreditLimit > 10000)
                .OrderByDescending(c => c.CreditLimit)
                .ThenBy(c => c.Name);
        }

        private static List<Order> GenerateSampleOrders()
        {
            return new List<Order>
            {
                new Order
                {
                    OrderDate = DateTime.Now.AddDays(-30),
                    Total = 99.99m,
                    Status = OrderStatus.Delivered,
                    Items = new List<OrderItem>
                    {
                        new("Product A", 2, 49.995m)
                    }
                },
                new Order
                {
                    OrderDate = DateTime.Now.AddDays(-5),
                    Total = 299.99m,
                    Status = OrderStatus.Processing
                }
            };
        }
    }

    // Pattern matching examples (C# 7+, enhanced in C# 8, 9, 10)
    public static class PatternMatchingExamples
    {
        // Switch expressions (C# 8+)
        public static decimal CalculateDiscount(Customer customer) => customer.Type switch
        {
            CustomerType.Regular => 0.05m,
            CustomerType.Premium => 0.10m,
            CustomerType.VIP => 0.20m,
            _ => 0m
        };

        // Pattern matching with property patterns (C# 8+)
        public static string DescribeOrder(Order order) => order switch
        {
            { Status: OrderStatus.Delivered, Total: > 1000 } => "High-value delivered order",
            { Status: OrderStatus.Delivered } => "Delivered order",
            { Status: OrderStatus.Cancelled } => "Cancelled order",
            { Total: > 500 } => "High-value pending order",
            _ => "Regular order"
        };

        // Tuple patterns (C# 8+)
        public static string CategorizeCustomer(CustomerType type, decimal creditLimit) => (type, creditLimit) switch
        {
            (CustomerType.VIP, > 50000) => "Elite VIP",
            (CustomerType.VIP, _) => "Standard VIP",
            (CustomerType.Premium, > 20000) => "High-value Premium",
            (_, > 10000) => "High credit customer",
            _ => "Standard customer"
        };

        // Relational patterns (C# 9+)
        public static string GetSizeCategory(int value) => value switch
        {
            < 0 => "Negative",
            0 => "Zero",
            > 0 and <= 10 => "Small",
            > 10 and <= 100 => "Medium",
            > 100 and <= 1000 => "Large",
            _ => "Extra Large"
        };
    }

    // Extension methods
    public static class CustomerExtensions
    {
        public static bool IsHighValue(this Customer customer)
        {
            return customer.CreditLimit > 50000 || customer.TotalOrderValue > 10000;
        }

        public static async Task<string> ToJsonAsync(this Customer customer)
        {
            await Task.Yield(); // Simulate async operation
            return JsonSerializer.Serialize(customer, new JsonSerializerOptions
            {
                WriteIndented = true,
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            });
        }
    }

    // Generic class with multiple type parameters and constraints
    public class Cache<TKey, TValue> 
        where TKey : notnull 
        where TValue : class
    {
        private readonly Dictionary<TKey, (TValue Value, DateTime Expiry)> _cache = new();
        private readonly TimeSpan _defaultExpiry;

        public Cache(TimeSpan defaultExpiry)
        {
            _defaultExpiry = defaultExpiry;
        }

        public void Set(TKey key, TValue value, TimeSpan? expiry = null)
        {
            var expiryTime = DateTime.UtcNow.Add(expiry ?? _defaultExpiry);
            _cache[key] = (value, expiryTime);
        }

        public TValue? Get(TKey key)
        {
            if (_cache.TryGetValue(key, out var entry))
            {
                if (entry.Expiry > DateTime.UtcNow)
                {
                    return entry.Value;
                }
                _cache.Remove(key);
            }
            return null;
        }
    }

    // Async enumerable (C# 8+)
    public class DataStreamer
    {
        public async IAsyncEnumerable<int> GenerateNumbersAsync(int count)
        {
            for (int i = 0; i < count; i++)
            {
                await Task.Delay(100);
                yield return i;
            }
        }
    }

    // Program class with top-level statements style
    public class Program
    {
        public static async Task Main(string[] args)
        {
            // Using declarations (C# 8+)
            using var httpClient = new HttpClient();
            
            // Target-typed new (C# 9+)
            IRepository<Customer> repository = new InMemoryRepository<Customer>();
            var service = new CustomerService(repository, httpClient);
            
            // Create and save customer
            var customer = new Customer
            {
                Name = "John Doe",
                Email = "john@example.com",
                CreditLimit = 15000,
                Type = CustomerType.Premium
            };
            
            await repository.CreateAsync(customer);
            
            // Pattern matching
            var discount = PatternMatchingExamples.CalculateDiscount(customer);
            Console.WriteLine($"Customer discount: {discount:P}");
            
            // Extension method
            if (customer.IsHighValue())
            {
                Console.WriteLine("High-value customer detected!");
            }
            
            // Async enumerable
            var streamer = new DataStreamer();
            await foreach (var number in streamer.GenerateNumbersAsync(5))
            {
                Console.WriteLine($"Received: {number}");
            }
            
            // Null-conditional and null-coalescing
            var latestOrder = customer.GetLatestOrder();
            var orderTotal = latestOrder?.Total ?? 0;
            Console.WriteLine($"Latest order total: {orderTotal:C}");
            
            // String interpolation with format
            Console.WriteLine($"Customer: {customer.Name,-20} Credit: {customer.CreditLimit,10:C}");
        }
    }
}