# n4o-graph-api

> API and minimal web interface to [NFDI4Objects Knowledge Graph](https://nfdi4objects.github.io/n4o-graph/).

This repository implements public web APIs to the NFDI4Objects Knowledge Graph. The Knowledge Graph internally consists of an RDF Triple Store and a Labeled Property Graph. These databases can be queried [with SPARQL(#sparql-api) and [with Cypher](#property-graph-api) respectively using the API endpoints provided by this web application. For background information see the [Knowledge Graph Manual](https://nfdi4objects.github.io/n4o-graph/) (in German).

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [SPARQL API](#sparql-api)
  - [Property Graph API](#property-graph-api)
- [Development](#development)
- [License](#license)

## Installation

Required Python modules are listed in `requirements.txt`. Use [deployment method of your choice](https://flask.palletsprojects.com/en/2.0.x/deploying/#self-hosted-options). The application must be configured first.

## Configuration

A local file `config.yaml` is needed with configuration. Use this as boilerplate:

~~~yaml
cypher: 
  uri: "bolt://localhost:7687"
  user: ""
  password: "" 
  timeout: 30
  examples:
    - name: Get some people
      query: "MATCH (n:E21_Person) RETURN n LIMIT 10"
    - name: List all classes (= node labels)
      query: "MATCH (n)\n RETURN distinct labels(n) AS classes, count(*) AS count"
sparql:
  endpoint: "https://dbpedia.org/sparql"
  examples:
    - name: List all classes
      query: |
        SELECT DISTINCT ?class WHERE { [] a ?class }
    - name: Get number of triples
      query: |
        SELECT (COUNT(*) as ?triples) 
        WHERE { ?s ?p ?o } 
    - name: List all named graphs with metadata
      query: |
        PREFIX dct: <http://purl.org/dc/terms/>
        SELECT DISTINCT ?graph ?title ?source ?issued
        WHERE {
          GRAPH ?graph { }
          OPTIONAL { ?graph dct:title ?title }
          OPTIONAL { ?graph dct:source ?source }  
          OPTIONAL { ?graph dct:issued ?issued }
        }
~~~

Make sure the Neo4j (or compatible) database is read-only because this application does not guarantee to filter out write queries!

## Usage

### SPARQL API

This webservice implements [SPARQL query API](https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-operation) at `/api/sparl`. The query is transformed to a POST request and passed to the backend SPARQL endpoint.

### Property Graph API

The Property Graph API at `/api/cypher` expects a HTTP GET query parameter `query` with a Cypher query or a HTTP POST request with a Cypher query as request body. The return format is a (possibly empty) JSON array of result objects. On failure, an error object is returned. Each response objects is maps query variables to values. Each value is one of:

- number, string, boolean, or null
- array of values
- [PG-JSONL](https://pg-format.github.io/specification/#pg-json) node or edge object for nodes and edges
- [PG-JSON](https://pg-format.github.io/specification/#pg-jsonl) graph object for pathes

The following examples use n4o-graph-apis application running at <https://graph.gbv.de/> for illustration. This URL will be changed! Use base URL
<http://localhost:8000/> for testing a local installation.

#### Query with Python

```python
import requests
import json

api = "https://graph.gbv.de/api/cypher"
query = "MATCH (m:E16_Measurement) RETURN m LIMIT 2"
results = requests.get(api, { "query": query }).json()
```

#### Query with JavaScript

```js
const api = "https://graph.gbv.de/api/cypher"
const query = "MATCH (m:E16_Measurement) RETURN m LIMIT 2"
results = await fetch(api, { query }).then(res => res.json())
```

#### Query with curl

The Cypher query must be URL-escaped, this is done by using argument [--data-urlencode](https://curl.se/docs/manpage.html#--data-urlencode):

```sh
curl -G https://graph.gbv.de/api/cypher --data-urlencode 'query=MATCH (m:E16_Measurement) RETURN m LIMIT 2'
```

The Cypher query can also be passed from a file:

```sh
curl -G https://graph.gbv.de/api/cypher --data-urlencode 'query@queryfile.cypher'
```

## Development

To locally run the application first install required Python dependencies with virtualenv:

~~~sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
~~~

Then locally run for testing:

~~~sh
python app.py --help
~~~

Please run `make lint` to detect Python coding style violations and `make fix` to fix some of these violations.

## License

MIT License

