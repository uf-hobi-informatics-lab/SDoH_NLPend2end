#create training and test bio for NER
import sys
sys.path.append("../ClinicalTransformerNER/")
sys.path.append("../NLPreprocessing/")
import os
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from sklearn.model_selection import train_test_split
import shutil 
import fileinput
import pandas as pd
from annotation2BIO import generate_BIO, pre_processing, read_annotation_brat, BIOdata_to_file
MIMICIII_PATTERN = "\[\*\*|\*\*\]"

data_dir=sys.argv[1]
#output_name='test'

#data stat
file_ids = set()
enss = []

for fn in Path(data_dir).glob("*.ann"):
    file_ids.add(fn.stem)
    _, ens, _ = read_annotation_brat(fn)
    #print( _)
    enss.extend(ens)
print("test files: ", len(file_ids), list(file_ids)[:5])
print("total test eneitites: ", len(enss))
print("Entities distribution by types:\n", "\n".join([str(c) for c in Counter([each[1] for each in enss]).most_common()]))
# generate bio

file_ids=list(file_ids)
#same process but have train test split as 1:1
train_dev_ids, test_ids = train_test_split(file_ids, train_size=0.62, random_state=13, shuffle=True)#use  1:1 split
print('length of training and test')
len(train_dev_ids), len(test_ids)
train_dev_root = Path('../data/training_set_new')
test_root = Path('../data/test_set_new')
ents=['Abuse',
 'Alcohol_freq',
 'Alcohol_other',
 'Alcohol_type',
 'Alcohol_use',
 'Drug_freq',
 'Drug_other',
 'Drug_type',
 'Drug_use',
 'Education',
 'Employment_location',
 'Employment_other',
 'Employment_status',
 'Ethnicity',
 'Financial_constrain',
 'Gender',
 'Gender_status',
 'Language',
 'Living_Condition',
 'Living_supply',
 'Marital_status',
 'Occupation',
 'Partner',
 'Physical_act',
 'Protection',
 'Race',
 'SDoH_other',
 'Sdoh_freq',
 'Sdoh_status',
 'Sex_act',
 'Smoking_freq_other',
 'Smoking_freq_ppd',
 'Smoking_freq_py',
 'Smoking_freq_qy',
 'Smoking_freq_sy',
 'Smoking_type',
 'Social_cohesion',
 'Substance_use_status',
 'Tobacco_use',
 'Transportation']
#create notes file
Path(train_dev_root).mkdir(parents=True, exist_ok=True)
Path(test_root).mkdir(parents=True, exist_ok=True)
train_root=Path(data_dir)
#copy file to train and test
for fid in train_dev_ids:
    txt_fn = train_root / (fid + ".txt")
    ann_fn = train_root / (fid + ".ann")
    txt_fn1 = train_dev_root / (fid + ".txt")
    ann_fn1 = train_dev_root / (fid + ".ann")
    shutil.copyfile(txt_fn, txt_fn1)
    with open(ann_fn) as f:
        lines=f.readlines()
        lines_used=[]
        i=1
        for line in lines:
            if line[0]=='T':
                entity_name=line.split('\t',2)[1].split(' ',1)[0]
                entity_num=line.split('\t',2)[1].split(' ',1)[1]
                #print(entity_name)
                if entity_name in ents:
                    lines_used = lines_used+['T'+str(i)+'\t'+entity_name+' '+entity_num+'\t'+line.split('\t',2)[2]]
                    i+=1
            if line[0]=='R':
                lines_used = lines_used+[line]
    with open(ann_fn1,'w') as f1:
        f1.writelines(lines_used)
    
#     shutil.copyfile(ann_fn, ann_fn1)
for fid in test_ids:
    txt_fn = train_root / (fid + ".txt")
    ann_fn = train_root / (fid + ".ann")
    txt_fn1 = test_root / (fid + ".txt")
    ann_fn1 = test_root / (fid + ".ann")
    shutil.copyfile(txt_fn, txt_fn1)
    with open(ann_fn) as f:
        lines=f.readlines()
        lines_used=[]
        i=1
        for line in lines:
            if line[0]=='T':
                entity_name=line.split('\t',2)[1].split(' ',1)[0]
                entity_num=line.split('\t',2)[1].split(' ',1)[1]
                #print(entity_name)
                if entity_name in ents:
                    lines_used = lines_used+['T'+str(i)+'\t'+entity_name+' '+entity_num+'\t'+line.split('\t',2)[2]]
                    i+=1
            if line[0]=='R':
                lines_used = lines_used+[line]
    with open(ann_fn1,'w') as f1:
        f1.writelines(lines_used)
#save the statistics result for training and test
use_ids = set()
enss = []
result_root = Path('../results/')
result_root.mkdir(parents=True, exist_ok=True)
for fn in train_dev_root.glob("*.ann"):
    use_ids.add(fn.stem)
    _, ens, _ = read_annotation_brat(fn)
    enss.extend(ens)
d1=dict(Counter([each[1] for each in enss]))
df=pd.Series(d1).to_frame()
df.to_csv ('../results/train_set_entities.csv', index = True, header=True)
#for test
use_ids = set()
enss = []
for fn in test_root.glob("*.ann"):
    use_ids.add(fn.stem)
    _, ens, _ = read_annotation_brat(fn)
    enss.extend(ens)
d1=dict(Counter([each[1] for each in enss]))
df=pd.Series(d1).to_frame()
df.to_csv ('../results/test_set_entities.csv', index = True, header=True)

#transfore to bio file
train_dev_ids = list(train_dev_ids)
train_ids, dev_ids = train_test_split(train_dev_ids, train_size=0.9, random_state=13, shuffle=True)
test_bio = "../bio/"+'bio_test_new'
training_bio = "../bio/"+'bio_training_new'
output_root1 = Path(test_bio)
output_root2 = Path(training_bio)
output_root1.mkdir(parents=True, exist_ok=True)
output_root2.mkdir(parents=True, exist_ok=True)

for fid in train_dev_ids:
    txt_fn = train_dev_root / (fid + ".txt")
    ann_fn = train_dev_root / (fid + ".ann")
    bio_fn = output_root2 / (fid + ".bio.txt")
    
    txt, sents = pre_processing(txt_fn, deid_pattern=MIMICIII_PATTERN)
    e2idx, entities, rels = read_annotation_brat(ann_fn)
    nsents, sent_bound = generate_BIO(sents, entities, file_id=fid, no_overlap=False)
    #print(nsents)
    #print(bio_fn)
    #break
    BIOdata_to_file(bio_fn, nsents)
# train
with open(training_bio+"/train.txt", "w") as f:
    for fid in train_ids:
        f.writelines(fileinput.input(output_root2 / (fid + ".bio.txt")))
    fileinput.close()
        
# dev
with open(training_bio+"/dev.txt", "w") as f:
    for fid in dev_ids:
        f.writelines(fileinput.input(output_root2 / (fid + ".bio.txt")))
    fileinput.close()

#test
for fn in test_root.glob("*.txt"):
    txt_fn = fn
    bio_fn = output_root1 / (fn.stem + ".bio.txt")
    
    txt, sents = pre_processing(txt_fn, deid_pattern=MIMICIII_PATTERN)
    nsents, sent_bound = generate_BIO(sents, [], file_id=txt_fn, no_overlap=False)
    
    BIOdata_to_file(bio_fn, nsents)
