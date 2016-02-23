from databasic import mongo

if __name__ == '__main__':
	mongo.remove_all_sample_data()
	print 'removed cached sample data results'