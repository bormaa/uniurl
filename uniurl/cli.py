import sys
import json
import argparse
import requests
import os
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Union
from .core import URLHandler
import re

def get_random_agent():
    """Get a random user agent using fake-useragent"""
    try:
        ua = UserAgent()
        return ua.random
    except Exception as e:
        # Fallback to a recent Chrome user agent if fake-useragent fails
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def parse_headers(headers_list: List[str]) -> Dict[str, str]:
    """Parse header arguments into a dictionary"""
    headers = {}
    for header in headers_list:
        try:
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()
        except ValueError:
            print(f"Warning: Skipping invalid header format: {header}")
    return headers

def process_url(url: str, use_random_agent: bool = False, custom_headers: Dict[str, str] = None) -> Dict[str, Union[str, int, dict]]:
    """Process a single URL and return the result"""
    try:
        headers = {}
        if use_random_agent:
            headers['User-Agent'] = get_random_agent()
        if custom_headers:
            headers.update(custom_headers)
            
        response = requests.get(url.strip(), headers=headers, allow_redirects=False)  # Don't follow redirects
        
        return {
            "url": url,
            "status_code": response.status_code,
            "content_length": len(response.content),
            "content":response.content,
            "headers": dict(response.headers),
            "request_headers": headers
        }
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None

def process_urls(urls: List[str], max_workers: int = 10, use_random_agent: bool = False, custom_headers: Dict[str, str] = None) -> List[Dict]:
    """Process multiple URLs concurrently"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            lambda url: process_url(url, use_random_agent, custom_headers),
            urls
        ))
    return results

def read_urls_from_file(file_path: str) -> tuple[List[str], Dict]:
    """Read URLs from a file, expecting dirsearch format: STATUS_CODE SIZE URL"""
    try:
        abs_path = os.path.abspath(file_path)
        print(f"Attempting to read file: {abs_path}")
        
        if not os.path.exists(abs_path):
            print(f"Error: File not found: {file_path}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Attempted absolute path: {abs_path}")
            sys.exit(1)
            
        urls = []
        lengths = []  # List to store lengths parallel to urls
        removed = {"duplicate_lengths": []}  # Track removed URLs
        pattern = re.compile(r'^\d{3}\s+(\d+(?:KB|B|MB|GB)?)\s+(\S+)$')
        
        with open(abs_path, 'r') as f:
            for line in f:
                line = line.strip()
                match = pattern.match(line)
                if match:
                    size, url = match.groups()
                    
                    # Convert size to bytes for comparison
                    size_value = size.lower()
                    if 'kb' in size_value:
                        size_bytes = int(float(size_value.replace('kb', '')) * 1024)
                    elif 'mb' in size_value:
                        size_bytes = int(float(size_value.replace('mb', '')) * 1024 * 1024)
                    elif 'gb' in size_value:
                        size_bytes = int(float(size_value.replace('gb', '')) * 1024 * 1024 * 1024)
                    else:
                        size_bytes = int(size_value.replace('b', ''))
                    
                    # Keep URL if length not seen before
                    if size_bytes not in lengths:
                        lengths.append(size_bytes)
                        urls.append(url)
                    else:
                        removed["duplicate_lengths"].append({
                            "url": url,
                            "length": size_bytes
                        })
        
        if not urls:
            print(f"Warning: No valid URLs found in file: {file_path}")
        
        # Sort URLs by their response size (largest first)
        urls_with_lengths = list(zip(urls, lengths))
        urls_with_lengths.sort(key=lambda x: x[1], reverse=True)
        urls = [url for url, _ in urls_with_lengths]
        return urls, removed
            
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        sys.exit(1)

def read_urls_from_json(file_path: str) -> tuple[List[str], Dict]:
    """Read URLs from a JSON file"""
    try:
        abs_path = os.path.abspath(file_path)
        print(f"Attempting to read JSON file: {abs_path}")
        
        if not os.path.exists(abs_path):
            print(f"Error: JSON file not found: {file_path}")
            print(f"Current working directory: {os.getcwd()}")
            sys.exit(1)
            
        urls = []
        lengths = []  # List to store lengths parallel to urls
        removed = {"duplicate_lengths": []}  # Track removed URLs
        
        with open(abs_path, 'r') as f:
            data = json.load(f)
            entries = []
            
            # Handle different JSON formats
            if isinstance(data, list):
                entries = data
            elif isinstance(data, dict):
                if 'results' in data:
                    entries = data['results']
                elif 'urls' in data:
                    entries = data['urls']
                        
            # Process entries
            for entry in entries:
                if isinstance(entry, dict):
                    url = entry.get('url')
                    content_length = entry.get('content-length', 0)
                else:
                    # If entry is just a string URL
                    url = entry
                    content_length = 0
                
                if not url:
                    continue
                
                # Convert content_length to int if it's not already
                try:
                    length_bytes = int(content_length)
                except (ValueError, TypeError):
                    length_bytes = 0
                
                # Keep URL if length not seen before
                if length_bytes not in lengths:
                    lengths.append(length_bytes)
                    urls.append(url)
                else:
                    removed["duplicate_lengths"].append({
                        "url": url,
                        "length": length_bytes
                    })
                    
            if not urls:
                print(f"Warning: No valid URLs found in JSON file: {file_path}")
            
            # Sort URLs by their content length (largest first)
            urls_with_lengths = list(zip(urls, lengths))
            urls_with_lengths.sort(key=lambda x: x[1], reverse=True)
            urls = [url for url, _ in urls_with_lengths]
            return urls, removed
            
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        sys.exit(1)

def read_from_pipe() -> List[str]:
    """Read URLs from pipe/stdin"""
    urls = []
    lengths = []  # List to store lengths parallel to urls
    pattern = re.compile(r'^\d{3}\s+(\d+(?:KB|B|MB|GB)?)\s+(\S+)$')
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        # Try to match dirsearch format first
        match = pattern.match(line)
        if match:
            size, url = match.groups()
            
            # Convert size to bytes for comparison
            size_value = size.lower()
            if 'kb' in size_value:
                size_bytes = int(float(size_value.replace('kb', '')) * 1024)
            elif 'mb' in size_value:
                size_bytes = int(float(size_value.replace('mb', '')) * 1024 * 1024)
            elif 'gb' in size_value:
                size_bytes = int(float(size_value.replace('gb', '')) * 1024 * 1024 * 1024)
            else:
                size_bytes = int(size_value.replace('b', ''))
            
            # Keep URL if length not seen before
            if size_bytes not in lengths:
                lengths.append(size_bytes)
                urls.append(url)
    
    # Sort URLs by their response size (largest first)
    urls_with_lengths = list(zip(urls, lengths))
    urls_with_lengths.sort(key=lambda x: x[1], reverse=True)
    urls = [url for url, _ in urls_with_lengths]
    return urls

def filter_results(results: List[Dict]) -> tuple[List[Dict], Dict]:
    """Filter results to remove 404s and handle redirects"""
    filtered_results = []
    redirect_locations = []  # List to track redirect destinations
    removed = {
        "404": [],
        "duplicate_redirects": [],
        "failed_requests": []
    }
    
    for result in results:
        if not result:  # Skip None results from failed requests
            removed["failed_requests"].append(result)
            continue
            
        status = result.get('status_code', 0)
        url = result.get('url', '')
        
        # Skip 404s
        if status == 404:
            removed["404"].append(url)
            continue
            
        # Handle redirects (300-399)
        if 300 <= status <= 399:
            location = result.get('headers', {}).get('location', '')
            if location:
                # Store the first URL that redirects to this location
                if location not in redirect_locations:
                    redirect_locations.append(location)
                    filtered_results.append(result)
                else:
                    removed["duplicate_redirects"].append({
                        "url": url,
                        "location": location
                    })
            else:
                # Keep redirect responses without location header
                filtered_results.append(result)
        else:
            # Keep all non-404 and non-redirect responses
            filtered_results.append(result)
    
    return filtered_results, removed

def check_single_redirect(url_info: Dict, use_random_agent: bool = False, custom_headers: Dict[str, str] = None) -> tuple[str, str]:
    """Check a single URL for redirect and return tuple of (url, location)"""
    url = url_info['url']
    try:
        headers = {}
        if use_random_agent:
            headers['User-Agent'] = get_random_agent()
        if custom_headers:
            headers.update(custom_headers)
            
        response = requests.get(url, headers=headers, allow_redirects=False)
        
        if 300 <= response.status_code <= 399:
            location = response.headers.get('location', '')
            if location:
                return url, location
                
    except Exception as e:
        if args.verbose:
            print(f"Error checking redirect for {url}: {str(e)}")
    
    return None, None

def check_redirect_urls(removed_urls: List[Dict], use_random_agent: bool = False, custom_headers: Dict[str, str] = None, max_workers: int = 10) -> List[str]:
    """Check removed URLs for unique redirects using concurrent processing"""
    redirect_locations = set()
    additional_urls = []
    
    # Group URLs by length
    length_groups = {}
    for url_info in removed_urls:
        length = url_info['length']
        if length not in length_groups:
            length_groups[length] = []
        length_groups[length].append(url_info)
    
    # For each length group, take first 50 URLs
    urls_to_check = []
    for length, urls in length_groups.items():
        urls_to_check.extend(urls[:50])
        if args.verbose:
            print(f"Length {length}: checking {min(50, len(urls))} of {len(urls)} URLs")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map the check_single_redirect function over selected URLs
        futures = []
        for url_info in urls_to_check:
            future = executor.submit(
                check_single_redirect, 
                url_info, 
                use_random_agent, 
                custom_headers
            )
            futures.append(future)
        
        # Process results as they complete
        for future in futures:
            url, location = future.result()
            if url and location and location not in redirect_locations:
                redirect_locations.add(location)
                additional_urls.append(url)
                
    return additional_urls

def main():
    parser = argparse.ArgumentParser(description='Process URLs from dirsearch output and verify their status')
    parser.add_argument('-f', '--file', help='Input file containing URLs (one per line)')
    parser.add_argument('-j', '--json', help='Input JSON file containing URLs')
    parser.add_argument('-w', '--workers', type=int, default=50, help='Number of worker threads')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-r', '--random-agent', action='store_true', help='Use random User-Agent for requests')
    parser.add_argument('-H', '--header', action='append', help='Add custom header (format: "Key: Value")', default=[])
    parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose output')
    parser.add_argument('--json-output', action='store_true', help='Output in JSON format')
    global args
    args = parser.parse_args()

    if args.verbose:
        print(f"Current working directory: {os.getcwd()}")

    # Parse custom headers
    custom_headers = parse_headers(args.header)

    # Check if we're receiving input from a pipe
    is_pipe = not sys.stdin.isatty()
    # Determine input source and read URLs
    if args.file:
        if is_pipe:
            print("Warning: Both file and pipe input detected. Using file input.")
        urls, removed_initial = read_urls_from_file(args.file)
    elif args.json:
        if is_pipe:
            print("Warning: Both JSON file and pipe input detected. Using JSON input.")
        urls, removed_initial = read_urls_from_json(args.json)
    elif is_pipe:
        if args.verbose:
            print("Reading URLs from pipe...")
        urls, removed_initial = read_from_pipe()
    else:
        parser.print_help()
        sys.exit(1)

    if not urls:
        print("Error: No URLs found from input source")
        sys.exit(1)

    if args.verbose:
        print(f"Found {len(urls)} URLs to process")
        print("First few URLs:")
        for url in urls[:5]:
            print(f"  {url}")

    # Check removed URLs for unique redirects
    if removed_initial.get("duplicate_lengths"):
        if args.verbose:
            print("\nChecking removed URLs for unique redirects...")
        
            
        additional_urls = check_redirect_urls(
            removed_initial["duplicate_lengths"],
            use_random_agent=args.random_agent,
            custom_headers=custom_headers,
            max_workers=args.workers  # Use the same number of workers as main processing
        )
        if additional_urls:
            if args.verbose:
                print(f"Found {len(additional_urls)} additional URLs with unique redirects")
            urls.extend(additional_urls)

    # Process URLs
    results = process_urls(
        urls, 
        args.workers,
        use_random_agent=args.random_agent,
        custom_headers=custom_headers
    )
    
    # Filter results and get removed URLs
    filtered_results, removed_filter = filter_results(results)

    # Print debug information about removed URLs only in verbose mode
    if args.verbose:
        print("\nRemoved URLs Summary:")
        
        if removed_initial["duplicate_lengths"]:
            print("\nRemoved due to duplicate content lengths:")
            for item in removed_initial["duplicate_lengths"]:
                print(f"  {item['url']} (length: {item['length']})")
        
        if removed_filter["404"]:
            print("\nRemoved 404 URLs:")
            for url in removed_filter["404"]:
                print(f"  {url}")
        
        if removed_filter["duplicate_redirects"]:
            print("\nRemoved duplicate redirects:")
            for item in removed_filter["duplicate_redirects"]:
                print(f"  {item['url']} -> {item['location']}")
                
        if removed_filter["failed_requests"]:
            print("\nFailed requests:")
            for result in removed_filter["failed_requests"]:
                if result and result.get('url'):
                    print(f"  {result['url']}: {result.get('error', 'Unknown error')}")

    if args.json_output:
        output_data = {
            "results": filtered_results,
            "total": len(filtered_results),
            "successful": sum(1 for r in filtered_results if r.get('status_code') == 200),
            "removed": {
                "initial": removed_initial,
                "filter": removed_filter
            } if args.verbose else {},  # Only include removed data if verbose
            "settings": {
                "random_agent": args.random_agent,
                "custom_headers": custom_headers
            }
        }
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
        else:
            print(json.dumps(output_data, indent=2))
    else:
        # Format text output lines
        output_lines = []
        for result in filtered_results:
            status = result.get('status_code', 0)
            length = result.get('content_length', 0)
            url = result.get('url', '')
            
            # Convert length to human readable format
            if length >= 1024 * 1024 * 1024:
                size_str = f"{length / (1024 * 1024 * 1024):.1f}GB"
            elif length >= 1024 * 1024:
                size_str = f"{length / (1024 * 1024):.1f}MB"
            elif length >= 1024:
                size_str = f"{length / 1024:.1f}KB"
            else:
                size_str = f"{length}B"
                
            # Format line like dirsearch output
            line = f"{status}     {size_str:<6} {url}"
            output_lines.append(line)
        
        # Add summary line
        summary = f"\nTotal: {len(filtered_results)} | 200 OK: {sum(1 for r in filtered_results if r.get('status_code') == 200)}"
        output_lines.append(summary)
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                f.write('\n'.join(output_lines))
        else:
            print("\nResults:")
            print('\n'.join(output_lines))

if __name__ == '__main__':
    main() 