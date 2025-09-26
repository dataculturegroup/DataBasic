import os
import json
import logging
import requests
import tempfile

# need to have a default here so docker-based build doesn't require any env vars
DEFAULT_SAMPLE_DATA_SERVER = 'http://static.databasic.io/'


def init_samples():
    """
    Here we need to fetch the sample files and save a path to where they are into the .json file.
    TODO: change this later to process them all here into the database so they are no longer lazy-processed?
    :return:
    """
    print("Trying to get sample files!")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    samples_config_file_path = os.path.join(base_dir, 'config', 'sample-data.json')
    print("Retrieving sample files from: ", samples_config_file_path)

    # tell the dumb thing this is NOT ASCII
    samples = json.load(open(samples_config_file_path, 'r', encoding='utf-8'))
    
    if os.environ.get('APP_MODE', None) == "development":
        # change the paths to absolute ones
        for sample in samples:
            sample['path'] = os.path.join(base_dir, sample['source'])
        print("  Updated sample data with base dir: {}".format(base_dir))
    else:
        # copy from server to local temp dir and change to abs paths (to temp dir files)
        url_base = os.environ.get('SAMPLE_DATA_SERVER', DEFAULT_SAMPLE_DATA_SERVER)
        for sample in samples:
            url = url_base + sample['source']
            print("  Loading sample data file: {}".format(url))
            
            #reading files as utf-8 
            
            requests.encoding = 'utf-8'
            text = requests.get(url).text

            # write files as utf-8 
           
            f = tempfile.NamedTemporaryFile(mode="w", delete=False, encoding='utf-8')
            f.write(text)
            f.close()
            os.chmod(f.name, 0o444)
            sample['path'] = f.name
        print("  Downloaded sample data and saved to tempdir")
    for sample in samples:
        file_size = os.stat(sample['path']).st_size
        print("  Cached {} bytes of {} to {}".format(file_size, sample['source'], sample['path']))
    
    # write it out so the app can load it, with the `path`s we just filled in
    json.dump(samples, open(samples_config_file_path, 'w'), ensure_ascii=False)


if __name__ == "__main__":
    init_samples()
