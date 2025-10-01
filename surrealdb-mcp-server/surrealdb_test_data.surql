-- SurrealDB Test Database Setup
-- Compatible with SurrealDB and SurrealMCP

-- Switch to test namespace and database
USE NS test;
USE DB test;

-- Create users
CREATE user:john CONTENT {
    name: 'John Doe',
    email: 'john@example.com',
    age: 30,
    created_at: time::now()
};

CREATE user:jane CONTENT {
    name: 'Jane Smith',
    email: 'jane@example.com',
    age: 28,
    created_at: time::now()
};

CREATE user:bob CONTENT {
    name: 'Bob Wilson',
    email: 'bob@example.com',
    age: 35,
    created_at: time::now()
};

-- Create posts
CREATE post:post1 CONTENT {
    title: 'Getting Started with SurrealDB',
    content: 'SurrealDB is a revolutionary database that combines SQL and NoSQL.',
    author: user:john,
    status: 'published',
    views: 245,
    created_at: time::now()
};

CREATE post:post2 CONTENT {
    title: 'Building Modern Web Applications',
    content: 'Modern web development has evolved significantly.',
    author: user:jane,
    status: 'published',
    views: 532,
    created_at: time::now()
};

CREATE post:post3 CONTENT {
    title: 'The Future of AI',
    content: 'AI is transforming how we write code.',
    author: user:bob,
    status: 'draft',
    views: 0,
    created_at: time::now()
};

-- Create products
CREATE product:laptop1 CONTENT {
    name: 'ProBook X1',
    description: 'High-performance laptop',
    price: 1299.99,
    stock: 15,
    category: 'electronics'
};

CREATE product:phone1 CONTENT {
    name: 'SmartPhone Pro',
    description: 'Latest smartphone',
    price: 999.99,
    stock: 25,
    category: 'electronics'
};

CREATE product:book1 CONTENT {
    name: 'Database Design',
    description: 'Guide to database design',
    price: 49.99,
    stock: 100,
    category: 'books'
};

-- Create relationships
RELATE user:john->follows->user:jane;
RELATE user:jane->follows->user:john;
RELATE user:bob->follows->user:john;

RELATE user:john->likes->post:post1;
RELATE user:jane->likes->post:post1;
RELATE user:bob->likes->post:post2;

RELATE user:john->wrote->post:post1;
RELATE user:jane->wrote->post:post2;
RELATE user:bob->wrote->post:post3;

-- Create orders (using backticks for reserved word)
CREATE `order`:order1 CONTENT {
    customer: user:john,
    items: [
        {
            product: product:laptop1,
            quantity: 1,
            price: 1299.99
        }
    ],
    total: 1299.99,
    status: 'delivered',
    created_at: time::now()
};

CREATE `order`:order2 CONTENT {
    customer: user:jane,
    items: [
        {
            product: product:phone1,
            quantity: 1,
            price: 999.99
        }
    ],
    total: 999.99,
    status: 'shipped',
    created_at: time::now()
};

-- Create comments
CREATE comment:c1 CONTENT {
    post: post:post1,
    author: user:jane,
    content: 'Great article!',
    created_at: time::now()
};

CREATE comment:c2 CONTENT {
    post: post:post2,
    author: user:john,
    content: 'Very informative.',
    created_at: time::now()
};

-- Simple verification queries (run these separately)
SELECT * FROM user;
SELECT * FROM post;
SELECT * FROM product;