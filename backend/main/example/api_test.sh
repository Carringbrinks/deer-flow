#!/bin/bash

set -e

BASE_URL="http://localhost:18001"

USERNAME="admin@test.com"
PASSWORD="123456789."

COOKIE_FILE="/data2/deer-flow/backend/debug/cookies.txt"

echo "=============================="
echo "1. Login"
echo "=============================="

LOGIN_RESPONSE=$(curl -i -s -c $COOKIE_FILE \
  -X POST "$BASE_URL/api/v1/auth/login/local" \
  -H "accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=${USERNAME}&password=${PASSWORD}")

echo "$LOGIN_RESPONSE"

echo ""
echo "=============================="
echo "2. Extract CSRF token"
echo "=============================="

CSRF_TOKEN=$(grep -i csrf $COOKIE_FILE | awk '{print $7}' | tail -n 1)

if [ -z "$CSRF_TOKEN" ]; then
  echo "❌ CSRF token not found in cookies.txt"
  echo "Please check Set-Cookie headers."
  exit 1
fi

echo "CSRF_TOKEN: $CSRF_TOKEN"

echo ""
echo "=============================="
echo "3. Create Thread"
echo "=============================="

THREAD_RESPONSE=$(curl -s -b $COOKIE_FILE \
  -X POST "$BASE_URL/api/threads" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -d '{}')

echo "$THREAD_RESPONSE"

THREAD_ID=$(echo "$THREAD_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['thread_id'])")

echo ""
echo "THREAD_ID: $THREAD_ID"

# echo ""
# echo "=============================="
# echo "4. Create Run (non-stream)"
# echo "=============================="

# curl -s -b $COOKIE_FILE \
#   -X POST "$BASE_URL/api/threads/$THREAD_ID/runs" \
#   -H "Content-Type: application/json" \
#   -H "X-CSRF-Token: $CSRF_TOKEN" \
#   -d '{
#     "input": {
#       "messages": [
#         {
#           "role": "user",
#           "content": "你是谁"
#         }
#       ]
#     }
#   }'

echo ""
echo "=============================="
echo "5. Stream Run (SSE)"
echo "=============================="

curl -N -b $COOKIE_FILE \
  -X POST "$BASE_URL/api/threads/$THREAD_ID/runs/stream" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -H "Accept: text/event-stream" \
  -d '{
    "input": {
      "messages": [
        {
          "role": "user",
          "content": "你是谁"
        }
      ]
    }
  }'