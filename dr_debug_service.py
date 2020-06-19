#import yaml
import flask
from flask import request, jsonify, request, send_from_directory
import concurrent.futures
import cx_Oracle
import yaml
import time
import logging

app = flask.Flask(__name__,
                  static_url_path='',
                  static_folder=''
                  )
app.config['DEBUG'] = True
app.config['ENV'] = 'development'
app.config['JSON_KEYS_SORT'] = False

logging.basicConfig(level=logging.DEBUG,
                    filemode='a',
                    format='{asctime} - {levelname} - [{funcName}:{lineno}] - {message}',
                    style='{')

"""
http://127.0.0.1:5000/t-rex/api/query?ENV=SIT&KEY=SVCORDER_ID&VALUE=23/%2045
"""

"""
Refer to below link for better reading on decorators
https://realpython.com/primer-on-python-decorators/#simple-decorators
"""
def perf(f):
    def _perf(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        logging.debug('--> START - Calling {}({})'.format(f.__name__, signature))
        start_time = time.perf_counter()
        retVal = f(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        logging.debug('--> END   - {} - in {:.4f} secs'.format(f.__name__, run_time))
        #logging.debug(f'--> END   - {f.__name__!r} returned {retVal!r} - in {run_time:.4f} secs')
        return retVal
    return _perf

####################################################################################################################

@perf
class TRex:
    def __init__(self, env, key, value):
        logging.debug("Inside Trex constructor")
        self._env = env
        self._key = key
        self._value = value

        self._svc_order_id = ""
        self._service_id = ""
        self._trail_id = 0
        self._db_conn = {}
        self._db_keys = {}
        self._db_keys[self._key] = self._value

        self._results = {'env':self._env,
                         'key':self._key,
                         'value':self._value
                         }

    def results(self, results = None):
        if results != None :
            self._results = results

        return self._results

    @perf
    def _load_init_keys(self):
        """
        Place holder function to load other KEY's, based on the given key.
        Database is already opened during this time and the DEFAULT connection can be used for the same
        """
        self._db_keys['DEPTNO'] = "10,20,30,40"
        self._db_keys['GRADE'] = "1,2,3,4,5"


    def _is_open(self, conn):
        try:
            logging.debug(f'Checking connection status')
            return True
        except cx_Oracle.Error as error:
            logging.error(error)

    def _handle_db_connection(self, list_of_domain_conn):
        try:
            domain_name, db_conn = list_of_domain_conn
            logging.debug("Inside {}".format(list_of_domain_conn))

            if domain_name not in self._db_conn:
                logging.debug('DB Connection = {}'.format(db_conn))

                connection = cx_Oracle.connect(db_conn)
                self._db_conn[domain_name] = connection

                logging.debug('Total connections [{}] so far are {}'.format(len(self._db_conn), self._db_conn))

            elif domain_name in self._db_conn:
                if self._is_open(self._db_conn[domain_name]):
                    logging.debug(f'Closing the DB connection for {self._db_conn[domain_name]}')
                    self._db_conn[domain_name].close()
                else:
                    logging.debug(f'DB connection already close for for {self._db_conn[domain_name]}')

                self._db_conn.popitem(domain_name)

        except cx_Oracle.Error as error:
            logging.error(error)

    @perf
    def _handle_db_connections(self):
        try:
            """
            You can let Python automatically closes the connection when the reference to the connection goes out of scope by using the `with` block:
            """
            with open(r'config.yaml') as file:
                documents = yaml.full_load(file)

                if self._env in documents:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                        executor.map(self._handle_db_connection, list(documents[self._env].items()))

        except Exception as error:
            logging.error(error)

    @perf
    def _fetch_records_per_table(self, cur, p_table_name, p_key, p_table_wclause):
        try:
            logging.debug(f'Table name is [{p_table_name}] : kEY is [{p_key}] : wClause is [{p_table_wclause}]')

            if p_table_wclause is None:
                query = "SELECT * FROM {} WHERE {} in ({})".format(p_table_name,
                                                                   p_key,
                                                                   self._db_keys[p_key] if p_key in self._db_keys else None)
            else:
                query = "SELECT * FROM {} {} ({})".format(p_table_name,
                                                          p_table_wclause,
                                                          self._db_keys[p_key] if p_key in self._db_keys else None)

            logging.debug('Query is [{}]'.format(query))
            cur.execute(query)
            logging.debug(f'Columns for {p_table_name} are {[row[0] for row in cur.description]}')
            records = [[row[0] for row in cur.description]]

            for itr in cur:
                records.append(list(itr))

            logging.debug(f'Final Data for {p_table_name} are {records}')

            return records

        except cx_Oracle.Error as error:
            logging.error(error)

    @perf
    def _fetch_records_per_domain(self, domain_name, list_tables):
        try:
            logging.debug('Domain name is {}'.format(domain_name))
            if domain_name in self._db_conn:
                connection = self._db_conn[domain_name]
                # show the version of the Oracle Database
                logging.debug(connection.version)
                cur = connection.cursor()

                for itrTables in list_tables:
                    table_name = itrTables['NAME'] if 'NAME' in itrTables else None
                    table_key = itrTables['KEY'] if 'KEY' in itrTables else None
                    table_wclause = itrTables['EXPLICIT_WCLAUSE'] if 'EXPLICIT_WCLAUSE' in itrTables else None

                    db_results = self._fetch_records_per_table(cur, table_name, table_key, table_wclause)

                    if domain_name not in self._results:
                        self._results[domain_name] = {}

                    self._results[domain_name][table_name] = db_results

        except cx_Oracle.Error as error:
            logging.error(error)

    @perf
    def processAPI(self):
        self._load_init_keys()
        self._handle_db_connections()

        with open(r'tables.yaml') as file:
            documents = yaml.full_load(file)

            if 'domains' in documents:
                for itrDomains in documents['domains']:
                    domain_name = itrDomains['name'] if 'name' in itrDomains else None
                    if 'tables' in itrDomains:
                        self._fetch_records_per_domain(domain_name, itrDomains['tables'])

        self._handle_db_connections()

####################################################################################################################

@perf
@app.route('/', methods=['GET'])
def root():
    logging.debug('Entering root')
    return app.send_static_file('index.html')

# TODO - Try making this a json input rather than a query parameter
@perf
@app.route('/t-rex/api/query', methods=['GET'])
def query():

    ####################################################################################################################
    logging.debug('Is json Request: {}'.format(request.is_json))
    try:
        if request.args:
            p_env = request.args['ENV'] if 'ENV' in request.args else 'None'
            p_key = request.args['KEY'] if 'KEY' in request.args else 'None'
            p_value = request.args['VALUE'] if 'VALUE' in request.args else 'None'

        logging.debug('ENV - type(p_env) = {} - value = {}'.format(type(p_env), p_env) )
        logging.debug('KEY - type(p_key) = {} - value = {}'.format(type(p_key), p_key))
        logging.debug('VALUE - type(p_value) = {} - value = {}'.format(type(p_value), p_value))

        if p_env == 'None' or p_key == 'None' or p_value == 'None' :
            ## TODO - see if we can comeup with an exception class and properly passon the message. currently, status code is missing
            ## https://flask.palletsprojects.com/en/1.1.x/patterns/apierrors/
            raise Exception('Invalid Parameters')

    ####################################################################################################################

        objTRex = TRex(p_env, p_key, p_value)
        objTRex.processAPI()
        logging.debug(f'Final Results are {objTRex.results()}')

    ####################################################################################################################

    except Exception as e:
        logging.error('Error: {}'.format(e))
        raise jsonify('Error: {}'.format(e))
    else:
        logging.debug('There is NO exception')

    return jsonify(objTRex.results())

def main():
    logging.debug("Hello!")
    app.config["DEBUG"] = True

if __name__ == "__main__": main()

app.run()