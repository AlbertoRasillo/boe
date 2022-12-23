#!/usr/bin/python3.7

import requests
import smtplib
import re
from lxml import etree
from email.mime.text import MIMEText
import os


def busquedaIdBoe():
    url  = 'https://www.boe.es/rss/boe.php?s=2B'

    # Realizamos la petición a la página
    response = requests.get(url)

    # Lista de patrones a buscar
    patrones = ['Oposiciones y concursos', 'Oposición']

    # Definimos una expresión regular para buscar la parte variable del patrón
    pattern = r'Referencia: BOE-(?P<tipo>\w+)-(?P<fecha>\d+)-(?P<numero>\d+)'

    # Creamos una lista vacía para almacenar los resultados
    coincidencias = []

    # Creamos una lista vacía para almacenar los resultados
    resultados = []

    # Convertimos la respuesta HTTP a una secuencia de bytes
    xml_bytes = bytes(response.text, 'utf-8')

    # Parseamos la secuencia de bytes utilizando lxml
    root = etree.fromstring(xml_bytes)

    # Recorremos todos los elementos del documento
    for elemento in root.iter():
      if elemento.text is not None and any(patron.lower() in elemento.text.lower() for patron in patrones):
          # Comprobamos si el elemento contiene algún patrón de la lista
          if any(patron.lower() in elemento.text.lower() for patron in patrones):
            # Si se ha encontrado una coincidencia, la mostramos por pantalla
            coincidencias.append(elemento.text)
            match = re.search(pattern, elemento.text)
            # Si se ha encontrado una coincidencia con la expresión regular, añadimos los grupos de captura a la lista de resultados
            if match is not None:
              resultados.append({
                'tipo': match.group('tipo'),
                'fecha': match.group('fecha'),
                'numero': match.group('numero')
              })
    boe = []
    for resultado in resultados:
        boeid = resultado['tipo']+'-'+resultado['fecha']+'-'+resultado['numero']
        boeid = 'BOE-'+boeid
        boe.append(boeid)
    return boe

def buscarOposciones(boeid, fichero):
    url  = 'https://www.boe.es/diario_boe/xml.php?id='+boeid
    # Realizamos la petición a la página
    response = requests.get(url)

    # Lista de patrones a buscar
    # patrones = ['territorial', 'POL\ÍTICA TERRITORIAL', 'MINISTERIO DE POL\ÍTICA TERRITORIAL Y FUNCI\ÓN P\ÚBLICA',]
      patrones = ['Profesor', 'Médico', 'Astronauta']
    
    # Creamos una lista vacía para almacenar los resultados
    coincidencias = []
    url_boe_pdf = []

    # Flag cuando se encuntra el patron y coger el pdf
    encontrado = False

    # Convertimos la respuesta HTTP a una secuencia de bytes
    xml_bytes = bytes(response.text, 'utf-8')

    # Parseamos la secuencia de bytes utilizando lxml
    root = etree.fromstring(xml_bytes)

    # Recorremos todos los elementos del documento
    for elemento in root.iter():
      if elemento.text is not None and any(patron.lower() in elemento.text.lower() for patron in patrones):
          # Comprobamos si el elemento contiene algún patrón de la lista
          if any(patron.lower() in elemento.text.lower() for patron in patrones):
            # Si se ha encontrado una coincidencia, la mostramos por pantalla
            coincidencias.append(elemento.text)
            encontrado = True
            
    for elemento in root.iter():
      if elemento is not None and elemento.tag == "url_pdf" and encontrado == True:
          url_pdf = 'https://www.boe.es'+elemento.text
          url_boe_pdf.append(url_pdf)
    
    boe_enviado = False
    if coincidencias:
      boe_enviado = buscarSiBoeEnviado(boeid, fichero)
    
    # Si se han encontrado coincidencias, enviamos un email
    if coincidencias and not boe_enviado:
      # Dirección del servidor de correo
      server = smtplib.SMTP('smtp-mail.server.com', 587)
      server.starttls()

      # Dirección de correo y contraseña del remitente
      server.login('account@email.com', 'password')

      # Dirección del destinatario
      destinatario = 'destination@mail.com'

      # Asunto y cuerpo del mensaje
      asunto = '{} Aunto del correo '.format(boeid)
      cuerpo = 'Se han encontrado las siguientes coincidencias:\n' + '\n'.join(coincidencias)
      cuerpo = cuerpo + '\n Enlace del {}: {} {}'.format(boeid, url_boe_pdf, url)

      # Creamos el mensaje
      mensaje = MIMEText(cuerpo, 'plain', 'utf-8')
      mensaje['Subject'] = f'{asunto}'

      # Enviamos el email
      server.sendmail('sender@email.com', destinatario, mensaje.as_bytes())

      # Cerramos la conexión con el servidor
      server.quit()

      guardaBoeEnviado(boeid, fichero)

def guardaBoeEnviado(boeid, fichero):
    with open(fichero, 'a') as archivo:
        archivo.write('\n'+boeid)

def buscarSiBoeEnviado(boeid, fichero):
    # Abrimos el archivo en modo lectura
    with open(fichero, 'r') as f:
        texto = f.read()
        # Buscamos la cadena de texto en la variable
        indice = texto.find(boeid)
        if indice !=-1:
           return True
        else:
           return False

if __name__ == '__main__':

    directorio_actual = os.path.dirname(__file__)
    path_fichero = os.path.join(directorio_actual, "boes_enviados.txt")
    
    boe = busquedaIdBoe()
    for boeid in boe:
        buscarOposciones(boeid, path_fichero)
