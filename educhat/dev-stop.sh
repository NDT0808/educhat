#!/bin/bash

echo "Stopping development environment..."

# Kill ports 1818-1836
for port in {1818..1836}; do
  pid=$(lsof -t -i:$port)
  if [ -n "$pid" ]; then
    echo "Killing process on port $port (PID: $pid)"
    kill -9 $pid 2>/dev/null
  fi
done

echo "Development environment stopped."
