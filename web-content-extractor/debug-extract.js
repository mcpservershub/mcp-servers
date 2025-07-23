import { extractContent } from "@wrtnlabs/web-content-extractor";
import fetch from "node-fetch";

async function debugExtract() {
  try {
    console.log('Fetching google.com...');
    const response = await fetch('https://google.com');
    const html = await response.text();
    
    console.log('HTML length:', html.length);
    console.log('First 200 chars:', html.substring(0, 200));
    
    console.log('Attempting to extract content...');
    const result = extractContent(html);
    console.log('Extraction successful!');
    console.log('Result type:', typeof result);
    console.log('Result:', result);
    
  } catch (error) {
    console.error('Error details:', error);
    console.error('Stack:', error.stack);
  }
}

debugExtract();