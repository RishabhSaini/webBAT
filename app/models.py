from app import db
from geoalchemy2 import Geometry, Geography
import geoalchemy2
from sqlalchemy.dialects.postgresql import ARRAY
from enum import Enum,IntEnum

class trigger_type(IntEnum):
    GRB = 1
    GW = 2
    neutrino = 3
    FRB = 4

class MoU_group(IntEnum):
    LVK = 1
    CHIME = 2

class trigger(db.Model):
    __tablename__ = 'triggers'

    trigid = db.Column(db.Integer, primary_key=True)
    trigger_time = db.Column(db.TIMESTAMP, nullable=False)
    event_name = db.Column(ARRAY(db.String), nullable= False)
    trigger_type = db.Column(db.Enum(trigger_type), nullable=False)
    trigger_instruments = db.Column(ARRAY(db.String), nullable=False)
    position = db.Column(Geography('POINT',srid=4326))
    position_error = db.Column(db.Float)
    localization_mapurl = db.Column(db.String)
    comment = db.Column(db.String)
    rates_data = db.Column(db.Boolean)
    event_data = db.Column(db.Boolean)
    rates_detection = db.Column(db.Boolean)
    BAT_position = db.Column(db.Boolean)
    coverage_frac = db.Column(db.Float)
    swift_LatLon = db.Column(Geography('POINT',srid=4326))
    swift_altitude = db.Column(db.Float)
    # swift_radec = db.Column(Geography('POINT', srid=4326))
    # swift_roll = db.Column(db.Float)
    earth_radec = db.Column(Geography('POINT', srid=4326))
    private = db.Column(db.Boolean)
    MoU_group = db.Column(db.Enum(MoU_group))
    slewing = db.Column(db.Boolean)

    # def __init__(self, met, trigger_type, ):
    #     self.met = met
    #     self.trigger_time = author
    #     self.published = published

    def __repr__(self):
        return '<trigid {}>'.format(self.trigid)
    
    def __eq__(self, other):
        if other.event_name in self.event_name \
        and self.trigger_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:22] == other.trigger_time \
        and self.trigger_type.name == other.trigger_type \
        and self.position_error == other.position_error \
        and other.trigger_instruments in self.trigger_instruments\
        and self.localization_mapurl == other.localization_mapurl:
            return True
        else:
            return False

class realtime_pointing(db.Model):
    timestamp = db.Column(db.TIMESTAMP, primary_key=True)
    position = db.Column(Geography('POINT',srid=4326), nullable=False)
    roll = db.Column(db.Float, nullable=False)