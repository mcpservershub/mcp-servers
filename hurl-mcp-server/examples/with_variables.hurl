# Request with variables
GET {{base_url}}/get
User-Agent: {{user_agent}}
HTTP 200
[Asserts]
jsonpath "$.headers.User-Agent" == "{{user_agent}}"