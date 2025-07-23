import { extractContent } from "@wrtnlabs/web-content-extractor";

const testHtml = `
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Hello World</h1>
    <p>This is a test paragraph.</p>
</body>
</html>
`;

try {
  console.log('Testing extractContent with simple HTML...');
  const result = extractContent(testHtml);
  console.log('Success:', result);
} catch (error) {
  console.error('Error:', error.message);
  console.error('Stack:', error.stack);
}