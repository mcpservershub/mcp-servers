# First request - get a UUID
GET https://httpbin.org/uuid
HTTP 200
[Captures]
uuid: jsonpath "$.uuid"

# Second request - use the captured UUID
POST https://httpbin.org/post
Content-Type: application/json
{
  "id": "{{uuid}}",
  "action": "test"
}
HTTP 200
[Asserts]
jsonpath "$.json.id" == "{{uuid}}"