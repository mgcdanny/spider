import requests
from html.parser import HTMLParser
import multiprocessing as mp
import argparse
from statistics import mean, median, variance
import re

# /wiki/Agglomeration_communities_in_France
# /wiki/Urban_communities_in_France
# /wiki/Agglomeration_communities_in_France
# /wiki/Urban_communities_in_France
# /wiki/Timeline_of_the_introduction_of_television_in_countries

#https://pymotw.com/2/multiprocessing/communication.html


def update_cache(cache, key, vals):
    cache[key] = list(set(cache[key] + vals))


class Spider(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.is_p = False
        self.is_italic = False
        self.is_parens = False
        self.is_link = False
        self.link = None
        self.next_link = None

    def follow_link(self, attrs):
        if self.is_link and self.is_p and (not self.is_italic) and (not self.is_parens) and (self.next_link is None):
            self.next_link = {k:v for k,v in attrs}.get('href')
            if self.next_link:
                if any([c in [':', '#', 'wikimedia'] for c in self.next_link]):  # ignore 'bad' links
                    self.next_link = None

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.is_p = True
        if tag == 'i':
            self.is_italic = True
        if tag == 'a':
            self.is_link = True
        self.follow_link(attrs)

    def handle_endtag(self, tag):
        if tag == 'p':
            self.is_p = False
        if tag == 'i':
            self.is_italic = False
        if tag == 'a':
            self.is_link = False

    def handle_data(self, data):
        if '(' in data:  # does not handle nested parens like: ((...)<a></a>)
            self.is_parens = True
        if ')' in data:
            self.is_parens = False

    def crawl(self, link):
        page = requests.get(link)
        self.link = page.url  # handles the special case '/wiki/Special:Random'
        self.feed(page.text)


def analyze(graphs):
    """summary stats for the graphs:
    >>> graphs = [{'win': ['a', 'b', 'philosophy']}, {'win': ['c', 'd', 'philosophy']}, {'fail': ['e', 'f', 'g', 'h', 'i', 'j', 'k']}]
    >>> analyze(graphs)
    ... {'min': 2, 'max': 2, 'mean': 2.0, 'median': 2.0, 'var': 0.0}
    """
    win_path_lengths = []
    fail_path_lengths = []

    for graph in graphs:
        if graph.get('win'):
            win_path_lengths.append(len(graph['win']) - 1)
        if graph.get('fail'):
            fail_path_lengths.append(len(graph['fail']) - 1)

    #stats
    win_perc = sum(win_path_lengths)/sum([sum(win_path_lengths), sum(fail_path_lengths)])
    min_path_length = min(win_path_lengths)
    max_path_length = max(win_path_lengths)
    mean_path_length = mean(win_path_lengths)
    median_path_length = median(win_path_lengths)
    var_path_length = variance(win_path_lengths)

    print('Cache is enabled by default, turning it off will affect the distributions')
    print('Percentage of pages leading to Philosophy: {}'.format(win_perc))
    print('Distribution of paths leading to Philosophy: min {}, max {}, mean {}, median {}, var {}'.format(
           min_path_length, max_path_length, mean_path_length, median_path_length, var_path_length))

    return dict(min=min_path_length,
                max=max_path_length,
                mean=mean_path_length,
                median=median_path_length,
                var=var_path_length)


def make_dot_file(graphs, fname='graph.dot'):
    """ Create a graphviz directed graph via cli:
        dot -Tpng graph.dot -o graph.png
    
    >>> make_dot_file([{'win': ['a', 'b', 'philosohpy']}, {'win': 'c', 'd', 'philosophy'}])
    >>> 'diagraph{a->b; b->philosophy; c->d, d->philosophy;}'
    """

    with open(fname, 'w') as dot:
        dot.write('digraph { \n')
        code = []
        for graph in graphs:
            nodes = graph.get('win')
            if nodes:
                nodes = [re.sub('[^a-zA-Z]+','',node.replace('/wiki/','')) for node in nodes] #remove non-alpha chars
                code.extend([connect+';\n' for connect in ['->'.join(pair) for pair in [nodes[n:n+2] for n in range(len(nodes)-1)]]])
        dot.writelines(set(code))
        dot.write('}')


def run(link, cache, config, graph, use_cache):
    """From link, follow the first The scrape function interprets and acts upon the state of the Spider object"""
    print(link)

    if link != config['start']:
        graph.append(link)

    spider = Spider()
    spider.crawl(config['root']+link)

    #rules
    is_honeypot = not spider.next_link
    is_infinity = spider.next_link in graph
    is_cached_fail = spider.next_link in cache['fail'] and use_cache
    is_cached_win  = spider.next_link in cache['win']  and use_cache

    if is_cached_win or spider.next_link == config['stop']:
        cache = update_cache(cache, 'win', graph)
        graph.append(spider.next_link)
        return {'win': graph}

    if is_cached_fail:
        cache = update_cache(cache, 'fail', graph)
        graph.append(spider.next_link)
        return {'fail': graph, 'reason': 'cached fail'}

    if is_honeypot:
        cache = update_cache(cache, 'fail', graph)
        graph.append(spider.next_link)
        return {'fail': graph, 'reason': 'no more links'}

    if is_infinity:
        cache = update_cache(cache, 'fail', graph)
        graph.append(spider.next_link)
        return {'fail': graph, 'reason': 'recursion detected'}

    return run(spider.next_link, cache, config, graph, use_cache)



def main_cli():

    parser = argparse.ArgumentParser(description='Wikipedia Web Crawler')

    parser.add_argument('--processes','-p', type=int, default=4,
                       help='number of processes for the pool')

    parser.add_argument('--samples', '-s', type=int, default=10,
                       help='number of webpages to crawl')

    parser.add_argument('--cache', dest='use_cache', action='store_true',
                       help='use cache (default)')

    parser.add_argument('--no-cache', dest='use_cache', action='store_false',
                       help='do not use cache')

    parser.set_defaults(use_cache=True)

    args = parser.parse_args()
    
    config = {'start': '/wiki/Special:Random',
              'stop':  '/wiki/Philosophy',
              'root':  'https://en.wikipedia.org'}

    mgr = mp.Manager()

    cache = mgr.dict({'fail': mgr.list(), 'win': mgr.list()})

    with mp.Pool(args.processes) as pool:
        graphs = pool.starmap(run, [(config['start'], cache, config, [], args.use_cache) for i in range(args.samples)])
    
    analyze(graphs)

    return graphs



if __name__ == '__main__':
    graphs = main_cli()
