#! /usr/bin/python
##
## test program for requests to get tz_offset for current timezone
##

import requests
import logging

# Get params from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    logging.error("WiFi connect failed: no secrets.py file")
    raise


def get_tzoffset():
    url = f'https://io.adafruit.com/api/v2/{secrets["aio_username"]}/' + \
          f'integrations/time/strftime?x-aio-key={secrets["aio_key"]}&fmt=%25z'
    logging.info(f"url= {url}")
    with requests.get(url) as response:
        logging.info(f"strftime call returned: {response.status_code}")
        # check status_code = 200??
        val = int(response.text)/100
        #logging.info(f"tz_offset: {response.text} ->  {val}")
        return int(val)


def main():
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                        level=logging.INFO)
    val = get_tzoffset()
    print (f'get_tzoffset() returned {val}')


if __name__ == "__main__" :
    # Any use for argv's?
    main()
        
    
