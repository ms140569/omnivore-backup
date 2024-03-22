#!/usr/bin/env python3
'''Backup data from Omnivore using GraphQL API'''
import os
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List
import argparse

# see: https://github.com/graphql-python/gql

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

DEFAULT_CHUNK_SIZE: int = 100
DEFAULT_URL = "https://api-prod.omnivore.app/api/graphql"

@dataclass
class PageInfo:
    """PageInfo"""
    hasNextPage: bool
    hasPreviousPage: bool
    startCursor: str
    endCursor: str
    totalCount: int

@dataclass
class Label:
    """Label"""
    name: str

@dataclass
class SearchItem:
    """SearchItem"""
    title: str
    url: str
    labels: List[Label]
    publishedAt: str
    savedAt: str

@dataclass
class SearchItemEdge:
    """SearchItemEdge"""
    cursor: str
    node: SearchItem

def main():
    '''Backup data from Omnivore using GraphQL API'''

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", type=int,
                        dest="chunksize",
                        default=str(DEFAULT_CHUNK_SIZE),
                        help="Chunksize to fetch. Default: " + str(DEFAULT_CHUNK_SIZE))

    parser.add_argument("-u", "--url",
                        default=DEFAULT_URL,
                        help="URL to load from, default: " + DEFAULT_URL)
    args = parser.parse_args()
    token = os.getenv("TOKEN")

    if not token:
        print("You have to provide a access key in the TOKEN environment variable.")
        sys.exit(1)

    backup = OmnivoreBackup(args.chunksize, args.url, token)
    backup.run()

class OmnivoreBackup:
    """Backup data from Omnivore using GraphQL API"""
    def __init__(self, chunksize: int, url: str, token: str):
        self.chunksize = chunksize
        self.url = url
        self.query = None
        self.token = token
        self.client: Client
        self.edges: List[SearchItemEdge] = []

    def run(self):
        """Initiate the data processing"""
        transport = AIOHTTPTransport(self.url, headers={
            'Authorization': self.token, 
            'Content-Type': 'application/json'})

        self.client = Client(transport=transport)

        self.query = gql(
              """
              query Search($query: String!, $first: Int, $after: String) {
                search(query: $query, first: $first, after: $after) {
                  ... on SearchSuccess {
                    edges {
                      cursor
                      node {
                        title
                        url
                        labels {
                          name
                        }
                        publishedAt
                        savedAt
                      }
                    }
                    pageInfo {
                      hasNextPage
                      hasPreviousPage
                      startCursor
                      endCursor
                      totalCount
                    }
                  }
                  ... on SearchError {
                    errorCodes
                  }
                }
              }
          """
          )

        try:
            self._fetch()
        except KeyboardInterrupt:
            self._finish()

        self._finish()

    def _finish(self):
        # print(f"Loaded {len(self.edges)} records.")
        print(_generate_csv(self.edges))

    def _fetch(self):
        # print(f"Fetching data from {self.url} using chunksize {self.chunksize}")

        has_next_page = True
        cursor = 0

        while has_next_page:
            result = self.client.execute(self.query,
                                        variable_values=_params_for_cursor(
                                            self.chunksize, cursor))
            page_info = PageInfo(**result['search']['pageInfo'])

            # print(f"Fetched cursor: {cursor} from total: {page_info.totalCount}" )

            has_next_page = page_info.hasNextPage
            cursor = page_info.endCursor

            for edge in result['search']['edges']:
                sie = SearchItemEdge(cursor=edge['cursor'], node=SearchItem(**edge['node']))
                self.edges.append(sie)

def _params_for_cursor(chunk_size: int, cursor: int) -> dict:
    return {
      "query": "",
      "first": chunk_size,
      "after": "" if cursor == 0 else str(cursor) 
      }

def _generate_csv(edges: List[SearchItemEdge]) -> str:
    output = 'url,state,labels,saved_at,published_at\n'

    # Times are The Unix timestamp in milliseconds

    for edge in edges:
        node = edge.node
        line = ",".join([
            node.url, 
            "SUCCEEDED",
            _format_labels(node.labels),
            _unix_ts(node.savedAt),
            _unix_ts(node.savedAt if not node.publishedAt else node.publishedAt)
            ])
        line += '\n'
        output += line

    return output

def _format_labels(labels: List[Label]) -> str:
    return "\"[" + ",".join([label["name"] for label in labels]) + "]\""

def _unix_ts(timestamp: str) -> str:
    d = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    return str(int(d.timestamp()*1e3))

if __name__ == "__main__":
    sys.exit(main())
