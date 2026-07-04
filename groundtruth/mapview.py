"""Emit a self-contained Leaflet map of certified works: the citizen-facing
'public works ledger'. Open the generated HTML in any browser."""
import json

TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>GroundTruth: public works ledger</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{height:100%%;margin:0} .lg{font:14px/1.4 sans-serif}</style>
</head><body><div id="map"></div><script>
var works = %s;
var map = L.map('map').setView([works[0].lat, works[0].lon], 14);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  {attribution:'&copy; OpenStreetMap'}).addTo(map);
works.forEach(function(w){
  var color = w.status === 'PAID' ? 'green' : (w.status === 'CERTIFIED' ? 'orange' : 'gray');
  L.circleMarker([w.lat, w.lon], {radius: 10, color: color, fillOpacity: 0.7})
   .addTo(map)
   .bindPopup('<div class="lg"><b>' + w.description + '</b><br>' +
      w.sor_code + ' | ' + w.qty + ' ' + w.unit + '<br>' +
      'Certified by: ' + w.engineer + '<br>' +
      'Amount: Rs ' + w.amount.toLocaleString('en-IN') + '<br>' +
      'Status: <b>' + w.status + '</b></div>');
});
</script></body></html>
"""


def write_map(path: str, works: list):
    with open(path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE % json.dumps(works))
    return path
