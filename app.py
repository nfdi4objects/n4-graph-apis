import json
import re
import sys
import os
from flask import Flask, render_template, request, make_response, send_from_directory
from waitress import serve
import argparse
import mimeparse
import traceback
from rdflib import URIRef
from datetime import datetime

from app import CypherBackend, SparqlProxy, ApiError, Config


# TODO: move to library file
def file_info(path, name):
    stat = os.stat(os.path.join(path, name))
    return {
        "name": name,
        "time": datetime.fromtimestamp(stat.st_mtime),
        "size": stat.st_size
    }


def jsonify(data, status=200, indent=3, sort_keys=False):
    response = make_response(json.dumps(
        data, indent=indent, sort_keys=sort_keys))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['mimetype'] = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.status_code = status
    return response


app = Flask(__name__)


def render(template, **vars):
    # TODO: better title?
    title = template.split(".")[0]
    return render_template(template, title=title, githash=app.config["githash"], **vars)


@app.errorhandler(ApiError)
def handle_api_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status
    return response


@app.errorhandler(Exception)
def handle_exception(error):
    if app.config["debug"]:
        print(traceback.format_exc())
    if hasattr(error, 'message'):
        message = error.message
    else:
        message = str(error)
    return handle_api_error(ApiError(message))


@app.route('/')
def index():
    return render('index.html')


@app.route('/license')
def license():
    return render('license.html')


@app.context_processor
def utility_processor():
    return dict(URIRef=URIRef)


rdf_formats = {
    'application/x-turtle': 'turtle',
    'text/turtle': 'turtle',
    'application/rdf+xml': 'xml',
    'application/trix': 'trix',
    'application/n-quads': 'nquads',
    'application/n-triples': 'nt',
    'text/n-triples': 'nt',
    'text/rdf+nt': 'nt',
    'application/n3': 'n3',
    'text/n3': 'n3',
    'text/rdf+n3': 'n3'
}


@app.route('/terminology')
@app.route('/terminology/')
def terminology():
    # TODO: server RDF as well
    return render('terminologies.html')


@app.route('/repository')
@app.route('/repository/')
def repository():
    return render('repositories.html')


@app.route('/collection', defaults={'id': None, 'path': None})
@app.route('/collection/', defaults={'id': None, 'path': None})
@app.route('/collection/<int:id>', defaults={'path': None})
@app.route('/collection/<int:id>/', defaults={'path': ""})
@app.route('/collection/<int:id>/<path:path>')
def collection(id, path):
    if not id:
        # TODO: server RDF as well
        return render('collections.html')

    format = request.args.get("format")
    html_wanted = "html" in request.headers["Accept"] or format == "html"

    stage_base = app.config.get("stage")
    stage_path = os.path.join(stage_base, str(id)) if stage_base else None
    if path is not None:
        if stage_base:
            if path == "":
                files = map(lambda f: file_info(stage_path, f),
                            os.listdir(stage_path))
                return render('import.html', files=files, id=id)
            else:
                return send_from_directory(stage_path, path)
        # TODO: more beautiful message
        return "Not found!"

    uri = "https://graph.nfdi4objects.net/collection/" + str(id)
    graph = app.config["sparql-proxy"].request(
        "DESCRIBE <" + uri + ">",
        {"named-graph-uri": "https://graph.nfdi4objects.net/collection/"})

    if html_wanted:
        if len(graph) > 0:
            stage = "./" + \
                str(id) + "/" if stage_path and os.path.isdir(stage_path) else None
            return render('collection.html', uri=uri, graph=graph, stage=stage)
        else:
            return render('collection.html', uri=uri, graph=None), 404
    else:
        mimetype = "text/plain"
        if format in set(rdf_formats.values()):
            mimetype = [
                type for type in rdf_formats if rdf_formats[type] == format][0]
        else:
            accept = request.headers.get("Accept")
            types = list(rdf_formats.keys())
            mimetype = mimeparse.best_match(types, accept)
            if mimetype in rdf_formats:
                format = rdf_formats[mimetype]
            else:
                format = "turtle"
                mimetype = "text/turtle"

        print("Format, mimetype")
        print(format, mimetype)

        response = make_response("Not found", 404)
        response.mimetype = "text/plain"
        if len(graph) > 0:
            # TODO: add known namespaces for pretty Turtle
            response = make_response(graph.serialize(format=format), 200)
            response.mimetype = mimetype
        return response


# Detect write queries the simple way. This also block some valid read-queries.
def isAllowedCypherQuery(cmd: str) -> bool:
    return re.search('merge|create|delete|set', cmd, re.IGNORECASE) is None


@app.route('/api/cypher', methods=('GET', 'POST'))
def cypher_api():
    query = ''
    if 'query' in request.args:     # GET
        query = request.args.get('query')
    elif request.data:              # POST
        query = request.data.decode('UTF-8')

    if query:
        if isAllowedCypherQuery(query):
            answer = app.config["cypher-backend"].execute(query)
        else:
            raise ApiError("Cypher query is not allowed!", 403)
    else:
        raise ApiError('missing or empty "query" parameter', 400)

    return jsonify(answer)


@app.route('/api/sparql', methods=('GET', 'POST'))
def sparql_api():
    return app.config["sparql-proxy"].proxyRequest(request)


@app.route('/cypher')
def cypher_form():
    return render('cypher.html')


@app.route('/sparql')
def sparql_form():
    return render('sparql.html', **config["sparql"])


@app.route('/tools')
def tools():
    return render('tools.html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int,
                        default=8000, help="Server port")
    parser.add_argument(
        '-w', '--wsgi', action=argparse.BooleanOptionalAction, help="Use WSGI server")
    parser.add_argument('-c', '--config', type=str,
                        default="config.yaml", help="Config file")
    parser.add_argument('-d', '--debug', action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    try:
        config = Config(args.config, args.debug)
    except Exception as err:
        print(str(err), file=sys.stderr)
        sys.exit(1)

    for key in config.keys():
        app.config[key] = config[key]

    app.config["sparql-proxy"] = SparqlProxy(
        config["sparql"]["endpoint"], config["debug"])
    if "cypher" in config:
        app.config["cypher-backend"] = CypherBackend(config['cypher'])

    opts = {"port": args.port, "debug": config["debug"]}
    if args.wsgi:
        serve(app, host="0.0.0.0", **opts)
    else:
        app.run(host="0.0.0.0", **opts)
