import argparse
import requests
import concurrent.futures
from urllib.parse import urlparse, parse_qs, urlunparse
from colorama import Fore, Style
import urllib3

# ⚠️ Desactiva advertencias SSL (cuando se use verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(Fore.RED + """\n
    ______                      ____                                  __           
   / ____/___  __  ______ ___  / __ \____ __________ _____ ___  ___  / /____  _____
  / __/ / __ \/ / / / __ `__ \/ /_/ / __ `/ ___/ __ `/ __ `__ \/ _ \/ __/ _ \/ ___/
 / /___/ / / / /_/ / / / / / / ____/ /_/ / /  / /_/ / / / / / /  __/ /_/  __/ /    
/_____/_/ /_/\__,_/_/ /_/ /_/_/    \__,_/_/   \__,_/_/ /_/ /_/\___/\__/\___/_/     
                                                                                 
Create By: Hernan Rodriguez | Team Offsec Peru \n""" + Style.RESET_ALL)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

def conector(url):
    try:
        with requests.Session() as session:
            session.headers.update({'User-Agent': USER_AGENT})
            respuesta = session.get(url, timeout=5)
            return respuesta.text, respuesta.status_code, respuesta.headers
    except requests.exceptions.SSLError:
        try:
            with requests.Session() as session:
                session.headers.update({'User-Agent': USER_AGENT})
                respuesta = session.get(url, timeout=5, verify=False)
                return respuesta.text, respuesta.status_code, respuesta.headers
        except requests.exceptions.RequestException as e:
            print(f"[SSL fallback] {e}")
            return "", 404, {}
    except requests.exceptions.RequestException as e:
        print(e)
        return "", 404, {}

def procesar_url(url, lista_negra, args, urls_validas, urls_imprimidas, archivo_salida, params_vistos):
    parsed = urlparse(url)
    if parsed.netloc == args.dominio and parsed.query:
        query_parseado = parse_qs(parsed.query)
        if all(extension not in url for extension in lista_negra) and any(query_parseado.values()):
            path = parsed.path.lstrip('/')
            if not query_parseado:
                return
            primer_parametro = next(iter(query_parseado))
            clave = f"{path}?{primer_parametro}"

            if clave in params_vistos:
                return  # Ya se procesó esta ruta+parametro, ignorar

            params_vistos.add(clave)

            query_modificada = parsed.query
            url_modificada = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', query_modificada, ''))

            if args.verificar:
                if url_modificada not in urls_imprimidas:
                    urls_imprimidas.add(url_modificada)
                    contenido, status_code, headers = conector(url_modificada)
                    if status_code in {200, 301, 302, 401, 403, 500}:
                        urls_validas.add(url_modificada)
                        if status_code == 200:
                            print(f"[{Fore.GREEN}+{Style.RESET_ALL}] {url_modificada}")
                        else:
                            print(f"[{Fore.GREEN}+{Style.RESET_ALL}] {url_modificada} - Código de estado: {status_code}")
                        if archivo_salida:
                            with open(archivo_salida, "a", encoding="utf-8") as file:
                                file.write(f"{url_modificada}\n")
            else:
                if url_modificada not in urls_imprimidas:
                    urls_imprimidas.add(url_modificada)
                    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] {url_modificada}")

def principal():
    parser = argparse.ArgumentParser(description='Script para obtener URLs de Wayback Machine')
    parser.add_argument('-t', '--dominio', type=str, help='Especifica el dominio a buscar en Wayback Machine', required=True)
    parser.add_argument('-e', '--excluir', type=str, help='Especifica las extensiones para excluir, separadas por comas')
    parser.add_argument('-o', '--salida', type=str, help='Especifica el archivo para exportar las URLs válidas')
    parser.add_argument('-v', '--verificar', action='store_true', help='Verifica si las URL resultantes son accesibles')
    parser.add_argument('--subsitios', action='store_true', help='Incluir subdominios en la búsqueda')
    parser.add_argument('--intentos', type=int, default=3, help='Número de reintentos en caso de conexión fallida')

    args = parser.parse_args()

    if args.verificar and not args.salida:
        print(f"{Fore.RED}[!] Debes especificar un archivo de salida con -o cuando usas -v para guardar URLs.{Style.RESET_ALL}")
        return

    if args.subsitios:
        url = f"https://web.archive.org/cdx/search/cdx?url=*.{args.dominio}/*&output=txt&fl=original&collapse=urlkey&page=/"
    else:
        url = f"https://web.archive.org/cdx/search/cdx?url={args.dominio}/*&output=txt&fl=original&collapse=urlkey&page=/"

    reintentar = True
    intentos = 0
    respuesta = ""
    while reintentar and intentos <= args.intentos:
        respuesta, _, _ = conector(url)
        if not respuesta:
            reintentar = True
            intentos += 1
        else:
            reintentar = False
    if not respuesta:
        return

    lista_negra = set()
    urls_validas = set()
    urls_imprimidas = set()
    params_vistos = set()

    if args.excluir:
        if "," in args.excluir:
            lista_negra = {extension.strip() for extension in args.excluir.split(",")}
        else:
            lista_negra.add(args.excluir)

    if lista_negra:
        print(f"\u001b[31m[!] Las URL que contienen estas extensiones se excluirán: {lista_negra}\u001b[0m\n")
    else:
        print("[!] No hay extensiones para excluir.")

    contenido, _, headers = conector(f"http://{args.dominio}")
    print(f"Cabeceras válidas del dominio: {headers}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(procesar_url, url, lista_negra, args, urls_validas, urls_imprimidas, args.salida, params_vistos): url
            for url in set(respuesta.split())
        }
        for future in concurrent.futures.as_completed(future_to_url):
            pass

    # Resumen final
    print(f"\n{Fore.YELLOW}[*] Total URLs encontradas: {len(urls_imprimidas)}{Style.RESET_ALL}")
    if args.verificar:
        print(f"{Fore.YELLOW}[*] URLs que respondieron con códigos válidos: {len(urls_validas)}{Style.RESET_ALL}")

if __name__ == '__main__':
    principal()
