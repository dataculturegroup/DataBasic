from databasic import mongo
import sys

VALID_COLLECTION_NAMES = ['wordcounter', 'wtfcsv', 'samediff', 'connectthedots']


def main(argv):
    if '-rm-samples' in argv:
        mongo.remove_all_sample_data()
        print 'removed sample data'
    if '-rm-expired' in argv:
        mongo.remove_all_expired_results()
        print 'removed expired results'
    if '-rm-by-id' in argv:
        if argv[1] not in VALID_COLLECTION_NAMES:
            print("Error - invalid collection name, must be one of {}".format(', '.join(VALID_COLLECTION_NAMES)))
            sys.exit(1)
        print 'removing {} from {}'.format(argv[2], argv[1])
        results = mongo.remove_by_id(argv[1], argv[2])
        print '  removed {} rows'.format(results['n'])


if __name__ == '__main__':
    main(sys.argv[1:])
