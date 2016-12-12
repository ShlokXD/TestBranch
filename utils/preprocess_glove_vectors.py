import numpy as np



# Parameters
ROOT_PATH = '/media/HDD_2TB/DATASETS/'
base_path = ROOT_PATH +'cnn_polarity/DATA/'
vectors_path = base_path + 'glove.42B.300d.txt'
dest_file = 'glove_300'

def glove2npy(glove_path, base_path_save, dest_file):

    vecs_dict = dict()
    print "Loading vectors from %s"%(glove_path)

    glove_vectors = [x[:-1] for x in open(glove_path).readlines()]
    n_vecs = len(glove_vectors)
    print "Found %d vectors in %s"%(n_vecs, glove_path)
    i = 0
    for vector in glove_vectors:
        v = vector.split()
        word = v[0]
        vec = np.asarray(v[1:], dtype='float32')
        vecs_dict[word] = vec
        i += 1
        if i % 1000 == 0:
            print "Processed",i,"vectors (",100*float(i)/n_vecs,"%)\r",
    print
    # Store dict
    print "Saving word vectors in %s" % (base_path_save +'/' + dest_file + '.npy')
    np.save(base_path_save + '/' + dest_file + '.npy', vecs_dict)
    print
if __name__ == "__main__":
    glove2npy(vectors_path, base_path, dest_file)
