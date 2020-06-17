#import yaml
import flask
from flask import request, jsonify, request, send_from_directory
import concurrent.futures
import cx_Oracle
import yaml
import time

app = flask.Flask(__name__,
                  static_url_path='',
                  static_folder=''
                  )
app.config['DEBUG'] = True
app.config['ENV'] = 'development'
app.config['JSON_KEYS_SORT'] = False

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
        print(f'--> START - Calling {f.__name__}({signature})')
        start_time = time.perf_counter()
        retVal = f(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f'--> END   - {f.__name__} - in {run_time:.4f} secs')
        #print(f'--> END   - {f.__name__!r} returned {retVal!r} - in {run_time:.4f} secs')
        return retVal
    return _perf

####################################################################################################################

@perf
class TRex:
    def __init__(self, env, key, value):
        print("Inside Trex constructor")
        self._env = env
        self._key = key
        self._value = value

        self._svc_order_id = ""
        self._service_id = ""
        self._trail_id = 0
        self._db_conn = {}
        self._db_keys = {}
        self._db_keys['DEPTNO'] = "10,20,30,40"
        self._db_keys['GRADE'] = "1,2,3,4,5"
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
    def _fetch_records_per_table(self, cur, p_table_name, p_key, p_table_wclause):
        try:
            if p_table_wclause is None:
                query = "SELECT * FROM {} WHERE {} in ({})".format(p_table_name,
                                                                   p_key,
                                                                   self._db_keys[p_key] if p_key in self._db_keys else None)
            else:
                query = "SELECT * FROM {} {} ({})".format(p_table_name,
                                                          p_table_wclause,
                                                          self._db_keys[p_key] if p_key in self._db_keys else None)

            print('Query is {}'.format(query))
            cur.execute(query)
            print([row[0] for row in cur.description])
            records = [[row[0] for row in cur.description]]

            for itr in cur:
                records.append(list(itr))

            print(records)
            print(cur.description)

            return records

        except cx_Oracle.Error as error:
            print(error)

    def _close_all_db_connections(self):
        try:
            for key, value in self._db_conn.items():
                print(f'Closing the DB connection for {key}')
                value.close()
        except cx_Oracle.Error as error:
            print(error)

    def _open_db_connection(self, list_of_domain_conn):
        try:
            domain_name, db_conn = list_of_domain_conn
            print("Inside ", list_of_domain_conn)

            connection = cx_Oracle.connect(db_conn)
            print('DB Connection = {}'.format(db_conn))

            self._db_conn[domain_name] = connection
            print(self._db_conn)
        except cx_Oracle.Error as error:
            print(error)

    @perf
    def _open_db_connections_loop(self):
        try:
            """
            You can let Python automatically closes the connection when the reference to the connection goes out of scope by using the `with` block:
            """
            with open(r'config.yaml') as file:
                documents = yaml.full_load(file)

                if self._env in documents:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                        executor.map(self._open_db_connection, list(documents[self._env].items()))

        except Exception as error:
            print(error)

    @perf
    def _fetch_records_per_domain(self, domain_name, list_tables):
        try:
            if domain_name in self._db_conn:
                connection = self._db_conn[domain_name]
                # show the version of the Oracle Database
                print(connection.version)
                cur = connection.cursor()

                for itrTables in list_tables:
                    table_name = itrTables['NAME'] if 'NAME' in itrTables else None
                    table_key = itrTables['KEY'] if 'KEY' in itrTables else None
                    table_wclause = itrTables['EXPLICIT_WCLAUSE'] if 'EXPLICIT_WCLAUSE' in itrTables else None

                    print('Table name is {}'.format(table_name))
                    print('Table key is {}'.format(table_key))
                    print('Table wClause is {}'.format(table_wclause))

                    db_results = self._fetch_records_per_table(cur, table_name, table_key, table_wclause)
                    if domain_name not in self._results:
                        self._results[domain_name] = {}

                    self._results[domain_name][table_name] = db_results

                print(self._results)

        except cx_Oracle.Error as error:
            print(error)

    @perf
    def processAPI(self):

        self._open_db_connections_loop()

        with open(r'tables.yaml') as file:
            documents = yaml.full_load(file)

            if 'domains' in documents:
                for itrDomains in documents['domains']:
                    domain_name = itrDomains['name'] if 'name' in itrDomains else None
                    print('Domain name is {}'.format(domain_name))
                    if 'tables' in itrDomains:
                        self._fetch_records_per_domain(domain_name, itrDomains['tables'])

        self._close_all_db_connections()


####################################################################################################################

@perf
@app.route('/', methods=['GET'])
def root():
    print('Entering root')
    return app.send_static_file('index.html')

# TODO - Try making this a json input rather than a query parameter
@perf
@app.route('/t-rex/api/query', methods=['GET'])
def query():
    #print_request(request)

    ####################################################################################################################
    print('Is json Request: {}'.format(request.is_json))
    try:
        if request.args:
            p_env = request.args['ENV'] if 'ENV' in request.args else 'None'
            p_key = request.args['KEY'] if 'KEY' in request.args else 'None'
            p_value = request.args['VALUE'] if 'VALUE' in request.args else 'None'

        print('type(p_env) = {} - value = {}'.format(type(p_env), p_env) )
        print('type(p_key) = {} - value = {}'.format(type(p_key), p_key))
        print('type(p_value) = {} - value = {}'.format(type(p_value), p_value))

        if p_env == 'None' or p_key == 'None' or p_value == 'None' :
            ## TODO - see if we can comeup with an exception class and properly passon the message. currently, status code is missing
            ## https://flask.palletsprojects.com/en/1.1.x/patterns/apierrors/
            raise Exception('Invalid Parameters')

    ####################################################################################################################

        objTRex = TRex(p_env, p_key, p_value)
        print(jsonify(objTRex.results()))
        print(objTRex.results())
        print(objTRex)
        print(objTRex.__dict__)  ## This is also an alternative to use rather than overriding __str__
        objTRex.processAPI()

    ####################################################################################################################

    except Exception as e:
        print('Error: {}'.format(e))
        raise jsonify('Error: {}'.format(e))
    else:
        print('There is NO exception')

    return jsonify(objTRex.results())

def print_request(request):
    host = request.host
    print(f"host: {host}")

    host_url = request.host_url
    print(f"host_url: {host_url}")

    path = request.path
    print(f"path: {path}")

    full_path = request.full_path
    print(f"full_path: {path}")

    url = request.url
    print(f"url: {url}")

    base_url = request.base_url
    print(f"base_url: {base_url}")

    url_root = request.url_root
    print(f"url_root: {url_root}")

    headers = request.headers
    print(headers)

def main():
    print("Hello!")
    app.config["DEBUG"] = True

if __name__ == "__main__": main()

app.run()