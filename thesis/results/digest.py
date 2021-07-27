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

def remove_suffix(suffix):
    def inner(x: str):
        if x.endswith(suffix):
            return x[:-len(suffix)]
        return x
    return inner

def pct_std(c):
    return c.std() / c.mean() * 100

def pct_diff(base):
    def pct_diff(c):
        real_base = base[base.index == c.index[0]]
        return (c.mean() - real_base.mean()) / abs(real_base.mean()) * 100
    return pct_diff

def fixup_column_names(df):
    def fixup(s):
        s.replace('-', ' ') \
        .title().replace('Bpfbox', 'BPFBox') \
        .replace('Apparmor', 'AppArmor') \
        .replace('Bpfcontain', 'BPFContain')
    df.rename(columns=fixup, inplace=True, level=0)


def ingest() -> pd.DataFrame:
    """Ingest data from json file"""

    with open('results.json') as f:
        data = json.load(f)

    #results = pd.json_normalize(data['results'], record_path='results')
    #print(results)

    #df = pd.DataFrame.from_records(data['results'], record_path='base.value')

    # Normalize JSON file
    df = pd.json_normalize(data['results'])

    # Rename columns
    df.rename(remove_prefix('results.'), axis='columns', inplace=True)
    df.rename(columns={'test':'suite', 'arguments':'test'}, inplace=True)

    # Rename test suites
    df['suite'] = df['suite'].str.replace('pts/osbench-1.0.2', 'OSBench', regex=False)
    df['suite'] = df['suite'].str.replace('pts/build-linux-kernel-1.11.0', 'Kernel Compilation', regex=False)
    df['suite'] = df['suite'].str.replace('pts/apache-1.7.2', 'Apache', regex=False)

    # Rename units
    df['units'] = df['units'].str.replace('us', 'μs')

    # Turn results into lists
    for c in df.filter(regex='all_results'):
        df[c] = df[c].map(lambda s: list(s.split(':')))

    df = df[df.columns.drop(list(df.filter(regex='value')))]
    df = df.explode(list(df.filter(regex='all_results')))
    df.rename(remove_suffix('.all_results'), axis='columns', inplace=True)

    result_cols = [
            'base',
            'apparmor-passive',
            'apparmor-allow',
            'apparmor-complaining',
            'bpfbox-passive',
            'bpfbox-allow',
            'bpfbox-complaining',
            'bpfcontain-passive',
            'bpfcontain-allow',
            'bpfcontain-complaining',
            ]

    for c in result_cols:
        df[c] = pd.to_numeric(df[c])

    df = df.groupby(['suite', 'test', 'units'], as_index=False).agg(['mean', 'std', pct_std, pct_diff(df['base'])]).reset_index()

    # Print the data frame for testing
    #print(df)
    #print(df.xs('mean', axis=1, level=1, drop_level=True))

    return df


def digest(df: pd.DataFrame, prefix: str):
    """Process data frame from ingest() and save to new files"""
    print(df)



def main():
    df = ingest()

    osbench = df[df['suite'] == 'OSBench']
    digest(osbench, 'osbench')

    kernel = df[df['suite'] == 'Kernel Compilation']
    digest(kernel, 'kernel-compilation')

    apache = df[df['suite'] == 'Apache']
    digest(apache, 'apache')



if __name__ == '__main__':
    main()
