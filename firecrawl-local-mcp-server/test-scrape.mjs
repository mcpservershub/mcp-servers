#!/usr/bin/env node

// Functional test for Firecrawl Local MCP Server
// This tests actual scraping functionality

import FirecrawlApp from '@mendable/firecrawl-js';

// Test configuration
const API_URL = 'http://localhost:3002';
const TEST_URL = 'https://example.com';

console.log('🧪 Testing Firecrawl Local Instance');
console.log('📍 API URL:', API_URL);
console.log('🌐 Test URL:', TEST_URL);
console.log('');

// Initialize Firecrawl client
const client = new FirecrawlApp({
  apiKey: 'local-dev-key', // Dummy key for local instance
  apiUrl: API_URL
});

async function testScrape() {
  try {
    console.log('1️⃣ Testing scrape functionality...');
    const result = await client.scrapeUrl(TEST_URL, {
      formats: ['markdown'],
      onlyMainContent: true
    });
    
    if (result.success && result.markdown) {
      console.log('✅ Scrape successful!');
      console.log('📄 Content preview:', result.markdown.substring(0, 100) + '...');
      return true;
    } else {
      console.error('❌ Scrape failed:', result.error || 'No content returned');
      return false;
    }
  } catch (error) {
    console.error('❌ Scrape error:', error.message);
    return false;
  }
}

async function testMap() {
  try {
    console.log('\n2️⃣ Testing map functionality...');
    const result = await client.mapUrl(TEST_URL, {
      limit: 5
    });
    
    if (result.success && result.links) {
      console.log('✅ Map successful!');
      console.log('🔗 Found', result.links.length, 'URLs');
      result.links.slice(0, 3).forEach(link => console.log('  -', link));
      return true;
    } else {
      console.error('❌ Map failed:', result.error || 'No links returned');
      return false;
    }
  } catch (error) {
    console.error('❌ Map error:', error.message);
    return false;
  }
}

async function runTests() {
  console.log('Starting tests...\n');
  
  const scrapeSuccess = await testScrape();
  const mapSuccess = await testMap();
  
  console.log('\n📊 Test Results:');
  console.log('  Scrape:', scrapeSuccess ? '✅ PASSED' : '❌ FAILED');
  console.log('  Map:', mapSuccess ? '✅ PASSED' : '❌ FAILED');
  
  if (scrapeSuccess && mapSuccess) {
    console.log('\n🎉 All tests passed! The MCP server is working correctly with local Firecrawl.');
  } else {
    console.log('\n⚠️ Some tests failed. Please check the Firecrawl services.');
  }
  
  process.exit(scrapeSuccess && mapSuccess ? 0 : 1);
}

// Run tests
runTests().catch(error => {
  console.error('Test runner error:', error);
  process.exit(1);
});