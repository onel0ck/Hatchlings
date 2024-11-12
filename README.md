# Revolving Games Account Checker

Script for automatic account registration in Revolving Games through message signing.

Telegram: https://t.me/unluck_1l0ck
X: https://x.com/1l0ck

## Features
- Multi-threaded wallet processing
- Proxy support with automatic rotation
- 3 retry attempts for each account on proxy error
- Detailed logging process
- Successful results saved to file
- Automatic handling of private keys with '0x' prefix

## Installation
1. Clone the repository
```bash
git clone https://github.com/onel0ck/Hatchlings
cd Hatchlings
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

## Setup
1. Create `wallets.txt` and add private keys (one per line)
```
private_key1  # can be with or without 0x prefix
0xprivate_key2  # both formats will work
```

2. Create `proxies.txt` and add proxies (one per line)
```
http://user:pass@ip:port
http://ip:port
```

## Usage
```bash
python main.py or python3 main.py
```

Results will be saved to:
- `result.txt` - successful registrations in `private_key:token` format
- `revolving_checker.log` - detailed script operation log

## Requirements
- Python 3.8+
- Dependencies from requirements.txt

## Disclaimer
This script is for educational purposes only. Use at your own risk.
