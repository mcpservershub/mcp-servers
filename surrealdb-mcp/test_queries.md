# SurrealDB Test Queries for MCP Server

## Basic CRUD Operations

### SELECT Queries
```sql
-- Get all users
SELECT * FROM user;

-- Get specific user
SELECT * FROM user:john;

-- Get users with conditions
SELECT * FROM user WHERE age > 25;

-- Get posts with pagination
SELECT * FROM post ORDER BY created_at DESC LIMIT 10 START 0;

-- Get published posts with author info
SELECT *, author.name as author_name 
FROM post 
WHERE status = 'published' 
ORDER BY views DESC;
```

### INSERT Operations
```sql
-- Insert a new user
INSERT INTO user {
    id: user:testuser,
    name: "Test User",
    email: "test@example.com",
    username: "testuser",
    age: 25
};

-- Insert a new post
INSERT INTO post {
    title: "My Test Post",
    content: "This is test content",
    author: user:john,
    status: "draft"
};
```

### UPDATE Operations
```sql
-- Update user settings
UPDATE user:john SET settings.theme = "dark";

-- Increment post views
UPDATE post:post1 SET views += 1;

-- Update multiple fields
UPDATE user:jane MERGE {
    bio: "Updated bio",
    settings: {
        notifications: false
    }
};
```

### DELETE Operations
```sql
-- Delete a specific record
DELETE user:testuser;

-- Delete with condition
DELETE comment WHERE likes < 1;

-- Delete all draft posts (careful!)
DELETE post WHERE status = 'draft';
```

## Relationship Queries

### Graph Traversal
```sql
-- Get users that John follows
SELECT * FROM user:john->follows->user;

-- Get John's followers
SELECT * FROM user<-follows<-user:john;

-- Get posts liked by a user
SELECT * FROM user:jane->likes->post;

-- Multi-level traversal (followers of followers)
SELECT * FROM user:john->follows->user->follows->user;
```

### Creating Relationships
```sql
-- Create a follow relationship
RELATE user:john->follows->user:charlie;

-- Create a like relationship
RELATE user:alice->likes->post:post5;

-- Create a comment relationship with data
RELATE user:bob->commented->post:post1 
SET content = "Great post!", created_at = time::now();
```

## Advanced Queries

### Aggregations
```sql
-- Count users by age group
SELECT 
    math::floor(age / 10) * 10 as age_group,
    count() as total
FROM user
GROUP BY age_group;

-- Get post statistics
SELECT 
    status,
    count() as count,
    math::sum(views) as total_views,
    math::mean(views) as avg_views
FROM post
GROUP BY status;

-- Top commented posts
SELECT 
    id,
    title,
    (SELECT count() FROM comment WHERE post = $parent.id) as comment_count
FROM post
ORDER BY comment_count DESC
LIMIT 5;
```

### Subqueries
```sql
-- Users with their post count
SELECT *,
    (SELECT count() FROM post WHERE author = $parent.id) as post_count,
    (SELECT count() FROM comment WHERE author = $parent.id) as comment_count
FROM user;

-- Products with reviews
SELECT *,
    (SELECT math::mean(rating) FROM review WHERE product = $parent.id) as avg_rating,
    (SELECT count() FROM review WHERE product = $parent.id) as review_count
FROM product
WHERE category = category:laptops;
```

### Complex Filters
```sql
-- Posts with multiple conditions
SELECT * FROM post 
WHERE status = 'published' 
    AND views > 100 
    AND created_at > time::now() - 30d
    AND 'technology' IN tags;

-- Users who have posted and commented
SELECT DISTINCT user FROM (
    SELECT author as user FROM post
    UNION
    SELECT author as user FROM comment
);
```

## E-commerce Queries

### Product Queries
```sql
-- Products in stock
SELECT * FROM product WHERE stock > 0 AND is_available = true;

-- Products by price range
SELECT * FROM product 
WHERE price BETWEEN 100 AND 1000 
ORDER BY price ASC;

-- Products with category hierarchy
SELECT 
    p.*,
    c.name as category_name,
    c.parent.name as parent_category
FROM product p
INNER JOIN category c ON p.category = c.id;
```

### Order Queries
```sql
-- Recent orders
SELECT * FROM `order` 
WHERE created_at > time::now() - 7d 
ORDER BY created_at DESC;

-- Orders by status
SELECT 
    status,
    count() as total_orders,
    math::sum(total) as revenue
FROM `order`
GROUP BY status;

-- User order history
SELECT 
    o.*,
    u.name as customer_name
FROM `order` o
INNER JOIN user u ON o.user = u.id
WHERE o.user = user:john
ORDER BY o.created_at DESC;
```

## Analytics Queries

### User Analytics
```sql
-- Most active users
SELECT 
    u.id,
    u.name,
    (SELECT count() FROM post WHERE author = u.id) as posts,
    (SELECT count() FROM comment WHERE author = u.id) as comments,
    (SELECT count() FROM follows WHERE in = u.id) as following,
    (SELECT count() FROM follows WHERE out = u.id) as followers
FROM user u
ORDER BY posts DESC;

-- User engagement
SELECT 
    u.name,
    count(DISTINCT p.id) as posts_liked,
    count(DISTINCT c.id) as comments_made
FROM user u
LEFT JOIN likes l ON l.in = u.id
LEFT JOIN post p ON l.out = p.id
LEFT JOIN comment c ON c.author = u.id
GROUP BY u.id;
```

### Content Analytics
```sql
-- Trending posts (last 7 days)
SELECT 
    id,
    title,
    views,
    (SELECT count() FROM likes WHERE out = $parent.id) as likes,
    (SELECT count() FROM comment WHERE post = $parent.id) as comments
FROM post
WHERE published_at > time::now() - 7d
ORDER BY (views + likes * 10 + comments * 5) DESC
LIMIT 10;

-- Tag popularity
SELECT 
    t.name,
    count(tg.id) as usage_count
FROM tag t
LEFT JOIN tagged tg ON tg.out = t.id
GROUP BY t.id
ORDER BY usage_count DESC;
```

## Transaction Examples

### Begin Transaction
```sql
BEGIN TRANSACTION;

-- Create order with inventory update
LET $order = CREATE order SET
    user = user:john,
    items = [{product: product:laptop1, quantity: 1, price: 1299.99}],
    total = 1299.99,
    status = "pending";

-- Update product stock
UPDATE product:laptop1 SET stock -= 1;

-- Verify stock didn't go negative
IF (SELECT stock FROM product:laptop1) < 0 {
    THROW "Insufficient stock";
};

COMMIT TRANSACTION;
```

## Function Usage

### Custom Functions
```sql
-- Get user statistics (using custom function)
SELECT fn::user_stats(user:john);

-- Get product ratings (using custom function)
SELECT 
    p.*,
    fn::product_rating(p.id) as rating_info
FROM product p;
```

### Built-in Functions
```sql
-- String functions
SELECT 
    string::uppercase(name) as upper_name,
    string::lowercase(email) as lower_email,
    string::len(bio) as bio_length
FROM user;

-- Date functions
SELECT 
    *,
    time::format(created_at, "%Y-%m-%d") as date,
    time::now() - created_at as age
FROM post
WHERE created_at > time::now() - 30d;

-- Math functions
SELECT 
    math::min(price) as min_price,
    math::max(price) as max_price,
    math::mean(price) as avg_price,
    math::stddev(price) as price_stddev
FROM product;
```

## Testing with MCP Tools

When testing with MCP Inspector, you can use these queries with the following tools:

1. **`query`** - Execute any of the above queries directly
2. **`select`** - Use for filtered selections with pagination
3. **`insert`** - Add new records
4. **`update`** - Modify existing records
5. **`delete`** - Remove records
6. **`relate`** - Create relationships

### Example MCP Tool Calls

```javascript
// Using query tool
query("SELECT * FROM user WHERE age > 25")

// Using select tool
select("post", {
    where: "status = 'published'",
    order: "views DESC",
    limit: 10
})

// Using insert tool
insert("user", {
    name: "New User",
    email: "newuser@example.com",
    username: "newuser",
    age: 30
})

// Using relate tool
relate("user:john", "follows", "user:newuser")
```