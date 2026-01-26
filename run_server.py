"""
Simple HTTP server to run the website locally
"""
import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

PORT = 8001  # Different port from Project02 to avoid conflicts
DIRECTORY = Path(__file__).resolve().parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        # Add no-cache headers for JSON files
        if self.path.endswith('.json'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        super().end_headers()
    
    def do_GET(self):
        # Redirect root path to index03.html
        if self.path == '/' or self.path == '/index.html':
            self.send_response(301)
            self.send_header('Location', '/index03.html')
            self.end_headers()
            return
        super().do_GET()

def main():
    # Check if data directory exists
    data_dir = DIRECTORY / "data"
    if not data_dir.exists():
        print("Warning: data/ directory not found.")
        print("Please run 'python fetch_data.py' first to fetch data.")
        print()
    
    # Check if data file exists
    data_file = data_dir / "hyig_data.json"
    if not data_file.exists():
        print("Warning: data/hyig_data.json not found.")
        print("Please run 'python fetch_data.py' first to fetch data.")
        print()
    
    import socket
    # Check if port is available BEFORE printing messages
    try:
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.bind(("", PORT))
        test_sock.close()
    except OSError as e:
        print(f"ERROR: Port {PORT} is already in use.")
        print(f"Please close the existing server or use a different port.")
        import sys
        sys.exit(1)
    
    print(f"Starting server at http://localhost:{PORT}")
    print(f"Serving directory: {DIRECTORY}")
    print("Press Ctrl+C to stop the server")
    print()
    
    # Open browser automatically
    try:
        webbrowser.open(f'http://localhost:{PORT}')
    except:
        pass

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    main()
