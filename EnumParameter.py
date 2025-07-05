import argparse
import aiohttp
import asyncio
import requests
import concurrent.futures
from urllib.parse import urlparse, parse_qs, urlunparse
from colorama import Fore, Style
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Colors:
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    RESET = Style.RESET_ALL

print(Fore.RED + """\n
    ______                      ____                                  __           
   / ____/___  __  ______ ___  / __ \\____ __________ _____ ___  ___  / /____  _____
  / __/ / __ \\/ / / / __ `__ \\/ /_/ / __ `/ ___/ __ `/ __ `__ \\/ _ \\/ __/ _ \\/ ___/
 / /___/ / / / /_/ / / / / / / ____/ /_/ / /  / /_/ / / / / / /  __/ /_/  __/ /    
/_____/_/ /_/\\__,_/_/ /_/ /_/_/    \\__,_/_/   \\__,_/_/ /_/ /_/\\___/\\__/\\___/_/     
                                                                                 
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

def should_skip_url(url):
    return any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.gif', '.css', '.woff', '.svg', '.ico', '.ttf', '.eot', '.mp4', '.mp3'])

async def fetch_wayback_urls(session, domain):
    print(f"{Colors.CYAN}[+] Buscando en Wayback para {domain}...{Colors.RESET}")
    url = f"https://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original&collapse=urlkey"
    urls = []
    try:
        async with session.get(url, timeout=20) as resp:
            data = await resp.json(content_type=None)
            for entry in data[1:]:
                if not should_skip_url(entry[0]):
                    urls.append(entry[0])
    except Exception as e:
        print(f"{Colors.YELLOW}[!] Error con Wayback para {domain}: {e}{Colors.RESET}")
    print(f"{Colors.GREEN}[+] URLs encontradas: {len(urls)}{Colors.RESET}")
    return urls

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
                return

            params_vistos.add(clave)

            url_modificada = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', parsed.query, ''))

            if args.verificar:
                if url_modificada not in urls_imprimidas:
                    urls_imprimidas.add(url_modificada)
                    contenido, status_code, headers = conector(url_modificada)
                    if status_code in {200, 301, 302, 401, 403, 500}:
                        urls_validas.add(url_modificada)
                        print(f"[{Fore.GREEN}+{Style.RESET_ALL}] {url_modificada} - Código: {status_code}")
                        if archivo_salida:
                            with open(archivo_salida, "a", encoding="utf-8") as file:
                                file.write(f"{url_modificada}\n")
            else:
                if url_modificada not in urls_imprimidas:
                    urls_imprimidas.add(url_modificada)
                    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] {url_modificada}")

async def main_async(args, lista_negra, urls_validas, urls_imprimidas, params_vistos):
    async with aiohttp.ClientSession(headers={'User-Agent': USER_AGENT}) as session:
        urls_wayback = await fetch_wayback_urls(session, args.dominio)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {
            executor.submit(procesar_url, url, lista_negra, args, urls_validas, urls_imprimidas, args.salida, params_vistos): url
            for url in set(urls_wayback)
        }
        for future in concurrent.futures.as_completed(future_to_url):
            pass

def principal():
    parser = argparse.ArgumentParser(description='Script para obtener URLs de Wayback Machine')
    parser.add_argument('-t', '--dominio', type=str, required=True, help='Dominio a buscar')
    parser.add_argument('-e', '--excluir', type=str, help='Extensiones a excluir separadas por comas')
    parser.add_argument('-o', '--salida', type=str, help='Archivo para exportar las URLs válidas')
    parser.add_argument('-v', '--verificar', action='store_true', help='Verifica si las URLs son accesibles')

    args = parser.parse_args()

    if args.verificar and not args.salida:
        print(f"{Colors.RED}[!] Debes especificar un archivo con -o cuando usas -v{Colors.RESET}")
        return

    lista_negra = set()
    if args.excluir:
        lista_negra = {ext.strip() for ext in args.excluir.split(',')}

    if lista_negra:
        print(f"{Colors.YELLOW}[!] Se excluirán URLs con estas extensiones: {lista_negra}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}[!] No se excluirán extensiones{Colors.RESET}")

    contenido, _, headers = conector(f"http://{args.dominio}")
    print(f"\n{Colors.GREEN}[*] Cabeceras del dominio: {headers}{Colors.RESET}\n")

    urls_validas = set()
    urls_imprimidas = set()
    params_vistos = set()

    asyncio.run(main_async(args, lista_negra, urls_validas, urls_imprimidas, params_vistos))

    print(f"\n{Colors.YELLOW}[*] Total URLs únicas: {len(urls_imprimidas)}{Colors.RESET}")
    if args.verificar:
        print(f"{Colors.YELLOW}[*] URLs válidas: {len(urls_validas)}{Colors.RESET}")

if __name__ == '__main__':
    principal()
