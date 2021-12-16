import datetime
import sys
import re
import decimal
import csv
import time
import collections
from operator import itemgetter
import math
import logging
import six
import databasic.logic.wordhandler as wordhandler
import agate
from dateutil.parser import parse

from databasic import NLTK_STOPWORDS_BY_LANGUAGE

NoneType = type(None)

SAMPLE_FOR_TYPE = True  # controls whether we sample values to determine what type a column is
MAX_UNIQUE = 5
NUMBER_MAX_UNIQUE = 10
MAX_FREQ = 5
OPERATIONS = ('min', 'max', 'sum', 'mean', 'median', 'stdev', 'nulls', 'unique', 'freq', 'len', 'deciles')

MONTHS = ['jan', 'january', 'feb', 'february', 'mar', 'march', 'apr', 'april', 'may', 'jun', 'june', 'jul', 'july',
          'aug', 'august', 'sep', 'september', 'oct', 'october', 'nov', 'november', 'dec', 'december']
DAYS_OF_WEEK = ['sun', 'sunday', 'mon', 'monday', 'tues', 'tue', 'tuesday', 'wed', 'wednesday', 'thu', 'thur', 'thurs',
                'thursday', 'fri', 'friday', 'sat', 'saturday']

logger = logging.getLogger(__name__)


def get_summary(input_path, has_header_row=True, language='en'):
    """
    Public API: call this to get results!
    """
    wtfcsvstat = WTFCSVStat(input_path, has_header_row)
    results = wtfcsvstat.get_summary(language)
    return results


class WTFCSVStat:
    """
    A hacked-up version of after CSVState
    """

    def __init__(self, input_path, has_header_row=True):
        self.input_path = input_path
        self.has_header_row = has_header_row
        self.input_file = open(input_path, 'r')

    def detectDelimiter(self):
        with open(self.input_path, 'r') as myCsvfile:
            header = myCsvfile.readline()
            if header.find(",") != -1:
                logger.debug("Detected delimiter ,")
                return ","
            if header.find(";") != -1:
                logger.debug("Detected delimiter ;")
                return ";"
            if header.find("\t") != -1:
                logger.debug("Detected delimiter \t")
                return "\t"
        return ","

    def detected_column_type(self, a_table, col_index):
        agate_col_class = a_table.column_types[col_index]
        if agate_col_class == agate.Text:
            return str
        elif agate_col_class == agate.Number:
            return float
        elif agate_col_class == agate.Boolean:
            return bool
        elif agate_col_class == agate.Date:
            return datetime.date
        elif agate_col_class == agate.DateTime:
            return datetime.datetime
        return None

    def get_summary(self, language):
        summary_start = time.time()
        results = {}

        if not self._csv_has_rows(self.input_path):
            results['row_count'] = 0
            results['columns'] = []
            return results

        start_time = time.time()
        delim = self.detectDelimiter()

        try:
            tab = agate.Table.from_csv(self.input_file, delimiter=delim, quotechar='"')
        except Exception as e:
            logger.debug("Error making a table from the CSV")
            logger.error(e)
            return 'bad_formatting'

        logger.debug("  %f ms to create table from csv" % (1000 * (time.time() - start_time)))

        row_count = len(tab.rows) + 1  # this value is inaccurate so I'm adding 1
        if self.has_header_row:
            row_count -= 1
        results['row_count'] = row_count
        logger.debug("  found %d rows" % row_count)

        column_count = len(tab.columns)
        empty_header_count = 0

        results['columns'] = []
        for c in tab.columns:
            logger.debug("  column: %s" % c.name)

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
            column_info['index'] = c.index + 1
            column_info['name'] = c.name
            detected_type = self.detected_column_type(tab, c.index)
            column_info['type'] = detected_type.type.__name__ if not isinstance(detected_type,type(None)) else 'none'
            values = sorted([r[c.index] for r in tab.rows if r[c.index] is not None])

            stats = {}

            # clean the data, based on the type it is
            if column_info['type'] in ['datetime.datetime', 'datetime.date']:
                values = [self.is_date(v).replace(tzinfo=None) for v in values if self.is_date(v) is not None]
            elif column_info['type'] == 'float':
                values = [self.is_number(v) for v in values if self.is_number(v) is not None]
            elif column_info['type'] == 'str':
                values = [v for v in values if v != '&nbsp;']
            # logger.debug("    cleaned in %f ms" % ((time.time()-start_time)*1000))

            # do the default operations on the values
            for op in OPERATIONS:
                stats[op] = getattr(self, 'get_%s' % op)(column_info['type'], values, stats)
                # logger.debug("      %s in %f" % (op,(time.time()-op_start_time)*1000))
            # logger.debug("    default ops took %f ms" % ((time.time()-start_time)*1000))

            if column_info['type'] == 'None':
                column_info['type'] = 'empty'
                continue

            column_info['nulls'] = stats['nulls']

            t = column_info['type']
            dt = 'undefined'
            if any(t in s for s in ['float', 'int', 'long', 'complex']):
                dt = 'numbers'
            if 'str' in t:
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
                    column_info['most_freq_values'] = sorted(self.get_most_freq_values(column_info['type'], stats),
                                                             key=itemgetter('value'))
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
                if len(stats['unique']) <= MAX_UNIQUE and column_info['type'] != bool:
                    column_info['values'] = self.get_most_freq_values(column_info['type'], stats)
                    column_info['most_freq_values'] = self.get_most_freq_values(column_info['type'], stats)
                else:
                    column_info['uniques'] = len(stats['unique'])

                    # get the most frequent repeating values, if any
                    if column_info['uniques'] != len(values):
                        column_info['most_freq_values'] = self.get_most_freq_values(column_info['type'], stats)
                        if column_info['uniques'] is not 'bool':
                            column_info['others'] = stats['others']

                    # for text columns, get the longest string
                    if column_info['uniques'] == 'str':
                        column_info['max_str_len'] = stats['len']

            if (column_info['type'] == 'str') and (not 'most_freq_values' in column_info):
                # TODO: these results could be cleaned up using textmining
                # TODO: send in the language properly?
                stopwords_language = NLTK_STOPWORDS_BY_LANGUAGE[language]
                column_info['word_counts'] = wordhandler.get_word_counts(
                    str([s for s in values]).strip('[]').replace("u'", '').replace("',", ''),
                    True, True, stopwords_language, False, False)

            results['columns'].append(column_info)

        logger.debug("  done in %f ms" % ((time.time() - summary_start) * 1000))
        return results

    def get_most_freq_values(self, c, stats):
        most_freq_values = []
        for value, count in stats['freq']:
            if isinstance(value, decimal.Decimal):
                value = float(value)
            most_freq_values.append({
                'value': value,
                'count': count
            })
        return most_freq_values

    def get_min(self, c, values, stats):
        if c == 'none':
            return None

        v = min(values)

        return format_datetime(c, v)

    def get_max(self, c, values, stats):
        if c == 'none':
            return None

        v = max(values)

        return format_datetime(c, v)

    def get_sum(self, c, values, stats):
        if c not in ['int', 'float']:
            return None

        return sum(values)

    def get_mean(self, c, values, stats):
        if c not in ['int', 'float']:
            return None

        if 'sum' not in stats:
            stats['sum'] = self.get_sum(c, values, stats)

        return float(stats['sum']) / len(values)

    def get_median(self, c, values, stats):
        if c not in ['int', 'float']:
            return None

        return median(values)

    def get_stdev(self, c, values, stats):
        if c not in ['int', 'float']:
            return None

        if 'mean' not in stats:
            stats['mean'] = self.get_mean(c, values, stats)

        return math.sqrt(sum(math.pow(v - stats['mean'], 2) for v in values) / len(values))

    def get_nulls(self, c, values, stats):
        null_count = 0
        for v in values:
            if v is None:
                null_count += 1
        return null_count

    def get_unique(self, c, values, stats):
        return set(values)

    def get_freq(self, c, values, stats):
        if c not in ['int', 'float', 'complex']:
            mostfrequent = freq(values)
        else:
            mostfrequent = freq(values, n=NUMBER_MAX_UNIQUE)
        if 'others' not in stats:
            stats['others'] = len([v for v in values if v not in (v2 for v2, c in mostfrequent)])
        return mostfrequent

    def get_len(self, c, values, stats):
        if c != 'str':
            return None

        return c.max_length()

    # not *literally* deciles, but kinda similar
    def get_deciles(self, c, values, stats):
        if c not in ['int', 'float', 'datetime.date', 'datetime.time', 'datetime.datetime'] or len(
                values) <= NUMBER_MAX_UNIQUE:
            return None
        mx = max(values)
        mn = min(values)
        if c is float:
            range_size = (mx - mn) / 10.0
        else:
            range_size = (mx - mn) / 10

        decile_groups = []
        for x in range(10):
            decile_groups.append(mn + (range_size * x))

        def get_values_in_range(from_val, to_val):
            count = len([v for v in values if v >= from_val and v < to_val])
            pretty_from = from_val
            val = pretty_value(from_val) + " - " + pretty_value(to_val)
            return {'value': val, 'count': count}

        def pretty_value(val):
            if c == 'int':
                return str(val)
            if c in ['datetime.date', 'datetime.time', 'datetime.datetime']:
                return format_datetime(c, val)
            if mx - mn > 10:
                return str(round(val)).replace('.0', '')
            else:
                return str(round(val * 100) / 100).replace('.0', '')

        deciles = []
        for d in range(len(decile_groups) - 1):
            from_val = decile_groups[d]
            to_val = decile_groups[d + 1]
            deciles.append(get_values_in_range(from_val, to_val))

        from_val = decile_groups[len(decile_groups) - 1]
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
        except (ValueError, TypeError):
            pass

        try:
            import unicodedata
            return unicodedata.numeric(s)
        except (TypeError, ValueError):
            pass

        return None

    def _csv_has_rows(self, file_path):
        with open(file_path, 'rU') as f:
            # Read in parameter values as a dictionary
            paradict = csv.DictReader(f)
            for line in paradict:
                return True
        return False


def format_datetime(c, val):
    if c in ['datetime.datetime', 'datetime.date', 'datetime.time']:
        if c == 'datetime.date':
            return "%02d/%02d/%02d" % (val.day, val.month, val.year)
        elif c == 'datetime.time':
            return "%02d:%02d" % (val.hour, val.minute)
        else:
            return "%02d/%02d/%02d %02d:%02d" % (val.day, val.month, val.year, val.hour, val.minute)
    return val


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
    counter = collections.Counter(l)
    results = counter.most_common(n)
    return results


if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("You must pass in a csv file to parse!")
        sys.exit(1)
    wtfcsvstat = WTFCSVStat(sys.argv[1])
    # results = wtfcsvstat.get_summary()
    # print(results)
