import { extractContent } from "@wrtnlabs/web-content-extractor";

const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <meta name="description" content="This is a test page">
</head>
<body>
    <h1>Test Content</h1>
    <p>This is some test content.</p>
    <a href="https://example.com">Link 1</a>
    <a href="https://example2.com">Link 2</a>
</body>
</html>
`;

const result = extractContent(html);
console.log("Result type:", typeof result);
console.log("Result:", JSON.stringify(result, null, 2));