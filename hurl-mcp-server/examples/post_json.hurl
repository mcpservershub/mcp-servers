# POST JSON data
POST https://httpbin.org/post
Content-Type: application/json
{
  "name": "test",
  "value": 123
}
HTTP 200
[Asserts]
jsonpath "$.json.name" == "test"
jsonpath "$.json.value" == 123