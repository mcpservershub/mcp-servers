/**
 * Java example for Tree-sitter MCP testing
 * Demonstrates OOP, generics, streams, lambdas, and modern Java features
 */

package com.example.treesitter;

import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import java.util.stream.*;
import java.time.*;
import java.nio.file.*;
import java.io.IOException;

// Interface with default and static methods
interface Vehicle {
    void start();
    void stop();
    
    default void honk() {
        System.out.println("Beep beep!");
    }
    
    static Vehicle createDefault() {
        return new Car("Default", "Model", 2023);
    }
}

// Abstract class
abstract class AbstractVehicle implements Vehicle {
    protected String brand;
    protected String model;
    protected int year;
    
    public AbstractVehicle(String brand, String model, int year) {
        this.brand = brand;
        this.model = model;
        this.year = year;
    }
    
    public abstract double calculateValue();
    
    @Override
    public String toString() {
        return String.format("%d %s %s", year, brand, model);
    }
}

// Concrete class with inheritance
class Car extends AbstractVehicle {
    private double mileage;
    private List<String> features;
    
    public Car(String brand, String model, int year) {
        super(brand, model, year);
        this.features = new ArrayList<>();
        this.mileage = 0.0;
    }
    
    @Override
    public void start() {
        System.out.println("Car engine started");
    }
    
    @Override
    public void stop() {
        System.out.println("Car engine stopped");
    }
    
    @Override
    public double calculateValue() {
        double baseValue = 20000;
        double depreciationRate = 0.15;
        int currentYear = LocalDate.now().getYear();
        int age = currentYear - year;
        return baseValue * Math.pow(1 - depreciationRate, age);
    }
    
    public void addFeature(String feature) {
        features.add(feature);
    }
}

// Generic class
class Repository<T extends Identifiable> {
    private Map<Long, T> storage = new ConcurrentHashMap<>();
    private AtomicLong idGenerator = new AtomicLong(1);
    
    public T save(T entity) {
        if (entity.getId() == null) {
            entity.setId(idGenerator.getAndIncrement());
        }
        storage.put(entity.getId(), entity);
        return entity;
    }
    
    public Optional<T> findById(Long id) {
        return Optional.ofNullable(storage.get(id));
    }
    
    public List<T> findAll() {
        return new ArrayList<>(storage.values());
    }
    
    public void delete(Long id) {
        storage.remove(id);
    }
    
    public List<T> findByPredicate(Predicate<T> predicate) {
        return storage.values().stream()
            .filter(predicate)
            .collect(Collectors.toList());
    }
}

// Interface for generic constraint
interface Identifiable {
    Long getId();
    void setId(Long id);
}

// Record (Java 14+)
record Person(String name, int age, String email) implements Identifiable {
    private static Long id;
    
    // Compact constructor
    public Person {
        if (age < 0) {
            throw new IllegalArgumentException("Age cannot be negative");
        }
        if (!email.contains("@")) {
            throw new IllegalArgumentException("Invalid email format");
        }
    }
    
    @Override
    public Long getId() {
        return id;
    }
    
    @Override
    public void setId(Long newId) {
        id = newId;
    }
}

// Enum with methods
enum Status {
    PENDING("Waiting for processing"),
    PROCESSING("Currently being processed"),
    COMPLETED("Successfully completed"),
    FAILED("Failed with errors");
    
    private final String description;
    
    Status(String description) {
        this.description = description;
    }
    
    public String getDescription() {
        return description;
    }
    
    public boolean isTerminal() {
        return this == COMPLETED || this == FAILED;
    }
}

// Functional interface
@FunctionalInterface
interface Calculator<T extends Number> {
    T calculate(T a, T b);
    
    default Calculator<T> andThen(Calculator<T> after) {
        return (a, b) -> after.calculate(calculate(a, b), b);
    }
}

// Main class with various demonstrations
public class Example {
    
    // Static nested class
    static class Configuration {
        private Properties properties = new Properties();
        
        public void setProperty(String key, String value) {
            properties.setProperty(key, value);
        }
        
        public String getProperty(String key) {
            return properties.getProperty(key);
        }
    }
    
    // Method with varargs
    public static <T> List<T> createList(T... elements) {
        return Arrays.asList(elements);
    }
    
    // Stream operations
    public static void demonstrateStreams() {
        List<Integer> numbers = IntStream.rangeClosed(1, 100)
            .boxed()
            .collect(Collectors.toList());
        
        // Complex stream pipeline
        Map<Boolean, List<Integer>> partitioned = numbers.stream()
            .filter(n -> n % 2 == 0)
            .map(n -> n * n)
            .filter(n -> n < 1000)
            .collect(Collectors.partitioningBy(n -> n > 100));
        
        // Parallel stream
        long sum = numbers.parallelStream()
            .mapToLong(Integer::longValue)
            .sum();
        
        System.out.println("Sum: " + sum);
    }
    
    // CompletableFuture example
    public static CompletableFuture<String> fetchDataAsync(String url) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                Thread.sleep(1000);
                return "Data from " + url;
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });
    }
    
    // Try-with-resources
    public static void readFile(String path) {
        try (var reader = Files.newBufferedReader(Paths.get(path))) {
            reader.lines()
                .filter(line -> !line.isEmpty())
                .map(String::trim)
                .forEach(System.out::println);
        } catch (IOException e) {
            System.err.println("Error reading file: " + e.getMessage());
        }
    }
    
    // Switch expression (Java 14+)
    public static String getDayType(DayOfWeek day) {
        return switch (day) {
            case MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY -> "Weekday";
            case SATURDAY, SUNDAY -> "Weekend";
        };
    }
    
    // Pattern matching (Java 17+)
    public static String formatValue(Object obj) {
        return switch (obj) {
            case Integer i -> "Integer: " + i;
            case String s -> "String: " + s;
            case Double d -> "Double: " + d;
            case null -> "null value";
            default -> "Unknown type: " + obj.getClass().getSimpleName();
        };
    }
    
    public static void main(String[] args) {
        // Create and use objects
        Car car = new Car("Toyota", "Camry", 2022);
        car.start();
        car.honk();
        System.out.println("Car value: $" + car.calculateValue());
        
        // Use repository with generics
        Repository<Person> personRepo = new Repository<>();
        Person person = new Person("Alice", 30, "alice@example.com");
        personRepo.save(person);
        
        // Lambda expressions
        Calculator<Integer> adder = (a, b) -> a + b;
        Calculator<Integer> multiplier = (a, b) -> a * b;
        System.out.println("Result: " + adder.calculate(5, 3));
        
        // Method references
        List<String> names = Arrays.asList("Alice", "Bob", "Charlie");
        names.forEach(System.out::println);
        
        // Stream operations
        demonstrateStreams();
        
        // CompletableFuture
        CompletableFuture<String> future = fetchDataAsync("https://api.example.com");
        future.thenAccept(System.out::println);
        
        // Optional
        Optional<String> optional = Optional.of("Hello")
            .filter(s -> s.length() > 3)
            .map(String::toUpperCase);
        optional.ifPresent(System.out::println);
    }
}