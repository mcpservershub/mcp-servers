  Option 1: Use the Full Docker Compose Setup (Recommended)

  Run the complete Selenium Grid with MCP server:

  # Start the complete setup (includes Selenium Hub + Browser nodes + MCP server)
  docker-compose -f docker-compose.selenium-grid.yml up -d

  # Check that all services are running
  docker-compose -f docker-compose.selenium-grid.yml ps

  # Test the MCP server
  docker exec -it selenium-mcp-server python -c "
  import requests
  response = requests.get('http://selenium-hub:4444/wd/hub/status')
  print('✅ Selenium Grid is reachable:', response.status_code == 200)
  "

  Option 2: Run MCP Server with Host Network

  If you want to run the MCP server container separately but connect to a local Selenium Grid:

  # Start Selenium Grid only
  docker-compose -f docker-compose.selenium-grid.yml up -d selenium-hub chrome firefox edge

  # Run MCP server with host networking
  docker run -it --rm --network="host" \
    -e SELENIUM_GRID_URL="http://localhost:4444/wd/hub" \
    your-selenium-mcp-image

  Option 3: Use External Network

  Connect both to the same network:

  # Create a network
  docker network create selenium-network

  # Start Selenium Grid with custom network
  docker-compose -f docker-compose.selenium-grid.yml up -d
  docker network connect selenium-network selenium-hub

  # Run MCP server in the same network
  docker run -it --rm --network selenium-network \
    -e SELENIUM_GRID_URL="http://selenium-hub:4444/wd/hub" \
    your-selenium-mcp-image

  Option 4: Use Local WebDriver (Fallback)

  If you want to test without Selenium Grid, unset the Grid URL:

  # Run without SELENIUM_GRID_URL to use local WebDriver
  docker run -it --rm \
    -e SELENIUM_GRID_URL="" \
    --cap-add=SYS_ADMIN \
    --security-opt seccomp=unconfined \
    your-selenium-mcp-image

  🧪 Testing the Solution:

  Check Grid Connectivity:

  # From within the MCP container
  docker exec -it selenium-mcp-server sh -c "
  # Test DNS resolution
  nslookup selenium-hub

  # Test HTTP connectivity
  wget -q -O- http://selenium-hub:4444/wd/hub/status || echo 'Connection failed'
  "

  Check Network Setup:

  # List networks
  docker network ls

  # Inspect the selenium-grid network
  docker network inspect selimium_selenium-grid

  # Check which containers are connected
  docker-compose -f docker-compose.selenium-grid.yml ps

  Verify MCP Inspector Configuration:

  For MCP Inspector, make sure you're connecting to the container that's part of the docker-compose setup:

  {
    "command": "docker",
    "args": ["exec", "-i", "selenium-mcp-server", "python", "-m", "selenium_mcp.server"],
    "env": {
      "SELENIUM_GRID_URL": "http://selenium-hub:4444/wd/hub"
    }
  }

  🎯 Most Likely Solution:

  Based on the error, you're probably running the MCP server container outside of the docker-compose setup. Use Option 1 - start the
   complete docker-compose setup:

  # This will start: Hub + Chrome + Firefox + Edge + MCP Server
  docker-compose -f docker-compose.selenium-grid.yml up -d

  # Wait for services to be ready (especially the hub)
  docker-compose -f docker-compose.selenium-grid.yml logs -f selenium-hub

  # Test the start_browser tool
  docker exec -it selenium-mcp-server python -c "
  from selenium_mcp.server import start_browser
  import asyncio
  result = asyncio.run(start_browser('chrome', True))
  print('Result:', result)
  "

  This should resolve the hostname resolution issue! 🚀
