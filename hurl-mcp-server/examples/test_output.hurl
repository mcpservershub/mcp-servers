# Test API request with output file
GET https://httpbin.org/json
HTTP 200
[Asserts]
header "Content-Type" contains "application/json"
jsonpath "$.slideshow.title" == "Sample Slide Show"