# UniURL

A tool designed to process dirsearch output and filter out duplicate or false positive URLs.

## What it does

- Takes dirsearch output and filters duplicate content lengths
- Preserves URLs with unique redirect locations
- Supports multiple input methods (file, JSON, pipe)
- Concurrent processing for faster results
- Random User-Agent support
- Custom header support

## Installation

```bash
pip install uniurl
```

## Help

```bash
usage: uniurl [-h] [-f FILE] [-j JSON] [-w WORKERS] [-o OUTPUT] [-r]
[-H HEADER] [-v] [--json-output]
Process URLs from dirsearch output and verify their status
options:
-h, --help show help message
-f FILE, --file FILE input file containing URLs
-j JSON, --json JSON input JSON file containing URLs
-w WORKERS number of worker threads (default: 50)
-o OUTPUT output file (default: stdout)
-r, --random-agent use random User-Agent
-H HEADER add custom header (format: "Key: Value")
-v, --verbose show verbose output
--json-output output in JSON format
```

## Usage Examples

### From dirsearch output text file

```bash
uniurl -f output.txt
```

#### txt format

```bash
200 4KB https://example.com/path1
301 1KB https://example.com/path2
```

### From dirsearch output json file

```bash
uniurl -j output.json
```

#### JSON format

```json
{
"results": [
{
"url": "https://example.com/path1",
"content-length": 4096
}
]
}

```