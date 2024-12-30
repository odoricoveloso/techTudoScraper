import os
import time
import json
import random
import logging
import requests
from bs4 import BeautifulSoup
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pprint import pprint



# Função para configurar o logger
def configurar_logger(nome_logger, log_filename):
    logger = logging.getLogger(nome_logger)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d_%H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.info(f'Log iniciado em: {date.today()}')
    return logger



# Função para configurar o ChromeDriver
def configurar_chrome_driver():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--headless')
    logger.info('ChromeDriver configurado com sucesso.')
    return options



# Função para salvar os dados em um arquivo JSON
def salvar_json(dados, nome_arquivo):
    with open(os.path.join(os.getcwd(), nome_arquivo), encoding='utf-8', mode='w') as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)
    logger.info(f'Dados salvos em: {nome_arquivo}')



# Função para listar categorias de notícias
def listar_categorias():
    categorias = {}
    url = 'https://www.techtudo.com.br/sitemap.ghtml'
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', class_=lambda x: x and x.startswith('sitemap-item')):
            if link.get('href') is not None:
                categorias[link.get_text().strip().upper()] = link.get('href')
    logger.info(f'Quantidade de categorias encontradas: {len(categorias)}')
    return categorias



# Função para carregar mais notícias
def carregar_mais_noticias(driver, qtd_noticias):
    lista_noticias = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-type="materia"]'))
    )
    while len(lista_noticias) < qtd_noticias:
        logger.info(f'Carregando mais notícias... {len(lista_noticias)} de {qtd_noticias}')
        try:
            botao_carregar_mais = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class^="load-more"] a'))
            )
            driver.execute_script("arguments[0].click();", botao_carregar_mais)
            time.sleep(random.randint(3, 5))
            lista_noticias = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-type="materia"]'))
            )
            try:
                botao_carregar_mais = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class^="load-more"] a'))
                )
            except:
                logger.info('Não há mais notícias para carregar.')
                break
        except:
            logger.error('Erro ao carregar mais notícias')
            break



# Funçao para listar as notícias de uma categoria
def listar_noticias_categoria(categoria, categoria_url, qtd_noticias, chrome_options):
    logger.info(f'Listando notícias da categoria: {categoria}')
    noticias = {}
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(categoria_url)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class^="load-more"] a'))
        )
    carregar_mais_noticias(driver, qtd_noticias)
    
    lista_noticias = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-type="materia"]'))
        )
    logger.info(f'Quantidade de notícias encontradas: {len(lista_noticias)}')

    logger.info('Capturando dados das notícias...')
    for noticia in lista_noticias[:qtd_noticias]:
        time.sleep(random.randint(3, 5))
        try:
            id_noticia = noticia.find_element(By.CSS_SELECTOR, 'div[class^="feed-post"]').get_attribute('id')
            titulo = noticia.find_element(By.CSS_SELECTOR, 'h2 a').text.strip()
            link = noticia.find_element(By.CSS_SELECTOR, 'h2 a').get_attribute('href')
            resumo = noticia.find_element(By.CSS_SELECTOR, 'p[class="feed-post-body-resumo"]').text.strip()
            imagem = noticia.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
            noticias[id_noticia] = {
                'titulo': titulo,
                'resumo': resumo,
                'link': link,
                'imagem': imagem
                }
            time.sleep(random.randint(1, 3))
        except:
            print(f'Erro ao capturar notícia: {noticia}')
    driver.quit()
    return noticias



# Execução do script
if __name__ == '__main__':
    
    logger = configurar_logger('meu_logger', os.path.join(os.getcwd(), 'techTudoScraper.log'))
    chrome_options = configurar_chrome_driver()
    categorias = listar_categorias()
    for i, (categoria, url) in enumerate(categorias.items(), start=1):
        print(f'{i} - {categoria}')
    
    try:
        categoria_escolhida_index = int(input('Escolha o número de uma categoria: '))
        categoria_escolhida = list(categorias.keys())[categoria_escolhida_index - 1]
        if categoria_escolhida:
            qtd_noticias = int(input('Quantidade de notícias a serem capturadas: '))
            noticias = listar_noticias_categoria(categoria_escolhida, categorias[categoria_escolhida], qtd_noticias, chrome_options)
            salvar_json(noticias, f'noticias_{categoria_escolhida}.json')
        else:
            logger.error("Categoria escolhida não é válida.")
    except (IndexError, ValueError):
        logger.error("Número de categoria inválido.")