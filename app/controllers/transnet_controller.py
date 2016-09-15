from flask import request, json, Response

from app.models.relation import Relation


class TransnetController:
    def index(self):
        if not request.args.get('bounds'):
            return Response(json.dumps([]), mimetype='application/json')

        bounds_parts = request.args.get("bounds").split(',')
        relations = Relation.with_points_and_lines_in_bounds(bounds_parts)

        return Response(json.dumps(relations), mimetype='application/json')
