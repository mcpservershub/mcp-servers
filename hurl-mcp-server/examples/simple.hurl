# Simple GET request
GET https://httpbin.org/get
HTTP 200
[Asserts]
header "Content-Type" contains "application/json"
jsonpath "$.url" == "https://httpbin.org/get"