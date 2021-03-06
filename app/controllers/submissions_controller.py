from app import GisApp
from flask import render_template, flash, redirect, abort, session, url_for, request, g, json, Response
from geoalchemy2 import Geometry, func
from geoalchemy2.functions import GenericFunction
import app.helpers.point_form
import sys, os, traceback, base64
import hashlib
from app import db
from app.models.point import Point
from app.models.submission import Submission
from app.models.picture import Picture
from app.models.user import User
from flask.ext.login import current_user
from httplib2 import Http
from flask.ext.hashing import Hashing
from sqlalchemy.orm import contains_eager

class SubmissionsController:

    def index(self):
        submissions = db.session.query(Submission).\
            join(Submission.points).outerjoin(Point.pictures).join(Submission.user).\
            filter(Point.merged_to == None, Submission.revised).\
            options(contains_eager(Submission.points).contains_eager(Point.pictures)).\
            all()
        submissions = list(map(lambda submission: submission.serialize_for_mobileapp(), submissions))
        return Response(json.dumps(submissions),  mimetype='application/json')

    def create(self):
        
        try:
            json_packet = request.get_json(force=True)
            json_data = json_packet["data_packet"]

            if "id_token" in json_data:
                email = self.__validate_id_token(json_data["id_token"])
            elif "access_token" in json_data:
                email = self.__validate_access_token(json_data["access_token"])
            if email is None:
                return "Invalid Id Token", 400
            user = app.models.user.User.query.filter_by(email=email).first()
            if user is None:
                user = app.models.user.User(email=email, action_permissions={})
                db.session.add(user)
                db.session.commit()

            submission = Submission.query.filter(Submission.user_id == user.id, Submission.submission_id == int(json_data['submission_id'])).first()
            if submission is None:
                submission = self.__make_submission(json_data, user)
                db.session.add(submission)
                db.session.flush()
            new_point = self.__make_point(json_data, submission)
            db.session.add(new_point)
            db.session.flush()

            if "image" in json_data:
                new_picture = self.__make_picture(submission.id, new_point.id, user.id)
                new_picture.filepath = self.__save_image(submission.id, new_point.id, json_data['image'])
                db.session.add(new_picture)
            db.session.commit()

            hashing = Hashing(GisApp)
            # json_data_dump = json.dumps(json_data)
            # json_data_hash = hashing.hash_value(json_data_dump, '')
            # json_data_hash = hashlib.sha256(json_data_dump)

            return Response(json.dumps({ "status" : "ok", "received_data" : "json_data_hash", "point" : str(new_point) }))
        except Exception as e:
            return Response(json.dumps({ "status" : "error", "error_message" : str(e), "trace" : traceback.format_exc() })), 500



    def __make_point(self, data, submission):
        new_point = Point()
        new_point.geom = "POINT({} {})".format(data["point"]["latitude"], data["point"]["longitude"])
        new_point.properties = data["point"]["properties"]
        new_point.revised = False
        new_point.approved = False
        new_point.submission_id = submission.id 
        return new_point

    def __make_submission(self, data, user):
        new_submission = Submission()
        new_submission.submission_id = data["submission_id"]
        new_submission.number_of_points = data["number_of_points"]
        new_submission.user_id = user.id 
        new_submission.revised = False
        new_submission.approved = False
        return new_submission

    def __make_picture(self, submission_id, point_id, user_id):
        new_picture = Picture()
        new_picture.point_id = point_id
        new_picture.submission_id = submission_id
        new_picture.user_id = user_id
        return new_picture



    def __save_image(self,submission_id, point_id, encoded_string):
        directory = "app/static/uploads/submissions/" + str(submission_id)
        if not os.path.exists(directory):
            os.makedirs(directory)
        fh = open(directory + "/" + str(point_id) + ".png", "wb")
        fh.write(base64.b64decode(encoded_string))
        fh.close()
        return "static/uploads/submissions/" + str(submission_id) + "/" + str(point_id) + ".png"

    def __validate_id_token(self, id_token):
        '''Verifies that an id-token is valid and
        meant for this app.

        Returns None on fail, and an e-mail on success'''
        h = Http()
        resp, cont = h.request("https://www.googleapis.com/oauth2/v1/tokeninfo?id_token=" + id_token, "GET")

        if not resp['status'] == '200':
            return None

        try:
            data = json.loads(cont)
        except TypeError:
            # Running this in Python3
            # httplib2 returns byte objects
            data = json.loads(cont.decode())


        if(data['audience'] != GisApp.config.get('GOOGLE_CLIENT_ID')):
            raise

        if(data['issued_to'] not in ["498377614550-8k5gt5hgp13fveqia1md2qjjr6a99qqr.apps.googleusercontent.com", "498377614550-i7b06cjlssr1g9549o46djrkhks6jktl.apps.googleusercontent.com"]):
            raise

        if(data['expires_in'] <= 0):
            raise

        return data['email']


    def __validate_access_token(self, access_token):
        '''Verifies that an access-token is valid and
        meant for this app.

        Returns None on fail, and an e-mail on success'''
        h = Http()
        resp, cont = h.request("https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=" + access_token, "GET")

        if not resp['status'] == '200':
            return None

        try:
            data = json.loads(cont)
        except TypeError:
            # Running this in Python3
            # httplib2 returns byte objects
            data = json.loads(cont.decode())


        if(data['audience'] != "271653534564-dc97mvagb3m59abrqk4hcaqnfl57c1vn.apps.googleusercontent.com"):
            raise

        if(data['issued_to'] != "271653534564-dc97mvagb3m59abrqk4hcaqnfl57c1vn.apps.googleusercontent.com"):
            raise

        if(data['expires_in'] <= 0):
            raise

        return data['email']