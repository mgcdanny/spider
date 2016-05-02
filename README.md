# Wikipedia Webcrawler

Using the 'random link' hyperlink on Wikipedia, follow the first link until the Philosophy page is reached. A basic analysis of the path is printed to the screen after succesful completion of the script.

The folder images/ has an experimental output of a an image depicting the graph created by following the links to Philosophy. Open graph.png to see an example.


## Quickstart:

Get the cli help:
    $ python run.py --help

Using Defaults:
    $ python run.py

Setting number of concurrent processes to 10 and crawls 500 links:
    $ python run.py -p 10 -s 500

Disable the cache
    $ python run.py -p 10 -s 10 --no-cache


## Requirements
 - python3.X
 - requests
 - pip install -r requirements.txt


## Tests
    $ python tests.py
