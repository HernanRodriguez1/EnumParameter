# EnumParameter

Es una herramienta de enumeración web diseñada para ayudar en tareas de bug bounty y enumeración de aplicaciones web. Utiliza el servicio de Wayback Machine para recuperar URLs históricas de un dominio dado y realiza una serie de acciones sobre ellas, como la exclusión de ciertas extensiones, la verificación de su accesibilidad y la exportación de las URLs válidas a un archivo.

## Características principales:

- **Enumeración de URLs:** Utiliza el servicio de Wayback Machine para obtener URLs históricas de un dominio dado, lo que puede ayudar a descubrir endpoints olvidados o eliminados.

- **Exclusión de extensiones:** Permite especificar extensiones de archivo que se excluirán de los resultados, lo que ayuda a reducir el ruido y centrarse en URLs potencialmente relevantes.

- **Verificación de accesibilidad:** Opcionalmente, verifica la accesibilidad de las URLs resultantes, descartando aquellas que no responden correctamente o devuelven errores.

- **Exportación de resultados:** Guarda las URLs válidas en un archivo de salida especificado por el usuario, lo que facilita su posterior análisis.

- **Banner grabbing del servidor:** Realiza una solicitud adicional a la raíz del dominio para obtener y mostrar las cabeceras válidas del servidor, lo que proporciona información sobre la tecnología utilizada y puede ayudar en la identificación de vulnerabilidades.


## Extraer endpoints desde Internet Archive
```sh
python3 EnumParameter.py  -t www.paginaweb.com.pe -e jpeg -o urls.txt
```
![1](https://github.com/HernanRodriguez1/EnumParameter/assets/66162160/a2ce5d97-331c-4927-82c7-6defc7d937fe)


## Extraer endpoints desde Internet Archive y validar su disponibilidad de los recursos
```sh
python3 EnumParameter.py  -t www.paginaweb.com.pe -e jpeg -v -o urls.txt
```
![2](https://github.com/HernanRodriguez1/EnumParameter/assets/66162160/b76c6292-ee64-4e42-89cf-1da0243389a0)


## Extensiones que se deberian filtrar
```sh
jpg,png,jpeg,doc,pdf,xls,ppt,mp3,mp4,zip,rar,gif,bmp,tiff,wav
```

## Requisitos previos:
Python 3.x
Módulos Python: requests, colorama

## Contribuciones y problemas:
Si encuentras algún problema o tienes alguna sugerencia de mejora, no dudes en abrir un problema en este repositorio. ¡Las contribuciones también son bienvenidas!
