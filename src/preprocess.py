import geopandas as gpd
from shapely.geometry import LineString, Point
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def regresa_puntos(s):
  if s.size > 1:
    return s.tolist()

def get_start_end_distance(line):
  start = Point(line.coords[0])
  end = Point(line.coords[-1])
  return start.distance(end)

def get_trayectories(path_input_points, path_input_polygons, threshold):
    tuits = gpd.read_file(path_input_points)
    tuits.drop(['id', 'fecha', 'hora', 'contenido', 'intervalo'], axis=1, inplace=True)
    input_polygons = gpd.read_file(path_input_polygons)
    tuits = tuits.to_crs("EPSG:32614")
    tuits = gpd.sjoin(tuits, input_polygons)
    tuits['fecha_hora_dt'] = pd.to_datetime(
        tuits['fecha_hora'],
        format='%Y-%m-%d %H:%M:%S',
        utc=True)
    tuits.fecha_hora_dt = tuits.fecha_hora_dt.dt.tz_convert(
        'America/Mexico_City')
    tuits.sort_index(inplace=True)
    trayectorias = (tuits.groupby([pd.Grouper(key='fecha_hora_dt', freq='1D'), 
                    pd.Grouper(key='fecha_hora_dt', freq='4H', base=2), 
                    'uname']))[['geometry']].agg(regresa_puntos)
    trayectorias.index.names =['dia', 'intervalo', 'uname']
    trayectorias = trayectorias[trayectorias['geometry'].notnull()]
    trayectorias['linea'] = trayectorias['geometry'].apply(lambda x: LineString(x))
    trayectorias.drop(['geometry'], axis=1, inplace=True)
    trayectorias.rename({'linea': 'geometry'}, axis=1, inplace=True)
    trayectorias = gpd.GeoDataFrame(trayectorias)
    trayectorias['separation'] = trayectorias['geometry'].apply(get_start_end_distance)
    trayectorias = trayectorias[trayectorias['separation'] >= threshold]
    return(trayectorias)

def preprocesa_archivo(file_path):
  un_mes = pd.read_csv(file_path)
  distritos = gpd.read_file("../data/shapes/DistritosEODHogaresZMVM2017.shp")
  un_mes = un_mes.loc[:,['ID', 'Usuario', 'Fecha_tweet', 'Latitud', 'Longitud']]
  un_mes = (gpd.GeoDataFrame(un_mes, geometry=gpd.points_from_xy                                          (un_mes.Longitud, un_mes.Latitud))
          .drop(['Latitud', 'Longitud'], axis=1)
          .set_crs(4326)
          )
  un_mes = (gpd.sjoin(un_mes, distritos.to_crs(4326))
      .drop(['index_right', 'Descripcio'], axis=1)
      )
  un_mes['fecha_hora_dt'] = pd.to_datetime(
      un_mes['Fecha_tweet'],
      format='%Y-%m-%d %H:%M:%S',
      utc=False)
  return un_mes