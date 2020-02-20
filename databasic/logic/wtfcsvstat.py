import datetime
import os
import sys
import re
import csv
import time
import collections
from operator import itemgetter
import math
import logging
import six
import codecs
import wordhandler
import numpy.random
from csvkit import table
from dateutil.parser import parse
import filehandler

from databasic import NLTK_STOPWORDS_BY_LANGUAGE

NoneType = type(None)

SAMPLE_FOR_TYPE = True  # controls whether we sample values to determine what type a column is
MAX_UNIQUE = 5
NUMBER_MAX_UNIQUE = 10
MAX_FREQ = 5
OPERATIONS =('min', 'max', 'sum', 'mean', 'median', 'stdev', 'nulls', 'unique', 'freq', 'len', 'deciles')

MONTHS = ['jan', 'january', 'feb', 'february', 'mar', 'march', 'apr', 'april', 'may', 'jun', 'june', 'jul', 'july', 'aug', 'august', 'sep', 'september', 'oct', 'october', 'nov', 'november', 'dec', 'december']
DAYS_OF_WEEK = ['sun', 'sunday', 'mon', 'monday', 'tues', 'tue', 'tuesday', 'wed', 'wednesday', 'thu', 'thur', 'thurs', 'thursday', 'fri', 'friday', 'sat', 'saturday']

logger = logging.getLogger(__name__)

'''
Public API: call this to get results!
'''
def get_summary(input_path, has_header_row=True):
    wtfcsvstat = WTFCSVStat(input_path, has_header_row)
    results = wtfcsvstat.get_summary()
    return results

'''
A hacked-up version of after CSVState
'''
class WTFCSVStat():
    
    def __init__(self, input_path, has_header_row=True):
        self.input_path = input_path
        self.has_header_row = has_header_row
        utf8_file_path = filehandler.convert_to_utf8(input_path)
        logger.debug("converted to utf8 at %s" % utf8_file_path)
        self.input_file = codecs.open(utf8_file_path,'r',filehandler.ENCODING_UTF_8)
    
    # copied from CSVKitUtility
    def _open_input_file(self, path, enc):
        if six.PY2:
            mode = 'rbw'
        else:
            mode = 'rt'

        (_, extension) = os.path.splitext(path)

        f = open(path)
        # f = codecs.open(path, mode, encoding='utf-8')

        return f

    def detectDelimiter(self):
        with open(self.input_path, 'r') as myCsvfile:
            header=myCsvfile.readline()
            if header.find(",")!=-1:
                logger.debug("Detected delimiter ,")
                return ","
            if header.find(";")!=-1:
                logger.debug("Detected delimiter ;")
                return ";"
            if header.find("\t")!=-1:
                logger.debug("Detected delimiter \t")
                return "\t"
        return ","

    def get_summary(self):
        summary_start = time.clock()
        results = {}
        
        operations = [op for op in OPERATIONS]

        if self._csv_has_rows(self.input_path) == False:
            results['row_count'] = 0
            results['columns'] = []
            return results

        start_time = time.clock()
        tab = None
        delim = self.detectDelimiter()

        try:
            tab = table.Table.from_csv(self.input_file,delimiter=delim,quotechar='"')
        except Exception as e:
            logger.debug("Error making a table from the CSV")
            return 'bad_formatting'

        logger.debug("  %f ms to create table from csv" % (1000*(time.clock()-start_time)))

        row_count = tab.count_rows() + 1 # this value is inaccurate so I'm adding 1
        if self.has_header_row:
            row_count -= 1
        results['row_count'] = row_count
        logger.debug("  found %d rows" % row_count)

        column_count = len(tab)
        empty_header_count = 0
        
        results['columns'] = []
        for c in tab:
            #logger.debug("  column: %s" % c.name)

            """
            skip over columns that don't have headers
            also count the number of columns without headers
            and if all columns are missing headers, tell the user that the csv is poorly formatted
            """
            if c.name == '_unnamed':
                empty_header_count += 1
                if empty_header_count == column_count:
                    return 'bad_formatting'
                continue

            column_info = {}
            column_info['index'] = c.order + 1
            column_info['name'] = c.name
            
            values = sorted(filter(lambda i: i is not None, c))

            stats = {} 

            # figure out what type the column is
            start_time = time.clock()

            date_count = 0
            time_count = 0
            number_count = 0
            value_count = len(values)
            if SAMPLE_FOR_TYPE and value_count>100:    # try sampling to speed this up
                sampled_values = numpy.random.choice(values,100)
            else: 
                sampled_values = values
            sampled_value_count = len(sampled_values)

            for v in sampled_values:
                if type(v) in [float, int, long, complex] or self.is_number(unicode(v)):
                    number_count += 1
                if self.is_date(v) is not None:
                    v = self.is_date(v)
                    if v.time() != datetime.time(0, 0):
                        time_count += 1
                    if v.date() != datetime.date.today():
                        date_count += 1

            if sampled_value_count > 0:
                date_percent = float(date_count) / float(sampled_value_count)
                time_percent = float(time_count) / float(sampled_value_count)
                number_percent = float(number_count) / float(sampled_value_count)
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
                elif time_percent > threshold:
                    c.type = datetime.time
            else:
                c.type = float

            #logger.debug("    type is %s (%f ms)" % (c.type, (time.clock()-start_time)*1000))

            # clean the data, based on the type it is
            start_time = time.clock()
            if c.type == datetime.datetime or c.type == datetime.date or c.type == datetime.time:
                old_len = len(values)
                values = [ self.is_date(v).replace(tzinfo=None) for v in values if self.is_date(v) is not None ]
                new_len = len(values)
                #logger.debug("    removed %d bad values" % (old_len-new_len))
            elif c.type == float:
                old_len = len(values)
                values = [ self.is_number(v) for v in values if self.is_number(v) is not None ]
                new_len = len(values)
                #logger.debug("    removed %d bad values" % (old_len-new_len))
            elif c.type == unicode:
                old_len = len(values)
                values = [ v for v in values if v != '&nbsp;' ]
                new_len = len(values)
                #logger.debug("    removed %d bad values" % (old_len-new_len))
            #logger.debug("    cleaned in %f ms" % ((time.clock()-start_time)*1000))

            # do the default operations on the values
            start_time = time.clock()
            for op in OPERATIONS:
                op_start_time = time.clock()
                stats[op] = getattr(self, 'get_%s' % op)(c, values, stats)
                #logger.debug("      %s in %f" % (op,(time.clock()-op_start_time)*1000))
            #logger.debug("    default ops took %f ms" % ((time.clock()-start_time)*1000))

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
                        if c.type is not bool:
                            column_info['others'] = stats['others']

                    # for text columns, get the longest string
                    if c.type == six.text_type:
                        column_info['max_str_len'] = stats['len']

            if 'unicode' in column_info['type'] and not 'most_freq_values' in column_info:
                # TODO: these results could be cleaned up using textmining
                # TODO: send in the language properly?
                stopwords_language = NLTK_STOPWORDS_BY_LANGUAGE[g.current_lang]
                column_info['word_counts'] = wordhandler.get_word_counts(
                    str([s for s in values]).strip('[]').replace("u'", '').replace("',", ''),
                    True, True, stopwords_language, False, False)

            results['columns'].append( column_info )

        logger.debug("  done in %f ms" % ((time.clock()-summary_start)*1000 ))
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
        null_count = 0
        if c.has_nulls():
            for v in c:
                if v is None:
                    null_count += 1
        return null_count

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
            if mx-mn > 10:
                return str(round(val)).replace('.0', '')
            else:
                return str(round(val*100)/100).replace('.0','')

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
            date_str = six.text_type(date)
            if re.search('[a-zA-Z]', date_str) and date_str not in MONTHS and date_str not in DAYS_OF_WEEK:
                return None
            else:
                return parse(str(date_str))
        except:
            return None

    def is_number(self, s):
        try:
            return float(s)
        except ValueError:
            pass
     
        try:
            import unicodedata
            return unicodedata.numeric(s)
        except (TypeError, ValueError):
            pass
     
        return None

    def _csv_has_rows(self, file_path):
        with open(file_path, 'rU') as f:
            #Read in parameter values as a dictionary
            paradict = csv.DictReader(f)
            for line in paradict:
                return True
        return False

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
    counter=collections.Counter(l)
    results = counter.most_common(n)
    return results

if __name__ == "__main__":
    if(len(sys.argv)!=2):
        print("You must pass in a csv file to parse!")
        sys.exit(1)
    wtfcsvstat = WTFCSVStat(sys.argv[1])
    # results = wtfcsvstat.get_summary()
    # print(results)
