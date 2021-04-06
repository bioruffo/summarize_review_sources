# -*- coding: utf-8 -*-
"""
Created on Sat Apr  3 23:00:46 2021

@author: Roberto
"""
import pandas as pd
import glob
import re
import csv

class Paper:
    def __init__(self, datadict):
        self.data = self.convert(datadict)
        
    def add(self, datadict):
        data = self.convert(datadict)
        for key, value in data.items():
            if key not in self.data or not self.data[key]:
                self.data[key] = value
            else:
                if self.data[key].strip() == '':
                    self.data[key] = value
                        
        
    def convert(self, datadict):
        key_conversions = {
                       'Publication Year': 'Year',
                       'Medline PMID': 'PMID',
                       'Author Names': 'Authors',
                       'Article Title': 'Title',
                       'Pubmed Id': 'PMID',
                       'Journal/Book': 'Source title',
                       'Source Title': 'Source title'}
        value_conversions = {'Authors': lambda x: x.replace('.', ''),
                             'Title': lambda x:x.lower(),
                             'DOI': lambda x:x.lower()}
        datadict = {key_conversions.get(item, item): datadict[item] for item in datadict}
        datadict = {key: value_conversions.get(key, lambda x: x)(value) for key, value in datadict.items()}
        if 'First Author' not in datadict.keys():
            datadict['First Author'] = datadict['Authors'].split(',')[0]
        datadict['hash'] = do_hash(datadict['Authors'], datadict['Title'], datadict['Year'])
        datadict['info'] = ''
        return datadict
    
       
    def __repr__(self):
        return self.data['First Author']+','+self.data['Year']


class Papers:
    def __init__(self, datafiles):
        self.papers = []
        self.ids = {}
        for file in datafiles:
            self.readtab(file)
       
            
    def readtab(self, file):
        source = re.split('[\\\\/]', file)[-1]
        print("Loading data from", source)

        papno = 0
        outcomes = {'new': 0, 'updated': 0}
        # encoding for pubmed is 'utf-8-sig', the first 3 chars are the byte order mark 'ï»¿'
        #we need to check if separator is ',' or ';'
        with open(file, 'r', encoding='utf-8-sig') as f:
            line = f.readline()
            if ';' in line:
                sep = ';'
            elif ',' in line:
                sep=','
            else:
                sep='\t'
        reader = csv.reader(open(file, 'r', encoding='utf-8-sig'), delimiter=sep, quotechar='"')
        for i, line in enumerate(reader):
            if i == 0:
                header = line.copy()
                '''
                # bad removal of the byte order mark
                if header[0].startswith('ï»¿'):
                    header[0] = header[0][3:]
                '''
            else:
                data = {header[j]: line[j] for j in range(len(line))}
                data['Source'] = source
                paper = Paper(data)
                papno += 1
                outcome = self.update(paper)

                if paper.data['hash'] == 'joshmullsmal1997':
                    print(paper.data)
                    for key, value in self.ids.items():
                        if value == paper:
                            print(key)

                outcomes[outcome] += 1
        print('Read {} papers, {} new, {} updated'.format(papno, outcomes['new'], outcomes['updated']))
        

    def update(self, paper):
        outcome = 'updated'
        stored_ident = []
        for ident in ['DOI', 'PMID', 'hash']:
            if paper.data.get(ident, False) and paper.data[ident] in self.ids:
                stored_ident.append(self.ids[paper.data[ident]])
        if stored_ident != []:
            assert all(x is stored_ident[0] for x in stored_ident)
            stored_ident[0].add(paper.data)
            paper = stored_ident[0]
        else:
            self.papers.append(paper)
            outcome = 'new'
        for ident in ['DOI', 'PMID', 'hash']:
            if paper.data.get(ident, False):
                self.ids[paper.data[ident]] = paper
        return outcome
            
    
    
    def export(self, filename, shortensource=False):
        print('Exporting to:', filename)
        fields = ['DOI', 'PMID', 'hash', 'Title', 'Authors', 'Source title', 'Year', 'Full Text Link', \
                  'Source',  'info']
        lines = []
        for paper in sorted(self.papers, key = lambda x: x.data['hash']):
            data = [paper.data.get(field, '') for field in fields]
            if shortensource:
                data[fields.index('Source')] = shorten_source(data[fields.index('Source')])
            lines.append(data)
        with open(filename, 'w', encoding='utf8') as f:
            f.write('\t'.join(fields)+'\n')
            for line in lines:
                f.write('\t'.join(line)+'\n')
        print('Exported', len(lines), 'papers')



# helper functions
def oror(start, end):
    print(" OR ".join("#"+str(x) for x in range(start, end+1)))


def do_hash(authors, title, year):
    # from `Lastname, FN;` to `Lastname FN,` 
    if ';' in authors:
        authors = authors.replace(',', ' ').replace(';', ',')
    ausplit = [x.strip() for x in authors.split(',')]
    aujoin = ''.join(x.strip().split(' ')[0][:3].lower() for x in ausplit)
    tisplit = re.sub('[^a-z ]', '', title).split(' ') # we set all to lowercase earlier
    tijoin = ''.join(x.strip()[:3] for x in tisplit)
    return year+aujoin+tijoin


def shorten_source(string):
    strlow = string.lower()
    if 'pubmed' in strlow:
        return 'Pubmed'
    elif 'embase' in strlow:
        return 'Embase'
    elif 'scopus' in strlow:
        return 'Scopus'
    elif 'wos' in strlow or 'web_of_science' in strlow or 'webofscience' in strlow:
        return 'WoS'
    else:
        return string



if __name__ == '__main__':
    maindir = 'C:/Users/Roberto/Dropbox/Quarentena/CACD/Review/Searches/'
    capture = '_PARSE'
    diffdir = '4_NOVO'
    papers = Papers(glob.glob(maindir+diffdir+'/**/*'+capture+'.csv', recursive=True))
    papers.export(diffdir+'.tsv', shortensource=True)

    
    '''
    novoall = pd.read_csv('4_NOVO_all.tsv', sep='\t')
    novotak = pd.read_csv('4_NOVO_tak.tsv', sep='\t')
    diff = novoall[~novoall['hash'].isin(novotak['hash'])]
    diff.to_csv("diff.tsv", sep="\t", index=False)
    
    

    ### CUIDADO COM NOMES
    novoall = pd.read_csv('4_NOVO.tsv', sep='\t')
    diff = pd.read_csv('diff.tsv', sep='\t')
    diff = diff[['hash', 'info']]
    diffdict = dict(zip(diff['hash'], diff['info']))
    for key, value in diffdict.items():
        novoall.loc[novoall['hash'] == key, 'info'] = value
    novoall.to_csv("4_NOVO_updated.tsv", sep="\t", index=False)
    '''