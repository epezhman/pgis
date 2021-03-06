import unittest
import os
from flask import Flask
from app import GisApp
from flask.ext.testing import TestCase
from flask_environments import Environments
from tests.factories.powerline import PowerlineFactory
from app import db
from app.models.powerline import Powerline
import shapely

class MyTest(TestCase):

    def create_app(self):
        return GisApp 

    def test_serialize(self):
        PowerlineFactory();
        powerline = db.session.query(Powerline).first()
        self.assertEquals(powerline.serialize(), { 'tags' : [], 'id' : powerline.id, 'latlngs' : [(48.11, 10.1), (59.12, 10.15)] })

    def test_shape(self):
        PowerlineFactory()
        powerline = db.session.query(Powerline).first()
        assert(type(powerline.shape()) is shapely.geometry.linestring.LineString)
        self.assertEquals(list(powerline.shape().coords), [(48.11, 10.1), (59.12, 10.15)])

        
