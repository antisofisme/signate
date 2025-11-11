const http = require('http');

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end('<h1>Test Server Working on Port 3000!</h1><p>Node.js HTTP server is running.</p>');
});

server.listen(3000, '0.0.0.0', () => {
  console.log('Test server running on http://0.0.0.0:3000');
});