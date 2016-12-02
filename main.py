import logging
from timeit import default_timer as timer

from config import load_parameters
from data_engine.prepare_data import build_dataset
from model_zoo import Text_Classification_Model
from keras_wrapper.cnn_model import loadModel

import utils
import sys
import ast
logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logger = logging.getLogger(__name__)


def train_model(params):
    """
        Main function
    """

    if(params['RELOAD'] > 0):
        logging.info('Resuming training.')

    check_params(params)

    ########### Load data
    dataset = build_dataset(params)
    params['INPUT_VOCABULARY_SIZE'] = dataset.vocabulary_len[params['INPUTS_IDS_DATASET'][0]]
    ###########

    ########### Build model
    if(params['RELOAD'] == 0): # build new model
        text_class_model = Text_Classification_Model(params, type=params['MODEL_TYPE'], verbose=params['VERBOSE'],
                                              model_name=params['MODEL_NAME'], vocabularies=dataset.vocabulary,
                                              store_path=params['STORE_PATH'])

        # Define the inputs and outputs mapping from our Dataset instance to our model
        inputMapping = dict()
        for i, id_in in enumerate(params['INPUTS_IDS_DATASET']):
            pos_source = dataset.ids_inputs.index(id_in)
            id_dest = text_class_model.ids_inputs[i]
            inputMapping[id_dest] = pos_source
        text_class_model.setInputsMapping(inputMapping)

        outputMapping = dict()
        for i, id_out in enumerate(params['OUTPUTS_IDS_DATASET']):
            pos_target = dataset.ids_outputs.index(id_out)
            id_dest = text_class_model.ids_outputs[i]
            outputMapping[id_dest] = pos_target
        text_class_model.setOutputsMapping(outputMapping)

    else: # resume from previously trained model
        text_class_model = loadModel(params['STORE_PATH'], params['RELOAD'])
        text_class_model.setOptimizer()
    ###########


    ########### Callbacks
    callbacks = buildCallbacks(params, text_class_model, dataset)
    ###########


    ########### Training
    total_start_time = timer()

    logger.debug('Starting training!')
    training_params = {'n_epochs': params['MAX_EPOCH'], 'batch_size': params['BATCH_SIZE'],
                       'homogeneous_batches':params['HOMOGENEOUS_BATCHES'],
                       'shuffle': False if 'train' in params['EVAL_ON_SETS'] else True,
                       'epochs_for_save': params['EPOCHS_FOR_SAVE'], 'verbose': params['VERBOSE'],
                       'eval_on_sets': params['EVAL_ON_SETS_KERAS'], 'n_parallel_loaders': params['PARALLEL_LOADERS'],
                       'extra_callbacks': callbacks, 'reload_epoch': params['RELOAD'],
                       'data_augmentation': params['DATA_AUGMENTATION']}
    text_class_model.trainNet(dataset, training_params)


    total_end_time = timer()
    time_difference = total_end_time - total_start_time
    logging.info('In total is {0:.2f}s = {1:.2f}m'.format(time_difference, time_difference / 60.0))
    ###########



def apply_Clas_model(params):
    """
        Function for using a previously trained model for sampling.
    """

    ########### Load data
    dataset = build_dataset(params)
    params['INPUT_VOCABULARY_SIZE'] = dataset.vocabulary_len[params['INPUTS_IDS_DATASET'][0]]
    params['OUTPUT_VOCABULARY_SIZE'] = dataset.vocabulary_len[params['OUTPUTS_IDS_DATASET'][0]]
    ###########


    ########### Load model
    text_class_model = loadModel(params['STORE_PATH'], params['RELOAD'])
    text_class_model.setOptimizer()
    ###########


    ########### Apply sampling
    extra_vars = dict()
    extra_vars['tokenize_f'] = eval('dataset.' + params['TOKENIZATION_METHOD'])
    for s in params["EVAL_ON_SETS"]:

        # Apply model predictions
        params_prediction = {'batch_size': params['BATCH_SIZE'],
                             'n_parallel_loaders': params['PARALLEL_LOADERS'], 'predict_on_sets': [s]}

        predictions = text_class_model.predictNet(dataset, params_prediction)[s]

        # Store result
        filepath = text_class_model.model_path+'/'+ s +'.pred' # results file
        if params['SAMPLING_SAVE_MODE'] == 'list':
            utils.read_write.list2file(filepath, predictions)
        else:
            raise Exception, 'Only "list" is allowed in "SAMPLING_SAVE_MODE"'


        # Evaluate if any metric in params['METRICS']
        for metric in params['METRICS']:
            logging.info('Evaluating on metric ' + metric)
            filepath = text_class_model.model_path + '/' + s + '_sampling.' + metric  # results file

            # Evaluate on the chosen metric
            extra_vars[s] = dict()
            extra_vars[s]['references'] = dataset.extra_variables[s][params['OUTPUTS_IDS_DATASET'][0]]
            metrics = utils.evaluation.select[metric](
                pred_list=predictions,
                verbose=1,
                extra_vars=extra_vars,
                split=s)

            # Print results to file
            with open(filepath, 'w') as f:
                header = ''
                line = ''
                for metric_ in sorted(metrics):
                    value = metrics[metric_]
                    header += metric_ + ','
                    line += str(value) + ','
                f.write(header + '\n')
                f.write(line + '\n')
            logging.info('Done evaluating on metric ' + metric)


def buildCallbacks(params, model, dataset):
    """
        Builds the selected set of callbacks run during the training of the model
    """

    callbacks = []

    if params['METRICS']:
        # Evaluate training
        extra_vars = {'n_parallel_loaders': params['PARALLEL_LOADERS']}
        for s in params['EVAL_ON_SETS']:
            extra_vars[s] = dict()
            extra_vars[s]['references'] = dataset.extra_variables[s][params['OUTPUTS_IDS_DATASET'][0]]
            if dataset.dic_classes.get(params['OUTPUTS_IDS_DATASET'][0]):
                extra_vars['n_classes'] = len(dataset.dic_classes[params['OUTPUTS_IDS_DATASET'][0]])

        if params['EVAL_EACH_EPOCHS']:
            callback_metric = utils.callbacks.PrintPerformanceMetricOnEpochEnd(model, dataset,
                                                           gt_id=params['OUTPUTS_IDS_DATASET'][0],
                                                           metric_name=params['METRICS'],
                                                           set_name=params['EVAL_ON_SETS'],
                                                           batch_size=params['BATCH_SIZE'],
                                                           each_n_epochs=params['EVAL_EACH'],
                                                           extra_vars=extra_vars,
                                                           reload_epoch=params['RELOAD'],
                                                           save_path=model.model_path,
                                                           start_eval_on_epoch=params['START_EVAL_ON_EPOCH'],
                                                           write_samples=True,
                                                           write_type=params['SAMPLING_SAVE_MODE'],
                                                           early_stop=params['EARLY_STOP'],
                                                           patience=params['PATIENCE'],
                                                           stop_metric=params['STOP_METRIC'],
                                                           verbose=params['VERBOSE'])

        else:
            callback_metric = utils.callbacks.PrintPerformanceMetricEachNUpdates(model, dataset,
                                                           gt_id=params['OUTPUTS_IDS_DATASET'][0],
                                                           metric_name=params['METRICS'],
                                                           set_name=params['EVAL_ON_SETS'],
                                                           batch_size=params['BATCH_SIZE'],
                                                           each_n_updates=params['EVAL_EACH'],
                                                           extra_vars=extra_vars,
                                                           reload_epoch=params['RELOAD'],
                                                           save_path=model.model_path,
                                                           start_eval_on_epoch=params['START_EVAL_ON_EPOCH'],
                                                           write_samples=True,
                                                           write_type=params['SAMPLING_SAVE_MODE'],
                                                           early_stop=params['EARLY_STOP'],
                                                           patience=params['PATIENCE'],
                                                           stop_metric=params['STOP_METRIC'],
                                                           verbose=params['VERBOSE'])
        callbacks.append(callback_metric)

    return callbacks



def check_params(params):
    if 'Glove' in params['MODEL_TYPE'] and params['GLOVE_VECTORS'] is None:
        logger.warning("You set a model that uses pretrained word vectors but you didn't specify a vector file."
                       "We'll train WITHOUT pretrained embeddings!")
    if params["USE_DROPOUT"] and params["USE_BATCH_NORMALIZATION"]:
        logger.warning("It's not recommended to use both dropout and batch normalization")

if __name__ == "__main__":

    params = load_parameters()

    try:
        for arg in sys.argv[1:]:
            k, v = arg.split('=')
            params[k] = ast.literal_eval(v)
    except:
        print 'Overwritten arguments must have the form key=Value'
        exit(1)

    if(params['MODE'] == 'training'):
        logging.info('Running training.')
        train_model(params)
    elif(params['MODE'] == 'sampling'):
        logging.info('Running sampling.')
        apply_Clas_model(params)

    logging.info('Done!')
