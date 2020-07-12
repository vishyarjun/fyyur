#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask_migrate import Migrate
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import SQLALCHEMY_DATABASE_URI
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database - Done
app.config['SQLALCHEMY_DATABASE_URI']=SQLALCHEMY_DATABASE_URI

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  Venue_id=db.Column(db.Integer,db.ForeignKey('Venue.id'))
  Artist_id=db.Column(db.Integer,db.ForeignKey('Artist.id'))
  Show_date=db.Column(db.DateTime)

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String()))
    shows = db.relationship('Show',backref=db.backref('Venues',lazy=True)
    )

    # def __repr__(self):
    #   return self.name + '||' + self.city + '||'+ self.state + '||'+ self.address + '||'
    #   + self.phone + '||'+ self.image_link + '||'+ self.facebook_link + '||'+ self.website + '||'
    #   + self.seeking_talent + '||'+ self.seeking_description + '||'+ self.genres + '||'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venues = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))   
    shows = db.relationship('Show', backref=db.backref('Artists',lazy=True)
    )

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  all_venue = Venue.query.all() 
  data_dict=[]
  city_set = set()

  for venue in all_venue:
    ven = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows":0
    }
    if (venue.city, venue.state) not in city_set:
      city_set.add((venue.city,venue.state))
      data_dict.append({
        "city": venue.city,
        "state": venue.state,
        "venues":[]
      })
    
    filtered_entries = [entry for entry in data_dict if entry['city']==venue.city and entry['state']==venue.state]
    # app.logger.info(filtered_entries)
    filtered_entries[0]['venues'].append(ven)

  
  # app.logger.info(data_dict)
    
  return render_template('pages/venues.html', areas=data_dict);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_result = Venue.query.filter(Venue.name.ilike('%{}%'.format(request.form['search_term']))).all()
  app.logger.info(len(search_result))
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  ven = []
  for item in search_result:
    ven.append({
      "id": item.id,
      "name": item.name,
      "num_upcoming_shows": len(item.shows),
    })
  response={
    "count": len(search_result),
    "data": ven
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  ven = Venue.query.get(venue_id)
  future_shows = []
  past_shows = []
  for show in ven.shows:
    if show.Show_date>datetime.now():
      future_shows.append({
        "artist_id":show.Artist_id,
        "artist_name":show.Artists.name,
        "artist_image_link": show.Artists.image_link,
        "start_time":str(show.Show_date)
      })
    else:
      past_shows.append({
        "artist_id":show.Artist_id,
        "artist_name":show.Artists.name,
        "artist_image_link": show.Artists.image_link,
        "start_time":str(show.Show_date)
      })

  data = {    
    "id": ven.id,
    "name": ven.name,
    "genres": ven.genres,
    "address": ven.address,
    "city": ven.city,
    "state": ven.state,
    "phone": ven.phone,
    "website": ven.website,
    "facebook_link": ven.facebook_link,
    "seeking_talent": ven.seeking_talent,
    "seeking_description": ven.seeking_description,
    "image_link": ven.image_link,
    # update hardcoded values when implementing shows
    "past_shows": past_shows,
    "upcoming_shows": future_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(future_shows),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error=False
  
  venue = Venue(    
    name = request.form['name'],
    city = request.form['city'],
    state = request.form['state'],
    address = request.form['address'],
    phone = request.form['phone'],
    image_link = request.form['image_link'],
    facebook_link = request.form['facebook_link'],
    website = request.form['website'],
    seeking_talent = True if request.form['seeking_talent'] else False,
    seeking_description = request.form['seeking_description'],
    genres = request.form.getlist('genres'))
  try:
    # app.logger.info(venue)
    db.session.add(venue)
    db.session.commit()
  except SQLAlchemyError as e:
    app.logger.error(e)
    error=True
    db.session.rollback()
  finally:
    db.session.close()
    if not error:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    else:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  artists_data = []
  for artist in artists:
    artists_data.append({
    "id": artist.id,
    "name": artist.name,
    })
  # app.logger.info(artists_data)

  # TODO: replace with real data returned from querying the database
  data=[{
    "id": 4,
    "name": "Guns N Petals",
  }, {
    "id": 5,
    "name": "Matt Quevedo",
  }, {
    "id": 6,
    "name": "The Wild Sax Band",
  }]
  return render_template('pages/artists.html', artists=artists_data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_result = Artist.query.filter(Artist.name.ilike('%{}%'.format(request.form['search_term']))).all()
  app.logger.info(len(search_result))
  art = []
  for item in search_result:
    art.append({
      "id": item.id,
      "name": item.name,
      "num_upcoming_shows": len(item.shows),
    })
  response={
    "count": len(search_result),
    "data": art
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  future_shows = []
  past_shows = []
  for show in artist.shows:
    if show.Show_date>datetime.now():
      future_shows.append({
        "artist_id":show.Artist_id,
        "artist_name":show.Artists.name,
        "artist_image_link": show.Artists.image_link,
        "start_time":str(show.Show_date)
      })
    else:
      past_shows.append({
        "artist_id":show.Artist_id,
        "artist_name":show.Artists.name,
        "artist_image_link": show.Artists.image_link,
        "start_time":str(show.Show_date)
      })
  data={
    "id": artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venues": artist.seeking_venues,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": future_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(future_shows),
  }
  data['genres'] = ''.join(list(filter(lambda x : x!= '{' and x!='}', artist.genres ))).split(',')
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error=False
  try:
    artist = Artist(    
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      website = request.form['website'],
      seeking_venues = True if request.form['seeking_venues'] else False,
      seeking_description = request.form['seeking_description'],
      genres = request.form.getlist('genres'))
    # app.logger.info('length is {}'.format(len(artist.genres)))

    db.session.add(artist)
    db.session.commit()
  except SQLAlchemyError as e:
    app.logger.error(e)
    error=True
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  shows = db.session.query(Show).all()
  # app.logger.info(shows)
  show_data=[]
  for show in shows:
    temp={
    "venue_id": show.Venues.id,
    "venue_name": show.Venues.name,
    "artist_id": show.Artists.id,
    "artist_name": show.Artists.name,
    "artist_image_link": show.Artists.image_link,
    "start_time": str(show.Show_date)
    }
    show_data.append(temp)

  return render_template('pages/shows.html', shows=show_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error=False
  try:
    show = Show(
      Venue_id=request.form['artist_id'],
      Artist_id=request.form['venue_id'],
      Show_date=request.form['start_time']
    )
    db.session.add(show)
    db.session.commit()
  except SQLAlchemyError as e:
    app.logger.error(e)
    error=True
    db.session.rollback()
  finally:
    db.session.close()
  if not error:
    flash('Show at {} was successfully listed!'.format(request.form['start_time']))
  else:
    flash('An error occurred. Show at {} could not be listed.'.format(request.form['start_time']))
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
