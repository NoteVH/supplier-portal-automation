"""
Módulo principal do bot de automação.

Contém as funções de navegação e execução do pagamento automático de despesas
no portal de fornecedores.
"""

import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from src.config import (
    PORTAL_URL,
    IMPLICIT_WAIT,
    DEFAULT_TIMEOUT,
    CONTAS,
)
from src.utils import normalize

# Localizadores compartilhados
LOCALIZADOR_BOTOES = (By.CSS_SELECTOR, ".action-button-options")
XPATH_CONFIRMACAO = "//button[contains(@class, 'btn-confirm-payment')]"


def criar_driver() -> webdriver.Chrome:
    """
    Cria e retorna uma instância configurada do ChromeDriver.

    Returns:
        webdriver.Chrome: instância do driver pronta para uso.
    """
    driver = webdriver.Chrome()
    driver.implicitly_wait(IMPLICIT_WAIT)
    return driver


def login(driver: webdriver.Chrome, user: str, password: str) -> None:
    """
    Realiza o login no portal com as credenciais fornecidas.

    Args:
        driver: Instância do Selenium WebDriver.
        user: Nome de usuário.
        password: Senha do usuário.
    """
    print("Iniciando login...")
    driver.get(PORTAL_URL)

    # Caso o campo de usuário não carregue, faz um refresh
    try:
        campo_usuario = driver.find_element(By.ID, "username_field")
    except NoSuchElementException:
        driver.refresh()
        campo_usuario = driver.find_element(By.ID, "username_field")

    campo_senha = driver.find_element(By.ID, "password_field")
    botao_login = driver.find_element(By.ID, "btn_login_submit")

    escolha_cg = Select(driver.find_element(By.ID, "company_select_id"))
    escolha_cg.select_by_index(1)

    campo_usuario.send_keys(user)
    campo_senha.send_keys(password)
    botao_login.click()
    print("Login enviado.")


def ir_financeiro(driver: webdriver.Chrome) -> None:
    """
    Navega pelo menu até a seção de despesas do financeiro.

    Args:
        driver: Instância do Selenium WebDriver.
    """
    print("Navegando para Financeiro")
    try:
        # Fecha modal irritante se aparecer
        try:
            botao_irritante = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "modal_notification_close_btn"))
            )
            botao_irritante.click()
        except Exception:
            pass

        link_financeiro = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Financeiro"))
        )
        link_financeiro.click()

        link_movimentacoes = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Movimentações"))
        )
        link_movimentacoes.click()

        link_despesas = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Despesas"))
        )
        link_despesas.click()

        WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.frame_to_be_available_and_switch_to_it(0)
        )
    except Exception as e:
        print(f"Erro ao navegar para o financeiro: {e}")


def pagar_despesa(
    driver: webdriver.Chrome,
    fornecedor_nome: str,
    data_despesa: str,
    data_pagamento: str,
) -> None:
    """
    Executa a rotina de pagamento para um determinado fornecedor.

    Para cada despesa listada na tabela, o script:
      1. Verifica se já foi paga
      2. Abre o menu de ações
      3. Clica em "Pagar"
      4. Identifica a conta contábil correta
      5. Preenche o formulário de pagamento
      6. Confirma o pagamento

    Args:
        driver: Instância do Selenium WebDriver.
        fornecedor_nome: Nome do fornecedor conforme aparece no sistema.
        data_despesa: Data de vencimento para filtrar (dd/mm/aaaa).
        data_pagamento: Data do pagamento (dd/mm/aaaa).
    """
    print(f"Iniciando rotina de pagamento para: {fornecedor_nome}")

    # Prepara lista ordenada de contas (da mais específica para a menos)
    lista_chaves = []
    for nome, valor in CONTAS.items():
        lista_chaves.append((nome, normalize(nome), valor))
    lista_chaves.sort(key=lambda t: len(t[1]), reverse=True)

    # Preencher filtro de pesquisa
    try:
        data_inicial = WebDriverWait(driver, DEFAULT_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "filter_start_date"))
        )
        data_final = driver.find_element(By.ID, "datafinal")

        data_inicial.clear()
        data_inicial.send_keys(data_despesa)
        data_final.clear()
        data_final.send_keys(data_despesa)

        selecionar_fornecedor = Select(driver.find_element(By.ID, "fornecedorId"))
        try:
            selecionar_fornecedor.select_by_visible_text(fornecedor_nome)
        except Exception:
            print(f"Aviso: Não achou '{fornecedor_nome}' exato.")

        botao_pesquisar = driver.find_element(By.ID, "btn_search_submit")
        botao_pesquisar.click()
        time.sleep(3)
    except Exception as e:
        print(f"Erro ao preencher o filtro de pesquisa: {e}")
        return

    # Loop para pagar as despesas
    i = 0
    while True:
        try:
            botoes_frescos = driver.find_elements(*LOCALIZADOR_BOTOES)
        except Exception:
            print("Erro ao listar botoes. recarregando a pagina")
            time.sleep(2)
            botoes_frescos = driver.find_elements(*LOCALIZADOR_BOTOES)

        if i >= len(botoes_frescos):
            print("--- Fim da lista de botões visíveis/carregados nesta página ---")
            break

        botao_fresco = botoes_frescos[i]

        # Rolagem até o botão
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'});",
                botao_fresco,
            )
            time.sleep(1)
        except Exception:
            pass

        # Verifica se a linha já está paga
        linha_texto = ""
        try:
            row_elem = botao_fresco.find_element(By.XPATH, "./ancestor::tr")
            linha_texto = row_elem.text or ""
            if "Pago" in linha_texto or "PAGO" in linha_texto:
                i += 1
                continue
        except Exception:
            linha_texto = ""

        try:
            bot_y = botao_fresco.location.get("y", None)
        except Exception:
            bot_y = None

        # Abre o menu de opções
        try:
            driver.execute_script("arguments[0].click();", botao_fresco)
        except Exception:
            try:
                botao_fresco.click()
            except Exception:
                i += 1
                continue

        time.sleep(2)

        # Procura o link "Pagar"
        link_de_pagar = None
        try:
            candidatos = [
                el
                for el in driver.find_elements(By.XPATH, "//a[normalize-space()='Pagar']")
                if el.is_displayed()
            ]
            if candidatos:
                if bot_y is not None:
                    candidatos.sort(key=lambda el: abs((el.location.get("y", 0)) - bot_y))
                melhor_candidato = candidatos[0]
                texto = melhor_candidato.get_attribute("innerText") or melhor_candidato.text
                if "Pagar" in texto:
                    link_de_pagar = melhor_candidato
        except Exception:
            link_de_pagar = None

        if not link_de_pagar:
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
            i += 1
            continue

        # Clica em "Pagar"
        try:
            driver.execute_script("arguments[0].click();", link_de_pagar)
        except Exception:
            link_de_pagar.click()

        # Identifica a conta no modal
        modal_text = ""
        try:
            modal_element = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "modal-content"))
            )
            modal_text = modal_element.text or ""
        except Exception:
            pass

        combined_raw = (linha_texto or "") + " " + modal_text
        normalized_combined = normalize(combined_raw)

        conta_valor = None
        for _orig, chave_norm, valor in lista_chaves:
            if chave_norm in normalized_combined:
                conta_valor = valor
                break

        if conta_valor is None:
            print(f"Item {i}: Conta não identificada. Pulando.")
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.5)
            except Exception:
                pass
            i += 1
            continue

        # Preenche o formulário de pagamento
        try:
            parcial = Select(driver.find_element(By.NAME, "partial_payment_option"))
            dt_input = driver.find_element(By.ID, "payment_date_input")
            conta_select = Select(driver.find_element(By.NAME, "account_id_select"))

            parcial.select_by_index(1)
            dt_input.clear()
            dt_input.send_keys(data_pagamento)
            conta_select.select_by_value(conta_valor)
        except Exception as erro:
            print(f"Erro ao preencher formulário: {erro}")
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
            i += 1
            continue

        # Confirma o pagamento
        try:
            botao_final = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, XPATH_CONFIRMACAO))
            )
            driver.execute_script("arguments[0].click();", botao_final)

            WebDriverWait(driver, 8).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".alert-success")) > 0
                or len(d.find_elements(By.CSS_SELECTOR, ".modal.in")) == 0
            )
            print(f"Item {i} PAGO com sucesso!")
        except Exception as erro:
            print(f"Erro ao finalizar pagamento do item {i}: {erro}")
            driver.execute_script("window.location.href='?status=error_reload'")
            try:
                WebDriverWait(driver, DEFAULT_TIMEOUT).until(
                    EC.presence_of_element_located(LOCALIZADOR_BOTOES)
                )
            except TimeoutException:
                break

        i += 1