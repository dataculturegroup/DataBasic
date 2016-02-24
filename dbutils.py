from databasic import mongo
import sys, getopt

def main(argv):
	if '-rm-samples' in argv:
		mongo.remove_all_sample_data()
		print 'removed sample data'
	if '-rm-expired' in argv:
		mongo.remove_all_expired_results()
		print 'removed expired results'

if __name__ == '__main__':
	main(sys.argv[1:])