#!/usr/bin/env python
import datetime, os, sys, json, tempfile, re
import gzip
import bz2
from heapq import nlargest
from operator import itemgetter
import math
import logging
import six
import codecs
import wordhandler
import pytz
import calendar

from csvkit import CSVKitReader, table
from lazyfile import LazyFile
from dateutil.parser import parse

NoneType = type(None)

MAX_UNIQUE = 5
NUMBER_MAX_UNIQUE = 10
MAX_FREQ = 5
OPERATIONS =('min', 'max', 'sum', 'mean', 'median', 'stdev', 'nulls', 'unique', 'freq', 'len', 'deciles')

MONTHS = ['jan', 'january', 'feb', 'february', 'mar', 'march', 'apr', 'april', 'may', 'jun', 'june', 'jul', 'july', 'aug', 'august', 'sep', 'september', 'oct', 'october', 'nov', 'november', 'dec', 'december']
DAYS_OF_WEEK = ['sun', 'sunday', 'mon', 'monday', 'tues', 'tue', 'tuesday', 'wed', 'wednesday', 'thu', 'thur', 'thurs', 'thursday', 'fri', 'friday', 'sat', 'saturday']

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

        f = open(path)

        return f

    def get_summary(self):
        results = {}
        
        operations = [op for op in OPERATIONS]

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

            date_count = 0
            time_count = 0
            number_count = 0
            value_count = len(values)

            def remove_broken_datetimes():
                new_values = []
                for v in values:
                    new = self.is_date(v)
                    if new is not None:
                        new_values.append(new.replace(tzinfo=None))
                return new_values

            for v in values:
                if type(v) in [float, int, long, complex]:
                    number_count += 1
                if self.is_date(v) is not None:
                    v = self.is_date(v)
                    if v.time() != datetime.time(0, 0):
                        time_count += 1
                    if v.date() != datetime.date.today():
                        date_count += 1

            if value_count > 0:
                date_percent = float(date_count) / float(value_count)
                time_percent = float(time_count) / float(value_count)
                number_percent = float(number_count) / float(value_count)
            else:
                date_percent = 0
                time_percent = 0
                number_percent = 0
                
            threshold = 0.5

            if number_percent < threshold:
                if date_percent > threshold:
                    if time_percent > threshold:
                        c.type = datetime.datetime
                    else:
                        c.type = datetime.date
                    values = remove_broken_datetimes()
                elif time_percent > threshold:
                    c.type = datetime.time
                    values = remove_broken_datetimes()

            for op in OPERATIONS:
                stats[op] = getattr(self, 'get_%s' % op)(c, values, stats)

            if c.type == None:
                column_info['type'] = 'empty'
                continue
                
            column_info['type'] = c.type.__name__
            column_info['nulls'] = stats['nulls']

            t = column_info['type']
            dt = 'undefined'
            if any(t in s for s in ['float', 'int', 'long', 'complex']):
                dt = 'numbers'
            if 'unicode' in t:
                dt = 'text'
            if 'time' in t:
                dt = 'times'
            if 'date' in t:
                dt = 'dates'
            if 'datetime' in t:
                dt = 'dates and times'
            if 'bool' in t:
                dt = 'booleans'
            column_info['display_type_name'] = dt

            if dt in ['numbers', 'dates', 'times', 'dates and times']:
                if len(stats['unique']) <= NUMBER_MAX_UNIQUE:
                    column_info['most_freq_values'] = sorted(self.get_most_freq_values(stats), key=itemgetter('value'))
                else:
                    column_info['uniques'] = len(stats['unique'])
                    column_info['min'] = stats['min']
                    column_info['max'] = stats['max']
                    column_info['deciles'] = stats['deciles']
                    if dt in 'numbers':
                        column_info['sum'] = stats['sum']
                        column_info['mean'] = stats['mean']
                        column_info['median'] = stats['median']
                        column_info['stdev'] = stats['stdev']
            else:
                # if there are few unique values, get every value and their frequency
                if len(stats['unique']) <= MAX_UNIQUE and c.type is not bool:
                    column_info['values'] = self.get_most_freq_values(stats)
                    column_info['most_freq_values'] = self.get_most_freq_values(stats)
                else:
                    column_info['uniques'] = len(stats['unique'])

                    # get the most frequent repeating values, if any
                    if column_info['uniques'] != len(values):
                        column_info['most_freq_values'] = self.get_most_freq_values(stats)
                        column_info['others'] = stats['others']

                    # for text columns, get the longest string
                    if c.type == six.text_type:
                        column_info['max_str_len'] = stats['len']

            if 'unicode' in column_info['type'] and not 'most_freq_values' in column_info:
                # TODO: these results could be cleaned up using textmining
                column_info['word_counts'] = wordhandler.get_word_counts(str([s for s in values]).strip('[]').replace("u'", '').replace("',", ''))

            results['columns'].append( column_info )
        return results

    def get_most_freq_values(self, stats):
        most_freq_values = []
        for value, count in stats['freq']:
            most_freq_values.append({
                'value': value,
                'count': count
                })
        return most_freq_values

    def get_min(self, c, values, stats):
        if c.type == NoneType:
            return None

        v = min(values)

        return format_datetime(c, v)

    def get_max(self, c, values, stats):
        if c.type == NoneType:
            return None

        v = max(values)

        return format_datetime(c, v)

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
        if c.type not in [int, float, long, complex]:
            mostfrequent = freq(values)
        else:
            mostfrequent = freq(values, n=NUMBER_MAX_UNIQUE)
        if 'others' not in stats:
            stats['others'] = len([v for v in values if v not in (v2 for v2, c in mostfrequent)])
        return mostfrequent

    def get_len(self, c, values, stats):
        if c.type != six.text_type:
            return None

        return c.max_length()

    # not *literally* deciles, but kinda similar
    def get_deciles(self, c, values, stats):
        if c.type not in [int, float, datetime.date, datetime.time, datetime.datetime] or len(values) <= NUMBER_MAX_UNIQUE:
            return None
        mx = max(values)
        mn = min(values)
        if c.type is float:
            range_size = (mx-mn)/10.0
        else:
            range_size = (mx-mn)/10

        decile_groups = []
        for x in xrange(10):
            decile_groups.append(mn+(range_size*x))

        def get_values_in_range(from_val, to_val):
            count = len([v for v in values if v >= from_val and v < to_val])
            pretty_from = from_val
            val = pretty_value(from_val) + " - " + pretty_value(to_val)
            return {'value': val, 'count': count}

        def pretty_value(val):
            if c.type is int:
                return str(val)
            if c.type in [datetime.date, datetime.time, datetime.datetime]:
                return format_datetime(c, val)
            if val < 1:
                return str(val)
            else:
                return str(round(val)).replace('.0','')

        deciles = []
        for d in xrange(len(decile_groups)-1):
            from_val = decile_groups[d]
            to_val = decile_groups[d+1]
            deciles.append(get_values_in_range(from_val, to_val))

        from_val = decile_groups[len(decile_groups)-1]
        to_val = mx
        deciles.append(get_values_in_range(from_val, to_val))

        return deciles

    def is_date(self, date):
        try:
            if re.search('[a-zA-Z]', date) and date not in MONTHS and date not in DAYS_OF_WEEK:
                return None
            else:
                return parse(str(date))
        except:
            return None

def format_datetime(c, val):
    if c.type in [datetime.datetime, datetime.date, datetime.time]:
        if c.type is datetime.date:
            return "%02d/%02d/%02d" % (val.day,val.month,val.year)
        elif c.type is datetime.time:
            return "%02d:%02d" % (val.hour,val.minute)
        else:
            return "%02d/%02d/%02d %02d:%02d" % (val.day,val.month,val.year,val.hour,val.minute)
    return unicode(val)

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
