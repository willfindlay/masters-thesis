#!/usr/bin/env python3

import pandas as pd
import numpy as np
import json

from flatten_json import flatten
from pprint import pprint

def remove_prefix(prefix):
    def inner(x: str):
        if x.startswith(prefix):
            return x[len(prefix):]
        return x
    return inner

def ingest():
    """Ingest data from json file"""

    with open('results.json') as f:
        data = json.load(f)

    #results = pd.json_normalize(data['results'], record_path='results')
    #print(results)

    #raw_df = pd.DataFrame.from_records(data['results'], record_path='base.value')
    raw_df = pd.json_normalize(data['results'])
    raw_df = raw_df.rename(remove_prefix('results.'), axis='columns')
    print(raw_df.T)


def digest():
    """Process data frame from ingest() and save to new files"""
    pass



def main():
    ingest()



if __name__ == '__main__':
    main()
