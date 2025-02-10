# n4o-graph-api

[![License](https://img.shields.io/github/license/nfdi4objects/n4o-graph-apis.svg)](https://github.com/nfdi4objects/n4o-graph-apis/blob/master/LICENSE)
[![Test](https://github.com/nfdi4objects/n4o-graph-apis/actions/workflows/test.yml/badge.svg)](https://github.com/nfdi4objects/n4o-graph-apis/actions/workflows/test.yml)
[![Docker](https://img.shields.io/badge/Docker-ghcr.io%2Fnfdi4objects%2Fn4o--graph--apis-informational)](https://github.com/nfdi4objects/n4o-graph-apis/pkgs/container/n4o-graph-apis)

> API and minimal web interface to the NFDI4Objects Knowledge Graph (N4O KG)

This repository implements public web APIs to the NFDI4Objects Knowledge Graph,
available at <https://graph.nfdi4objects.net/>. The Knowledge Graph database
can be queried [with SPARQL](#sparql-api) and (if configured) [with
Cypher](#property-graph-api) respectively using the API endpoints provided by
this web application. In addition, collection URIs starting with
<https://graph.nfdi4objects.net/collection/> are served as linked open data and
import reports can be inspected.

For additional information see the [Knowledge Graph Manual](https://nfdi4objects.github.io/n4o-graph/) (in German).

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [SPARQL](#sparql)
  - [Cypher](#cypher)
- [Usage](#usage)
  - [SPARQL API](#sparql-api)
  - [Linked Open Data](#linked-open-data)
  - [Property Graph API](#property-graph-api)
- [Development](#development)
- [License](#license)

## Requirements

Requires Python >= 3.5 to run from sources (Python modules are listed in `requirements.txt`) or Docker.

A backend API (SPARQL and optional Neo4J/Cypher) must be available and [configured](#configuration).

File system read access to the import staging area is required, if enabled via configuration.

## Installation

Use Python flask [deployment method of your choice](https://flask.palletsprojects.com/en/2.0.x/deploying/#self-hosted-options)
or Docker.

Docker images are generated and [published at GitHub](https://github.com/nfdi4objects/n4o-graph-apis/pkgs/container/n4o-graph-apis) from the `main` branch. Alternatively build the image locally [as described below](#development).

There is a [`docker-compose.yml`](docker-compose.yml) for deployment. If needed, it can be configured with a local file `.env`. This is work in progress and details may change!

~~~sh
docker compose create
docker compose start
docker compose stop
~~~~

## Configuration

A local file `config.yaml` is needed with configuration. See [`config.example.yaml`](config.example.yaml) as boilerplate and documentation. Configuration is only loaded once at startup.

### SPARQL

The default configuration expects a SPARL endpoint at <http://localhost:3030/n4o-rdf-import/>. This can be provided with Fuseki triple store and a database `n4o-rdf-import` locally created like this:

~~~sh
curl --data "dbName=n4o-rdf-import&dbType=tdb2" http://localhost:3030/$/datasets
~~~

The RDF database is expected to be grouped in named graphs:

- Graph `https://graph.nfdi4objects.net/collection/> contains information about collections
- Graphs `https://graph.nfdi4objects.net/collection/X` where X is an integer contain information from individual collections
- Graph `https://graph.nfdi4objects.net/terminology/` contains information about terminologies
- Graphs `http://bartoc.org/en/node/X` where X is an integer contain information from individual terminologies
- The default graph must be configured as union graph.

See <https://github.com/nfdi4objects/n4o-import> for additional information to set up, initialize and fill the Triple Store.

### Cypher

The Cypher backend is optional. When using Neo4j (or compatible) make sure the database is read-only because this application only applies a simple filter to detect Cypher write queries!

## Usage

### SPARQL API

This webservice implements [SPARQL query API](https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-operation) at `/api/sparl`. The query is transformed to a POST request and passed to the backend SPARQL endpoint.

### Linked Open Data

Information about collections, each identified by an URI starting with <https://graph.nfdi4objects.net/collection/>, can be retrieved as Linked Open Data (LOD) at path `/collection` in HTML and in RDF serializations. The data is retrieved via [SPARQL API](#sparql-api), so retrieving <https://graph.nfdi4objects.net/collection/1> results in the same data as this SPARQL query from graph <https://graph.nfdi4objects.net/collection/>:

~~~sparql
DESCRIBE <https://graph.nfdi4objects.net/collection/1> FROM <https://graph.nfdi4objects.net/collection/>
~~~

The RDF serialization is determined via HTTP Content Negotiation or with optional query parameter `format`.

Information about terminologies will be made available from <https://graph.nfdi4objects.net/terminology/>.

### Property Graph API

The Property Graph API at `/api/cypher` expects a HTTP GET query parameter `query` with a Cypher query or a HTTP POST request with a Cypher query as request body. The return format is a (possibly empty) JSON array of result objects. On failure, an error object is returned. Each response objects is maps query variables to values. Each value is one of:

- number, string, boolean, or null
- array of values
- [PG-JSONL](https://pg-format.github.io/specification/#pg-json) node or edge object for nodes and edges
- [PG-JSON](https://pg-format.github.io/specification/#pg-jsonl) graph object for pathes

The following examples use n4o-graph-apis application running at <https://graph.nfdi4objects.net/> for illustration. Use base URL
<http://localhost:8000/> for testing a local installation:

```python
import requests
import json

api = "https://graph.nfdi4objects.net/api/cypher"
query = "MATCH (m:E16_Measurement) RETURN m LIMIT 2"
results = requests.get(api, { "query": query }).json()
```

```js
const api = "https://graph.nfdi4objects.net/api/cypher"
const query = "MATCH (m:E16_Measurement) RETURN m LIMIT 2"
results = await fetch(api, { query }).then(res => res.json())
```

To query with curl, the Cypher query must be URL-escaped, this is done by using argument [--data-urlencode](https://curl.se/docs/manpage.html#--data-urlencode):

```sh
curl -G https://graph.nfdi4objects.net/api/cypher --data-urlencode 'query=MATCH (m:E16_Measurement) RETURN m LIMIT 2'
```

The Cypher query can also be passed from a file:

```sh
curl -G https://graph.nfdi4objects.net/api/cypher --data-urlencode 'query@queryfile.cypher'
```

## Development

To locally run the application first install required Python dependencies with virtualenv:

~~~sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
~~~

Then locally run for testing:

~~~sh
python app.py --help
~~~

Alternatively run `make .venv` and `make dev`.

Please run `make lint` to detect Python coding style violations and `make fix` to fix some of these violations. Some unit tests are run with `make test`.

To populate the configured knowledge graph databases with actual data, see the source code repository <https://github.com/nfdi4objects/n4o-import>.

To locally build the Docker image run `make docker`. The container is named `n4o-graph-apis`, so it can be run for testing:

~~~sh
docker run --rm --net=host -p 8000:8000 -v ./config.yaml:/app/config.yaml:ro n4o-graph-apis
~~~

## License

MIT License

