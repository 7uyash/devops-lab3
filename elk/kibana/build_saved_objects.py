"""Generates saved_objects.ndjson (data view, visualizations, saved search, dashboard) for Kibana."""
import json
import os

IDX = "shoplite-logs"
REF = [{"name": "kibanaSavedObjectMeta.searchSourceJSON.index", "type": "index-pattern", "id": IDX}]


def ss(query=""):
    return json.dumps({"query": {"query": query, "language": "kuery"}, "filter": [],
                       "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"})


def axes(title):
    return {"grid": {"categoryLines": False},
            "categoryAxes": [{"id": "CategoryAxis-1", "type": "category", "position": "bottom", "show": True,
                              "style": {}, "scale": {"type": "linear"},
                              "labels": {"show": True, "filter": True, "truncate": 100}, "title": {}}],
            "valueAxes": [{"id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value", "position": "left",
                           "show": True, "style": {}, "scale": {"type": "linear", "mode": "normal"},
                           "labels": {"show": True, "rotate": 0, "filter": False, "truncate": 100},
                           "title": {"text": title}}],
            "addTooltip": True, "addLegend": True, "legendPosition": "right", "times": [],
            "addTimeMarker": False, "labels": {"show": False},
            "thresholdLine": {"show": False, "value": 10, "width": 1, "style": "full", "color": "#E7664C"}}


def series(kind, label):
    return [{"show": True, "type": kind, "mode": "stacked", "data": {"label": label, "id": "1"},
             "valueAxis": "ValueAxis-1", "drawLinesBetweenPoints": True, "lineWidth": 2,
             "interpolate": "linear", "showCircles": True}]


def vis(vid, title, vtype, params, aggs, query=""):
    return {"id": vid, "type": "visualization", "migrationVersion": {"visualization": "7.10.0"},
            "attributes": {"title": title, "description": "", "uiStateJSON": "{}", "version": 1,
                           "visState": json.dumps({"title": title, "type": vtype, "params": params, "aggs": aggs}),
                           "kibanaSavedObjectMeta": {"searchSourceJSON": ss(query)}},
            "references": REF}


def terms(i, field, schema, size=10):
    return {"id": i, "enabled": True, "type": "terms", "schema": schema,
            "params": {"field": field, "size": size, "order": "desc", "orderBy": "1",
                       "otherBucket": False, "missingBucket": False}}


COUNT = {"id": "1", "enabled": True, "type": "count", "schema": "metric", "params": {}}
AVG = {"id": "1", "enabled": True, "type": "avg", "schema": "metric", "params": {"field": "duration_ms"}}
DATE_HIST = {"id": "2", "enabled": True, "type": "date_histogram", "schema": "segment",
             "params": {"field": "@timestamp", "interval": "auto", "min_doc_count": 1, "extended_bounds": {}}}
METRIC = {"addTooltip": True, "addLegend": False, "type": "metric",
          "metric": {"percentageMode": False, "useRanges": False, "colorSchema": "Green to Red",
                     "metricColorMode": "None", "colorsRange": [{"from": 0, "to": 100000}],
                     "labels": {"show": True}, "invertColors": False,
                     "style": {"bgFill": "#000", "bgColor": False, "labelColor": False, "subText": "",
                               "fontSize": 48}}}
PIE = {"type": "pie", "addTooltip": True, "addLegend": True, "legendPosition": "right", "isDonut": True,
       "labels": {"show": True, "values": True, "last_level": True, "truncate": 100}}


def bar(title):
    return {**axes(title), "type": "histogram", "seriesParams": series("histogram", title)}


objs = [
    {"id": IDX, "type": "index-pattern", "migrationVersion": {"index-pattern": "7.6.0"},
     "attributes": {"title": "shoplite-logs-*", "timeFieldName": "@timestamp"}, "references": []},
    vis("vis-total", "Total log events", "metric", METRIC, [COUNT]),
    vis("vis-errors", "Server errors (5xx)", "metric", METRIC, [COUNT], "status >= 500"),
    vis("vis-status", "Requests by status class", "pie", PIE, [COUNT, terms("2", "status_class", "segment")]),
    vis("vis-levels", "Log events over time by level", "histogram", bar("Events"),
        [COUNT, DATE_HIST, terms("3", "level", "group", 5)]),
    vis("vis-endpoints", "Requests per endpoint", "histogram", bar("Requests"),
        [COUNT, terms("2", "path", "segment", 10)]),
    vis("vis-latency", "Average response time (ms) per endpoint", "histogram", bar("Avg duration (ms)"),
        [AVG, terms("2", "path", "segment", 10)]),
    {"id": "search-errors", "type": "search", "migrationVersion": {"search": "7.9.3"},
     "attributes": {"title": "Errors and warnings", "description": "",
                    "columns": ["level", "method", "path", "status", "error_message", "user", "instance"],
                    "sort": [["@timestamp", "desc"]],
                    "kibanaSavedObjectMeta": {"searchSourceJSON": ss("level:ERROR or level:WARNING")}},
     "references": REF},
]

LAYOUT = [("vis-total", 0, 0, 12, 8), ("vis-errors", 12, 0, 12, 8), ("vis-status", 24, 0, 24, 8),
          ("vis-levels", 0, 8, 48, 13), ("vis-endpoints", 0, 21, 24, 13), ("vis-latency", 24, 21, 24, 13),
          ("search-errors", 0, 34, 48, 14)]
panels, refs = [], []
for i, (oid, x, y, w, h) in enumerate(LAYOUT):
    panels.append({"version": "7.10.0", "gridData": {"x": x, "y": y, "w": w, "h": h, "i": str(i + 1)},
                   "panelIndex": str(i + 1), "embeddableConfig": {}, "panelRefName": f"panel_{i}"})
    refs.append({"name": f"panel_{i}", "type": "search" if oid.startswith("search") else "visualization",
                 "id": oid})
objs.append({"id": "shoplite-dashboard", "type": "dashboard", "migrationVersion": {"dashboard": "7.9.3"},
             "attributes": {"title": "ShopLite - Centralized Logs", "description": "Lab 3 logging dashboard",
                            "panelsJSON": json.dumps(panels), "timeRestore": True,
                            "timeFrom": "now-30m", "timeTo": "now",
                            "refreshInterval": {"pause": True, "value": 0},
                            "optionsJSON": json.dumps({"useMargins": True, "hidePanelTitles": False}),
                            "version": 1,
                            "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(
                                {"query": {"query": "", "language": "kuery"}, "filter": []})}},
             "references": refs})

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_objects.ndjson")
with open(out, "w", newline="\n") as f:
    for o in objs:
        f.write(json.dumps(o) + "\n")
print(f"wrote {len(objs)} saved objects to {out}")
