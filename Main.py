
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
import unicodedata
import time

driver = webdriver.Chrome()
driver.implicitly_wait(50) # caso demore muito pra carregar

def login(user, password):
    print("Iniciando login...")
    # URL CENSURADA
    driver.get("http://internal-portal.company.com/default.asp")
    #Eliminar erro de as vezes nao carregar por algum motivo
    try:
        campoUsuario = driver.find_element(By.ID, 'username_field')
    except NoSuchElementException:
        driver.refresh()
        campoUsuario = driver.find_element(By.ID, 'username_field')


    campoSenhaUsuario = driver.find_element(By.ID, 'password_field')
    botaoLogin = driver.find_element(By.ID, 'btn_login_submit')
    
    escolhaCG = Select(driver.find_element(By.ID, 'company_select_id'))
    escolhaCG.select_by_index(1)


    campoUsuario.send_keys(user)
    campoSenhaUsuario.send_keys(password)
    botaoLogin.click()
    print("Login enviado.")

def irFinanceiro():
    print("Navegando para Financeiro")
    try:
        # Tenta fechar botao se aparecer
        try:
            
            botaoIrritante = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'modal_notification_close_btn')))
            botaoIrritante.click()
        except:
            pass

        link_financeiro = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Financeiro")))
        link_financeiro.click()
        
        link_movimentacoes = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Movimentações")))
        link_movimentacoes.click()
        
        link_despesas = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Despesas")))
        link_despesas.click()

        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it(0))
    except Exception as e:
        print(f"Erro ao navegar para o financeiro: {e}")

def pagardespesa(fornecedorNome, dataDespesa, dataPagamento):
    print(f"Iniciando rotina de pagamento para: {fornecedorNome}")
    
    # CGS da empresa - valores fictícios colocados
    dicionarioValoresDeContas = {
        "supplier_a_contract_1": "29",
        "supplier_b_contract_2": "30",
        "internal_resources": "31"
    }
    
    # Função auxiliar de normalização
    def normalize(texto_feio):
        return unicodedata.normalize('NFKD', texto_feio or "").encode('ASCII', 'ignore').decode().lower().strip()
    
    listachaves = []
    for nome, valor in dicionarioValoresDeContas.items():
        listachaves.append((nome, normalize(nome), valor))
    listachaves.sort(key=lambda t: len(t[1]), reverse=True)
    
    #pesquisar as despesas
    try:
    
        dataInicial = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'filter_start_date')))
        dataFinal = driver.find_element(By.ID, 'datafinal')
        
        dataInicial.clear()
        dataInicial.send_keys(dataDespesa)
        dataFinal.clear()
        dataFinal.send_keys(dataDespesa)
        
    
        SelecionarFornecedor = Select(driver.find_element(By.ID, 'fornecedorId'))
        try:
            SelecionarFornecedor.select_by_visible_text(fornecedorNome)
        except:
            print(f"Aviso: Não achou '{fornecedorNome}' exato.")
        
        botaoPesquisar = driver.find_element(By.ID, 'btn_search_submit')
        botaoPesquisar.click()
        time.sleep(3) 
        
    except Exception as e:
        print(f"Erro ao preencher o filtro de pesquisa: {e}")
        return


    LOCALIZADOR_BOTOES = (By.CSS_SELECTOR, ".action-button-options")

    # loop pra pagar as despesas
    i = 0
    while True:
        try:
            botoesFrescos = driver.find_elements(*LOCALIZADOR_BOTOES)
        except:
            print("Erro ao listar botoes. recarregando a pagina")
            time.sleep(2)
            botoesFrescos = driver.find_elements(*LOCALIZADOR_BOTOES)

        if i >= len(botoesFrescos):
            print("--- Fim da lista de botões visíveis/carregados nesta página ---")
            break

        botao_fresco = botoesFrescos[i]
        # tentativa 1
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center', inline: 'center'});", botao_fresco)
            time.sleep(1)
        except Exception:
            pass

        # tentativa 2
        linha_texto = ""
        try:
            row_elem = botao_fresco.find_element(By.XPATH, "./ancestor::tr")
            linha_texto = row_elem.text or ""
            
            if "Pago" in linha_texto or "PAGO" in linha_texto:
                i += 1
                continue
        except Exception:
            row_text = ""

        try:
            bot_y = botao_fresco.location.get('y', None)
        except Exception:
            bot_y = None

        # --- Abre o menu/opções ---
        try:
            driver.execute_script("arguments[0].click();", botao_fresco)
        except Exception:
            try:
                botao_fresco.click()
            except:
                i += 1
                continue
        
        time.sleep(2)

        #Procurar o link pra pagar
        linkDePagar = None
        try:
            candidatos = [elemento for elemento in driver.find_elements(By.XPATH, "//a[normalize-space()='Pagar']") if elemento.is_displayed()]
            
            if candidatos:
                if bot_y is not None:
                    candidatos.sort(key=lambda el: abs((el.location.get('y', 0)) - bot_y))
                
                melhor_candidato = candidatos[0]
                
                txt = melhor_candidato.get_attribute("innerText") or melhor_candidato.text
                if "Pagar" in txt:
                    linkDePagar = melhor_candidato
            
        except Exception:
             linkDePagar = None

        if not linkDePagar:
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except:
                pass
            i += 1
            continue

        #Clica em Pagar
        try:
            driver.execute_script("arguments[0].click();", linkDePagar)
        except Exception:
            linkDePagar.click()

        # Identifica a Conta no Modal
        modal_text = ""
        try:
            
            modal_element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, "modal-content")))
            modal_text = modal_element.text or ""
        except Exception:
            pass

        combined_raw = (row_text or "") + " " + modal_text
        normalized_combined = normalize(combined_raw)

        conta_valor = None
        for orig, chave_norm, valor in listachaves:
            if chave_norm in normalized_combined:
                conta_valor = valor
                break

        if conta_valor is None:
            print(f"Item {i}: Conta não identificada. Pulando.")
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.5)
            except:
                pass
            i += 1
            continue

        # --- Preenche o Formulário de Pagamento ---
        try:

            parcial = Select(driver.find_element(By.NAME, "partial_payment_option"))
            dt_input = driver.find_element(By.ID, "payment_date_input")
            conta_select = Select(driver.find_element(By.NAME, "account_id_select"))
            
            parcial.select_by_index(1)
            dt_input.clear()
            dt_input.send_keys(dataPagamento)
            conta_select.select_by_value(conta_valor)
            
        except Exception as erro:
            print(f"Erro ao preencher formulário: {erro}")
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except:
                pass
            i += 1
            continue

        try:
            xpath_confirmacao = "//button[contains(@class, 'btn-confirm-payment')]"
            
            botao_final = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath_confirmacao)))
            
            driver.execute_script("arguments[0].click();", botao_final)
            
            WebDriverWait(driver, 8).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, ".alert-success")) > 0 or len(d.find_elements(By.CSS_SELECTOR, ".modal.in")) == 0
            )
            print(f"Item {i} PAGO com sucesso!")
            
        except Exception as erro:
            print(f"Erro ao finalizar pagamento do item {i}: {erro}")
            driver.execute_script("window.location.href='?status=error_reload'") # URL parameter censurado
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located(LOCALIZADOR_BOTOES))
            except:
                break

        i += 1

# --- Execução Principal ---
if __name__ == "__main__":
    print("--- SISTEMA DE PAGAMENTO AUTOMÁTICO ---")
    print("Qual o fornecedor?")
    print("1 = MINISTERIO DA FAZENDA") 
    print("2 = MINISTERIO DO TRABALHO") 
    print("3 = TODOS FORNECEDORES")
    forn_opcao = input("Opção: ")
    
    if forn_opcao == "1":
        fornecedorNome = "MINISTERIO DA FAZENDA  -" #é como é no sistema
    elif forn_opcao == "2":
        fornecedorNome = "MINISTERIO DO TRABALHO  -"
    else:
        fornecedorNome = "Todos"

    user = input("Qual seu usuario? ")
    password = input("Qual sua senha? ")
    dataDespesa = input("Qual a data do vencimento (dd/mm/aaaa)? ")
    dataPagamento = input("Qual a data do pagamento (dd/mm/aaaa)? ")

    login(user, password)
    irFinanceiro()
    pagardespesa(fornecedorNome, dataDespesa, dataPagamento)

    input("Processo concluído. Pressione Enter para fechar o navegador.")
    driver.quit()