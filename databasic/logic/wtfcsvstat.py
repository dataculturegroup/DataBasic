#!/usr/bin/env python
import datetime, os, sys, json, tempfile
import gzip
import bz2
from heapq import nlargest
from operator import itemgetter
import math
import logging
import six
import codecs

from csvkit import CSVKitReader, table
from lazyfile import LazyFile

NoneType = type(None)

MAX_UNIQUE = 5
MAX_FREQ = 5
OPERATIONS =('min', 'max', 'sum', 'mean', 'median', 'stdev', 'nulls', 'unique', 'freq', 'len')



'''
Public API: call this to get results!
'''
def get_summary(input_path, has_header_row=True, encoding='utf-8'):
    wtfcsvstat = WTFCSVStat(input_path, has_header_row, encoding)
    results = wtfcsvstat.get_summary()
    return results

'''
A hacked-up version of after CSVState
'''
class WTFCSVStat():
    
    def __init__(self, input_path, has_header_row=True, encoding='utf-8'):
        self.has_header_row = has_header_row
        self.input_file = self._open_input_file(input_path, encoding)
        
    
    # copied from CSVKitUtility
    def _open_input_file(self, path, enc):
        if six.PY2:
            mode = 'rbw'
        else:
            mode = 'rt'

        (_, extension) = os.path.splitext(path)

        pathbak = os.path.join(tempfile.gettempdir(),os.path.basename(path) + '.bak')
        os.rename(path, pathbak)
        with open(pathbak, 'r') as infile, open(path, 'w') as outfile:
            for line in infile:
                outfile.write(line.replace('\n', ' '))
        os.remove(pathbak)

        # f = codecs.open(path, mode, encoding=enc) # this was causing problems
        f = open(path)

        return f

    def get_summary(self):
        results = {}
        
        operations = [op for op in OPERATIONS]

        # TODO: this breaks if cell contains a newline
        tab = table.Table.from_csv(self.input_file)

        row_count = tab.count_rows() + 1 # this value is inaccurate so I'm adding 1
        if self.has_header_row:
            row_count -= 1
        results['row_count'] = row_count
        
        results['columns'] = []
        for c in tab:
            column_info = {}
            column_info['index'] = c.order + 1
            column_info['name'] = c.name
            
            values = sorted(filter(lambda i: i is not None, c))

            stats = {} 

            for op in OPERATIONS:
                stats[op] = getattr(self, 'get_%s' % op)(c, values, stats)

            
            if c.type == None:
                column_info['type'] = 'empty'
                continue
                
            column_info['type'] = c.type.__name__
            column_info['nulls'] = stats['nulls']

            if len(stats['unique']) <= MAX_UNIQUE and c.type is not bool:
                column_info['values'] = [six.text_type(u) for u in list(stats['unique'])]
            else:
                if c.type not in [six.text_type, bool]:
                    column_info['min'] = stats['min']
                    column_info['max'] = stats['max']
                    if c.type in [int, float]:
                        column_info['sum'] = stats['sum']
                        column_info['mean'] = stats['mean']
                        column_info['median'] = stats['median']
                        column_info['stdev'] = stats['stdev']
                column_info['uniques'] = len(stats['unique'])

                if len(stats['unique']) != len(values):
                    for value, count in stats['freq']:
                        column_info['most_freq_values'] = {six.text_type(value): count for value,count in stats['freq']}

                if c.type == six.text_type:
                    column_info['max_str_len'] = stats['len']

            results['columns'].append( column_info )
        return results

    def get_min(self, c, values, stats):
        if c.type == NoneType:
            return None

        v = min(values)

        if v in [datetime.datetime, datetime.date, datetime.time]:

            return v.isoformat()
        
        return str(v)

    def get_max(self, c, values, stats):
        if c.type == NoneType:
            return None

        v = max(values)

        if v in [datetime.datetime, datetime.date, datetime.time]:
            return v.isoformat()
        return str(v)

    def get_sum(self, c, values, stats):
        if c.type not in [int, float]:
            return None

        return sum(values)

    def get_mean(self, c, values, stats):
        if c.type not in [int, float]:
            return None

        if 'sum' not in stats:
            stats['sum'] = self.get_sum(c, values, stats)

        return float(stats['sum']) / len(values)

    def get_median(self, c, values, stats):
        if c.type not in [int, float]:
            return None

        return median(values)

    def get_stdev(self, c, values, stats):
        if c.type not in [int, float]:
            return None

        if 'mean' not in stats:
            stats['mean'] = self.get_mean(c, values, stats)

        return math.sqrt(sum(math.pow(v - stats['mean'], 2) for v in values) / len(values)) 

    def get_nulls(self, c, values, stats):
        return c.has_nulls()

    def get_unique(self, c, values, stats):
        return set(values) 

    def get_freq(self, c, values, stats):
        mostfrequent = freq(values)
        return mostfrequent

    def get_len(self, c, values, stats):
        if c.type != six.text_type:
            return None

        return c.max_length()

def median(l):
    """
    Compute the median of a list.
    """
    length = len(l)

    if length % 2 == 1:
        return l[(length + 1) // 2 - 1]
    else:
        a = l[(length // 2) - 1]
        b = l[length // 2]
    return (float(a + b)) / 2  

def freq(l, n=MAX_FREQ):
    """
    Count the number of times each value occurs in a column.
    """
    count = {}

    for x in l:
        s = six.text_type(x)

        if s in count:
            count[s] += 1
        else:
            count[s] = 1

    # This will iterate through dictionary, return N highest
    # values as (key, value) tuples.
    top = nlargest(n, six.iteritems(count), itemgetter(1))
    result = []
    for item in top:
        result.append((str(item[0]).replace('.','_'), item[1]))
    return result

if __name__ == "__main__":
    if(len(sys.argv)!=2):
        print("You must pass in a csv file to parse!")
        sys.exit(1)
    wtfcsvstat = WTFCSVStat(sys.argv[1])
    results = wtfcsvstat.get_summary()
    print(results)
