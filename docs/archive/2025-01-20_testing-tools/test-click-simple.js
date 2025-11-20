const http = require('http');

// Test dengan melakukan HTTP request dan parsing HTML
async function testPlayerPage() {
  console.log('🔍 Testing player page at http://192.168.5.12:8080\n');
  
  return new Promise((resolve, reject) => {
    http.get('http://192.168.5.12:8080/', (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        console.log('✅ Page loaded successfully\n');
        
        // Check if status icons exist
        const hasNetworkStatus = data.includes('id="network-status"');
        const hasServerStatus = data.includes('id="server-status"');
        
        console.log('📋 Status Icons in HTML:');
        console.log('  - Network status:', hasNetworkStatus ? '✅ FOUND' : '❌ NOT FOUND');
        console.log('  - Server status:', hasServerStatus ? '✅ FOUND' : '❌ NOT FOUND');
        
        // Check if JavaScript bundle is loaded
        const jsMatch = data.match(/src="\/assets\/index-([^"]+)\.js"/);
        if (jsMatch) {
          const jsFile = jsMatch[0].match(/src="([^"]+)"/)[1];
          console.log('\n📦 JavaScript bundle:', jsFile);
          
          // Try to fetch and check if ConnectionLogPopup is in the bundle
          http.get(`http://192.168.5.12:8080${jsFile}`, (jsRes) => {
            let jsData = '';
            
            jsRes.on('data', (chunk) => {
              jsData += chunk;
            });
            
            jsRes.on('end', () => {
              const hasConnectionLogPopup = jsData.includes('ConnectionLogPopup');
              const hasAttachClickHandlers = jsData.includes('attachClickHandlers');
              const hasAddEventListener = jsData.includes('addEventListener');
              
              console.log('\n📋 JavaScript Bundle Contents:');
              console.log('  - ConnectionLogPopup:', hasConnectionLogPopup ? '✅ FOUND' : '❌ NOT FOUND');
              console.log('  - attachClickHandlers:', hasAttachClickHandlers ? '✅ FOUND' : '❌ NOT FOUND');
              console.log('  - addEventListener:', hasAddEventListener ? '✅ FOUND' : '❌ NOT FOUND');
              
              if (hasConnectionLogPopup && hasAttachClickHandlers) {
                console.log('\n✅ All required code is present in the bundle!');
                console.log('\n📝 Next step: Open browser and check console logs');
                console.log('   URL: http://192.168.5.12:8080');
                console.log('   Press F12 to open DevTools');
                console.log('   Look for logs starting with [ConnectionLogPopup]');
                console.log('   Click on the network/server status icons');
              } else {
                console.log('\n❌ Some code is missing from bundle!');
              }
              
              resolve();
            });
          }).on('error', reject);
        } else {
          console.log('\n❌ JavaScript bundle not found in HTML!');
          resolve();
        }
      });
    }).on('error', reject);
  });
}

testPlayerPage().catch(console.error);
