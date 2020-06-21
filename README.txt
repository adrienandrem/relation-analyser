relation-analyser

a real-time relation analysis service.

Given a relation id, it tests for validation of multipolygons of any kind, admin boundaries (and also linear relations to some extend).

You can use permalinks of the form: http://server.tld/cgi-bin/index.py?relation=123456.

See also discussion page on OSM Wiki https://wiki.openstreetmap.org/wiki/FR_talk:Serveurs/analyser.openstreetmap.fr


Results:

./doc/img/Osmose3-2010.png

The result is a map, with the relation displayed over it. Tags, nodes where the problem is are displayed.

  - a yellow marker is displayed for an opening in the relation
  - a green Marker for self intersection

A direct link to JOSM is given to repair the relation where it has a problem.


Dependencies:

- OSM API
- OsmApi python library
- JTS
- Inkscape


Elle a été un peu nettoyée de dépendances d'accès en dur, et utilise
l'api.openstreetmap.fr au lieu de l'api officielle.


Bidouillé par sly sylvain at letuffe point org
