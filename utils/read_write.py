"""
Reads from input file or writes to the output file.

Author: Mateusz Malinowski
Email: mmalinow@mpi-inf.mpg.de

Modified by: Marc Bola\~nos
             \'Alvaro Peris
"""

import json
import numpy as np
import os
###
# Helpers
###
def _dirac(pred, gt):
    return int(pred==gt)

###
# Main functions
###
def file2list(filepath):
    with open(filepath,'r') as f:
        lines =[k for k in 
            [k.strip() for k in f.readlines()] 
        if len(k) > 0]

    return lines

def numpy2file(filepath, mylist, permission='w'):
    mylist = np.asarray(mylist)
    with open(filepath, permission) as f:
        np.save(f, mylist)

def listoflists2file(filepath,mylist,permission='w'):
    mylist = [str(sublist) for sublist in mylist]
    mylist = '\n'.join(str(mylist))
    if type(mylist[0]) is unicode:
        mylist=mylist.encode('utf-8')
    with open(filepath,permission) as f:
        f.writelines(mylist)

        
def list2file(filepath,mylist,permission='w'):
    mylist='\n'.join(str(mylist))
    if type(mylist[0]) is unicode:
        mylist=mylist.encode('utf-8')
    with open(filepath,permission) as f:
        f.writelines(mylist)

        
def list2vqa(filepath,mylist,qids,permission='w'):
    res = []
    for ans, qst in zip(mylist, qids):
        res.append({'answer': ans, 'question_id': int(qst)})
    with open(filepath,permission) as f:
        json.dump(res, f)
        

def dump_hdf5_simple(filepath, dataset_name, data):
    import h5py
    h5f = h5py.File(filepath, 'w')
    h5f.create_dataset(dataset_name, data=data)
    h5f.close()


def load_hdf5_simple(filepath, dataset_name):
    import h5py
    h5f = h5py.File(filepath, 'r')
    tmp = h5f[dataset_name][:]
    h5f.close()
    return tmp


def pickle_model(
        path, 
        model, 
        word2index_x,
        word2index_y,
        index2word_x,
        index2word_y):
    import sys
    import cPickle as pickle
    modifier=10
    tmp = sys.getrecursionlimit()
    sys.setrecursionlimit(tmp*modifier)
    with open(path, 'wb') as f:
        p_dict = {'model':model,
                'word2index_x':word2index_x,
                'word2index_y':word2index_y,
                'index2word_x':index2word_x,
                'index2word_y':index2word_y}
        pickle.dump(p_dict, f, protocol=2)
    sys.setrecursionlimit(tmp)


def unpickle_model(path):
    import cPickle as pickle
    with open(path, 'rb') as f:
        model = pickle.load(f)['model']
    return model


def unpickle_vocabulary(path):
    import cPickle as pickle
    p_dict = {}
    with open(path, 'rb') as f:
        pickle_load = pickle.load(f)
        p_dict['word2index_x'] = pickle_load['word2index_x']
        p_dict['word2index_y'] = pickle_load['word2index_y']
        p_dict['index2word_x'] = pickle_load['index2word_x']
        p_dict['index2word_y'] = pickle_load['index2word_y']
    return p_dict


def unpickle_data_provider(path):
    import cPickle as pickle
    with open(path, 'rb') as f:
        dp = pickle.load(f)['data_provider']
    return dp


def model_to_json(path, model):
    """
    Saves model as a json file under the path.
    """
    import json
    json_model = model.to_json()
    with open(path, 'w') as f:
        json.dump(json_model, f)


def json_to_model(path):
    """
    Loads a model from the json file.
    """
    import json
    from keras.models import model_from_json
    with open(path, 'r') as f:
        json_model = json.load(f)
    model = model_from_json(json_model)
    return model


def model_to_text(filepath, model_added):
    """
    Save the model to text file.
    """
    pass


def text_to_model(filepath):
    """
    Loads the model from the text file.
    """
    pass


def dict2file(mydict, path, title=None):
    """
    In:
        mydict - dictionary to save in a file
        path - path where acc_dict is stored
        title - the first sentence in the file;
            useful if we write many dictionaries
            into the same file
    """
    tmp = [str(x[0])+':'+str(x[1]) for x in mydict.items()]
    if title is not None:
        output_list = [title]
        output_list.extend(tmp)
    else:
        output_list = tmp
    list2file(path, output_list, 'a')


def create_dir_if_not_exists(directory):
    """
    Creates a directory if it doen't exist

    :param directory: Directory to create
    :return: None
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

