# from werkzeug.wsgi import wrap_file
import requests
from flask import Response
from .error import ApiError

from SPARQLWrapper import SPARQLWrapper


class SparqlProxy:

    def __init__(self, api, debug=False):
        self.api = api
        self.wrapper = SPARQLWrapper(api)
        self.debug = debug

    def proxyRequest(self, request):

        # see https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-operation
        if request.method == "GET":
            query = request.args.get("query", "")
        elif request.method == "POST":
            content = request.headers.get('content-type')
            if content == "application/sparql-query":
                query = request.data.decode('utf-8')
            elif content == "application/x-www-form-urlencoded":
                query = request.form.get("query", "")
            else:
                raise ApiError("Invalid Content-Type!", 400)
        else:
            raise ApiError("Request method not supported!", 400)

        if query == "":
            raise ApiError("Missing or empty query!", 400)

        params = {}
        for name in ["default-graph-uri", "named-graph-uri"]:
            if name in request.values:
                params[name] = request.values[name]

        # TODO: Set X-Forwarded-For and add more request headers?
        allowed = ["Accept", "Accept-Encoding", "Accept-Language"]
        headers = {k: v for k, v in request.headers.items() if k in allowed}

        headers["Content-Type"] = "application/sparql-query"

        # Some clients and servers disagree about meaning of not setting this server
        if not headers.get("Accept-Encoding"):
            headers["Accept-Encoding"] = ""

        if self.debug:
            print('SPARQL query %s %s: %s' % (params, headers, query))

        res = requests.post(self.api, data=query,
                            params=params, headers=headers, stream=True)

        allowed = ["Content-Type", "Vary",
                   "Cache-Control", "Pragma", "Content-Encoding"]
        headers = {k: v for k, v in res.raw.headers.items() if k in allowed}
        headers['Access-Control-Allow-Origin'] = '*'

        def generate():
            for chunk in res.raw.stream(decode_content=False):
                yield chunk
        out = Response(generate(), headers=headers)
        out.status_code = res.status_code
        return out

    def request(self, query, params={}):
        self.wrapper.setQuery(query)
        for name in ["default-graph-uri", "named-graph-uri"]:
            if name in params:
                self.wrapper.addParameter(name, params[name])
            else:
                self.wrapper.clearParameter(name)
        return self.wrapper.queryAndConvert()

    def alive(self):
        return self.request("ASK WHERE { ?s ?p ?o . }")
