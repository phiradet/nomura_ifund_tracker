# Nomura iFund tracker
A simple Python selenium script to scrap portfolio P/L data from Nomura iFund website

## Run
1. Make sure to have a Selenium Webdriver in `$PATH`. The current code is tested with [geckodriver v0.26.0](https://github.com/mozilla/geckodriver)
2. Execute the following code
```bash
USERNAME="<your_nomura_ifund_username>" PASSWORD="<your_nomura_ifund_password>" python main.py ./output
```