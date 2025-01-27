# n4o-graph-api

> API and minimal web interface to the NFDI4Objects Knowledge Graph (N4O KG)

This repository implements public web APIs to the NFDI4Objects Knowledge Graph,
available at <https://graph.nfdi4objects.net/>. The Knowledge Graph internally
consists of an RDF Triple Store and an experimental Labeled Property Graph.
These databases can be queried [with SPARQL](#sparql-api) and [with
Cypher](#property-graph-api) respectively using the API endpoints provided by
this web application. In addition, collection URIs starting with
<https://graph.nfdi4objects.net/collection/> are served as linked open data
from the triple store.

For background information see the [Knowledge Graph Manual](https://nfdi4objects.github.io/n4o-graph/) (in German).

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [SPARQL API](#sparql-api)
  - [Property Graph API](#property-graph-api)
  - [Linked Open Data](#linked-open-data)
- [Development](#development)
- [License](#license)

## Installation

Requires Python >= 3.5. Python modules are listed in `requirements.txt`. Use [deployment method of your choice](https://flask.palletsprojects.com/en/2.0.x/deploying/#self-hosted-options). The application must be configured first.

## Configuration

A local file `config.yaml` is needed with configuration. Use this as boilerplate:

~~~yaml
sparql:
  endpoint: http://localhost:3030/n4o-rdf-import/
  examples:
    - queries/*.rq
    - name: List all classes
      query: |
        SELECT DISTINCT ?class WHERE { [] a ?class }  examples:
cypher: 
  uri: bolt://localhost:7687
  user: ""
  password: "" 
  timeout: 30
  examples:
    - name: Get some people
      query: "MATCH (n:E21_Person) RETURN n LIMIT 10"
    - name: List all classes (= node labels)
      query: "MATCH (n)\n RETURN distinct labels(n) AS classes, count(*) AS count"
~~~

Make sure the Neo4j (or compatible) database is read-only because this application only applies a simple filter to detect Cypher write queries!

## Usage

### SPARQL API

This webservice implements [SPARQL query API](https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-operation) at `/api/sparl`. The query is transformed to a POST request and passed to the backend SPARQL endpoint.

### Property Graph API

The Property Graph API at `/api/cypher` expects a HTTP GET query parameter `query` with a Cypher query or a HTTP POST request with a Cypher query as request body. The return format is a (possibly empty) JSON array of result objects. On failure, an error object is returned. Each response objects is maps query variables to values. Each value is one of:

- number, string, boolean, or null
- array of values
- [PG-JSONL](https://pg-format.github.io/specification/#pg-json) node or edge object for nodes and edges
- [PG-JSON](https://pg-format.github.io/specification/#pg-jsonl) graph object for pathes

The following examples use n4o-graph-apis application running at <https://graph.nfdi4objects.net/> for illustration. This URL will be changed! Use base URL
<http://localhost:8000/> for testing a local installation.

#### Query with Python

```python
import requests
import json

api = "https://graph.nfdi4objects.net/api/cypher"
query = "MATCH (m:E16_Measurement) RETURN m LIMIT 2"
results = requests.get(api, { "query": query }).json()
```

#### Query with JavaScript

```js
const api = "https://graph.nfdi4objects.net/api/cypher"
const query = "MATCH (m:E16_Measurement) RETURN m LIMIT 2"
results = await fetch(api, { query }).then(res => res.json())
```

#### Query with curl

The Cypher query must be URL-escaped, this is done by using argument [--data-urlencode](https://curl.se/docs/manpage.html#--data-urlencode):

```sh
curl -G https://graph.nfdi4objects.net/api/cypher --data-urlencode 'query=MATCH (m:E16_Measurement) RETURN m LIMIT 2'
```

The Cypher query can also be passed from a file:

```sh
curl -G https://graph.nfdi4objects.net/api/cypher --data-urlencode 'query@queryfile.cypher'
```

### Linked Open Data

Information about collections, each identified by an URI starting with <https://graph.nfdi4objects.net/collection/>, can be retrieved as Linked Open Data (LOD) at path `/collection` in HTML and in RDF serializations. The data is retrieved via [SPARQL API](#sparql-api), so retrieving <https://graph.nfdi4objects.net/collection/1> results in the same data as this SPARQL query from graph <https://graph.nfdi4objects.net/collection/>:

~~~sparql
DESCRIBE <https://graph.nfdi4objects.net/collection/1> FROM <https://graph.nfdi4objects.net/collection/>
~~~

The RDF serialization is determined via HTTP Content Negotiation or with optional query parameter `format`.

Information about terminologies will be made available from <https://graph.nfdi4objects.net/terminology/>.

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

Alternatively run `make .venv` and `make dev`.

Please run `make lint` to detect Python coding style violations and `make fix` to fix some of these violations. Some unit tests are run with `make test`.

To populate the configured knowledge graph databases with actual data, see the source code repository <https://github.com/nfdi4objects/n4o-import>.

## License

MIT License

